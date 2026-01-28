import { useListings } from '@/hooks/useListings'
import { ListingCard } from '@/components/cards/ListingCard'
import './ListingsPage.css'

export function ListingsPage() {
  const { data: listings, isLoading, error } = useListings()

  return (
    <section className="listings-page">
      <h2>Browse Listings</h2>

      {error && <p className="error">Error loading listings: {error.message}</p>}

      {isLoading && (
        <div className="listings-grid">
          {[...Array(6)].map((_, i) => (
            <ListingCard key={i} listing={{} as any} index={i} loading />
          ))}
        </div>
      )}

      {!isLoading && listings && listings.length > 0 && (
        <div className="listings-grid">
          {listings.map((listing, index) => (
            <ListingCard key={listing.id} listing={listing} index={index} />
          ))}
        </div>
      )}

      {!isLoading && (!listings || listings.length === 0) && !error && <p>No listings found.</p>}
    </section>
  )
}
