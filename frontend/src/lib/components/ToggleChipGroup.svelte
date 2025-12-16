<script>
  export let label = '';
</script>

<div class="chip-group">
  {#if label}
    <span class="chip-group-label">{label}</span>
  {/if}
  <div class="chip-group-chips">
    <slot />
  </div>
</div>

<style>
  .chip-group {
    display: flex;
    flex-direction: column;
    gap: var(--space-2, 8px);
  }

  .chip-group-label {
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-xs, 10px);
    font-weight: var(--font-weight-semibold, 600);
    color: var(--color-text-tertiary, #999);
    letter-spacing: var(--tracking-widest, 0.1em);
    text-transform: uppercase;
  }

  .chip-group-chips {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2, 8px);
  }
</style>
