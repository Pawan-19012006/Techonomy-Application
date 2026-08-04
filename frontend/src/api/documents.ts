import { apiClient } from './axios';
import { DocumentMetadata, DocumentUploadResponse, DocumentDeleteResponse } from '../types';

export const getDocumentsApi = async (): Promise<DocumentMetadata[]> => {
  const response = await apiClient.get<DocumentMetadata[]>('/documents');
  return response.data;
};

export const getDocumentMetadataApi = async (docId: number): Promise<DocumentMetadata> => {
  const response = await apiClient.get<DocumentMetadata>(`/documents/${docId}`);
  return response.data;
};

export const uploadDocumentApi = async (file: File, pages: number = 1): Promise<DocumentUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<DocumentUploadResponse>(`/documents/upload?pages=${pages}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const deleteDocumentApi = async (docId: number): Promise<DocumentDeleteResponse> => {
  const response = await apiClient.delete<DocumentDeleteResponse>(`/documents/${docId}`);
  return response.data;
};
