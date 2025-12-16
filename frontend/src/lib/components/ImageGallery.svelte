<script lang="ts">
  export let images: string[] = [];
  export let altText: string = "Property photo";

  let active = 0;

  const select = (idx: number) => {
    active = idx;
  };
</script>

<div class="gallery">
  <div class="main">
    {#if images && images.length > 0}
      <img src={images[active]} alt={altText} loading="lazy" />
    {:else}
      <img src="/placeholder-image.svg" alt="No photos" class="placeholder" />
    {/if}
  </div>
  {#if images && images.length > 1}
    <div class="thumbs">
      {#each images as img, i}
        <button class:active={i === active} on:click={() => select(i)} aria-label={`Photo ${i + 1}`}>
          <img src={img} alt={altText} loading="lazy" />
        </button>
      {/each}
    </div>
  {/if}
  
</div>

<style>
  .gallery { display: grid; gap: 0.75rem; }
  .main { width: 100%; aspect-ratio: 16/10; background: #f2f2f2; overflow: hidden; border-radius: 8px; }
  .main img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .placeholder { opacity: 0.5; }
  .thumbs { display: grid; grid-auto-flow: column; gap: 0.5rem; overflow-x: auto; }
  .thumbs button { padding: 0; border: 2px solid transparent; border-radius: 6px; background: transparent; cursor: pointer; }
  .thumbs button.active { border-color: #1e88e5; }
  .thumbs img { width: 80px; height: 60px; object-fit: cover; display: block; border-radius: 4px; }
</style>

