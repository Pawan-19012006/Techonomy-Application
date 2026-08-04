import { useMutation, useQueryClient } from '@tanstack/react-query';
import { postChatQueryApi } from '../api/chat';
import { toast } from 'sonner';

export const useChatMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (query: string) => postChatQueryApi(query),
    onSuccess: () => {
      // Invalidate questions quota & dashboard query to reflect consumed token immediately
      queryClient.invalidateQueries({ queryKey: ['team-questions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['team-history'] });
    },
    onError: (error: any) => {
      const status = error?.response?.status;
      const detail = error?.response?.data?.detail;

      if (status === 429) {
        toast.error('Question Limit Reached: ' + (detail || 'You have used all available question tokens.'));
      } else {
        toast.error(detail || 'Failed to process prompt query.');
      }
    },
  });
};
