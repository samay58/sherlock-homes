import { api } from '$lib/api';
import type { PageLoad } from './$types';
import type { PropertyListing } from '$lib/types'; // Assuming types file exists or will be created

export const load: PageLoad = async ({ fetch }) => {
  console.log("Loading listings data...");
  try {
    const listings: PropertyListing[] = await api.get('/listings', fetch); 
    console.log(`Loaded ${listings?.length ?? 0} listings.`);
    return {
      listings: listings || [], 
      error: null as string | null // Explicitly type error
    };
  } catch (error) {
    console.error("Failed to load listings:", error);
    const errorMessage = error instanceof Error ? error.message : 'Failed to fetch listings';
    return {
      listings: [] as PropertyListing[], // Explicitly type empty array
      error: errorMessage
    };
  }
}; 