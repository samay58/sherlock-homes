<script lang="ts">
  import DossierCard from '$lib/components/DossierCard.svelte';
  import VibeSelector from '$lib/components/VibeSelector.svelte';
  import ToggleChip from '$lib/components/ToggleChip.svelte';
  import type { PageData } from './$types';
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  export let data: PageData;

  // Vibe state
  let selectedVibe: string | null = null;

  // Quick filter state
  let filters = {
    hasNaturalLight: false,
    hasOutdoorSpace: false,
    hasParking: false,
    quietLocation: false,
    priceReduced: false,
  };

  // Sorting state
  let sortBy = 'score';
  let minScore = 0;
  let sortedMatches = data.matches || [];
  let ingestionStatus: any = null;

  // Skip summary
  let skipSummary = '';

  // User feedback state: { listingId: 'like' | 'dislike' | 'neutral' | null }
  let userFeedback: Record<number, string | null> = {};

  // Sort and filter functions
  const applyFiltersAndSort = () => {
    if (!data.matches) return;

    let filtered = data.matches.filter(listing => {
      // Score filter
      if (listing.match_score && listing.match_score < minScore) return false;

      // Quick filters (instant, no Apply button)
      if (filters.hasNaturalLight && !listing.has_natural_light_keywords) return false;
      if (filters.hasOutdoorSpace && !listing.has_outdoor_space_keywords) return false;
      if (filters.hasParking && !listing.has_parking_keywords) return false;
      if (filters.quietLocation && (listing.tranquility_score || 50) < 60) return false;
      if (filters.priceReduced && !listing.is_price_reduced) return false;

      return true;
    });

    // Sort
    switch (sortBy) {
      case 'score':
        filtered = [...filtered].sort((a, b) =>
          (b.match_score || 0) - (a.match_score || 0)
        );
        break;
      case 'price_low':
        filtered = [...filtered].sort((a, b) =>
          (a.price || Infinity) - (b.price || Infinity)
        );
        break;
      case 'price_high':
        filtered = [...filtered].sort((a, b) =>
          (b.price || 0) - (a.price || 0)
        );
        break;
      case 'light':
        filtered = [...filtered].sort((a, b) =>
          (b.light_potential_score || 50) - (a.light_potential_score || 50)
        );
        break;
      case 'tranquility':
        filtered = [...filtered].sort((a, b) =>
          (b.tranquility_score || 50) - (a.tranquility_score || 50)
        );
        break;
      case 'newest':
        filtered = [...filtered].sort((a, b) =>
          (a.days_on_market || 999) - (b.days_on_market || 999)
        );
        break;
    }

    sortedMatches = filtered;

    // Generate skip summary
    const total = data.matches?.length || 0;
    const showing = sortedMatches.length;
    if (total > showing) {
      skipSummary = `Analyzed ${total} listings. Showing ${showing} that matter.`;
    } else {
      skipSummary = `Showing all ${showing} matches.`;
    }
  };

  // Handle vibe change
  const handleVibeChange = (event: CustomEvent) => {
    selectedVibe = event.detail.vibe;
    // In a full implementation, this would re-fetch with the vibe parameter
    // For now, just re-sort with vibe-appropriate defaults
    if (selectedVibe === 'light_chaser') {
      sortBy = 'light';
    } else if (selectedVibe === 'deal_hunter') {
      filters.priceReduced = true;
    }
    applyFiltersAndSort();
  };

  // Toggle filter
  const toggleFilter = (filterName: keyof typeof filters) => {
    filters[filterName] = !filters[filterName];
    applyFiltersAndSort();
  };

  // Fetch ingestion status
  const fetchIngestionStatus = async () => {
    try {
      const response = await fetch('/ingestion/status');
      if (response.ok) {
        ingestionStatus = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch ingestion status:', error);
    }
  };

  // Trigger data refresh
  const triggerIngestion = async () => {
    try {
      const response = await fetch('/admin/ingestion/run', {
        method: 'POST'
      });
      if (response.ok) {
        alert('Data ingestion started. This may take a few minutes.');
        setTimeout(fetchIngestionStatus, 5000);
      }
    } catch (error) {
      console.error('Failed to trigger ingestion:', error);
      alert('Failed to start data ingestion.');
    }
  };

  // React to changes
  $: sortBy, minScore, filters, applyFiltersAndSort();

  // Fetch user feedback for all listings
  const fetchUserFeedback = async () => {
    try {
      // Fetch all feedback for test user (user_id=1)
      const feedbackList = await api.get('/feedback/user/1');
      // Build lookup map
      userFeedback = {};
      for (const fb of feedbackList) {
        userFeedback[fb.listing_id] = fb.feedback_type;
      }
    } catch (error) {
      console.error('Failed to fetch user feedback:', error);
    }
  };

  // Handle feedback from DossierCard
  const handleFeedback = async (event: CustomEvent) => {
    const { listingId, feedbackType } = event.detail;

    try {
      if (feedbackType === null) {
        // Delete feedback (toggle off)
        await api.del(`/feedback/${listingId}`);
        userFeedback[listingId] = null;
      } else {
        // Create/update feedback
        await api.post(`/feedback/${listingId}`, { feedback_type: feedbackType });
        userFeedback[listingId] = feedbackType;
      }
      // Trigger reactivity
      userFeedback = { ...userFeedback };
    } catch (error) {
      console.error('Failed to update feedback:', error);
    }
  };

  onMount(() => {
    applyFiltersAndSort();
    fetchIngestionStatus();
    fetchUserFeedback();
  });
</script>

<svelte:head>
  <title>Your Matches - Sherlock Homes</title>
</svelte:head>

<section class="matches-page">
  <!-- Page Header -->
  <header class="page-header">
    <div class="header-content">
      <h1 class="page-title">Your Matches</h1>
      <p class="page-subtitle">Properties matching your criteria, ranked by fit.</p>
    </div>

    {#if ingestionStatus}
      <div class="data-freshness">
        <span class="freshness-label">Data:</span>
        {#if ingestionStatus.last_update_display}
          <span class="freshness-value {ingestionStatus.status}">
            {ingestionStatus.last_update_display}
          </span>
        {:else}
          <span class="freshness-value outdated">Never updated</span>
        {/if}
        <button class="refresh-btn" on:click={triggerIngestion}>
          Refresh
        </button>
      </div>
    {/if}
  </header>

  <!-- Vibe Selector -->
  <div class="vibe-section">
    <VibeSelector selected={selectedVibe} on:change={handleVibeChange} />
  </div>

  <!-- Quick Filters -->
  <div class="filters-section">
    <span class="filters-label">QUICK FILTERS</span>
    <div class="filter-chips">
      <ToggleChip
        label="Natural Light"
        active={filters.hasNaturalLight}
        on:click={() => toggleFilter('hasNaturalLight')}
      />
      <ToggleChip
        label="Outdoor Space"
        active={filters.hasOutdoorSpace}
        on:click={() => toggleFilter('hasOutdoorSpace')}
      />
      <ToggleChip
        label="Parking"
        active={filters.hasParking}
        on:click={() => toggleFilter('hasParking')}
      />
      <ToggleChip
        label="Quiet Location"
        active={filters.quietLocation}
        on:click={() => toggleFilter('quietLocation')}
      />
      <ToggleChip
        label="Price Reduced"
        active={filters.priceReduced}
        on:click={() => toggleFilter('priceReduced')}
      />
    </div>
  </div>

  <!-- Sort & Results Bar -->
  <div class="results-bar">
    <div class="sort-control">
      <label for="sort-select">Sort:</label>
      <select id="sort-select" bind:value={sortBy}>
        <option value="score">Match Score</option>
        <option value="newest">Newest First</option>
        <option value="light">Light Potential</option>
        <option value="tranquility">Quietest First</option>
        <option value="price_low">Price (Low)</option>
        <option value="price_high">Price (High)</option>
      </select>
    </div>

    <div class="score-filter">
      <label for="min-score">Min Score:</label>
      <input
        type="range"
        id="min-score"
        min="0"
        max="80"
        step="10"
        bind:value={minScore}
      />
      <span class="score-value">{minScore}</span>
    </div>

    <div class="skip-summary">
      {skipSummary}
    </div>
  </div>

  <!-- Results -->
  {#if data.error}
    <div class="error-state">
      <p class="error-message">Error loading matches: {data.error}</p>
    </div>
  {:else if sortedMatches && sortedMatches.length > 0}
    <div class="dossiers-grid">
      {#each sortedMatches as listing, index (listing.id)}
        <DossierCard
          {listing}
          {index}
          userFeedback={userFeedback[listing.id] || null}
          isTopMatch={index < 3}
          on:feedback={handleFeedback}
        />
      {/each}
    </div>
  {:else}
    <div class="empty-state">
      <p class="empty-message">No matches found for your current criteria.</p>
      <p class="empty-hint">Try adjusting filters or visit <a href="/criteria">My Criteria</a> to update your preferences.</p>
    </div>
  {/if}
</section>

<style>
  .matches-page {
    max-width: 100%;
  }

  /* Page Header */
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--space-6, 24px);
    padding-bottom: var(--space-4, 16px);
    border-bottom: 1px solid var(--color-border, #e5e5e5);
  }

  .page-title {
    font-family: var(--font-family-serif, Georgia, serif);
    font-size: var(--font-size-2xl, 32px);
    font-weight: var(--font-weight-normal, 400);
    color: var(--color-ink, #000);
    margin: 0 0 var(--space-1, 4px) 0;
    letter-spacing: var(--tracking-tight, -0.02em);
  }

  .page-subtitle {
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-sm, 12px);
    color: var(--color-text-secondary, #666);
    margin: 0;
  }

  .data-freshness {
    display: flex;
    align-items: center;
    gap: var(--space-2, 8px);
    font-family: var(--font-family-mono, monospace);
    font-size: var(--font-size-xs, 10px);
  }

  .freshness-label {
    color: var(--color-text-tertiary, #999);
    text-transform: uppercase;
    letter-spacing: var(--tracking-wider, 0.05em);
  }

  .freshness-value {
    padding: var(--space-1, 4px) var(--space-2, 8px);
    border-radius: var(--radius-sm, 2px);
    font-weight: var(--font-weight-medium, 500);
  }

  .freshness-value.up_to_date {
    color: var(--color-match-excellent, #15803d);
    background: #f0fdf4;
  }

  .freshness-value.stale {
    color: var(--color-match-moderate, #ca8a04);
    background: #fefce8;
  }

  .freshness-value.outdated {
    color: var(--color-match-poor, #dc2626);
    background: #fef2f2;
  }

  .refresh-btn {
    padding: var(--space-1, 4px) var(--space-2, 8px);
    background: transparent;
    border: 1px solid var(--color-border, #e5e5e5);
    border-radius: var(--radius-sm, 2px);
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-xs, 10px);
    font-weight: var(--font-weight-medium, 500);
    color: var(--color-text-secondary, #666);
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: var(--tracking-wider, 0.05em);
    transition: all 100ms var(--ease-out, ease-out);
  }

  .refresh-btn:hover {
    border-color: var(--color-ink, #000);
    color: var(--color-ink, #000);
  }

  /* Vibe Section */
  .vibe-section {
    margin-bottom: var(--space-6, 24px);
  }

  /* Filters Section */
  .filters-section {
    margin-bottom: var(--space-5, 20px);
  }

  .filters-label {
    display: block;
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-xs, 10px);
    font-weight: var(--font-weight-semibold, 600);
    color: var(--color-text-tertiary, #999);
    letter-spacing: var(--tracking-widest, 0.1em);
    margin-bottom: var(--space-3, 12px);
  }

  .filter-chips {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2, 8px);
  }

  /* Results Bar */
  .results-bar {
    display: flex;
    align-items: center;
    gap: var(--space-6, 24px);
    padding: var(--space-3, 12px) var(--space-4, 16px);
    background: var(--color-gray-100, #f5f5f5);
    border-radius: var(--radius-md, 4px);
    margin-bottom: var(--space-6, 24px);
  }

  .sort-control,
  .score-filter {
    display: flex;
    align-items: center;
    gap: var(--space-2, 8px);
  }

  .sort-control label,
  .score-filter label {
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-xs, 10px);
    font-weight: var(--font-weight-medium, 500);
    color: var(--color-text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: var(--tracking-wider, 0.05em);
  }

  .sort-control select {
    padding: var(--space-1, 4px) var(--space-2, 8px);
    border: 1px solid var(--color-border, #e5e5e5);
    border-radius: var(--radius-sm, 2px);
    background: var(--color-paper, #fff);
    font-family: var(--font-family-mono, monospace);
    font-size: var(--font-size-xs, 10px);
    cursor: pointer;
  }

  .score-filter input[type="range"] {
    width: 80px;
    accent-color: var(--color-ink, #000);
  }

  .score-value {
    font-family: var(--font-family-mono, monospace);
    font-size: var(--font-size-xs, 10px);
    font-weight: var(--font-weight-bold, 700);
    color: var(--color-ink, #000);
    min-width: 24px;
  }

  .skip-summary {
    margin-left: auto;
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-xs, 10px);
    color: var(--color-text-tertiary, #999);
    font-style: italic;
  }

  /* Dossiers Grid */
  .dossiers-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: var(--space-5, 20px);
  }

  /* Error State */
  .error-state {
    padding: var(--space-6, 24px);
    border: 1px solid var(--color-match-poor, #dc2626);
    border-radius: var(--radius-md, 4px);
    background: #fef2f2;
  }

  .error-message {
    font-family: var(--font-family-mono, monospace);
    font-size: var(--font-size-sm, 12px);
    color: var(--color-match-poor, #dc2626);
    margin: 0;
  }

  /* Empty State */
  .empty-state {
    padding: var(--space-8, 32px);
    text-align: center;
    border: 1px solid var(--color-border, #e5e5e5);
    border-radius: var(--radius-md, 4px);
  }

  .empty-message {
    font-family: var(--font-family-serif, Georgia, serif);
    font-size: var(--font-size-lg, 20px);
    color: var(--color-ink, #000);
    margin: 0 0 var(--space-2, 8px) 0;
  }

  .empty-hint {
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-sm, 12px);
    color: var(--color-text-secondary, #666);
    margin: 0;
  }

  .empty-hint a {
    color: var(--color-accent, #FF6600);
    text-decoration: none;
  }

  .empty-hint a:hover {
    text-decoration: underline;
  }

  /* Dark Mode */
  @media (prefers-color-scheme: dark) {
    .page-header {
      border-bottom-color: var(--color-border, #2a2a2a);
    }

    .results-bar {
      background: var(--color-gray-200, #1a1a1a);
    }

    .sort-control select {
      background: var(--color-surface, #111);
      border-color: var(--color-border, #2a2a2a);
      color: var(--color-text-primary, #e5e5e5);
    }

    .freshness-value.up_to_date {
      background: #052e16;
    }

    .freshness-value.stale {
      background: #422006;
    }

    .freshness-value.outdated {
      background: #450a0a;
    }

    .error-state {
      background: #450a0a;
      border-color: var(--color-match-poor, #dc2626);
    }

    .empty-state {
      border-color: var(--color-border, #2a2a2a);
    }
  }

  /* Responsive */
  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
      gap: var(--space-4, 16px);
    }

    .results-bar {
      flex-direction: column;
      align-items: stretch;
      gap: var(--space-3, 12px);
    }

    .skip-summary {
      margin-left: 0;
      text-align: center;
    }

    .dossiers-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
