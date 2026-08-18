import React, { useState, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Search, FileText, CheckCircle2, BookOpen, ArrowRight, ShieldCheck } from 'lucide-react';
import { useDocuments } from '../hooks/useDocuments';
import { TableRowSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorState } from '../components/common/ErrorState';

export const DocumentsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isAdminContext = location.pathname.startsWith('/admin');

  const { data: documents = [], isLoading, isError, refetch } = useDocuments();
  const [searchTerm, setSearchTerm] = useState('');

  const handleOpenDoc = (filename: string) => {
    const prefix = isAdminContext ? '/admin/documents' : '/documents';
    navigate(`${prefix}/${encodeURIComponent(filename)}`);
  };

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) =>
      doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [documents, searchTerm]);

  const totalPages = documents.reduce((acc, doc) => acc + (doc.pages || 1), 0);

  const formatFileSize = (bytes: number) => {
    if (!bytes) return '0 KB';
    if (bytes >= 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 select-none">
      
      {/* HEADER BANNER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-950 dark:text-white uppercase font-sans">
            EVENT DOCUMENTS
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Official documents provided for the KAIROS challenge.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="px-3.5 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900/60 text-indigo-900 dark:text-indigo-300 text-xs font-mono font-bold flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-indigo-500" />
            <span>{documents.length} Official Document(s)</span>
          </div>
        </div>
      </div>

      {/* SEARCH BAR & COUNTER */}
      <div className="kairos-card p-4 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
        <div className="relative w-full sm:w-96">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search documents by filename..."
            className="kairos-input w-full pl-10 text-xs font-normal"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        </div>

        <span className="text-xs font-mono font-bold text-slate-500 dark:text-slate-400">
          Showing {filteredDocuments.length} of {documents.length} available document(s)
        </span>
      </div>

      {/* DOCUMENT LIBRARY LIST */}
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
              ? `No document matching "${searchTerm}". Try clearing your search term.`
              : 'No official competition documents found in storage.'
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredDocuments.map((doc) => (
            <div
              key={doc.id}
              className="kairos-card p-5 hover:border-slate-400 dark:hover:border-slate-600 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 group shadow-md"
            >
              
              {/* Document Icon & Metadata */}
              <div className="flex items-center gap-4 min-w-0">
                <div className="p-3 rounded-2xl bg-slate-950 dark:bg-white text-white dark:text-slate-950 shrink-0 group-hover:scale-105 transition-transform shadow-sm">
                  <FileText className="w-6 h-6" />
                </div>

                <div className="min-w-0 space-y-1">
                  <h3 className="text-base font-extrabold text-slate-950 dark:text-white truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                    {doc.filename}
                  </h3>

                  <div className="flex items-center gap-3 text-xs font-mono text-slate-500 dark:text-slate-400">
                    <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-bold uppercase">
                      {doc.content_type || 'PDF'}
                    </span>
                    <span>•</span>
                    <span>{doc.pages} page(s)</span>
                    <span>•</span>
                    <span>{formatFileSize(doc.file_size)}</span>
                  </div>
                </div>
              </div>

              {/* Status & Open Document Action */}
              <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                <span className="hidden lg:inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 text-xs font-mono font-bold border border-emerald-200 dark:border-emerald-900/60">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Available</span>
                </span>

                <button
                  onClick={() => handleOpenDoc(doc.filename)}
                  className="kairos-btn-primary py-2.5 px-4 text-xs font-bold uppercase tracking-wider flex items-center gap-2 group-hover:translate-x-0.5 transition-all"
                >
                  <span>View Document</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>

            </div>
          ))}
        </div>
      )}

    </div>
  );
};
