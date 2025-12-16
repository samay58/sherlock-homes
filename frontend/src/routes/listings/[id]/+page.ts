import { api } from '$lib/api';
import type { PageLoad } from './$types';
import type { PropertyListing } from '$lib/types';
import { error as svelteKitError } from '@sveltejs/kit'; // Import SvelteKit's error helper

export const load: PageLoad = async ({ params, fetch }) => {
  const { id } = params; // Get the ID from the route parameters
  console.log(`Loading listing detail for ID: ${id}`);
  
  try {
    const listing = await api.get(`/listings/${id}`, fetch); 
    
    if (!listing) {
      // Use SvelteKit's error helper for 404
      throw svelteKitError(404, 'Listing not found');
    }

    return {
      listing: listing as PropertyListing, // Cast to our defined type
      error: null
    };
  } catch (error) {
    console.error(`Failed to load listing ${id}:`, error);
    
    // Handle potential 404 from API or other errors
    if (error instanceof Error && error.message.includes('404')) {
         throw svelteKitError(404, 'Listing not found');
    } else if (error instanceof Error) {
         // Use SvelteKit's error for other errors, passing the message
         throw svelteKitError(500, error.message || 'Failed to fetch listing');
    } else {
         // Fallback for unknown errors
         throw svelteKitError(500, 'An unknown error occurred');
    }
    
    // This return is now unreachable due to throwing errors, which is intended
    // return {
    //   listing: null,
    //   error: error.message || 'Failed to fetch listing'
    // };
  }
}; 