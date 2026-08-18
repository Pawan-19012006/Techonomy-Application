import React from 'react';
import { FileText, Eye, Trash2, Calendar, FileCheck } from 'lucide-react';
import { DocumentMetadata } from '../../types';

interface DocumentCardProps {
  document: DocumentMetadata;
  onView: (doc: DocumentMetadata) => void;
  onDelete: (docId: string | number) => void;
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
    <div className="kairos-card p-5 flex flex-col justify-between kairos-card-hover group">
      <div className="space-y-3">
        {/* Header Icon & Status */}
        <div className="flex items-start justify-between">
          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white">
            <FileText className="w-5 h-5" />
          </div>
          <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-900/60">
            {document.status || 'Ready'}
          </span>
        </div>

        {/* Title & Metadata */}
        <div>
          <h4 className="text-sm font-bold text-slate-950 dark:text-white line-clamp-1 group-hover:text-slate-700 dark:group-hover:text-slate-300 transition-colors">
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
            <FileCheck className="w-3.5 h-3.5 text-slate-700 dark:text-slate-300" />
            PDF
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-4 pt-3 flex items-center gap-2 border-t border-slate-100 dark:border-slate-800">
        <button
          onClick={() => onView(document)}
          className="flex-1 kairos-btn-secondary text-xs py-2 px-3 justify-center"
        >
          <Eye className="w-3.5 h-3.5" />
          <span>Inspect</span>
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
