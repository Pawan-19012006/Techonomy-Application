import React from 'react';
import { FileText, Eye, Trash2, Calendar, FileCheck } from 'lucide-react';
import { DocumentMetadata } from '../../types';

interface DocumentCardProps {
  document: DocumentMetadata;
  onView: (doc: DocumentMetadata) => void;
  onDelete: (docId: number) => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ document, onView, onDelete }) => {
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="enterprise-card p-5 flex flex-col justify-between hover:shadow-md transition-shadow group">
      <div className="space-y-3">
        {/* Header Icon & Status */}
        <div className="flex items-start justify-between">
          <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400">
            <FileText className="w-6 h-6" />
          </div>
          <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900">
            {document.status || 'Ready'}
          </span>
        </div>

        {/* Title & Metadata */}
        <div>
          <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 line-clamp-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
            {document.filename}
          </h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {document.pages} {document.pages === 1 ? 'page' : 'pages'} • {formatBytes(document.file_size)}
          </p>
        </div>

        {/* Details Footer */}
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            {new Date(document.uploaded_at).toLocaleDateString()}
          </span>
          <span className="flex items-center gap-1 font-mono">
            <FileCheck className="w-3.5 h-3.5 text-indigo-500" />
            PDF
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-4 pt-3 flex items-center gap-2">
        <button
          onClick={() => onView(document)}
          className="flex-1 enterprise-btn-secondary text-xs py-2 px-3 justify-center"
        >
          <Eye className="w-3.5 h-3.5" />
          View
        </button>
        <button
          onClick={() => onDelete(document.id)}
          className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 rounded-lg transition-colors border border-slate-200 dark:border-slate-800"
          title="Delete Document"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
