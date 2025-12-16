<script>
  export let type = 'text'; // text, card, list, image
  export let rows = 1;
  export let width = '100%';
  export let height = 'auto';
</script>

{#if type === 'text'}
  <div class="skeleton skeleton-text" style="width: {width};">
    {#each Array(rows) as _, i}
      <div class="skeleton-line" style="width: {i === rows - 1 ? '80%' : '100%'}"></div>
    {/each}
  </div>
{:else if type === 'card'}
  <div class="skeleton skeleton-card" style="width: {width}; height: {height};">
    <div class="skeleton-image"></div>
    <div class="skeleton-content">
      <div class="skeleton-title"></div>
      <div class="skeleton-description"></div>
      <div class="skeleton-metadata"></div>
    </div>
  </div>
{:else if type === 'list'}
  <div class="skeleton skeleton-list" style="width: {width};">
    {#each Array(rows) as _}
      <div class="skeleton-list-item">
        <div class="skeleton-avatar"></div>
        <div class="skeleton-list-content">
          <div class="skeleton-list-title"></div>
          <div class="skeleton-list-subtitle"></div>
        </div>
      </div>
    {/each}
  </div>
{:else if type === 'image'}
  <div class="skeleton skeleton-image-standalone" style="width: {width}; height: {height};"></div>
{/if}

<style>
  .skeleton {
    animation: skeleton-pulse 2s ease-in-out infinite;
  }
  
  @keyframes skeleton-pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
  
  /* Text Skeleton */
  .skeleton-text {
    display: flex;
    flex-direction: column;
    gap: var(--space-2, 8px);
  }
  
  .skeleton-line {
    height: var(--font-size-base, 16px);
    background: linear-gradient(
      90deg,
      var(--color-gray-200, #e5e5e5) 0%,
      var(--color-gray-100, #f5f5f5) 50%,
      var(--color-gray-200, #e5e5e5) 100%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    border-radius: var(--radius-sm, 4px);
  }
  
  /* Card Skeleton */
  .skeleton-card {
    background: var(--color-background, #fff);
    border: 1px solid var(--color-border, #e5e5e5);
    border-radius: var(--radius-xl, 12px);
    overflow: hidden;
  }
  
  .skeleton-card .skeleton-image {
    width: 100%;
    aspect-ratio: 16 / 10;
    background: linear-gradient(
      90deg,
      var(--color-gray-200, #e5e5e5) 0%,
      var(--color-gray-100, #f5f5f5) 50%,
      var(--color-gray-200, #e5e5e5) 100%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
  }
  
  .skeleton-content {
    padding: var(--space-5, 20px);
    display: flex;
    flex-direction: column;
    gap: var(--space-3, 12px);
  }
  
  .skeleton-title {
    height: 28px;
    width: 60%;
    background: linear-gradient(
      90deg,
      var(--color-gray-200, #e5e5e5) 0%,
      var(--color-gray-100, #f5f5f5) 50%,
      var(--color-gray-200, #e5e5e5) 100%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    border-radius: var(--radius-sm, 4px);
  }
  
  .skeleton-description {
    height: 16px;
    width: 100%;
    background: linear-gradient(
      90deg,
      var(--color-gray-200, #e5e5e5) 0%,
      var(--color-gray-100, #f5f5f5) 50%,
      var(--color-gray-200, #e5e5e5) 100%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    border-radius: var(--radius-sm, 4px);
  }
  
  .skeleton-metadata {
    height: 14px;
    width: 40%;
    background: linear-gradient(
      90deg,
      var(--color-gray-200, #e5e5e5) 0%,
      var(--color-gray-100, #f5f5f5) 50%,
      var(--color-gray-200, #e5e5e5) 100%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    border-radius: var(--radius-sm, 4px);
  }
  
  /* List Skeleton */
  .skeleton-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-4, 16px);
  }
  
  .skeleton-list-item {
    display: flex;
    align-items: center;
    gap: var(--space-3, 12px);
  }
  
  .skeleton-avatar {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-full, 9999px);
    background: linear-gradient(
      90deg,
      var(--color-gray-200, #e5e5e5) 0%,
      var(--color-gray-100, #f5f5f5) 50%,
      var(--color-gray-200, #e5e5e5) 100%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    flex-shrink: 0;
  }
  
  .skeleton-list-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--space-2, 8px);
  }
  
  .skeleton-list-title {
    height: 18px;
    width: 70%;
    background: linear-gradient(
      90deg,
      var(--color-gray-200, #e5e5e5) 0%,
      var(--color-gray-100, #f5f5f5) 50%,
      var(--color-gray-200, #e5e5e5) 100%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    border-radius: var(--radius-sm, 4px);
  }
  
  .skeleton-list-subtitle {
    height: 14px;
    width: 50%;
    background: linear-gradient(
      90deg,
      var(--color-gray-200, #e5e5e5) 0%,
      var(--color-gray-100, #f5f5f5) 50%,
      var(--color-gray-200, #e5e5e5) 100%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    border-radius: var(--radius-sm, 4px);
  }
  
  /* Image Skeleton */
  .skeleton-image-standalone {
    background: linear-gradient(
      90deg,
      var(--color-gray-200, #e5e5e5) 0%,
      var(--color-gray-100, #f5f5f5) 50%,
      var(--color-gray-200, #e5e5e5) 100%
    );
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    border-radius: var(--radius-lg, 8px);
  }
  
  @keyframes skeleton-loading {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }
  
  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .skeleton-line,
    .skeleton-card .skeleton-image,
    .skeleton-title,
    .skeleton-description,
    .skeleton-metadata,
    .skeleton-avatar,
    .skeleton-list-title,
    .skeleton-list-subtitle,
    .skeleton-image-standalone {
      background: linear-gradient(
        90deg,
        var(--color-gray-800, #262626) 0%,
        var(--color-gray-700, #404040) 50%,
        var(--color-gray-800, #262626) 100%
      );
      background-size: 200% 100%;
      animation: skeleton-loading 1.5s ease-in-out infinite;
    }
    
    .skeleton-card {
      background: var(--color-surface, #171717);
    }
  }
</style>