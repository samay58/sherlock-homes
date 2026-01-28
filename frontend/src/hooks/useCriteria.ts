import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Criteria } from '@/lib/types'

const USER_ID = 'test-user' // TODO: Replace with actual user management

export function useCriteria() {
  return useQuery({
    queryKey: ['criteria', USER_ID],
    queryFn: () => api.get<Criteria>(`/criteria/${USER_ID}`),
  })
}

export function useUpdateCriteria() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (criteria: Partial<Criteria>) =>
      api.put<Criteria>(`/criteria/${USER_ID}`, criteria),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['criteria', USER_ID] })
      queryClient.invalidateQueries({ queryKey: ['matches', USER_ID] })
    },
  })
}
