<script>
  import ListingCard from '$lib/components/ListingCard.svelte';

  export let data; // Data loaded from +page.js or +page.server.js
</script>

<svelte:head>
  <title>Browse Listings - Sherlock Homes</title>
</svelte:head>

<section>
  <h2>Browse Listings</h2>

  {#if data.error}
    <p class="error">Error loading listings: {data.error}</p>
  {:else if data.listings && data.listings.length > 0}
    <div class="listings-grid">
      {#each data.listings as listing (listing.id)}
        <ListingCard {listing} />
      {/each}
    </div>
    <!-- TODO: Add pagination controls later -->
  {:else}
    <p>No listings found.</p>
  {/if}
</section>

<style>
  .listings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); /* Responsive grid */
    gap: 1.5rem;
    margin-top: 1rem;
  }

  .error {
    color: red;
    border: 1px solid red;
    padding: 1rem;
    border-radius: 4px;
  }
</style> 