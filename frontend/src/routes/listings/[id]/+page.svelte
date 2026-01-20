<script lang="ts">
  import type { PageData } from './$types';
  import ImageGallery from '$lib/components/ImageGallery.svelte'; // Assuming a gallery component

  export let data: PageData;

  const { listing, error } = data;

  // Helper to format currency
  const formatPrice = (price) => {
    if (price == null) return 'Price N/A';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(price);
  };

  // Helper to format sqft
  const formatSqft = (sqft) => {
    if (sqft == null || sqft === 0) return 'N/A';
    return `${new Intl.NumberFormat('en-US').format(sqft)} sqft`;
  };

  const formatScore = (score) => {
    if (score == null) return '—';
    return `${Math.round(score)}%`;
  };

  const formatSignal = (value) => {
    if (value == null) return null;
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return null;
    return Math.round(numeric * 10) / 10;
  };

  const deriveSignal = (key, fallback) => {
    if (listing?.signals && listing.signals[key] != null) {
      return formatSignal(listing.signals[key]);
    }
    return formatSignal(fallback);
  };

  $: featureTags = [
    listing?.has_natural_light_keywords ? 'Natural Light' : null,
    listing?.has_high_ceiling_keywords ? 'High Ceilings' : null,
    listing?.has_outdoor_space_keywords ? 'Outdoor Space' : null,
    listing?.has_parking_keywords ? 'Parking' : null,
    listing?.has_view_keywords ? 'Views' : null,
    listing?.has_updated_systems_keywords ? 'Updated Systems' : null,
    listing?.has_architectural_details_keywords ? 'Character' : null,
  ].filter(Boolean);

  $: signalData = (() => {
    const data = [];
    const light = deriveSignal(
      'light_potential',
      listing?.light_potential_score != null ? listing.light_potential_score / 10 : null
    );
    const quiet = deriveSignal(
      'tranquility_score',
      listing?.tranquility_score != null ? listing.tranquility_score / 10 : null
    );
    const visual = deriveSignal(
      'visual_quality',
      listing?.visual_quality_score != null ? listing.visual_quality_score / 10 : null
    );
    const character = deriveSignal('nlp_character_score', null);

    if (light != null) data.push({ label: 'Light', value: light });
    if (quiet != null) data.push({ label: 'Quiet', value: quiet });
    if (visual != null) data.push({ label: 'Visual', value: visual });
    if (character != null) data.push({ label: 'Character', value: character });

    return data;
  })();

</script>

<svelte:head>
  <title>{ listing ? listing.address : 'Listing Detail' } - Sherlock Homes</title>
</svelte:head>

