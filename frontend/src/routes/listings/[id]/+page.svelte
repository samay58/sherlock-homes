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

        <!-- Qualitative Flags -->
        <h4>Features:</h4>
        <ul class="features">
          <li class:present={listing.has_natural_light_keywords}>Natural Light Keywords</li>
          <li class:present={listing.has_high_ceiling_keywords}>High Ceiling Keywords</li>
          <li class:present={listing.has_outdoor_space_keywords}>Outdoor Space Keywords</li>
        </ul>
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
      /* Styles for info section */
  }
  .price {
      font-size: 1.8rem;
      font-weight: bold;
      margin-bottom: 1rem;
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

  .features {
      list-style: none;
      padding: 0;
      margin: 0.5rem 0 0 0;
  }
  .features li {
      padding: 0.25rem 0;
      color: #888; /* Default muted color */
  }
   .features li.present {
       color: #28a745; /* Green if present */
       font-weight: 500;
   }
  .features li::before {
       content: '✘ '; /* Default X mark */
       color: #dc3545; /* Red */
       margin-right: 0.5em;
   }
   .features li.present::before {
       content: '✔ '; /* Check mark if present */
       color: #28a745; /* Green */
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