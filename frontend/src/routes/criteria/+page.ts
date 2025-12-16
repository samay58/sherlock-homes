import { api } from '$lib/api';
import type { PageLoad } from './$types';
import type { Criteria } from '$lib/types';
import { error as svelteKitError } from '@sveltejs/kit';

export const load: PageLoad = async ({ fetch }) => {
  console.log("Loading test user criteria...");
  try {
    // Pass fetch to api.get
    const criteria: Criteria = await api.get('/criteria/test-user', fetch);
    console.log("Loaded criteria:", criteria);
    
    return {
      criteria: criteria, 
      error: null as string | null 
    };
  } catch (error) {
    console.error("Failed to load criteria:", error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to fetch criteria';
     // Throw error to prevent page load if criteria can't be fetched initially
    throw svelteKitError(500, errorMessage);
    // return {
    //   criteria: null, // Or provide a default empty criteria object?
    //   error: errorMessage
    // };
  }
}; 