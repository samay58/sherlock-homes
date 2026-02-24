import type { PropertyListing } from '@/lib/types'
import { formatPrice, formatScore } from '@/lib/format'
import './ListingListItem.css'

interface ListingListItemProps {
  listing: PropertyListing
  isSelected: boolean
  onClick: () => void
}

export function ListingListItem({ listing, isSelected, onClick }: ListingListItemProps) {
  const excerpt = listing.description
    ? listing.description.slice(0, 120) + (listing.description.length > 120 ? '...' : '')
    : null

  return (
    <button
      className={`list-item ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
      aria-current={isSelected ? 'true' : undefined}
    >
      <div className="item-meta">
        <span className="item-hood">{listing.neighborhood || 'Unknown'}</span>
        <span className="item-dot">&middot;</span>
        <span className="item-score">{formatScore(listing.match_score)}</span>
      </div>
      <div className="item-address">{listing.address}</div>
      <div className="item-price">
        {formatPrice(listing.price)}
        {listing.beds != null && <span className="item-stat"> &middot; {listing.beds} bed</span>}
        {listing.baths != null && <span className="item-stat"> &middot; {listing.baths} bath</span>}
      </div>
      {excerpt && <div className="item-excerpt">{excerpt}</div>}
    </button>
  )
}
