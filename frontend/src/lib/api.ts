const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

function buildUrl(endpoint: string) {
  if (endpoint.startsWith('http')) return endpoint
  if (!API_BASE_URL) return endpoint
  return `${API_BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = buildUrl(endpoint)

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config)

    if (!response.ok) {
      let errorDetail = `HTTP error ${response.status}`
      try {
        const errorData = await response.json()
        errorDetail = errorData.detail || errorDetail
      } catch {
        // Ignore if error response is not JSON
      }
      throw new Error(errorDetail)
    }

    // Handle cases with no content (e.g., 204 No Content)
    if (response.status === 204) {
      return null as T
    }

    return response.json()
  } catch (error) {
    console.error(`API request failed for ${options.method || 'GET'} ${url}:`, error)
    const message = error instanceof Error ? error.message : 'fetch failed'
    throw new Error(message)
  }
}

export const api = {
  get: <T>(endpoint: string, options: RequestInit = {}) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, body: unknown, options: RequestInit = {}) =>
    request<T>(endpoint, { ...options, method: 'POST', body: JSON.stringify(body) }),

  put: <T>(endpoint: string, body: unknown, options: RequestInit = {}) =>
    request<T>(endpoint, { ...options, method: 'PUT', body: JSON.stringify(body) }),

  del: <T>(endpoint: string, options: RequestInit = {}) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
}
