import type { MouseEvent } from 'react'
import type { PropertyListing } from '@/lib/types'
import {
  formatPrice,
  formatScore,
  formatSqft,
  buildSignalData,
  buildFeatureTags,
  getScoreTier,
  getSourceLabel,
} from '@/lib/format'
import { ImageGallery } from '@/components/gallery/ImageGallery'
import './ListingDetail.css'

interface ListingDetailProps {
  listing: PropertyListing | null
  userFeedback: string | null
  onFeedback: (listingId: number, feedbackType: string | null) => void
  neighborhoodLabel: string
  isVisible: boolean
  onBack: () => void
}

export function ListingDetail({
  listing,
  userFeedback,
  onFeedback,
  neighborhoodLabel,
  isVisible,
  onBack,
}: ListingDetailProps) {
  if (!listing) {
    return (
      <div className={`listing-detail ${isVisible ? 'visible' : ''}`}>
        <div className="detail-empty" />
      </div>
    )
  }

  const signalData = buildSignalData(listing)
  const featureTags = buildFeatureTags(listing)
  const scoreTier = listing.match_score != null ? getScoreTier(listing.match_score) : null
  const sourceLabel = getSourceLabel(listing.source)

  const handleFeedback = (e: MouseEvent, type: string) => {
    e.stopPropagation()
    const newType = userFeedback === type ? null : type
    onFeedback(listing.id, newType)
  }

  return (
    <div className={`listing-detail ${isVisible ? 'visible' : ''}`}>
      {/* Toolbar */}
      <div className="detail-toolbar">
        <button className="detail-back" onClick={onBack} aria-label="Back to list">
          &larr; Back
        </button>
        <span className="detail-context">{neighborhoodLabel}</span>
        <div className="detail-actions">
          <button
            className={`fb-btn fb-like ${userFeedback === 'like' ? 'active' : ''}`}
            onClick={(e) => handleFeedback(e, 'like')}
            aria-label="Like"
            aria-pressed={userFeedback === 'like'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
            </svg>
          </button>
          <button
            className={`fb-btn fb-dislike ${userFeedback === 'dislike' ? 'active' : ''}`}
            onClick={(e) => handleFeedback(e, 'dislike')}
            aria-label="Dislike"
            aria-pressed={userFeedback === 'dislike'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
            </svg>
          </button>
          {listing.url && (
            <a
              href={listing.url}
              target="_blank"
              rel="noopener noreferrer"
              className="detail-source-link"
            >
              View on {sourceLabel}
            </a>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="detail-body">
        {/* Address + core stats */}
        <div className="detail-heading">
          <h1 className="detail-address">{listing.address}</h1>
          <div className="detail-stats-row">
            <span className="detail-price">{formatPrice(listing.price)}</span>
            {listing.beds != null && <span className="detail-stat">{listing.beds} bed</span>}
            {listing.baths != null && <span className="detail-stat">{listing.baths} bath</span>}
            {listing.sqft != null && listing.sqft > 0 && (
              <span className="detail-stat">{formatSqft(listing.sqft)}</span>
            )}
          </div>
          {listing.match_score != null && (
            <div className="detail-score-row">
              <span className={`detail-score-badge score-${scoreTier}`}>
                {formatScore(listing.match_score)}
              </span>
              {listing.score_tier && <span className="detail-tier">{listing.score_tier}</span>}
              {listing.score_points != null && (
                <span className="detail-points">{listing.score_points.toFixed(1)} pts</span>
              )}
            </div>
          )}
        </div>

        {/* Photos */}
        {listing.photos && listing.photos.length > 0 && (
          <div className="detail-gallery">
            <ImageGallery images={listing.photos} altText={`Photos of ${listing.address}`} />
          </div>
        )}

        {/* Match intelligence */}
        {(listing.match_reasons?.length || listing.key_tradeoff || listing.match_tradeoff) && (
          <section className="detail-section">
            <span className="detail-label">WHY THIS MATCHED</span>
            {listing.match_reasons && listing.match_reasons.length > 0 && (
              <ul className="match-reasons">
                {listing.match_reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            )}
            {(listing.key_tradeoff || listing.match_tradeoff) && (
              <p className="match-tradeoff">
                <span className="tradeoff-label">Low on</span>{' '}
                {listing.key_tradeoff || listing.match_tradeoff}
              </p>
            )}
            {listing.why_now && (
              <p className="match-whynow">
                <span className="tradeoff-label">Timing</span> {listing.why_now}
              </p>
            )}
          </section>
        )}

        {/* Signals */}
        {signalData.length > 0 && (
          <section className="detail-section">
            <span className="detail-label">SIGNALS</span>
            <div className="signal-row">
              {signalData.map((s) => (
                <div key={s.label} className="signal-item">
                  <span className="signal-name">{s.label}</span>
                  <span className="signal-value">{s.value}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Features */}
        {featureTags.length > 0 && (
          <section className="detail-section">
            <span className="detail-label">FEATURES</span>
            <div className="feature-row">
              {featureTags.map((f) => (
                <span key={f} className="feature-tag">{f}</span>
              ))}
            </div>
          </section>
        )}

        {/* Badges */}
        {(listing.is_price_reduced ||
          listing.is_back_on_market ||
          (listing.days_on_market != null && (listing.days_on_market <= 7 || listing.days_on_market > 90))) && (
          <div className="detail-badges">
            {listing.days_on_market != null && listing.days_on_market <= 7 && (
              <span className="badge badge-new">{listing.days_on_market}D NEW</span>
            )}
            {listing.is_price_reduced && (
              <span className="badge badge-reduced">PRICE REDUCED</span>
            )}
            {listing.is_back_on_market && (
              <span className="badge badge-back">BACK ON MARKET</span>
            )}
            {listing.days_on_market != null && listing.days_on_market > 90 && (
              <span className="badge badge-stale">{listing.days_on_market}D ON MARKET</span>
            )}
          </div>
        )}

        {/* Description */}
        {listing.description && (
          <section className="detail-section">
            <span className="detail-label">DESCRIPTION</span>
            <p className="detail-description">{listing.description}</p>
          </section>
        )}

        {/* Narrative */}
        {listing.match_narrative && (
          <section className="detail-section">
            <span className="detail-label">NOTE</span>
            <p className="detail-description">{listing.match_narrative}</p>
          </section>
        )}
      </div>
    </div>
  )
}
