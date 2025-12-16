<script>
  export let listing;
  export let index = 0;
  export let loading = false;
  export let showScore = true;
  export let isTopMatch = false; // Orange border for top 3

  let imageLoaded = false;
  let imageError = false;

  const formatPrice = (price) => {
    if (price == null) return 'Price TBD';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(price);
  };

  const formatNumber = (num) => {
    if (num == null) return '—';
    return new Intl.NumberFormat('en-US').format(num);
  };

  const calculatePricePerSqft = (price, sqft) => {
    if (!price || !sqft) return null;
    return Math.round(price / sqft);
  };

  $: detailUrl = `/listings/${listing?.id}`;
  $: primaryPhoto = listing?.photos?.[0] || '/placeholder-image.svg';
  $: pricePerSqft = calculatePricePerSqft(listing?.price, listing?.sqft);

  const handleImageLoad = () => { imageLoaded = true; };
  const handleImageError = () => { imageError = true; imageLoaded = true; };

  // Property intel - detected features (from NLP keyword analysis)
  $: intel = [
    { key: 'natural_light', label: 'Natural Light', detected: listing?.has_natural_light_keywords },
    { key: 'high_ceilings', label: 'High Ceilings', detected: listing?.has_high_ceiling_keywords },
    { key: 'outdoor_space', label: 'Outdoor Space', detected: listing?.has_outdoor_space_keywords },
    { key: 'parking', label: 'Parking', detected: listing?.has_parking_keywords },
    { key: 'view', label: 'View', detected: listing?.has_view_keywords },
    { key: 'updated', label: 'Updated', detected: listing?.has_updated_systems_keywords },
  ].filter(f => f.detected);

  // Score tier for styling
  const getScoreTier = (score) => {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'fair';
    return 'low';
  };

  $: scoreTier = listing?.match_score != null ? getScoreTier(listing.match_score) : null;
</script>

