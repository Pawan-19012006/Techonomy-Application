import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDocumentsApi, uploadDocumentApi, deleteDocumentApi } from '../api/documents';
import { toast } from 'sonner';

export const useDocuments = () => {
  const queryClient = useQueryClient();

  const documentsQuery = useQuery({
    queryKey: ['documents'],
    queryFn: getDocumentsApi,
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, pages }: { file: File; pages?: number }) => uploadDocumentApi(file, pages),
    onSuccess: (data) => {
      toast.success(data.message || 'Document uploaded successfully');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to upload document');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: number) => deleteDocumentApi(docId),
    onSuccess: (data) => {
      toast.success(data.message || 'Document deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to delete document');
    },
  });

  return {
    ...documentsQuery,
    uploadDocument: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    deleteDocument: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
  };
};
