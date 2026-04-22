"""
PromptBuilder — profession-aware prompt construction for AI feedback.

Design principles:
- Each profession has a deep, behaviorally-specific persona
- System prompt defines WHO the AI is and HOW it reasons
- User prompt provides the full decision context with metric arc
- JSON output schema is embedded in the system prompt for reliable parsing
- Language adapts to the scenario narrative language
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecisionHistoryItem:
    step_key: str
    step_title: str
    option_key: str
    option_label: str
    metrics_before: dict[str, float]
    metrics_after: dict[str, float]


@dataclass
class PromptContext:
    profession_slug: str
    step_key: str
    step_title: str
    step_narrative: str
    step_context_data: dict[str, Any]
    option_chosen_key: str
    option_chosen_label: str
    option_description: str | None
    # All options shown to the user (for alternative path analysis)
    all_options: list[dict]
    metrics_before: dict[str, float]
    metrics_after: dict[str, float]
    effects_applied: list[dict]
    # Full session arc (most recent N decisions)
    session_history: list[DecisionHistoryItem] = field(default_factory=list)
    # RAG docs injected by ContextAssembler
    retrieved_context: list[str] = field(default_factory=list)
    # Current session state flags (for context, not exposed as metrics)
    state_flags: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────
# PROFESSION PERSONAS  (system prompt base)
# ─────────────────────────────────────────────────────────

_PERSONAS: dict[str, str] = {

    "software_engineer": """\
You are Alex Rivera — a staff engineer and former engineering manager with 18 years building \
distributed systems at scale (banks, e-commerce, healthcare infrastructure). You've been the \
on-call engineer who rolled back production at 3 AM, the architect who had to tell the CTO \
their microservices plan would fail, and the senior who had to navigate a toxic code review \
situation. You give feedback like a trusted colleague debriefing after the incident — direct, \
specific, no ego. You care about the engineering culture as much as the technical outcome. \
You know that the best engineers are force multipliers for their teams, not lone heroes. \
You reference real engineering concepts naturally: incident management, technical debt, \
psychological safety, blameless post-mortems, Conway's Law.""",

    "doctor": """\
You are Dr. Amara Osei — a consultant physician with 22 years across emergency medicine, \
internal medicine, and clinical ethics. You've made impossible triage calls, delivered \
terminal diagnoses, and navigated the gap between what medicine can do and what patients \
want. You mentor residents like a thoughtful attending who respects their autonomy while \
being honest about what the evidence says. You never moralize — you analyze. Your feedback \
blends clinical precision with human compassion. You reference real clinical frameworks: \
evidence-based medicine, shared decision-making, the four principles of bioethics \
(autonomy, beneficence, non-maleficence, justice), triage protocols.""",

    "lawyer": """\
You are Margaret Chen — a senior partner at a litigation firm with 30 years of courtroom \
experience and a reputation for navigating ethical grey zones without compromising her \
integrity or her clients' interests. You've cross-examined witnesses, negotiated \
multi-million-dollar settlements, and advised clients whose interests conflicted with \
what you knew was right. Your feedback is precise, strategic, and occasionally uncomfortable. \
You don't pretend the law is simple. You reference real legal concepts: attorney-client \
privilege, duty of candor, zealous representation within ethical limits, proportionality \
in evidence requests, the difference between aggressive advocacy and misconduct.""",

    "business_manager": """\
You are David Kowalski — a former COO and now executive coach who has run three companies \
through growth, crisis, acquisition, and one near-bankruptcy. You've had to lay people off, \
cancel products the team loved, and tell a board things they didn't want to hear. You measure \
leadership not by the decisions themselves but by how they're made and communicated. Your \
feedback is honest about the human cost of business decisions. You reference real management \
frameworks: psychological safety, double-loop learning, radical candor, OKRs, the five \
dysfunctions of a team, crisis communication principles.""",
}

_DEFAULT_PERSONA = """\
You are a senior professional mentor with decades of experience in your field. \
You give honest, specific, mentoring feedback based on the decisions made \
in this professional simulation. Your goal is to help the trainee grow, not just validate them."""


# ─────────────────────────────────────────────────────────
# JSON OUTPUT SCHEMA  (embedded in system prompt)
# ─────────────────────────────────────────────────────────

_JSON_SCHEMA_INSTRUCTION = """

## Your output format

Respond ONLY with a JSON object — no prose before or after. Schema:

```json
{
  "feedback": "3-5 sentences of honest, mentoring narrative about this specific decision. Reference what actually happened (metrics, situation details). Be specific, not generic.",
  "key_insight": "One crisp sentence capturing the most important lesson from this decision.",
  "coaching_question": "One reflective question that will help the trainee think deeper. Not rhetorical — something they could actually journal or discuss.",
  "consequence_analysis": "1-2 sentences projecting: if this decision pattern continues, where does it lead? Both positive (if good decision) or cautionary (if risky).",
  "alternative_path": "1 sentence on what the main alternative would have led to differently. Only include if it adds genuine insight.",
  "tone": "one of: encouraging | critical | analytical | neutral"
}
```

Tone guide:
- "encouraging": decision was strong, reinforce the reasoning
- "critical": decision had real risks or missed something important — be honest but constructive
- "analytical": complex tradeoffs, explore nuance
- "neutral": exposition or information-gathering step

Language rule: detect the language of the scenario narrative and respond in that same language.
"""

