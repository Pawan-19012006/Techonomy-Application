import { getDocuments } from '../services/api';
import { DocumentMetadata } from '../types';

export const getDocumentsApi = async (): Promise<DocumentMetadata[]> => {
  try {
    const raw = await getDocuments();
    return raw.map((item, index) => ({
      id: item.id || item.filename || index + 1,
      filename: item.filename,
      file_path: item.filename,
      file_size: item.size_bytes || 0,
      content_type: 'application/pdf',
      pages: item.pages || 1,
      status: item.status || 'Available',
      uploaded_at: new Date().toISOString(),
    }));
  } catch (err) {
    console.error('Error fetching documents from backend:', err);
    return [];
  }
};
