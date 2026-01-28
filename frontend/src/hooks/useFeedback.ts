import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { TEST_USER_ID } from '@/lib/user'

type FeedbackType = 'like' | 'dislike' | 'neutral'

interface FeedbackPayload {
  listingId: number
  feedbackType: FeedbackType | null
}

export function useFeedback() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ listingId, feedbackType }: FeedbackPayload) =>
      feedbackType
        ? api.post(`/feedback/${listingId}`, { feedback_type: feedbackType })
        : api.del(`/feedback/${listingId}`),
    onSuccess: () => {
      // Optionally invalidate matches to remove disliked items
      queryClient.invalidateQueries({ queryKey: ['matches', TEST_USER_ID] })
    },
  })
}
