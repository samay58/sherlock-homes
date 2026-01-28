import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { PropertyListing } from '@/lib/types'

const USER_ID = 'test-user' // TODO: Replace with actual user management

export function useMatches() {
  return useQuery({
    queryKey: ['matches', USER_ID],
    queryFn: () => api.get<PropertyListing[]>(`/matches/${USER_ID}`),
  })
}
