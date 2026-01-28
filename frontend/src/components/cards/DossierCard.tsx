import { useState, type MouseEvent } from 'react'
import { Link } from 'react-router-dom'
import type { PropertyListing } from '@/lib/types'
import './DossierCard.css'

interface DossierCardProps {
  listing?: PropertyListing
  index?: number
  loading?: boolean
  showScore?: boolean
  isTopMatch?: boolean
  userFeedback?: string | null
  onFeedback?: (listingId: number, feedbackType: string | null) => void
}

const PRICE_FORMATTER = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})
const NUMBER_FORMATTER = new Intl.NumberFormat('en-US')

const formatPrice = (price: number | null) => (price == null ? 'Price TBD' : PRICE_FORMATTER.format(price))
const formatNumber = (num: number | null) => (num == null ? '—' : NUMBER_FORMATTER.format(num))

const getScoreTier = (score: number) => {
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  if (score >= 40) return 'fair'
  return 'low'
}

const normalizeSignal = (value: unknown) => {
  if (value == null) return null
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return null
  return Math.round(numeric * 10) / 10
}

const buildIntel = (listing: PropertyListing) =>
  [
    { key: 'natural_light', label: 'Natural Light', detected: listing.has_natural_light_keywords },
    { key: 'high_ceilings', label: 'High Ceilings', detected: listing.has_high_ceiling_keywords },
    { key: 'outdoor_space', label: 'Outdoor Space', detected: listing.has_outdoor_space_keywords },
    { key: 'parking', label: 'Parking', detected: listing.has_parking_keywords },
    { key: 'view', label: 'View', detected: listing.has_view_keywords },
    { key: 'updated', label: 'Updated', detected: listing.has_updated_systems_keywords },
  ].filter((feature) => feature.detected)