# ─────────────────────────────────────────────────────────
# METRIC DISPLAY NAMES  (human-readable in prompts)
# ─────────────────────────────────────────────────────────

_METRIC_LABELS: dict[str, dict[str, str]] = {
    "software_engineer": {
        "risk": "Production Risk",
        "reputation": "Engineering Reputation",
        "team_morale": "Team Morale",
        "score": "Performance Score",
    },
    "doctor": {
        "patient_stability": "Patient Stability",
        "diagnosis_accuracy": "Diagnostic Confidence",
        "team_trust": "Team Trust",
        "score": "Performance Score",
    },
    "lawyer": {
        "case_strength": "Case Strength",
        "client_trust": "Client Trust",
        "court_reputation": "Court Reputation",
        "score": "Performance Score",
    },
    "business_manager": {
        "company_health": "Company Health",
        "team_morale": "Team Morale",
        "stakeholder_trust": "Stakeholder Trust",
        "score": "Performance Score",
    },
}


class PromptBuilder:

    def build_system_prompt(self, profession_slug: str) -> str:
        persona = _PERSONAS.get(profession_slug, _DEFAULT_PERSONA)
        return persona + _JSON_SCHEMA_INSTRUCTION

    def build_user_prompt(self, ctx: PromptContext) -> str:
        parts: list[str] = []

        # ── Situation ────────────────────────────────────
        parts.append(f"## Scenario Step: {ctx.step_title}")
        parts.append(f"\n{ctx.step_narrative}")

        if ctx.step_context_data:
            ctx_lines = [f"  {k}: {v}" for k, v in ctx.step_context_data.items()]
            parts.append("\n**Situation facts:**\n" + "\n".join(ctx_lines))

        # ── Session arc (history) ─────────────────────────
        if ctx.session_history:
            parts.append("\n## Decision History (this session)")
            labels = _METRIC_LABELS.get(ctx.profession_slug, {})
            for h in ctx.session_history[-5:]:
                parts.append(f"- **{h.step_title}**: chose \"{h.option_label}\"")
            # Show metric trajectory from first decision to now
            if len(ctx.session_history) >= 2:
                first = ctx.session_history[0].metrics_before
                current = ctx.metrics_before
                trajectory_lines = []
                for k in first:
                    label = labels.get(k, k)
                    delta = current.get(k, 0) - first.get(k, 0)
                    if abs(delta) >= 1:
                        sign = "+" if delta > 0 else ""
                        trajectory_lines.append(f"  {label}: {first[k]:.0f} → {current.get(k, 0):.0f} ({sign}{delta:.0f})")
                if trajectory_lines:
                    parts.append("**Session trajectory so far:**\n" + "\n".join(trajectory_lines))

        # ── RAG context ───────────────────────────────────
        if ctx.retrieved_context:
            parts.append("\n## Relevant Professional Knowledge")
            for i, doc in enumerate(ctx.retrieved_context[:3], 1):
                parts.append(f"{i}. {doc}")

        # ── The decision ──────────────────────────────────
        parts.append(f"\n## Decision Made")
        parts.append(f"**Chosen:** \"{ctx.option_chosen_label}\"")
        if ctx.option_description:
            parts.append(f"*({ctx.option_description})*")

        # Show the other options considered (for alternative_path analysis)
        other_opts = [o for o in ctx.all_options if o.get("option_key") != ctx.option_chosen_key]
        if other_opts:
            opt_strs = [f"\"{o.get('label', o.get('option_key'))}\"" for o in other_opts[:2]]
            parts.append(f"**Other options available:** {', '.join(opt_strs)}")

        # ── Metric impact ─────────────────────────────────
        metric_lines = self._format_metric_impact(
            ctx.metrics_before, ctx.metrics_after, ctx.profession_slug
        )
        if metric_lines:
            parts.append(f"\n## Impact\n{metric_lines}")

        # ── Active state flags (domain context) ──────────
        active_flags = {k: v for k, v in ctx.state_flags.items() if v is True}
        if active_flags:
            flag_str = ", ".join(active_flags.keys())
            parts.append(f"\n**Active situation flags:** {flag_str}")

        parts.append("\nPlease provide your feedback as JSON.")
        return "\n".join(parts)

    def _format_metric_impact(
        self,
        before: dict[str, float],
        after: dict[str, float],
        profession_slug: str,
    ) -> str:
        labels = _METRIC_LABELS.get(profession_slug, {})
        lines = []
        for key in sorted(set(before) | set(after)):
            if key == "score":
                continue  # Score is derivative — not meaningful to show
            b = before.get(key, 0)
            a = after.get(key, 0)
            delta = a - b
            if abs(delta) < 0.5:
                continue
            label = labels.get(key, key.replace("_", " ").title())
            sign = "+" if delta > 0 else ""
            direction = "↑" if delta > 0 else "↓"
            lines.append(f"  {direction} **{label}**: {b:.0f} → {a:.0f} ({sign}{delta:.0f})")
        return "\n".join(lines) if lines else "  No significant metric changes."
