<script lang="ts">
  import { onMount } from 'svelte';
  import type { PageData } from './$types';
  import type { Criteria } from '$lib/types';
  import { api } from '$lib/api';

  export let data: PageData;

  let criteriaData: Partial<Criteria> = {}; // Use Partial for form binding
  let isLoading = false;
  let errorMessage: string | null = null;
  let successMessage: string | null = null;

  // Reactive statement to update form when props change
  $: {
    if (data.criteria) {
      // Initialize form with loaded data (or defaults if null)
      criteriaData = {
        name: data.criteria.name ?? 'My Criteria',
        price_min: data.criteria.price_min ?? null,
        price_max: data.criteria.price_max ?? null,
        beds_min: data.criteria.beds_min ?? null,
        baths_min: data.criteria.baths_min ?? null,
        sqft_min: data.criteria.sqft_min ?? null,
        require_natural_light: data.criteria.require_natural_light ?? false,
        require_high_ceilings: data.criteria.require_high_ceilings ?? false,
        require_outdoor_space: data.criteria.require_outdoor_space ?? false,
        // id and user_id are not directly editable here
      };
    } 
    // Reset messages if data changes
    errorMessage = data.error ?? null;
    successMessage = null; 
  }

  async function handleSubmit() {
    isLoading = true;
    errorMessage = null;
    successMessage = null;

    // Prepare payload, ensuring null values for empty number inputs
    // Create a clean payload based on criteriaData
    const payload: Partial<Criteria> = {
      name: criteriaData.name,
      price_min: criteriaData.price_min || null,
      price_max: criteriaData.price_max || null,
      beds_min: criteriaData.beds_min || null,
      baths_min: criteriaData.baths_min || null,
      sqft_min: criteriaData.sqft_min || null,
      require_natural_light: criteriaData.require_natural_light,
      require_high_ceilings: criteriaData.require_high_ceilings,
      require_outdoor_space: criteriaData.require_outdoor_space,
      // We don't send id or user_id, backend uses path param
      // is_active will be forced true by backend for this simple version
    };

    console.log("Saving criteria:", payload);

    try {
      const updatedCriteria: Criteria = await api.post('/criteria/test-user', payload);
      successMessage = "Criteria saved successfully!";
      console.log("Save successful:", updatedCriteria);
      // Update local form state to reflect saved data (including potentially new defaults/ID)
      criteriaData = { ...criteriaData, ...updatedCriteria }; 
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Failed to save criteria';
      console.error("Save failed:", error);
    } finally {
      isLoading = false;
    }
  }
</script>

<svelte:head>
  <title>My Criteria - Sherlock Homes</title>
</svelte:head>

<section>
  <h2>My Matching Criteria (Test User)</h2>

  {#if errorMessage}
    <p class="error">{errorMessage}</p>
  {/if}
  {#if successMessage}
    <p class="success">{successMessage}</p>
  {/if}

  {#if data.criteria} <!-- Only show form if initial load succeeded -->
    <form on:submit|preventDefault={handleSubmit} class="criteria-form">
      <div class="form-group">
        <label for="name">Criteria Name:</label>
        <input type="text" id="name" bind:value={criteriaData.name} />
      </div>

      <fieldset>
        <legend>Quantitative Filters</legend>
        <div class="form-row">
          <div class="form-group">
            <label for="price_min">Min Price:</label>
            <input type="number" id="price_min" bind:value={criteriaData.price_min} placeholder="Any" />
          </div>
          <div class="form-group">
            <label for="price_max">Max Price:</label>
            <input type="number" id="price_max" bind:value={criteriaData.price_max} placeholder="Any" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="beds_min">Min Beds:</label>
            <input type="number" step="1" min="0" id="beds_min" bind:value={criteriaData.beds_min} placeholder="Any" />
          </div>
          <div class="form-group">
            <label for="baths_min">Min Baths:</label>
            <input type="number" step="0.5" min="0" id="baths_min" bind:value={criteriaData.baths_min} placeholder="Any" />
          </div>
          <div class="form-group">
            <label for="sqft_min">Min Sqft:</label>
            <input type="number" step="50" min="0" id="sqft_min" bind:value={criteriaData.sqft_min} placeholder="Any" />
          </div>
        </div>
      </fieldset>

      <fieldset>
        <legend>Qualitative Filters</legend>
        <div class="form-group checkbox-group">
          <input type="checkbox" id="natural_light" bind:checked={criteriaData.require_natural_light} />
          <label for="natural_light">Require Natural Light Keywords?</label>
        </div>
        <div class="form-group checkbox-group">
          <input type="checkbox" id="high_ceilings" bind:checked={criteriaData.require_high_ceilings} />
          <label for="high_ceilings">Require High Ceiling Keywords?</label>
        </div>
        <div class="form-group checkbox-group">
          <input type="checkbox" id="outdoor_space" bind:checked={criteriaData.require_outdoor_space} />
          <label for="outdoor_space">Require Outdoor Space Keywords?</label>
        </div>
      </fieldset>

      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Saving...' : 'Save Criteria'}
      </button>
    </form>
  {:else if !errorMessage} <!-- Show loading if no error but no criteria yet (shouldn't happen if load throws) -->
    <p>Loading criteria...</p>
  {/if}
</section>

<style>
  .criteria-form fieldset {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
  }
  .criteria-form legend {
    font-weight: bold;
    padding: 0 0.5em;
  }
  .form-row {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    margin-bottom: 1rem;
  }
  .form-group {
    display: flex;
    flex-direction: column;
    margin-bottom: 1rem; 
    flex: 1; /* Allow flexible sizing */
    min-width: 150px; /* Prevent becoming too small */
  }
  .form-group label {
    margin-bottom: 0.3rem;
    font-size: 0.9rem;
    font-weight: 500;
  }
  .form-group input[type="text"],
  .form-group input[type="number"] {
    padding: 0.6rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1rem;
  }
   .checkbox-group {
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }
  .checkbox-group input[type="checkbox"] {
     width: 1.1em; 
     height: 1.1em;
  }
   .checkbox-group label {
     margin-bottom: 0;
     font-weight: normal;
   }

  button {
    padding: 0.7rem 1.5rem;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
  button:not(:disabled):hover {
    background-color: #0056b3;
  }
  .error {
    color: red;
    margin-bottom: 1rem;
    border: 1px solid red;
    padding: 0.5rem 1rem;
    border-radius: 4px;
  }
  .success {
    color: green;
    margin-bottom: 1rem;
    border: 1px solid green;
    padding: 0.5rem 1rem;
    border-radius: 4px;
  }
</style> 