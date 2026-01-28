import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { PropertyListing } from '@/lib/types'

export function useListings() {
  return useQuery({
    queryKey: ['listings'],
    queryFn: () => api.get<PropertyListing[]>('/listings/'),
  })
}

export function useListing(id: string | number) {
  return useQuery({
    queryKey: ['listing', id],
    queryFn: () => api.get<PropertyListing>(`/listings/${id}`),
    enabled: !!id,
  })
}
