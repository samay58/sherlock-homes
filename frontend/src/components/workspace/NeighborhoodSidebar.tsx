import type { SortOption, FilterState } from './WorkspaceView'
import './NeighborhoodSidebar.css'

interface NeighborhoodSidebarProps {
  neighborhoodCounts: Map<string, number>
  totalCount: number
  selectedNeighborhood: string | null
  onSelectNeighborhood: (hood: string | null) => void
  sortBy: SortOption
  onSortChange: (sort: SortOption) => void
  minScore: number
  onMinScoreChange: (score: number) => void
  filters: FilterState
  onToggleFilter: (key: keyof FilterState) => void
  isVisible: boolean
  onClose: () => void
}

const FILTER_OPTIONS: { key: keyof FilterState; label: string }[] = [
  { key: 'hasNaturalLight', label: 'Natural Light' },
  { key: 'hasOutdoorSpace', label: 'Outdoor Space' },
  { key: 'quietLocation', label: 'Quiet Location' },
  { key: 'priceReduced', label: 'Price Reduced' },
]

export function NeighborhoodSidebar({
  neighborhoodCounts,
  totalCount,
  selectedNeighborhood,
  onSelectNeighborhood,
  sortBy,
  onSortChange,
  minScore,
  onMinScoreChange,
  filters,
  onToggleFilter,
  isVisible,
  onClose,
}: NeighborhoodSidebarProps) {
  const sortedHoods = Array.from(neighborhoodCounts.entries()).sort((a, b) => b[1] - a[1])

  return (
    <aside className={`neighborhood-sidebar ${isVisible ? 'visible' : ''}`}>
      <div className="sidebar-header">
        <span className="sidebar-label">NEIGHBORHOODS</span>
        <button className="sidebar-close" onClick={onClose} aria-label="Close sidebar">
          &times;
        </button>
      </div>

      <nav className="sidebar-nav">
        <button
          className={`hood-item ${selectedNeighborhood === null ? 'active' : ''}`}
          onClick={() => onSelectNeighborhood(null)}
        >
          <span className="hood-name">All Matches</span>
          <span className="hood-count">{totalCount}</span>
        </button>
        {sortedHoods.map(([hood, count]) => (
          <button
            key={hood}
            className={`hood-item ${selectedNeighborhood === hood ? 'active' : ''}`}
            onClick={() => onSelectNeighborhood(hood)}
          >
            <span className="hood-name">{hood}</span>
            <span className="hood-count">{count}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-controls">
        <div className="control-group">
          <span className="control-label">SORT</span>
          <select
            className="sort-select"
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value as SortOption)}
          >
            <option value="score">Match Score</option>
            <option value="newest">Newest First</option>
            <option value="light">Light Potential</option>
            <option value="tranquility">Quietest First</option>
            <option value="price_low">Price (Low)</option>
            <option value="price_high">Price (High)</option>
          </select>
        </div>

        <div className="control-group">
          <span className="control-label">
            MIN SCORE: <span className="score-value">{minScore}</span>
          </span>
          <input
            type="range"
            min="0"
            max="80"
            step="10"
            value={minScore}
            onChange={(e) => onMinScoreChange(Number(e.target.value))}
            className="score-slider"
          />
        </div>

        <div className="control-group">
          <span className="control-label">FILTERS</span>
          <div className="filter-list">
            {FILTER_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                className={`filter-btn ${filters[opt.key] ? 'active' : ''}`}
                onClick={() => onToggleFilter(opt.key)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </aside>
  )
}
