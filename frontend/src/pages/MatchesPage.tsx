import { useState, useMemo, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useMatches } from '@/hooks/useMatches'
import { DossierCard } from '@/components/cards/DossierCard'
import { VibeSelector } from '@/components/filters/VibeSelector'
import { ToggleChip } from '@/components/filters/ToggleChip'
import { api } from '@/lib/api'
import { TEST_USER_ID } from '@/lib/user'
import './MatchesPage.css'

interface IngestionStatus {
  status: string
  last_update_display?: string
}

interface FeedbackEntry {
  listing_id: number
  feedback_type: string
}

export function MatchesPage() {
  const { data: matches, isLoading, error } = useMatches()

  // Vibe state
  const [selectedVibe, setSelectedVibe] = useState<string | null>(null)

  // Quick filter state
  const [filters, setFilters] = useState({
    hasNaturalLight: false,
    hasOutdoorSpace: false,
    hasParking: false,
    quietLocation: false,
    priceReduced: false,
  })

  // Sorting state
  const [sortBy, setSortBy] = useState('score')
  const [minScore, setMinScore] = useState(0)
  const [ingestionStatus, setIngestionStatus] = useState<IngestionStatus | null>(null)
  const [ingestionMessage, setIngestionMessage] = useState<string | null>(null)
  const [ingestionError, setIngestionError] = useState<string | null>(null)
  const [ingestionRunning, setIngestionRunning] = useState(false)

  // User feedback state
  const [userFeedback, setUserFeedback] = useState<Record<number, string | null>>({})

  // Fetch ingestion status
  const fetchIngestionStatus = useCallback(async () => {
    try {
      const data = await api.get<IngestionStatus>('/ingestion/status')
      setIngestionStatus(data)
      setIngestionError(null)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch ingestion status'
      console.error(message)
      setIngestionError(message)
    }
  }, [])

  // Trigger data refresh
  const triggerIngestion = async () => {
    try {
      setIngestionRunning(true)
      setIngestionMessage(null)
      setIngestionError(null)
      await api.post('/admin/ingestion/run', {})
      setIngestionMessage('Ingestion started. Check back in a few minutes.')
      setTimeout(fetchIngestionStatus, 5000)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start data ingestion'
      console.error(message)
      setIngestionError(message)
    } finally {
      setIngestionRunning(false)
    }
  }

  // Fetch user feedback for all listings
  const fetchUserFeedback = useCallback(async () => {
    try {
      const feedbackList = await api.get<FeedbackEntry[]>(`/feedback/user/${TEST_USER_ID}`)
      const feedbackMap: Record<number, string | null> = {}
      for (const fb of feedbackList) {
        feedbackMap[fb.listing_id] = fb.feedback_type
      }
      setUserFeedback(feedbackMap)
    } catch (error) {
      console.error('Failed to fetch user feedback:', error)
    }
  }, [])

  // Handle feedback from DossierCard
  const handleFeedback = async (listingId: number, feedbackType: string | null) => {
    try {
      if (feedbackType === null) {
        await api.del(`/feedback/${listingId}`)
      } else {
        await api.post(`/feedback/${listingId}`, { feedback_type: feedbackType })
      }
      setUserFeedback((prev) => ({ ...prev, [listingId]: feedbackType }))
    } catch (error) {
      console.error('Failed to update feedback:', error)
    }
  }

  // Handle vibe change
  const handleVibeChange = (vibe: string | null) => {
    setSelectedVibe(vibe)
    if (vibe === 'light_chaser') {
      setSortBy('light')
    } else if (vibe === 'deal_hunter') {
      setFilters((prev) => ({ ...prev, priceReduced: true }))
    }
  }

  // Toggle filter
  const toggleFilter = (filterName: keyof typeof filters) => {
    setFilters((prev) => ({ ...prev, [filterName]: !prev[filterName] }))
  }

  useEffect(() => {
    fetchIngestionStatus()
    fetchUserFeedback()
  }, [fetchIngestionStatus, fetchUserFeedback])

  // Sort and filter
  const sortedMatches = useMemo(() => {
    if (!matches) return []

    let filtered = matches.filter((listing) => {
      if (listing.match_score != null && listing.match_score < minScore) return false
      if (filters.hasNaturalLight && !listing.has_natural_light_keywords) return false
      if (filters.hasOutdoorSpace && !listing.has_outdoor_space_keywords) return false
      if (filters.hasParking && !listing.has_parking_keywords) return false
      if (filters.quietLocation && (listing.tranquility_score ?? 50) < 60) return false
      if (filters.priceReduced && !listing.is_price_reduced) return false
      return true
    })

    const sorted = [...filtered]
    switch (sortBy) {
      case 'score':
        sorted.sort((a, b) => (b.match_score || 0) - (a.match_score || 0))
        break
      case 'price_low':
        sorted.sort((a, b) => (a.price ?? Infinity) - (b.price ?? Infinity))
        break
      case 'price_high':
        sorted.sort((a, b) => (b.price ?? 0) - (a.price ?? 0))
        break
      case 'light':
        sorted.sort((a, b) => (b.light_potential_score ?? 50) - (a.light_potential_score ?? 50))
        break
      case 'tranquility':
        sorted.sort((a, b) => (b.tranquility_score ?? 50) - (a.tranquility_score ?? 50))
        break
      case 'newest':
        sorted.sort((a, b) => (a.days_on_market ?? 999) - (b.days_on_market ?? 999))
        break
    }

    return sorted
  }, [matches, minScore, filters, sortBy])

  // Skip summary
  const skipSummary = useMemo(() => {
    const total = matches?.length || 0
    const showing = sortedMatches.length
    if (total > showing) {
      return `Analyzed ${total} listings. Showing ${showing} that matter.`
    }
    return `Showing all ${showing} matches.`
  }, [matches?.length, sortedMatches.length])

  return (
    <section className="matches-page">
      {/* Page Header */}
      <header className="page-header">
        <div className="header-content">
          <h1 className="page-title">Your Matches</h1>
          <p className="page-subtitle">Properties matching your criteria, ranked by fit.</p>
        </div>

        {(ingestionStatus || ingestionMessage || ingestionError) && (
          <div className="data-freshness" role="status" aria-live="polite">
            <span className="freshness-label">Data:</span>
            {ingestionStatus?.last_update_display ? (
              <span className={`freshness-value ${ingestionStatus.status}`}>
                {ingestionStatus.last_update_display}
              </span>
            ) : (
              <span className="freshness-value outdated">Unknown</span>
            )}
            <button className="refresh-btn" onClick={triggerIngestion} disabled={ingestionRunning}>
              {ingestionRunning ? 'Refreshing…' : 'Refresh'}
            </button>
            {ingestionMessage && <span className="freshness-note">{ingestionMessage}</span>}
            {ingestionError && <span className="freshness-error">{ingestionError}</span>}
          </div>
        )}
      </header>

      {/* Vibe Selector */}
      <div className="vibe-section">
        <VibeSelector selected={selectedVibe} onChange={handleVibeChange} />
      </div>

      {/* Quick Filters */}
      <div className="filters-section">
        <span className="filters-label">QUICK FILTERS</span>
        <div className="filter-chips">
          <ToggleChip
            label="Natural Light"
            active={filters.hasNaturalLight}
            onClick={() => toggleFilter('hasNaturalLight')}
          />
          <ToggleChip
            label="Outdoor Space"
            active={filters.hasOutdoorSpace}
            onClick={() => toggleFilter('hasOutdoorSpace')}
          />
          <ToggleChip
            label="Parking"
            active={filters.hasParking}
            onClick={() => toggleFilter('hasParking')}
          />
          <ToggleChip
            label="Quiet Location"
            active={filters.quietLocation}
            onClick={() => toggleFilter('quietLocation')}
          />
          <ToggleChip
            label="Price Reduced"
            active={filters.priceReduced}
            onClick={() => toggleFilter('priceReduced')}
          />
        </div>
      </div>

      {/* Sort & Results Bar */}
      <div className="results-bar">
        <div className="sort-control">
          <label htmlFor="sort-select">Sort:</label>
          <select id="sort-select" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="score">Match Score</option>
            <option value="newest">Newest First</option>
            <option value="light">Light Potential</option>
            <option value="tranquility">Quietest First</option>
            <option value="price_low">Price (Low)</option>
            <option value="price_high">Price (High)</option>
          </select>
        </div>

        <div className="score-filter">
          <label htmlFor="min-score">Min Score:</label>
          <input
            type="range"
            id="min-score"
            min="0"
            max="80"
            step="10"
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
          />
          <span className="score-value">{minScore}</span>
        </div>

        <div className="skip-summary">{skipSummary}</div>
      </div>

      {/* Results */}
      {error && (
        <div className="error-state">
          <p className="error-message">Error loading matches: {error.message}</p>
        </div>
      )}

      {isLoading && (
        <div className="dossiers-grid">
          {[...Array(6)].map((_, i) => (
            <DossierCard key={i} index={i} loading />
          ))}
        </div>
      )}

      {!isLoading && !error && sortedMatches.length > 0 && (
        <div className="dossiers-grid">
          {sortedMatches.map((listing, index) => (
            <DossierCard
              key={listing.id}
              listing={listing}
              index={index}
              userFeedback={userFeedback[listing.id] || null}
              isTopMatch={index < 3}
              onFeedback={handleFeedback}
            />
          ))}
        </div>
      )}

      {!isLoading && !error && sortedMatches.length === 0 && (
        <div className="empty-state">
          <p className="empty-message">No matches found for your current criteria.</p>
          <p className="empty-hint">
            Try adjusting filters or visit <Link to="/criteria">My Criteria</Link> to update your
            preferences.
          </p>
        </div>
      )}
    </section>
  )
}