{#if loading}
  <div class="dossier-card dossier-card--skeleton" style="animation-delay: {index * 30}ms">
    <div class="skeleton skeleton-image"></div>
    <div class="dossier-body">
      <div class="skeleton skeleton-price"></div>
      <div class="skeleton skeleton-address"></div>
      <div class="skeleton skeleton-stats"></div>
    </div>
  </div>
{:else}
  <a href={detailUrl} class="dossier-link" style="animation-delay: {index * 30}ms">
    <article class="dossier-card" class:dossier-card--top={isTopMatch}>
      <!-- Photo Section -->
      <div class="dossier-photo">
        {#if !imageLoaded}
          <div class="photo-placeholder skeleton"></div>
        {/if}
        <img
          src={imageError ? '/placeholder-image.svg' : primaryPhoto}
          alt={listing.address}
          loading="lazy"
          on:load={handleImageLoad}
          on:error={handleImageError}
          class:loaded={imageLoaded}
        />

        <!-- Badges -->
        {#if listing.days_on_market != null && listing.days_on_market <= 7}
          <span class="dossier-badge dossier-badge--fresh">{listing.days_on_market}D NEW</span>
        {:else if listing.days_on_market != null && listing.days_on_market > 90}
          <span class="dossier-badge dossier-badge--stale">{listing.days_on_market}D</span>
        {:else if listing.is_new}
          <span class="dossier-badge dossier-badge--new">NEW</span>
        {/if}

        {#if showScore && listing.match_score != null}
          <div class="dossier-score dossier-score--{scoreTier}">
            <span class="score-pct">{Math.round(listing.match_score)}%</span>
            <span class="score-txt">MATCH</span>
          </div>
        {/if}
      </div>

      <!-- Body Section -->
      <div class="dossier-body">
        <!-- Price - Serif, commanding -->
        <div class="dossier-price">{formatPrice(listing.price)}</div>

        <!-- Address - Mono, precise -->
        <address class="dossier-address">{listing.address}</address>

        <!-- Stats Grid - Bento layout -->
        <div class="dossier-stats">
          <div class="stat">
            <span class="stat-value">{listing.beds || '—'}</span>
            <span class="stat-label">BD</span>
          </div>
          <div class="stat">
            <span class="stat-value">{listing.baths || '—'}</span>
            <span class="stat-label">BA</span>
          </div>
          <div class="stat">
            <span class="stat-value">{formatNumber(listing.sqft)}</span>
            <span class="stat-label">SQFT</span>
          </div>
          {#if pricePerSqft}
            <div class="stat stat--wide">
              <span class="stat-value">${formatNumber(pricePerSqft)}</span>
              <span class="stat-label">/SQFT</span>
            </div>
          {/if}
        </div>

        <!-- Property Intel -->
        {#if intel.length > 0}
          <div class="dossier-intel">
            <span class="intel-label">INTEL</span>
            <div class="intel-tags">
              {#each intel.slice(0, 3) as feature}
                <span class="intel-tag">{feature.label}</span>
              {/each}
              {#if intel.length > 3}
                <span class="intel-tag intel-tag--more">+{intel.length - 3}</span>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Match Narrative (if available) -->
        {#if listing.match_narrative}
          <p class="dossier-narrative">{listing.match_narrative}</p>
        {/if}
      </div>
    </article>
  </a>
{/if}

<style>
  .dossier-link {
    text-decoration: none;
    color: inherit;
    display: block;
    opacity: 0;
    animation: dossier-enter 200ms var(--ease-out, ease-out) forwards;
  }

  @keyframes dossier-enter {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .dossier-card {
    background: var(--color-paper, #fff);
    border: 1px solid var(--color-border, #e5e5e5);
    border-radius: var(--radius-md, 4px);
    overflow: hidden;
    transition: border-color 100ms var(--ease-out, ease-out);
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .dossier-card:hover {
    border-color: var(--color-ink, #000);
  }

  /* Top match - orange accent border */
  .dossier-card--top {
    border-color: var(--color-accent, #FF6600);
    border-width: 2px;
  }

  .dossier-card--top:hover {
    border-color: var(--color-accent-hover, #E65C00);
  }

  /* Photo Section */
  .dossier-photo {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 10;
    overflow: hidden;
    background: var(--color-gray-100, #f5f5f5);
  }

  .dossier-photo img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0;
    transition: opacity 200ms var(--ease-out, ease-out);
  }

  .dossier-photo img.loaded {
    opacity: 1;
  }

  .photo-placeholder {
    position: absolute;
    inset: 0;
  }

  /* Badges */
  .dossier-badge {
    position: absolute;
    top: var(--space-3, 12px);
    left: var(--space-3, 12px);
    padding: var(--space-1, 4px) var(--space-2, 8px);
    font-family: var(--font-family-mono, monospace);
    font-size: var(--font-size-xs, 10px);
    font-weight: var(--font-weight-bold, 700);
    letter-spacing: var(--tracking-wider, 0.05em);
    border-radius: var(--radius-sm, 2px);
    z-index: 1;
  }

  .dossier-badge--new {
    background: var(--color-ink, #000);
    color: var(--color-paper, #fff);
  }

  .dossier-badge--fresh {
    background: var(--color-score-excellent, #1B5E20);
    color: white;
  }

  .dossier-badge--stale {
    background: var(--color-gray-400, #999);
    color: white;
  }

  /* Score Badge */
  .dossier-score {
    position: absolute;
    top: var(--space-3, 12px);
    right: var(--space-3, 12px);
    padding: var(--space-2, 8px) var(--space-3, 12px);
    font-family: var(--font-family-mono, monospace);
    border-radius: var(--radius-md, 4px);
    display: flex;
    align-items: baseline;
    gap: var(--space-1, 4px);
    z-index: 2;
  }

  .dossier-score--excellent {
    background: var(--color-score-excellent, #1B5E20);
    color: white;
  }

  .dossier-score--good {
    background: var(--color-score-good, #2E7D32);
    color: white;
  }

  .dossier-score--fair {
    background: var(--color-score-fair, #F57C00);
    color: white;
  }

  .dossier-score--low {
    background: var(--color-gray-400, #999);
    color: white;
  }

  .score-pct {
    font-size: var(--font-size-md, 16px);
    font-weight: var(--font-weight-bold, 700);
    line-height: 1;
  }

  .score-txt {
    font-size: var(--font-size-xs, 10px);
    font-weight: var(--font-weight-medium, 500);
    letter-spacing: var(--tracking-wider, 0.05em);
    opacity: 0.9;
  }

  /* Body Section */
  .dossier-body {
    padding: var(--space-4, 16px);
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--space-2, 8px);
  }

  /* Price - Serif typography for authority */
  .dossier-price {
    font-family: var(--font-family-serif, Georgia, serif);
    font-size: var(--font-size-2xl, 32px);
    font-weight: var(--font-weight-normal, 400);
    letter-spacing: var(--tracking-tight, -0.02em);
    color: var(--color-ink, #000);
    line-height: 1.1;
  }

  /* Address - Mono typography for precision */
  .dossier-address {
    font-family: var(--font-family-mono, monospace);
    font-size: var(--font-size-sm, 12px);
    font-style: normal;
    color: var(--color-text-secondary, #666);
    letter-spacing: var(--tracking-wide, 0.02em);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* Stats Grid - Bento layout */
  .dossier-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border: 1px solid var(--color-border, #e5e5e5);
    border-radius: var(--radius-sm, 2px);
    margin-top: var(--space-2, 8px);
  }

  .stat {
    padding: var(--space-2, 8px) var(--space-1, 4px);
    text-align: center;
    border-right: 1px solid var(--color-border, #e5e5e5);
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .stat:last-child {
    border-right: none;
  }

  .stat--wide {
    grid-column: span 1;
  }

  .stat-value {
    font-family: var(--font-family-mono, monospace);
    font-size: var(--font-size-base, 14px);
    font-weight: var(--font-weight-semibold, 600);
    color: var(--color-ink, #000);
    line-height: 1;
  }

  .stat-label {
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-xs, 10px);
    font-weight: var(--font-weight-medium, 500);
    color: var(--color-text-tertiary, #999);
    letter-spacing: var(--tracking-widest, 0.1em);
    text-transform: uppercase;
  }

  /* Property Intel Section */
  .dossier-intel {
    margin-top: auto;
    padding-top: var(--space-3, 12px);
    border-top: 1px solid var(--color-border, #e5e5e5);
  }

  .intel-label {
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-xs, 10px);
    font-weight: var(--font-weight-semibold, 600);
    color: var(--color-text-tertiary, #999);
    letter-spacing: var(--tracking-widest, 0.1em);
    text-transform: uppercase;
    display: block;
    margin-bottom: var(--space-2, 8px);
  }

  .intel-tags {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-1, 4px);
  }

  .intel-tag {
    padding: var(--space-1, 4px) var(--space-2, 8px);
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-xs, 10px);
    font-weight: var(--font-weight-medium, 500);
    color: var(--color-ink, #000);
    background: var(--color-gray-100, #f5f5f5);
    border: 1px solid var(--color-border, #e5e5e5);
    border-radius: var(--radius-sm, 2px);
    letter-spacing: var(--tracking-wide, 0.02em);
    transition: all 100ms var(--ease-out, ease-out);
  }

  .dossier-card:hover .intel-tag {
    border-color: var(--color-gray-400, #999);
  }

  .intel-tag--more {
    background: transparent;
    color: var(--color-text-tertiary, #999);
  }

  /* Match Narrative */
  .dossier-narrative {
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-sm, 12px);
    font-style: italic;
    color: var(--color-text-secondary, #666);
    line-height: var(--line-height-normal, 1.5);
    margin: 0;
    margin-top: var(--space-2, 8px);
  }

  /* Skeleton State */
  .dossier-card--skeleton {
    opacity: 0;
    animation: dossier-enter 200ms var(--ease-out, ease-out) forwards;
  }

  .skeleton-image {
    width: 100%;
    aspect-ratio: 16 / 10;
  }

  .skeleton-price {
    height: 36px;
    width: 140px;
  }

  .skeleton-address {
    height: 16px;
    width: 200px;
  }

  .skeleton-stats {
    height: 52px;
    width: 100%;
    margin-top: var(--space-2, 8px);
  }

  /* Dark Mode */
  @media (prefers-color-scheme: dark) {
    .dossier-card {
      background: var(--color-surface, #111);
    }

    .dossier-photo {
      background: var(--color-gray-200, #2a2a2a);
    }

    .intel-tag {
      background: var(--color-gray-200, #2a2a2a);
    }
  }

  /* Responsive */
  @media (max-width: 640px) {
    .dossier-body {
      padding: var(--space-3, 12px);
    }

    .dossier-price {
      font-size: var(--font-size-xl, 24px);
    }

    .dossier-stats {
      grid-template-columns: repeat(3, 1fr);
    }

    .stat--wide {
      display: none;
    }
  }
</style>