<section class="listing-detail">
  {#if error}
    <p class="error">Error loading listing: {error}</p>
  {:else if listing}
    <h2>{listing.address}</h2>
    
    <div class="main-content">
      <div class="gallery-container">
         {#if listing.photos && listing.photos.length > 0}
           <ImageGallery images={listing.photos} altText={`Photos of ${listing.address}`} />
         {:else}
           <img src="/placeholder-image.svg" alt="Placeholder" class="placeholder-image" />
         {/if}
      </div>

      <div class="info-container">
        <div class="price">{formatPrice(listing.price)}</div>
        <div class="scoreline">
          <span class="score-percent">{formatScore(listing.match_score)}</span>
          {#if listing.score_points != null}
            <span class="score-points">{listing.score_points.toFixed(1)} pts</span>
          {/if}
          {#if listing.score_tier}
            <span class="score-tier">{listing.score_tier}</span>
          {/if}
        </div>
        <ul class="quick-stats">
          <li><strong>{listing.beds ?? 'N/A'}</strong> bds</li>
          <li><strong>{listing.baths ?? 'N/A'}</strong> ba</li>
          <li><strong>{formatSqft(listing.sqft)}</strong></li>
          {#if listing.year_built}<li>Built <strong>{listing.year_built}</strong></li>{/if}
        </ul>
        
        <div class="status-type">
          {#if listing.listing_status}<span class="tag status">{listing.listing_status}</span>{/if}
          {#if listing.property_type}<span class="tag type">{listing.property_type}</span>{/if}
        </div>

        {#if listing.url}
            <a href={listing.url} target="_blank" rel="noopener noreferrer" class="external-link">View on Zillow</a>
        {/if}

        {#if listing.walk_score}
          <p><strong>Walk Score®:</strong> {listing.walk_score}</p>
        {/if}

        {#if featureTags.length > 0}
          <div class="feature-block">
            <span class="feature-label">FEATURES</span>
            <div class="feature-tags">
              {#each featureTags as feature}
                <span class="feature-tag">{feature}</span>
              {/each}
            </div>
          </div>
        {/if}

        {#if listing.match_reasons?.length || listing.key_tradeoff || listing.why_now || listing.match_narrative}
          <div class="explain-block">
            <span class="feature-label">EXPLAINABILITY</span>
            {#if listing.match_reasons?.length}
              <p class="explain-row">
                <span class="explain-label">Top</span>
                <span class="explain-value">{listing.match_reasons.join(' · ')}</span>
              </p>
            {/if}
            {#if listing.key_tradeoff}
              <p class="explain-row">
                <span class="explain-label">Tradeoff</span>
                <span class="explain-value">{listing.key_tradeoff}</span>
              </p>
            {/if}
            {#if listing.why_now}
              <p class="explain-row">
                <span class="explain-label">Why now</span>
                <span class="explain-value">{listing.why_now}</span>
              </p>
            {/if}
            {#if listing.match_narrative}
              <p class="explain-row">
                <span class="explain-label">Note</span>
                <span class="explain-value">{listing.match_narrative}</span>
              </p>
            {/if}
          </div>
        {/if}

        {#if signalData.length > 0}
          <div class="signal-block">
            <span class="feature-label">SIGNALS</span>
            <div class="signal-tags">
              {#each signalData as signal}
                <span class="signal-tag">
                  <span class="signal-name">{signal.label}</span>
                  <span class="signal-value">{signal.value}</span>
                </span>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>

    {#if listing.description}
      <div class="description">
        <h3>Description</h3>
        <p>{listing.description}</p>
      </div>
    {/if}

  {:else}
    <p>Listing not found.</p>
  {/if}
</section>

<style>
  .listing-detail h2 {
    margin-bottom: 1.5rem;
  }
  .main-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-bottom: 2rem;
  }
  .gallery-container {
      /* Styles for gallery or placeholder */
      background-color: #f0f0f0; /* Placeholder background */
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 300px; /* Ensure it has some height */
  }
  .placeholder-image {
      max-width: 100px;
      opacity: 0.5;
  }

  .info-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
  }
  .price {
      font-family: var(--font-family-serif, Georgia, serif);
      font-size: 2rem;
      font-weight: 400;
      letter-spacing: -0.02em;
  }
  .scoreline {
      display: flex;
      align-items: baseline;
      gap: 0.75rem;
      font-family: var(--font-family-mono, monospace);
      font-size: 0.85rem;
      color: var(--color-text-tertiary, #999);
      text-transform: uppercase;
      letter-spacing: 0.08em;
  }
  .score-percent {
      font-size: 1rem;
      color: var(--color-ink, #000);
      letter-spacing: 0.05em;
  }
  .score-points {
      color: var(--color-text-secondary, #666);
  }
  .score-tier {
      color: var(--color-text-tertiary, #999);
  }
  .quick-stats {
      list-style: none;
      padding: 0;
      margin: 0 0 1rem 0;
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
      font-size: 1.1rem;
  }
   .quick-stats li strong {
       font-weight: 600;
   }

  .status-type {
      margin-bottom: 1rem;
      display: flex;
      gap: 0.5rem;
  }
  .tag {
      display: inline-block;
      padding: 0.25em 0.6em;
      font-size: 0.8rem;
      border-radius: 4px;
      background-color: #eee;
      color: #333;
  }
  .tag.status {
      background-color: #e7f3ff;
      color: #0366d6;
  }
  .tag.type {
       background-color: #f0f0f0;
   }
  
  .external-link {
       display: inline-block;
       margin-bottom: 1rem;
       color: #0366d6;
       text-decoration: none;
   }
   .external-link:hover {
       text-decoration: underline;
   }

  .feature-block,
  .signal-block,
  .explain-block {
      border: 1px solid var(--color-border, #e5e5e5);
      border-radius: 6px;
      padding: 0.75rem;
      background: var(--color-paper, #fff);
  }

  .feature-label {
      display: block;
      font-family: var(--font-family-sans, sans-serif);
      font-size: 0.65rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--color-text-tertiary, #999);
      margin-bottom: 0.5rem;
  }

  .feature-tags,
  .signal-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
  }

  .feature-tag,
  .signal-tag {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.2rem 0.5rem;
      font-family: var(--font-family-sans, sans-serif);
      font-size: 0.75rem;
      color: var(--color-ink, #000);
      background: var(--color-gray-100, #f5f5f5);
      border: 1px solid var(--color-border, #e5e5e5);
      border-radius: 999px;
  }

  .signal-name {
      font-size: 0.6rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--color-text-tertiary, #999);
  }

  .signal-value {
      font-family: var(--font-family-mono, monospace);
      font-size: 0.7rem;
  }

  .explain-row {
      margin: 0 0 0.6rem 0;
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
  }

  .explain-row:last-child {
      margin-bottom: 0;
  }

  .explain-label {
      font-size: 0.65rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--color-text-tertiary, #999);
  }

  .explain-value {
      font-size: 0.9rem;
      color: var(--color-ink, #000);
  }

  .description {
      margin-top: 2rem;
      border-top: 1px solid #eee;
      padding-top: 1.5rem;
  }
  .description h3 {
      margin-bottom: 1rem;
  }
  .description p {
      line-height: 1.6;
      white-space: pre-wrap; /* Preserve line breaks from description */
  }
  .error {
      color: red;
  }
</style> 
