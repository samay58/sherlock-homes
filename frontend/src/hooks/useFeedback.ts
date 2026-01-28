import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

const USER_ID = 'test-user' // TODO: Replace with actual user management

interface FeedbackPayload {
  listing_id: number
  feedback_type: 'like' | 'dislike' | 'skip'
}

export function useFeedback() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: FeedbackPayload) =>
      api.post(`/feedback/${USER_ID}`, payload),
    onSuccess: () => {
      // Optionally invalidate matches to remove disliked items
      queryClient.invalidateQueries({ queryKey: ['matches', USER_ID] })
    },
  })
}
