import { api } from '$lib/api';
import type { PageLoad } from './$types';
import type { PropertyListing } from '$lib/types';
import { error as svelteKitError } from '@sveltejs/kit';

export const load: PageLoad = async ({ fetch }) => {
  console.log("Loading matches for test user...");
  try {
    // Pass fetch to api.get
    const matches: PropertyListing[] = await api.get('/matches/test-user', fetch);
    console.log(`Loaded ${matches?.length ?? 0} matches.`);
    
    return {
      matches: matches || [], 
      error: null as string | null 
    };
  } catch (error) {
    console.error("Failed to load matches:", error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to fetch matches';
    // Allow page to load but show error
    return {
      matches: [] as PropertyListing[],
      error: errorMessage
    };
     // Alternatively, throw error: throw svelteKitError(500, errorMessage);
  }
}; 