<script>
  import { onMount } from 'svelte';
  
  export let listing;
  export let index = 0; // For staggered animations
  export let loading = false; // For skeleton state
  export let showScore = false; // Whether to show match score
  
  let imageLoaded = false;
  let imageError = false;
  
  const formatPrice = (price) => {
    if (price == null) return 'Price N/A';
    return new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: 'USD', 
      maximumFractionDigits: 0 
    }).format(price);
  };
  
  const formatSqft = (sqft) => {
    if (sqft == null || sqft === 0) return '';
    return `${new Intl.NumberFormat('en-US').format(sqft)} sqft`;
  };
  
  const detailUrl = `/listings/${listing?.id}`;
  const primaryPhoto = listing?.photos?.[0] || '/placeholder-image.svg';
  
  const handleImageLoad = () => {
    imageLoaded = true;
  };
  
  const handleImageError = () => {
    imageError = true;
    imageLoaded = true;
  };
  
  // Extract key features for tags
  const features = [];
  if (listing?.natural_light_flag) features.push('Natural Light');
  if (listing?.high_ceilings_flag) features.push('High Ceilings');
  if (listing?.outdoor_space_flag) features.push('Outdoor Space');
  if (listing?.modern_kitchen_flag) features.push('Modern Kitchen');
  
  // Get score display info
  const getScoreColor = (score) => {
    if (score >= 80) return 'score-excellent';
    if (score >= 60) return 'score-good';
    if (score >= 40) return 'score-fair';
    return 'score-low';
  };
  
  const getScoreBadgeText = (score) => {
    if (score >= 90) return 'Top Match';
    if (score >= 70) return 'Great Match';
    if (score >= 50) return 'Good Match';
    return 'Fair Match';
  };
  
  onMount(() => {
    // Trigger fade-in animation
    const timer = setTimeout(() => {
      imageLoaded = true;
    }, 50);
    return () => clearTimeout(timer);
  });
</script>

