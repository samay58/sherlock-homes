import './ToggleChip.css'

interface ToggleChipProps {
  label: string
  active?: boolean
  disabled?: boolean
  onClick?: () => void
}

export function ToggleChip({ label, active = false, disabled = false, onClick }: ToggleChipProps) {
  const handleClick = () => {
    if (disabled) return
    onClick?.()
  }

  return (
    <button
      type="button"
      className={`toggle-chip ${active ? 'toggle-chip--active' : ''} ${disabled ? 'toggle-chip--disabled' : ''}`}
      onClick={handleClick}
      disabled={disabled}
      aria-pressed={active}
    >
      {active && <span className="toggle-dot"></span>}
      {label}
    </button>
  )
}
