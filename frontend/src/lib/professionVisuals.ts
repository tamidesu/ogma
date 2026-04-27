export const STATUS_CONFIG = {
  stable:   { color: '#10b981', label: 'Тұрақты',   pulse: false },
  worried:  { color: '#f59e0b', label: 'Алаңдаулы', pulse: true  },
  active:   { color: '#3b82f6', label: 'Белсенді',  pulse: true  },
  panic:    { color: '#ef4444', label: 'Дүрбеліс!', pulse: true  },
  critical: { color: '#ef4444', label: 'Қауіпті!',  pulse: true  },
  positive: { color: '#10b981', label: 'Жақсы',     pulse: false },
  relieved: { color: '#10b981', label: 'Жеңілдеді', pulse: false },
  watching: { color: '#7c6fa8', label: 'Бақылауда', pulse: false },
  ready:    { color: '#3b82f6', label: 'Дайын',     pulse: false },
  dead:     { color: '#4a4065', label: '...',        pulse: false },
} as const

export type CharacterStatus = keyof typeof STATUS_CONFIG

export interface ProfessionCharacter {
  id: string
  name: string
  role: string
  avatar: string
  initStatus: CharacterStatus
  statusImages?: Partial<Record<CharacterStatus, string>>
}

export interface ProfessionVisuals {
  image: string
  imageFilter?: string
  gradient: string
  accent: string
  tagline: string
  skills: { name: string; score: number }[]
  preview: string[]
  avgTime: string
  completions: string
  rating: number
  characters: ProfessionCharacter[]
}

const MAP: Record<string, ProfessionVisuals> = {
  doctor: {
    image: '/images/doctor_bg.png',
    gradient: 'linear-gradient(135deg,#7c3aed 0%,#06b6d4 100%)',
    accent: '#06b6d4',
    tagline: 'Өмір мен өлім арасындағы шешімдер',
    skills: [
      { name: 'Клиникалық ойлау', score: 85 },
      { name: 'Диагностика', score: 78 },
      { name: 'Науқаспен қарым-қатынас', score: 72 },
      { name: 'Стрессті басқару', score: 65 },
      { name: 'Уақытты пайдалану', score: 80 },
    ],
    preview: ['Жедел жағдай диагностикасы', 'Операция жоспарлау', 'Науқасқа хабар беру'],
    avgTime: '15 мин', completions: '2,840', rating: 4.9,
    characters: [
      {
        id: 'patient', name: 'Дәрігер', role: 'Сіздің кейіпкеріңіз', avatar: '👨‍⚕️', initStatus: 'watching',
        statusImages: {
          stable:   '/images/doctor/ok.png',
          positive: '/images/doctor/like.png',
          relieved: '/images/doctor/like.png',
          ready:    '/images/doctor/ok.png',
          watching: '/images/doctor/thinking.png',
          active:   '/images/doctor/indignation.png',
          worried:  '/images/doctor/disapproval.png',
          panic:    '/images/doctor/rejection.png',
          critical: '/images/doctor/scary.png',
          dead:     '/images/doctor/scary.png',
        },
      },
      { id: 'nurse',  name: 'Медбике',       role: 'Медицина персоналы', avatar: '👩‍⚕️', initStatus: 'ready'    },
      { id: 'chief',  name: 'Проф. Дәрігер', role: 'Кардиология бастығы', avatar: '🧑‍⚕️', initStatus: 'watching' },
    ],
  },

  lawyer: {
    image: 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=900&q=85&fit=crop',
    imageFilter: 'brightness(0.45) saturate(1.8) hue-rotate(240deg)',
    gradient: 'linear-gradient(135deg,#7c3aed 0%,#f59e0b 100%)',
    accent: '#f59e0b',
    tagline: 'Әділдік пен стратегия арасында',
    skills: [
      { name: 'Заңды талдау', score: 90 },
      { name: 'Келіссөз жүргізу', score: 82 },
      { name: 'Дәлелдеу', score: 76 },
      { name: 'Клиентпен жұмыс', score: 88 },
      { name: 'Стратегиялық ойлау', score: 74 },
    ],
    preview: ['Сот процесіне дайындық', 'Келісімшартты талдау', 'Дауды шешу'],
    avgTime: '20 мин', completions: '1,290', rating: 4.8,
    characters: [
      { id: 'client',   name: 'Болат Сейтов',   role: 'Клиент (айыпталушы)', avatar: '😰', initStatus: 'worried'  },
      { id: 'judge',    name: 'Судья Аманова',  role: 'Судья',               avatar: '⚖️', initStatus: 'watching' },
      { id: 'opponent', name: 'Прокурор Нұров', role: 'Қарсы жақ',           avatar: '😤', initStatus: 'active'   },
    ],
  },

  business_manager: {
    image: 'https://images.unsplash.com/photo-1552664730-d307ca884978?w=900&q=85&fit=crop',
    imageFilter: 'brightness(0.45) saturate(1.8) hue-rotate(120deg)',
    gradient: 'linear-gradient(135deg,#7c3aed 0%,#10b981 100%)',
    accent: '#10b981',
    tagline: 'Командаңызды жаңа деңгейге жеткізіңіз',
    skills: [
      { name: 'Команданы басқару', score: 88 },
      { name: 'Стратегиялық жоспарлау', score: 80 },
      { name: 'Бюджеттеу', score: 70 },
      { name: 'Коммуникация', score: 92 },
      { name: 'Шешім қабылдау', score: 85 },
    ],
    preview: ['Дағдарысты басқару', 'Жаңа жобаны іске қосу', 'Команда конфликтісі'],
    avgTime: '18 мин', completions: '3,150', rating: 4.7,
    characters: [
      { id: 'dev',  name: 'Тимур (Senior Dev)', role: 'Кетуге ниетті қызметкер', avatar: '😤', initStatus: 'worried' },
      { id: 'ceo',  name: 'Асель, CEO',          role: 'Жалпы директор',          avatar: '😰', initStatus: 'panic'   },
      { id: 'team', name: 'Команда',              role: '5 адам',                  avatar: '👥', initStatus: 'worried' },
    ],
  },

  software_engineer: {
    image: '/images/programmer_bg.png',
    gradient: 'linear-gradient(135deg,#7c3aed 0%,#3b82f6 100%)',
    accent: '#3b82f6',
    tagline: 'Код — сіздің шешіміңіз',
    skills: [
      { name: 'Архитектуралық шешімдер', score: 86 },
      { name: 'Debugging', score: 91 },
      { name: 'Code review', score: 78 },
      { name: 'Командалық жұмыс', score: 82 },
      { name: 'Техникалық борыш', score: 68 },
    ],
    preview: ['Продакшн дағдарысы', 'Архитектура таңдау', 'Техникалық пікірталас'],
    avgTime: '25 мин', completions: '4,200', rating: 4.9,
    characters: [
      { id: 'cto',      name: 'Арман, CTO',       role: 'Техника директоры', avatar: '😤', initStatus: 'panic'   },
      { id: 'devops',   name: 'Санжар DevOps',     role: 'Инфраструктура',   avatar: '🧑‍💻', initStatus: 'worried' },
      { id: 'customer', name: 'Enterprise клиент', role: '$2M жоба иесі',    avatar: '😰', initStatus: 'worried' },
    ],
  },
}

