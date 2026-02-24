import type { PropertyListing } from '@/lib/types'
import type { SortOption } from './WorkspaceView'
import { ListingListItem } from './ListingListItem'
import './ListingList.css'

interface ListingListProps {
  listings: PropertyListing[]
  selectedId: number | null
  onSelectListing: (id: number) => void
  sortBy: SortOption
  neighborhoodLabel: string
  isLoading: boolean
  isVisible: boolean
  onOpenSidebar: () => void
}

const SORT_LABELS: Record<SortOption, string> = {
  score: 'Match Score',
  newest: 'Newest First',
  light: 'Light Potential',
  tranquility: 'Quietest',
  price_low: 'Price (Low)',
  price_high: 'Price (High)',
}

export function ListingList({
  listings,
  selectedId,
  onSelectListing,
  sortBy,
  neighborhoodLabel,
  isLoading,
  isVisible,
  onOpenSidebar,
}: ListingListProps) {
  return (
    <div className={`listing-list ${isVisible ? 'visible' : ''}`}>
      <div className="list-header">
        <button className="list-sidebar-toggle" onClick={onOpenSidebar} aria-label="Open neighborhoods">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
        <div className="list-header-text">
          <span className="list-title">{neighborhoodLabel}</span>
          <span className="list-sort">Sorted by {SORT_LABELS[sortBy]}</span>
        </div>
      </div>

      <div className="list-body">
        {isLoading && (
          <div className="list-loading">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="list-skeleton">
                <div className="skeleton-bar skeleton-hood" />
                <div className="skeleton-bar skeleton-addr" />
                <div className="skeleton-bar skeleton-desc" />
              </div>
            ))}
          </div>
        )}

        {!isLoading && listings.length === 0 && (
          <div className="list-empty">
            <span>No listings match your filters.</span>
          </div>
        )}

        {!isLoading &&
          listings.map((listing) => (
            <ListingListItem
              key={listing.id}
              listing={listing}
              isSelected={listing.id === selectedId}
              onClick={() => onSelectListing(listing.id)}
            />
          ))}
      </div>
    </div>
  )
}
