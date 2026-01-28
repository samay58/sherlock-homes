import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { PropertyListing } from '@/lib/types'
import { TEST_USER_ID } from '@/lib/user'

export function useMatches() {
  return useQuery({
    queryKey: ['matches', TEST_USER_ID],
    queryFn: () => api.get<PropertyListing[]>(`/matches/user/${TEST_USER_ID}`),
  })
}
