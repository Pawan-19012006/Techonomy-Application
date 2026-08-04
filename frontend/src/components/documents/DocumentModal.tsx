import React from 'react';
import { X, FileText, Download, Calendar, HardDrive, Layers, CheckCircle2 } from 'lucide-react';
import { DocumentMetadata } from '../../types';

interface DocumentModalProps {
  document: DocumentMetadata | null;
  isOpen: boolean;
  onClose: () => void;
}

export const DocumentModal: React.FC<DocumentModalProps> = ({ document, isOpen, onClose }) => {
  if (!isOpen || !document) return null;

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="enterprise-card w-full max-w-2xl overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 line-clamp-1">
                {document.filename}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Document Metadata & Viewer Status
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6">
          {/* Document Preview Placeholder Banner */}
          <div className="h-48 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex flex-col items-center justify-center text-center p-6 space-y-3">
            <FileText className="w-12 h-12 text-slate-400" />
            <div>
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                Interactive Document Preview
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-md">
                PDF document metadata is indexed and verified for RAG knowledge analysis.
              </p>
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
              <span className="text-[10px] font-semibold uppercase text-slate-400 flex items-center gap-1">
                <Layers className="w-3 h-3" /> Total Pages
              </span>
              <p className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-1">
                {document.pages} Pages
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
              <span className="text-[10px] font-semibold uppercase text-slate-400 flex items-center gap-1">
                <HardDrive className="w-3 h-3" /> File Size
              </span>
              <p className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-1">
                {formatBytes(document.file_size)}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
              <span className="text-[10px] font-semibold uppercase text-slate-400 flex items-center gap-1">
                <Calendar className="w-3 h-3" /> Upload Date
              </span>
              <p className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-1">
                {new Date(document.uploaded_at).toLocaleDateString()}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60">
              <span className="text-[10px] font-semibold uppercase text-slate-400 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-500" /> Status
              </span>
              <p className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mt-1 uppercase">
                {document.status || 'Ready'}
              </p>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/50">
          <span className="text-xs text-slate-500 font-mono">
            Document ID: #{document.id}
          </span>
          <div className="flex items-center gap-2">
            <button onClick={onClose} className="enterprise-btn-secondary text-xs">
              Close
            </button>
            <a
              href={`/api${document.file_path}`}
              target="_blank"
              rel="noreferrer"
              className="enterprise-btn-primary text-xs"
            >
              <Download className="w-3.5 h-3.5" />
              Download File
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
