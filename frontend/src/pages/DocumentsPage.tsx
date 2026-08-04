import React, { useState, useMemo } from 'react';
import { Search, UploadCloud, RefreshCw, FileText } from 'lucide-react';
import { useDocuments } from '../hooks/useDocuments';
import { DocumentCard } from '../components/documents/DocumentCard';
import { DocumentModal } from '../components/documents/DocumentModal';
import { UploadModal } from '../components/documents/UploadModal';
import { TableRowSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorState } from '../components/common/ErrorState';
import { DocumentMetadata } from '../types';

export const DocumentsPage: React.FC = () => {
  const { data: documents = [], isLoading, isError, refetch, uploadDocument, isUploading, deleteDocument } = useDocuments();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) =>
      doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [documents, searchTerm]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
            Documents
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            All company documents and reports available for your intelligence analysis.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="enterprise-btn-secondary text-xs"
            title="Refresh List"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
          <button
            onClick={() => setIsUploadModalOpen(true)}
            className="enterprise-btn-primary text-xs"
          >
            <UploadCloud className="w-4 h-4" />
            Upload Document
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="enterprise-card p-4 flex items-center justify-between gap-4">
        <div className="relative flex-1">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search documents by name..."
            className="enterprise-input w-full pl-10 text-sm"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        </div>
        <span className="text-xs text-slate-500 font-medium whitespace-nowrap">
          {filteredDocuments.length} document(s)
        </span>
      </div>

      {/* Loading / Error / Content */}
      {isLoading ? (
        <div className="space-y-3">
          <TableRowSkeleton />
          <TableRowSkeleton />
          <TableRowSkeleton />
        </div>
      ) : isError ? (
        <ErrorState onRetry={refetch} />
      ) : filteredDocuments.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No documents found"
          description={
            searchTerm
              ? `No document names matching "${searchTerm}". Try clearing your search.`
              : 'Upload your first document metadata file to begin knowledge indexing.'
          }
          actionLabel="Upload Document"
          onAction={() => setIsUploadModalOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredDocuments.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              onView={(docToView) => setSelectedDoc(docToView)}
              onDelete={(id) => deleteDocument(id)}
            />
          ))}
        </div>
      )}

      {/* Inspection Modal */}
      <DocumentModal
        document={selectedDoc}
        isOpen={!!selectedDoc}
        onClose={() => setSelectedDoc(null)}
      />

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUpload={async (file, pages) => {
          await uploadDocument({ file, pages });
        }}
        isUploading={isUploading}
      />
    </div>
  );
};
