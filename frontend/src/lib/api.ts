// Renaming the file by changing its content path
// The actual content should be moved from api.js to api.ts
// Assuming the correct content is what we last edited in api.js
// Simple API client utility using fetch

const SERVER_BASE_URL = 'http://api:8000'; // For SSR within Docker

// Define a type for the fetch function signature SvelteKit uses
type FetchFn = (info: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

// Pass fetch function as argument for SvelteKit load functions
async function request(endpoint: string, fetchFn: FetchFn = fetch, options: RequestInit = {}) { 
  let url: string;
  const isSSR = import.meta.env.SSR; // Store in variable
  console.log(`>>> API Request Context: SSR=${isSSR}`); // Log SSR status

  if (isSSR) {
      url = endpoint.startsWith('http') ? endpoint : `${SERVER_BASE_URL}${endpoint}`;
  } else {
      url = endpoint; 
  }
  console.log(`>>> API Request URL: ${url}`); // Log the final URL being used
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add authorization header later if needed
  // const token = getAuthToken(); // Function to get token from storage
  // if (token) {
  //   headers['Authorization'] = `Bearer ${token}`;
  // }

  const config: RequestInit = {
    ...options,
    headers,
  };

  // Explicitly set credentials for SSR fetch if needed (though allow_credentials=True should handle it)
  if (import.meta.env.SSR) {
      config.credentials = 'include'; // or 'same-origin' depending on need
  }

  try {
    // Use the passed fetch function (could be native fetch or SvelteKit's fetch)
    const response = await fetchFn(url, config); 
    if (!response.ok) {
      // Attempt to parse error detail from backend
      let errorDetail = `HTTP error ${response.status}`;
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorDetail;
      } catch (e) { /* Ignore if error response is not JSON */ }
      throw new Error(errorDetail);
    }
    // Handle cases with no content (e.g., 204 No Content)
    if (response.status === 204) {
        return null;
    }
    // Log raw text before parsing
    const rawText = await response.text();
    console.log(`<<< Raw API Response Text for ${url}:`, rawText.substring(0, 500)); // Log first 500 chars
    return JSON.parse(rawText); // Parse the text we already read
  } catch (error) {
    console.error(`API request failed for ${options.method || 'GET'} ${url}:`, error);
    // Rethrow with a more specific message if possible
    const message = error instanceof Error ? error.message : 'fetch failed';
    throw new Error(message); 
  }
}

// Update exported methods to accept fetchFn
export const api = {
  get: (endpoint: string, fetchFn: FetchFn = fetch, options: RequestInit = {}) => 
        request(endpoint, fetchFn, { ...options, method: 'GET' }),
  post: (endpoint: string, body: any, fetchFn: FetchFn = fetch, options: RequestInit = {}) => 
        request(endpoint, fetchFn, { ...options, method: 'POST', body: JSON.stringify(body) }),
  put: (endpoint: string, body: any, fetchFn: FetchFn = fetch, options: RequestInit = {}) => 
        request(endpoint, fetchFn, { ...options, method: 'PUT', body: JSON.stringify(body) }),
  del: (endpoint: string, fetchFn: FetchFn = fetch, options: RequestInit = {}) => 
        request(endpoint, fetchFn, { ...options, method: 'DELETE' }), // 'delete' is a reserved word
}; 