function defaultVisuals(color?: string | null): ProfessionVisuals {
  return {
    image: 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=900&q=85&fit=crop',
    gradient: `linear-gradient(135deg,#7c3aed,${color || '#e879f9'})`,
    accent: color || '#e879f9',
    tagline: 'Кәсіби дағдыларыңызды дамытыңыз',
    skills: [
      { name: 'Шешім қабылдау', score: 80 },
      { name: 'Коммуникация', score: 75 },
      { name: 'Аналитика', score: 70 },
      { name: 'Стрессті басқару', score: 65 },
    ],
    preview: ['Жағдайды бағалау', 'Шешім қабылдау', 'Нәтижені талдау'],
    avgTime: '15 мин', completions: '1,000+', rating: 4.7,
    characters: [
      { id: 'partner', name: 'Серіктес',  role: 'Команда мүшесі',   avatar: '👤', initStatus: 'watching' },
      { id: 'manager', name: 'Менеджер', role: 'Жетекші',           avatar: '👔', initStatus: 'watching' },
      { id: 'client',  name: 'Клиент',   role: 'Тапсырыс беруші',  avatar: '🤝', initStatus: 'worried'  },
    ],
  }
}

export function getVisuals(
  profession: { slug?: string | null; id?: string | null; color_hex?: string | null } | null | undefined,
): ProfessionVisuals {
  if (!profession) return defaultVisuals()
  const key = profession.slug ?? profession.id ?? ''
  return MAP[key] ?? defaultVisuals(profession.color_hex)
}

/** Derive a CharacterStatus from a normalised step_score (0–1). */
export function statusFromScore(score: number): CharacterStatus {
  if (score >= 0.8) return 'positive'
  if (score >= 0.6) return 'stable'
  if (score >= 0.4) return 'worried'
  return 'panic'
}