const buildSignalData = (listing: PropertyListing) => {
  const data: { label: string; value: number }[] = []

  const deriveSignal = (key: string, fallback: number | null) => {
    if (listing.signals && (listing.signals as Record<string, unknown>)[key] != null) {
      return normalizeSignal((listing.signals as Record<string, unknown>)[key])
    }
    return normalizeSignal(fallback)
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
}

export function DossierCard({
  listing,
  index = 0,
  loading = false,
  showScore = true,
  isTopMatch = false,
  userFeedback = null,
  onFeedback,
}: DossierCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)

  const handleFeedback = (e: MouseEvent, type: string) => {
    e.preventDefault()
    e.stopPropagation()
    if (!listing) return
    const newType = userFeedback === type ? null : type
    onFeedback?.(listing.id, newType)
  }

  if (loading || !listing) {
    return (
      <div className="dossier-card dossier-card--skeleton" style={{ animationDelay: `${index * 30}ms` }}>
        <div className="skeleton skeleton-image"></div>
        <div className="dossier-body">
          <div className="skeleton skeleton-price"></div>
          <div className="skeleton skeleton-address"></div>
          <div className="skeleton skeleton-stats"></div>
        </div>
      </div>
    )
  }

  const primaryPhoto = listing.photos?.[0] || '/placeholder-image.svg'
  const pricePerSqft = listing.price && listing.sqft ? Math.round(listing.price / listing.sqft) : null
  const intel = buildIntel(listing)
  const signalData = buildSignalData(listing)
  const scoreTier = listing.match_score != null ? getScoreTier(listing.match_score) : null

  return (
    <Link to={`/listings/${listing.id}`} className="dossier-link" style={{ animationDelay: `${index * 30}ms` }}>
      <article className={`dossier-card ${isTopMatch ? 'dossier-card--top' : ''}`}>
        {/* Photo Section */}
        <div className="dossier-photo">
          {!imageLoaded && <div className="photo-placeholder skeleton"></div>}
          <img
            src={imageError ? '/placeholder-image.svg' : primaryPhoto}
            alt={listing.address}
            loading="lazy"
            onLoad={() => setImageLoaded(true)}
            onError={() => {
              setImageError(true)
              setImageLoaded(true)
            }}
            className={imageLoaded ? 'loaded' : ''}
          />

          {/* Badges */}
          {listing.days_on_market != null && listing.days_on_market <= 7 && (
            <span className="dossier-badge dossier-badge--fresh">{listing.days_on_market}D NEW</span>
          )}
          {listing.days_on_market != null && listing.days_on_market > 90 && (
            <span className="dossier-badge dossier-badge--stale">{listing.days_on_market}D</span>
          )}

          {showScore && listing.match_score != null && (
            <div className={`dossier-score dossier-score--${scoreTier}`}>
              <span className="score-pct">{Math.round(listing.match_score)}%</span>
              <span className="score-txt">MATCH</span>
            </div>
          )}
        </div>

        {/* Body Section */}
        <div className="dossier-body">
          <div className="dossier-price">{formatPrice(listing.price)}</div>
          {(typeof listing.score_points === 'number' || listing.score_tier) && (
            <div className="dossier-scoreline">
              {typeof listing.score_points === 'number' && `${listing.score_points.toFixed(1)} pts`}
              {typeof listing.score_points === 'number' && listing.score_tier && ' · '}
              {listing.score_tier}
            </div>
          )}

          <address className="dossier-address">{listing.address}</address>

          {/* Stats Grid */}
          <div className="dossier-stats">
            <div className="stat">
              <span className="stat-value">{listing.beds || '—'}</span>
              <span className="stat-label">BD</span>
            </div>
            <div className="stat">
              <span className="stat-value">{listing.baths || '—'}</span>
              <span className="stat-label">BA</span>
            </div>
            <div className="stat">
              <span className="stat-value">{formatNumber(listing.sqft)}</span>
              <span className="stat-label">SQFT</span>
            </div>
            {pricePerSqft && (
              <div className="stat stat--wide">
                <span className="stat-value">${formatNumber(pricePerSqft)}</span>
                <span className="stat-label">/SQFT</span>
              </div>
            )}
          </div>

          {/* Property Intel */}
          {(intel.length > 0 || signalData.length > 0) && (
            <div className="dossier-intel">
              {intel.length > 0 && (
                <>
                  <span className="intel-label">INTEL</span>
                  <div className="intel-tags">
                    {intel.slice(0, 3).map((feature) => (
                      <span key={feature.key} className="intel-tag">{feature.label}</span>
                    ))}
                    {intel.length > 3 && (
                      <span className="intel-tag intel-tag--more">+{intel.length - 3}</span>
                    )}
                  </div>
                </>
              )}
              {signalData.length > 0 && (
                <>
                  <span className="signal-label">SIGNALS</span>
                  <div className="signal-tags">
                    {signalData.map((signal) => (
                      <span key={signal.label} className="signal-tag">
                        <span className="signal-name">{signal.label}</span>
                        <span className="signal-value">{signal.value}</span>
                      </span>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Why this matched */}
          {((listing.match_reasons && listing.match_reasons.length) || listing.match_tradeoff) ? (
            <div className="dossier-why">
              {listing.match_reasons && listing.match_reasons.length > 0 && (
                <>
                  <span className="why-label">WHY</span>
                  <span className="why-text">{listing.match_reasons.join(' · ')}</span>
                </>
              )}
              {listing.match_tradeoff && (
                <span className="why-tradeoff">Tradeoff: {listing.match_tradeoff}</span>
              )}
              {listing.why_now && (
                <span className="why-now">Why now: {listing.why_now}</span>
              )}
            </div>
          ) : listing.match_narrative ? (
            <p className="dossier-narrative">{listing.match_narrative}</p>
          ) : null}

          {/* Feedback Buttons */}
          <div className="dossier-feedback">
            <button
              className={`feedback-btn feedback-btn--like ${userFeedback === 'like' ? 'active' : ''}`}
              onClick={(e) => handleFeedback(e, 'like')}
              title="Like this listing"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
              </svg>
            </button>
            <button
              className={`feedback-btn feedback-btn--dislike ${userFeedback === 'dislike' ? 'active' : ''}`}
              onClick={(e) => handleFeedback(e, 'dislike')}
              title="Dislike this listing"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
              </svg>
            </button>
          </div>
        </div>
      </article>
    </Link>
  )
}
