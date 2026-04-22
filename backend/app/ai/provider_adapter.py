from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class StructuredFeedback:
    """
    Structured AI feedback — parsed from JSON response.
    All fields have sensible defaults so partial JSON never crashes.
    """
    feedback: str                  # 3-5 sentence mentoring narrative
    key_insight: str               # 1-sentence core lesson
    coaching_question: str         # 1 reflective question
    consequence_analysis: str      # Short projection: "if you keep this pattern..."
    tone: str                      # encouraging | critical | analytical | neutral
    alternative_path: str = ""     # Brief note on the road not taken (optional)


@dataclass
class FeedbackResult:
    structured: StructuredFeedback
    model: str
    prompt_version: str
    latency_ms: int
    raw_text: str = ""             # Full raw LLM output for debugging/eval

    # Convenience passthrough
    @property
    def text(self) -> str:
        return self.structured.feedback

    @property
    def tone(self) -> str:
        return self.structured.tone

    @property
    def key_insight(self) -> str:
        return self.structured.key_insight

    @property
    def coaching_question(self) -> str:
        return self.structured.coaching_question

    @property
    def consequence_analysis(self) -> str:
        return self.structured.consequence_analysis


class AIProvider(ABC):

    @abstractmethod
    async def generate_feedback(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 700,
    ) -> FeedbackResult:
        ...

    @abstractmethod
    async def generate_feedback_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 700,
    ):
        """Async generator yielding text chunks."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
