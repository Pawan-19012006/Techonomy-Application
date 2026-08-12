import { DocumentMetadata, DocumentUploadResponse, DocumentDeleteResponse } from '../types';

const MOCK_DOCUMENTS: DocumentMetadata[] = [
  {
    id: 1,
    filename: 'annual_report.pdf',
    file_path: '/data/documents/annual_report.pdf',
    file_size: 1548200,
    content_type: 'application/pdf',
    pages: 124,
    status: 'ready',
    team_id: 1,
    uploaded_at: new Date().toISOString(),
  },
  {
    id: 2,
    filename: 'financial_statement_2024.pdf',
    file_path: '/data/documents/financial_statement_2024.pdf',
    file_size: 842100,
    content_type: 'application/pdf',
    pages: 45,
    status: 'ready',
    team_id: 1,
    uploaded_at: new Date().toISOString(),
  },
  {
    id: 3,
    filename: 'market_research_report.pdf',
    file_path: '/data/documents/market_research_report.pdf',
    file_size: 2100400,
    content_type: 'application/pdf',
    pages: 89,
    status: 'ready',
    team_id: 1,
    uploaded_at: new Date().toISOString(),
  },
];

export const getDocumentsApi = async (): Promise<DocumentMetadata[]> => {
  return MOCK_DOCUMENTS;
};

export const getDocumentMetadataApi = async (docId: number): Promise<DocumentMetadata> => {
  return MOCK_DOCUMENTS.find((d) => d.id === docId) || MOCK_DOCUMENTS[0];
};

export const uploadDocumentApi = async (file: File, pages: number = 1): Promise<DocumentUploadResponse> => {
  const newDoc: DocumentMetadata = {
    id: Date.now(),
    filename: file.name,
    file_path: `/data/documents/${file.name}`,
    file_size: file.size,
    content_type: file.type || 'application/pdf',
    pages,
    status: 'ready',
    team_id: 1,
    uploaded_at: new Date().toISOString(),
  };
  return {
    message: 'Document uploaded successfully',
    document: newDoc,
  };
};

export const deleteDocumentApi = async (docId: number): Promise<DocumentDeleteResponse> => {
  return {
    message: 'Document deleted successfully',
    doc_id: docId,
  };
};
