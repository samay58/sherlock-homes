import './VibeSelector.css'

interface VibeSelectorProps {
  selected: string | null
  onChange: (vibe: string | null) => void
}

const vibes = [
  {
    id: 'light_chaser',
    name: 'Light Chaser',
    icon: '☀️',
    tagline: 'South-facing, big windows, views for days',
  },
  {
    id: 'urban_professional',
    name: 'Urban Pro',
    icon: '🏙️',
    tagline: 'Walk to work, nightlife-ready',
  },
  {
    id: 'deal_hunter',
    name: 'Deal Hunter',
    icon: '💰',
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
          >
            <span className="vibe-icon">{vibe.icon}</span>
            <span className="vibe-name">{vibe.name}</span>
            <span className="vibe-tagline">{vibe.tagline}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
