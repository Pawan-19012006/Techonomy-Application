import { useQuery } from '@tanstack/react-query';
import { getDocumentsApi } from '../api/documents';

export const useDocuments = () => {
  const documentsQuery = useQuery({
    queryKey: ['documents'],
    queryFn: getDocumentsApi,
  });

  return {
    ...documentsQuery,
    uploadDocument: async (_args?: { file: File; pages?: number }) => {},
    isUploading: false,
    deleteDocument: async (_docId?: any) => {},
    isDeleting: false,
  };
};
