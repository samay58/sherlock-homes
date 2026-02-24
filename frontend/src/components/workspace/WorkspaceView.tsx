import { useState, useMemo, useCallback, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMatches } from '@/hooks/useMatches'
import { api } from '@/lib/api'
import { TEST_USER_ID } from '@/lib/user'
import { NeighborhoodSidebar } from './NeighborhoodSidebar'
import { ListingList } from './ListingList'
import { ListingDetail } from './ListingDetail'
import './WorkspaceView.css'

interface FeedbackEntry {
  listing_id: number
  feedback_type: string
}

export type SortOption = 'score' | 'newest' | 'light' | 'tranquility' | 'price_low' | 'price_high'

export interface FilterState {
  hasNaturalLight: boolean
  hasOutdoorSpace: boolean
  quietLocation: boolean
  priceReduced: boolean
}

export function WorkspaceView() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { data: matches, isLoading, error } = useMatches()

  const selectedNeighborhood = searchParams.get('n') || null
  const selectedListingId = searchParams.get('l') ? Number(searchParams.get('l')) : null

  const [sortBy, setSortBy] = useState<SortOption>('score')
  const [minScore, setMinScore] = useState(0)
  const [filters, setFilters] = useState<FilterState>({
    hasNaturalLight: false,
    hasOutdoorSpace: false,
    quietLocation: false,
    priceReduced: false,
  })
  const [userFeedback, setUserFeedback] = useState<Record<number, string | null>>({})
  const [mobilePanel, setMobilePanel] = useState<'sidebar' | 'list' | 'detail'>('list')

  // Fetch user feedback
  const fetchUserFeedback = useCallback(async () => {
    try {
      const feedbackList = await api.get<FeedbackEntry[]>(`/feedback/user/${TEST_USER_ID}`)
      const feedbackMap: Record<number, string | null> = {}
      for (const fb of feedbackList) {
        feedbackMap[fb.listing_id] = fb.feedback_type
      }
      setUserFeedback(feedbackMap)
    } catch (err) {
      console.error('Failed to fetch user feedback:', err)
    }
  }, [])

  useEffect(() => {
    fetchUserFeedback()
  }, [fetchUserFeedback])

  // Handle feedback
  const handleFeedback = async (listingId: number, feedbackType: string | null) => {
    try {
      if (feedbackType === null) {
        await api.del(`/feedback/${listingId}`)
      } else {
        await api.post(`/feedback/${listingId}`, { feedback_type: feedbackType })
      }
      setUserFeedback((prev) => ({ ...prev, [listingId]: feedbackType }))
    } catch (err) {
      console.error('Failed to update feedback:', err)
    }
  }

  // Group by neighborhood
  const neighborhoodCounts = useMemo(() => {
    if (!matches) return new Map<string, number>()
    const counts = new Map<string, number>()
    for (const m of matches) {
      const hood = m.neighborhood || 'Unknown'
      counts.set(hood, (counts.get(hood) || 0) + 1)
    }
    return counts
  }, [matches])

  // Filter + sort
  const filteredListings = useMemo(() => {
    if (!matches) return []

    let filtered = matches.filter((listing) => {
      if (selectedNeighborhood && (listing.neighborhood || 'Unknown') !== selectedNeighborhood) return false
      if (listing.match_score != null && listing.match_score < minScore) return false
      if (filters.hasNaturalLight && !listing.has_natural_light_keywords) return false
      if (filters.hasOutdoorSpace && !listing.has_outdoor_space_keywords) return false
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
  }, [matches, selectedNeighborhood, minScore, filters, sortBy])

  // Selected listing object
  const selectedListing = useMemo(() => {
    if (!selectedListingId) return filteredListings[0] || null
    return filteredListings.find((l) => l.id === selectedListingId) || filteredListings[0] || null
  }, [filteredListings, selectedListingId])

  // Auto-select first listing when filter changes and current selection is not in filtered set
  useEffect(() => {
    if (filteredListings.length > 0 && selectedListingId) {
      const stillInList = filteredListings.some((l) => l.id === selectedListingId)
      if (!stillInList) {
        setSearchParams((prev) => {
          const next = new URLSearchParams(prev)
          next.set('l', String(filteredListings[0].id))
          return next
        }, { replace: true })
      }
    }
  }, [filteredListings, selectedListingId, setSearchParams])

  const setSelectedNeighborhood = (hood: string | null) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      if (hood) {
        next.set('n', hood)
      } else {
        next.delete('n')
      }
      next.delete('l')
      return next
    }, { replace: true })
  }

  const setSelectedListingId = (id: number) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set('l', String(id))
      return next
    }, { replace: true })
    setMobilePanel('detail')
  }

  const toggleFilter = (key: keyof FilterState) => {
    setFilters((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  if (error) {
    return (
      <div className="workspace-error">
        <p>Failed to load matches: {error.message}</p>
      </div>
    )
  }

  return (
    <div className="workspace">
      <NeighborhoodSidebar
        neighborhoodCounts={neighborhoodCounts}
        totalCount={matches?.length || 0}
        selectedNeighborhood={selectedNeighborhood}
        onSelectNeighborhood={setSelectedNeighborhood}
        sortBy={sortBy}
        onSortChange={setSortBy}
        minScore={minScore}
        onMinScoreChange={setMinScore}
        filters={filters}
        onToggleFilter={toggleFilter}
        isVisible={mobilePanel === 'sidebar'}
        onClose={() => setMobilePanel('list')}
      />

      <ListingList
        listings={filteredListings}
        selectedId={selectedListing?.id || null}
        onSelectListing={setSelectedListingId}
        sortBy={sortBy}
        neighborhoodLabel={selectedNeighborhood || 'All Matches'}
        isLoading={isLoading}
        isVisible={mobilePanel === 'list'}
        onOpenSidebar={() => setMobilePanel('sidebar')}
      />

      <ListingDetail
        listing={selectedListing}
        userFeedback={selectedListing ? userFeedback[selectedListing.id] || null : null}
        onFeedback={handleFeedback}
        neighborhoodLabel={selectedNeighborhood || 'All Matches'}
        isVisible={mobilePanel === 'detail'}
        onBack={() => setMobilePanel('list')}
      />
    </div>
  )
}
