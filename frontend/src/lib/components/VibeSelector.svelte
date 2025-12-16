<script>
  import { createEventDispatcher } from 'svelte';

  export let selected = null; // 'light_chaser' | 'urban_professional' | 'deal_hunter' | null

  const dispatch = createEventDispatcher();

  const vibes = [
    {
      id: 'light_chaser',
      name: 'Light Chaser',
      icon: '',
      tagline: 'South-facing, big windows, views for days',
      color: '#FFB300'
    },
    {
      id: 'urban_professional',
      name: 'Urban Pro',
      icon: '',
      tagline: 'Walk to work, nightlife-ready',
      color: '#1976D2'
    },
    {
      id: 'deal_hunter',
      name: 'Deal Hunter',
      icon: '',
      tagline: 'Price drops, motivated sellers',
      color: '#388E3C'
    }
  ];

  function selectVibe(vibeId) {
    const newValue = selected === vibeId ? null : vibeId;
    selected = newValue;
    dispatch('change', { vibe: newValue });
  }
</script>

<div class="vibe-selector">
  <span class="vibe-label">SORT BY VIBE</span>
  <div class="vibe-cards">
    {#each vibes as vibe}
      <button
        type="button"
        class="vibe-card"
        class:vibe-card--active={selected === vibe.id}
        on:click={() => selectVibe(vibe.id)}
      >
        <span class="vibe-icon">{vibe.icon}</span>
        <span class="vibe-name">{vibe.name}</span>
        <span class="vibe-tagline">{vibe.tagline}</span>
      </button>
    {/each}
  </div>
</div>

<style>
  .vibe-selector {
    display: flex;
    flex-direction: column;
    gap: var(--space-3, 12px);
  }

  .vibe-label {
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-xs, 10px);
    font-weight: var(--font-weight-semibold, 600);
    color: var(--color-text-tertiary, #999);
    letter-spacing: var(--tracking-widest, 0.1em);
  }

  .vibe-cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-3, 12px);
  }

  .vibe-card {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-1, 4px);
    padding: var(--space-4, 16px);
    background: var(--color-paper, #fff);
    border: 1px solid var(--color-border, #e5e5e5);
    border-radius: var(--radius-md, 4px);
    cursor: pointer;
    transition: all 100ms var(--ease-out, ease-out);
    text-align: left;
  }

  .vibe-card:hover {
    border-color: var(--color-ink, #000);
  }

  .vibe-card--active {
    border-color: var(--color-ink, #000);
    border-width: 2px;
    background: var(--color-gray-100, #f5f5f5);
  }

  .vibe-icon {
    font-size: var(--font-size-xl, 24px);
    line-height: 1;
  }

  .vibe-name {
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-sm, 12px);
    font-weight: var(--font-weight-semibold, 600);
    color: var(--color-ink, #000);
    letter-spacing: var(--tracking-wider, 0.05em);
    text-transform: uppercase;
  }

  .vibe-tagline {
    font-family: var(--font-family-sans, sans-serif);
    font-size: var(--font-size-xs, 10px);
    color: var(--color-text-tertiary, #999);
    line-height: var(--line-height-snug, 1.25);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .vibe-cards {
      grid-template-columns: 1fr;
    }

    .vibe-card {
      flex-direction: row;
      align-items: center;
      gap: var(--space-3, 12px);
    }

    .vibe-icon {
      font-size: var(--font-size-2xl, 32px);
    }

    .vibe-tagline {
      display: none;
    }
  }

  /* Dark mode */
  @media (prefers-color-scheme: dark) {
    .vibe-card {
      background: var(--color-surface, #111);
      border-color: var(--color-border, #2a2a2a);
    }

    .vibe-card--active {
      background: var(--color-gray-200, #2a2a2a);
    }
  }
</style>
