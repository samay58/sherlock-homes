import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Criteria } from '@/lib/types'
import { TEST_USER_ID } from '@/lib/user'

export function useCriteria() {
  return useQuery({
    queryKey: ['criteria', TEST_USER_ID],
    queryFn: () => api.get<Criteria>(`/criteria/user/${TEST_USER_ID}`),
  })
}

export function useUpdateCriteria() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (criteria: Partial<Criteria>) =>
      api.put<Criteria>(`/criteria/user/${TEST_USER_ID}`, criteria),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['criteria', TEST_USER_ID] })
      queryClient.invalidateQueries({ queryKey: ['matches', TEST_USER_ID] })
    },
  })
}
