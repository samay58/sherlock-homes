import './VibeSelector.css'

interface VibeSelectorProps {
  selected: string | null
  onChange: (vibe: string | null) => void
}

const SunIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
  </svg>
)

const BuildingsIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="4" y="2" width="16" height="20" rx="2" />
    <path d="M9 22v-4h6v4M8 6h.01M16 6h.01M12 6h.01M12 10h.01M8 10h.01M16 10h.01M12 14h.01M8 14h.01M16 14h.01" />
  </svg>
)

const TagIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z" />
    <path d="M7 7h.01" />
  </svg>
)

const vibes = [
  {
    id: 'light_chaser',
    name: 'Light Chaser',
    Icon: SunIcon,
    tagline: 'South-facing, big windows, views for days',
  },
  {
    id: 'urban_professional',
    name: 'Urban Pro',
    Icon: BuildingsIcon,
    tagline: 'Walk to work, nightlife-ready',
  },
  {
    id: 'deal_hunter',
    name: 'Deal Hunter',
    Icon: TagIcon,
    tagline: 'Price drops, motivated sellers',
  },
]

export function VibeSelector({ selected, onChange }: VibeSelectorProps) {
  const selectVibe = (vibeId: string) => {
    const newValue = selected === vibeId ? null : vibeId
    onChange(newValue)
  }

  return (
    <div className="vibe-selector">
      <span className="vibe-label">SORT BY VIBE</span>
      <div className="vibe-cards">
        {vibes.map((vibe) => (
          <button
            key={vibe.id}
            type="button"
            className={`vibe-card ${selected === vibe.id ? 'vibe-card--active' : ''}`}
            onClick={() => selectVibe(vibe.id)}
            aria-pressed={selected === vibe.id}
          >
            <span className="vibe-icon" role="img" aria-label={vibe.name}><vibe.Icon /></span>
            <span className="vibe-name">{vibe.name}</span>
            <span className="vibe-tagline">{vibe.tagline}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
