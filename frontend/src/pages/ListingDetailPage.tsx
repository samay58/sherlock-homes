import { useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { useListing } from '@/hooks/useListings'
import { ImageGallery } from '@/components/gallery/ImageGallery'
import './ListingDetailPage.css'

const formatPrice = (price: number | null) => {
  if (price == null) return 'Price N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(price)
}

const formatSqft = (sqft: number | null) => {
  if (sqft == null || sqft === 0) return 'N/A'
  return `${new Intl.NumberFormat('en-US').format(sqft)} sqft`
}

const formatScore = (score: number | null | undefined) => {
  if (score == null) return '—'
  return `${Math.round(score)}%`
}

const formatSignal = (value: unknown) => {
  if (value == null) return null
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return null
  return Math.round(numeric * 10) / 10
}

export function ListingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: listing, isLoading, error } = useListing(id!)

  const featureTags = useMemo(() => {
    if (!listing) return []
    return [
      listing.has_natural_light_keywords ? 'Natural Light' : null,
      listing.has_high_ceiling_keywords ? 'High Ceilings' : null,
      listing.has_outdoor_space_keywords ? 'Outdoor Space' : null,
      listing.has_parking_keywords ? 'Parking' : null,
      listing.has_view_keywords ? 'Views' : null,
      listing.has_updated_systems_keywords ? 'Updated Systems' : null,
      listing.has_architectural_details_keywords ? 'Character' : null,
    ].filter(Boolean) as string[]
  }, [listing])

  const signalData = useMemo(() => {
    if (!listing) return []
    const data: { label: string; value: number }[] = []

    const deriveSignal = (key: string, fallback: number | null) => {
      if (listing.signals && (listing.signals as Record<string, unknown>)[key] != null) {
        return formatSignal((listing.signals as Record<string, unknown>)[key])
      }
      return formatSignal(fallback)
    }

    const light = deriveSignal(
      'light_potential',
      listing.light_potential_score != null ? listing.light_potential_score / 10 : null
    )
    const quiet = deriveSignal(
      'tranquility_score',
      listing.tranquility_score != null ? listing.tranquility_score / 10 : null
    )
    const visual = deriveSignal(
      'visual_quality',
      listing.visual_quality_score != null ? listing.visual_quality_score / 10 : null
    )
    const character = deriveSignal('nlp_character_score', null)

    if (light != null) data.push({ label: 'Light', value: light })
    if (quiet != null) data.push({ label: 'Quiet', value: quiet })
    if (visual != null) data.push({ label: 'Visual', value: visual })
    if (character != null) data.push({ label: 'Character', value: character })

    return data
  }, [listing])

  if (isLoading) {
    return (
      <section className="listing-detail">
        <p>Loading listing...</p>
      </section>
    )
  }

  if (error) {
    return (
      <section className="listing-detail">
        <p className="error">Error loading listing: {error.message}</p>
      </section>
    )
  }

  if (!listing) {
    return (
      <section className="listing-detail">
        <p>Listing not found.</p>
      </section>
    )
  }

  return (
    <section className="listing-detail">
      <h2>{listing.address}</h2>

      <div className="main-content">
        <div className="gallery-container">
          {listing.photos && listing.photos.length > 0 ? (
            <ImageGallery images={listing.photos} altText={`Photos of ${listing.address}`} />
          ) : (
            <img src="/placeholder-image.svg" alt="Placeholder" className="placeholder-image" />
          )}
        </div>

        <div className="info-container">
          <div className="price">{formatPrice(listing.price)}</div>
          <div className="scoreline">
            <span className="score-percent">{formatScore(listing.match_score)}</span>
            {listing.score_points != null && (
              <span className="score-points">{listing.score_points.toFixed(1)} pts</span>
            )}
            {listing.score_tier && <span className="score-tier">{listing.score_tier}</span>}
          </div>
          <ul className="quick-stats">
            <li>
              <strong>{listing.beds ?? 'N/A'}</strong> bds
            </li>
            <li>
              <strong>{listing.baths ?? 'N/A'}</strong> ba
            </li>
            <li>
              <strong>{formatSqft(listing.sqft)}</strong>
            </li>
            {listing.year_built && (
              <li>
                Built <strong>{listing.year_built}</strong>
              </li>
            )}
          </ul>

          <div className="status-type">
            {listing.listing_status && <span className="tag status">{listing.listing_status}</span>}
            {listing.property_type && <span className="tag type">{listing.property_type}</span>}
          </div>

          {listing.url && (
            <a
              href={listing.url}
              target="_blank"
              rel="noopener noreferrer"
              className="external-link"
            >
              View on Zillow
            </a>
          )}

          {listing.walk_score && (
            <p>
              <strong>Walk Score®:</strong> {listing.walk_score}
            </p>
          )}

          {featureTags.length > 0 && (
            <div className="feature-block">
              <span className="feature-label">FEATURES</span>
              <div className="feature-tags">
                {featureTags.map((feature) => (
                  <span key={feature} className="feature-tag">
                    {feature}
                  </span>
                ))}
              </div>
            </div>
          )}

          {(listing.match_reasons?.length ||
            listing.key_tradeoff ||
            listing.why_now ||
            listing.match_narrative) && (
            <div className="explain-block">
              <span className="feature-label">EXPLAINABILITY</span>
              {listing.match_reasons?.length && (
                <p className="explain-row">
                  <span className="explain-label">Top</span>
                  <span className="explain-value">{listing.match_reasons.join(' · ')}</span>
                </p>
              )}
              {listing.key_tradeoff && (
                <p className="explain-row">
                  <span className="explain-label">Tradeoff</span>
                  <span className="explain-value">{listing.key_tradeoff}</span>
                </p>
              )}
              {listing.why_now && (
                <p className="explain-row">
                  <span className="explain-label">Why now</span>
                  <span className="explain-value">{listing.why_now}</span>
                </p>
              )}
              {listing.match_narrative && (
                <p className="explain-row">
                  <span className="explain-label">Note</span>
                  <span className="explain-value">{listing.match_narrative}</span>
                </p>
              )}
            </div>
          )}

          {signalData.length > 0 && (
            <div className="signal-block">
              <span className="feature-label">SIGNALS</span>
              <div className="signal-tags">
                {signalData.map((signal) => (
                  <span key={signal.label} className="signal-tag">
                    <span className="signal-name">{signal.label}</span>
                    <span className="signal-value">{signal.value}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {listing.description && (
        <div className="description">
          <h3>Description</h3>
          <p>{listing.description}</p>
        </div>
      )}
    </section>
  )
}