{#if loading}
  <!-- Skeleton Loading State -->
  <div class="listing-card skeleton-card" style="animation-delay: {index * 50}ms">
    <div class="skeleton skeleton-image"></div>
    <div class="info">
      <div class="skeleton skeleton-price"></div>
      <div class="skeleton skeleton-details"></div>
      <div class="skeleton skeleton-address"></div>
    </div>
  </div>
{:else}
  <a href={detailUrl} class="card-link" style="animation-delay: {index * 30}ms">
    <article class="listing-card">
      <div class="photo-container">
        {#if !imageLoaded}
          <div class="image-placeholder skeleton"></div>
        {/if}
        <img 
          src={imageError ? '/placeholder-image.svg' : primaryPhoto} 
          alt={`View of ${listing.address}`}
          loading="lazy"
          on:load={handleImageLoad}
          on:error={handleImageError}
          class:loaded={imageLoaded}
        />
        {#if listing.is_new}
          <span class="badge badge-new">New</span>
        {/if}
        {#if listing.price_reduction}
          <span class="badge badge-price-drop">Price Drop</span>
        {/if}
        {#if showScore && listing.match_score != null}
          <div class="match-score-badge {getScoreColor(listing.match_score)}">
            <span class="score-value">{Math.round(listing.match_score)}%</span>
            <span class="score-label">{getScoreBadgeText(listing.match_score)}</span>
          </div>
        {/if}
      </div>
      
      <div class="info">
        <div class="price-row">
          <h3 class="price">{formatPrice(listing.price)}</h3>
          {#if listing.price_per_sqft}
            <span class="price-per-sqft">${listing.price_per_sqft}/sqft</span>
          {/if}
        </div>
        
        <div class="details">
          <span class="detail-item">
            <span class="detail-value">{listing.beds || '—'}</span>
            <span class="detail-label">beds</span>
          </span>
          <span class="detail-separator">·</span>
          <span class="detail-item">
            <span class="detail-value">{listing.baths || '—'}</span>
            <span class="detail-label">baths</span>
          </span>
          {#if listing.sqft}
            <span class="detail-separator">·</span>
            <span class="detail-item">
              <span class="detail-value">{new Intl.NumberFormat('en-US').format(listing.sqft)}</span>
              <span class="detail-label">sqft</span>
            </span>
          {/if}
        </div>
        
        <address class="address">{listing.address}</address>
        
        {#if features.length > 0}
          <div class="features">
            {#each features.slice(0, 2) as feature}
              <span class="feature-tag">{feature}</span>
            {/each}
            {#if features.length > 2}
              <span class="feature-tag">+{features.length - 2}</span>
            {/if}
          </div>
        {/if}
      </div>
    </article>
  </a>
{/if}

<style>
  .card-link {
    text-decoration: none;
    color: inherit;
    display: block;
    opacity: 0;
    animation: card-fade-in var(--duration-normal, 200ms) var(--ease-out, ease-out) forwards;
  }
  
  @keyframes card-fade-in {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .listing-card {
    background: var(--color-background, #fff);
    border: 1px solid var(--color-border, #e5e5e5);
    border-radius: var(--radius-lg, 8px);
    overflow: hidden;
    transition: all var(--duration-normal, 200ms) var(--ease-out);
    position: relative;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .listing-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.1);
    border-color: var(--color-border-hover, #d4d4d4);
  }
  
  .listing-card::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--radius-xl, 12px);
    opacity: 0;
    transition: opacity var(--duration-fast, 100ms) var(--ease-out, ease-out);
    background: linear-gradient(
      to bottom,
      transparent 0%,
      transparent 50%,
      rgb(0 0 0 / 0.02) 100%
    );
    pointer-events: none;
  }
  
  .listing-card:hover::after {
    opacity: 1;
  }
  
  /* Photo Container */
  .photo-container {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 10;
    overflow: hidden;
    background: var(--color-gray-100, #f5f5f5);
  }
  
  .photo-container img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0;
    transition: all var(--duration-slow, 300ms) var(--ease-out, ease-out);
  }
  
  .photo-container img.loaded {
    opacity: 1;
  }
  
  .listing-card:hover img {
    transform: scale(1.05);
  }
  
  .image-placeholder {
    position: absolute;
    inset: 0;
    background: var(--color-gray-100, #f5f5f5);
  }
  
  /* Badges */
  .badge {
    position: absolute;
    top: var(--space-3, 12px);
    left: var(--space-3, 12px);
    padding: var(--space-1, 4px) var(--space-2, 8px);
    font-size: var(--font-size-xs, 12px);
    font-weight: var(--font-weight-semibold, 600);
    border-radius: var(--radius-md, 6px);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    z-index: 1;
  }
  
  .badge-new {
    background: rgb(16 185 129 / 0.9);
    color: white;
  }
  
  .badge-price-drop {
    background: rgb(239 68 68 / 0.9);
    color: white;
    left: auto;
    right: var(--space-3, 12px);
  }
  
  /* Info Section */
  .info {
    padding: var(--space-5, 20px);
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--space-3, 12px);
  }
  
  .price-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: var(--space-2, 8px);
  }
  
  .price {
    font-size: var(--font-size-xl, 28px);
    font-weight: var(--font-weight-semibold, 600);
    color: var(--color-text, #171717);
    margin: 0;
    letter-spacing: -0.02em;
  }
  
  .price-per-sqft {
    font-size: var(--font-size-sm, 14px);
    color: var(--color-text-tertiary, #737373);
  }
  
  .details {
    display: flex;
    align-items: center;
    gap: var(--space-2, 8px);
    color: var(--color-text-secondary, #525252);
    font-size: var(--font-size-sm, 14px);
  }
  
  .detail-item {
    display: flex;
    align-items: baseline;
    gap: var(--space-1, 4px);
  }
  
  .detail-value {
    font-weight: var(--font-weight-semibold, 600);
    color: var(--color-text, #171717);
  }
  
  .detail-label {
    color: var(--color-text-tertiary, #737373);
  }
  
  .detail-separator {
    color: var(--color-gray-300, #d4d4d4);
  }
  
  .address {
    font-style: normal;
    font-size: var(--font-size-base, 16px);
    color: var(--color-text-secondary, #525252);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  /* Features */
  .features {
    display: flex;
    gap: var(--space-2, 8px);
    flex-wrap: wrap;
    margin-top: auto;
  }
  
  .feature-tag {
    padding: var(--space-1, 4px) var(--space-2, 8px);
    background: var(--color-surface, #fafafa);
    color: var(--color-text-secondary, #525252);
    border-radius: var(--radius-full, 9999px);
    font-size: var(--font-size-xs, 12px);
    font-weight: var(--font-weight-medium, 500);
    border: 1px solid var(--color-border, #e5e5e5);
    transition: all var(--duration-fast, 100ms) var(--ease-out, ease-out);
  }
  
  .listing-card:hover .feature-tag {
    background: var(--color-gray-100, #f5f5f5);
    border-color: var(--color-gray-200, #e5e5e5);
  }
  
  /* Skeleton Loading */
  .skeleton-card {
    background: var(--color-background, #fff);
    border: 1px solid var(--color-border, #e5e5e5);
    border-radius: var(--radius-xl, 12px);
    overflow: hidden;
    opacity: 0;
    animation: card-fade-in var(--duration-normal, 200ms) var(--ease-out, ease-out) forwards;
  }
  
  .skeleton-image {
    width: 100%;
    aspect-ratio: 16 / 10;
  }
  
  .skeleton-price {
    height: 32px;
    width: 120px;
    margin-bottom: var(--space-2, 8px);
  }
  
  .skeleton-details {
    height: 20px;
    width: 180px;
    margin-bottom: var(--space-2, 8px);
  }
  
  .skeleton-address {
    height: 20px;
    width: 240px;
  }
  
  /* Match Score Badge */
  .match-score-badge {
    position: absolute;
    top: var(--space-3, 12px);
    right: var(--space-3, 12px);
    padding: var(--space-2, 8px) var(--space-3, 12px);
    border-radius: var(--radius-lg, 8px);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    min-width: 80px;
    z-index: 2;
    transition: all var(--duration-normal, 200ms) var(--ease-out, ease-out);
  }
  
  .match-score-badge.score-excellent {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.95), rgba(5, 150, 105, 0.95));
    color: white;
    box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);
  }
  
  .match-score-badge.score-good {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.95), rgba(37, 99, 235, 0.95));
    color: white;
    box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
  }
  
  .match-score-badge.score-fair {
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.95), rgba(245, 158, 11, 0.95));
    color: white;
    box-shadow: 0 4px 6px -1px rgba(251, 191, 36, 0.3);
  }
  
  .match-score-badge.score-low {
    background: linear-gradient(135deg, rgba(156, 163, 175, 0.95), rgba(107, 114, 128, 0.95));
    color: white;
    box-shadow: 0 4px 6px -1px rgba(156, 163, 175, 0.3);
  }
  
  .match-score-badge:hover {
    transform: scale(1.05);
  }
  
  .score-value {
    font-size: var(--font-size-lg, 18px);
    font-weight: var(--font-weight-bold, 700);
    line-height: 1;
    letter-spacing: -0.02em;
  }
  
  .score-label {
    font-size: var(--font-size-xs, 11px);
    font-weight: var(--font-weight-medium, 500);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.95;
  }
  
  /* Adjust price-drop badge position when score is shown */
  .match-score-badge ~ .badge-price-drop {
    top: calc(var(--space-3, 12px) + 80px);
  }
  
  /* Dark Mode Support */
  @media (prefers-color-scheme: dark) {
    .listing-card {
      background: var(--color-surface, #171717);
    }
    
    .photo-container {
      background: var(--color-gray-800, #262626);
    }
    
    .image-placeholder {
      background: var(--color-gray-800, #262626);
    }
  }
  
  /* Responsive */
  @media (max-width: 640px) {
    .info {
      padding: var(--space-4, 16px);
    }
    
    .price {
      font-size: var(--font-size-lg, 21px);
    }
  }
</style>