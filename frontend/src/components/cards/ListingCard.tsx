import { useState, useMemo, useEffect } from 'react'
import { Link } from 'react-router-dom'
import type { PropertyListing } from '@/lib/types'
import './ListingCard.css'

interface ListingCardProps {
  listing: PropertyListing
  index?: number
  loading?: boolean
  showScore?: boolean
}

const formatPrice = (price: number | null) => {
  if (price == null) return 'Price N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(price)
}

const getScoreColor = (score: number) => {
  if (score >= 80) return 'score-excellent'
  if (score >= 60) return 'score-good'
  if (score >= 40) return 'score-fair'
  return 'score-low'
}

const getScoreBadgeText = (score: number) => {
  if (score >= 90) return 'Top Match'
  if (score >= 70) return 'Great Match'
  if (score >= 50) return 'Good Match'
  return 'Fair Match'
}

export function ListingCard({ listing, index = 0, loading = false, showScore = false }: ListingCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)

  useEffect(() => {
    // Trigger fade-in animation
    const timer = setTimeout(() => {
      setImageLoaded(true)
    }, 50)
    return () => clearTimeout(timer)
  }, [])

  const primaryPhoto = listing?.photos?.[0] || '/placeholder-image.svg'

  const pricePerSqft = useMemo(() => {
    if (!listing?.price || !listing?.sqft) return null
    return Math.round(listing.price / listing.sqft)
  }, [listing?.price, listing?.sqft])

  const features = useMemo(() => {
    return [
      listing?.has_natural_light_keywords ? 'Natural Light' : null,
      listing?.has_high_ceiling_keywords ? 'High Ceilings' : null,
      listing?.has_outdoor_space_keywords ? 'Outdoor Space' : null,
      listing?.has_parking_keywords ? 'Parking' : null,
      listing?.has_view_keywords ? 'Views' : null,
      listing?.has_updated_systems_keywords ? 'Updated' : null,
      listing?.has_architectural_details_keywords ? 'Character' : null,
    ].filter(Boolean) as string[]
  }, [listing])

  if (loading) {
    return (
      <div className="listing-card skeleton-card" style={{ animationDelay: `${index * 50}ms` }}>
        <div className="skeleton skeleton-image"></div>
        <div className="info">
          <div className="skeleton skeleton-price"></div>
          <div className="skeleton skeleton-details"></div>
          <div className="skeleton skeleton-address"></div>
        </div>
      </div>
    )
  }

  return (
    <Link to={`/listings/${listing?.id}`} className="card-link" style={{ animationDelay: `${index * 30}ms` }}>
      <article className="listing-card">
        <div className="photo-container">
          {!imageLoaded && <div className="image-placeholder skeleton"></div>}
          <img
            src={imageError ? '/placeholder-image.svg' : primaryPhoto}
            alt={`View of ${listing.address}`}
            loading="lazy"
            onLoad={() => setImageLoaded(true)}
            onError={() => {
              setImageError(true)
              setImageLoaded(true)
            }}
            className={imageLoaded ? 'loaded' : ''}
          />
          {showScore && listing.match_score != null && (
            <div className={`match-score-badge ${getScoreColor(listing.match_score)}`}>
              <span className="score-value">{Math.round(listing.match_score)}%</span>
              <span className="score-label">{getScoreBadgeText(listing.match_score)}</span>
            </div>
          )}
        </div>

        <div className="info">
          <div className="price-row">
            <h3 className="price">{formatPrice(listing.price)}</h3>
            {pricePerSqft && <span className="price-per-sqft">${pricePerSqft}/sqft</span>}
          </div>

          <div className="details">
            <span className="detail-item">
              <span className="detail-value">{listing.beds || '—'}</span>
              <span className="detail-label">beds</span>
            </span>
            <span className="detail-separator">·</span>
            <span className="detail-item">
              <span className="detail-value">{listing.baths || '—'}</span>
              <span className="detail-label">baths</span>
            </span>
            {listing.sqft && (
              <>
                <span className="detail-separator">·</span>
                <span className="detail-item">
                  <span className="detail-value">{new Intl.NumberFormat('en-US').format(listing.sqft)}</span>
                  <span className="detail-label">sqft</span>
                </span>
              </>
            )}
          </div>

          <address className="address">{listing.address}</address>

          {features.length > 0 && (
            <div className="features">
              {features.slice(0, 2).map((feature) => (
                <span key={feature} className="feature-tag">{feature}</span>
              ))}
              {features.length > 2 && (
                <span className="feature-tag">+{features.length - 2}</span>
              )}
            </div>
          )}
        </div>
      </article>
    </Link>
  )
}
