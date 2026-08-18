import React, { useState, useMemo } from 'react';
import { Search, UploadCloud, RefreshCw, FileText, CheckCircle2, ShieldCheck, Database } from 'lucide-react';
import { useDocuments } from '../hooks/useDocuments';
import { DocumentModal } from '../components/documents/DocumentModal';
import { UploadModal } from '../components/documents/UploadModal';
import { TableRowSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorState } from '../components/common/ErrorState';
import { DocumentMetadata } from '../types';

export const DocumentsPage: React.FC = () => {
  const { data: documents = [], isLoading, isError, refetch } = useDocuments();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) =>
      doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [documents, searchTerm]);

  const totalPages = documents.reduce((acc, doc) => acc + (doc.pages || 1), 0);

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white">
            Event Documents
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Official competition documents indexed for AI vector retrieval.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="kairos-btn-secondary text-xs"
            title="Refresh List"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setIsUploadModalOpen(true)}
            className="kairos-btn-primary text-xs"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="kairos-card p-5 space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Total Sources
          </span>
          <div className="text-2xl font-extrabold text-slate-950 dark:text-white">
            {documents.length} Document(s)
          </div>
        </div>

        <div className="kairos-card p-5 space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Indexed Pages
          </span>
          <div className="text-2xl font-extrabold text-slate-950 dark:text-white">
            {totalPages} Pages
          </div>
        </div>

        <div className="kairos-card p-5 space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Vector Collection
          </span>
          <div className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
            <ShieldCheck className="w-6 h-6" />
            <span>company_knowledge</span>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="kairos-card p-4 flex items-center justify-between gap-4">
        <div className="relative flex-1">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search indexed documents by filename..."
            className="kairos-input w-full pl-10 text-sm"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        </div>
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 whitespace-nowrap">
          Showing {filteredDocuments.length} of {documents.length}
        </span>
      </div>

      {/* Documents Table (Screenshot Task List Style) */}
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
          title="No matching documents found"
          description={
            searchTerm
              ? `No document matching "${searchTerm}". Try clearing your search filter.`
              : 'Your knowledge base is waiting for its first source document.'
          }
          actionLabel="Upload Document"
          onAction={() => setIsUploadModalOpen(true)}
        />
      ) : (
        <div className="kairos-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 uppercase tracking-wider font-bold">
                  <th className="py-3.5 px-4">Filename</th>
                  <th className="py-3.5 px-4">Page Count</th>
                  <th className="py-3.5 px-4">File Size</th>
                  <th className="py-3.5 px-4">Content Type</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
                {filteredDocuments.map((doc) => (
                  <tr
                    key={doc.id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="py-4 px-4 font-bold text-slate-950 dark:text-slate-100 flex items-center gap-2.5">
                      <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                        <FileText className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                      </div>
                      <span>{doc.filename}</span>
                    </td>
                    <td className="py-4 px-4 text-slate-600 dark:text-slate-400">
                      {doc.pages} page(s)
                    </td>
                    <td className="py-4 px-4 text-slate-600 dark:text-slate-400">
                      {(doc.file_size / (1024 * 1024)).toFixed(2)} MB
                    </td>
                    <td className="py-4 px-4 text-slate-500 dark:text-slate-400 font-mono text-[11px]">
                      {doc.content_type}
                    </td>
                    <td className="py-4 px-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 text-[11px] font-semibold border border-emerald-200/60 dark:border-emerald-900/60">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                        Indexed
                      </span>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <button
                        onClick={() => setSelectedDoc(doc)}
                        className="kairos-btn-secondary py-1.5 px-3 text-xs"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Document View Modal */}
      {selectedDoc && (
        <DocumentModal
          document={selectedDoc}
          onClose={() => setSelectedDoc(null)}
        />
      )}

      {/* Upload Modal */}
      {isUploadModalOpen && (
        <UploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
        />
      )}

    </div>
  );
};
