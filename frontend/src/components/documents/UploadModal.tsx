import React, { useState } from 'react';
import { X, UploadCloud, File, AlertCircle } from 'lucide-react';
import { useDocuments } from '../../hooks/useDocuments';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload?: (file: File, pages: number) => Promise<void>;
  isUploading?: boolean;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUpload: customOnUpload,
  isUploading: customIsUploading,
}) => {
  const { uploadDocument, isUploading: hookIsUploading } = useDocuments();
  const isUploading = customIsUploading ?? hookIsUploading;

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pages, setPages] = useState<number>(10);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a document file to upload.');
      return;
    }

    try {
      if (customOnUpload) {
        await customOnUpload(selectedFile, pages);
      } else {
        await uploadDocument({ file: selectedFile, pages });
      }
      setSelectedFile(null);
      setPages(10);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to upload document.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
      <div className="kairos-card w-full max-w-lg overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
        
        {/* Header */}
        <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-950 dark:text-white">
                Upload Document Metadata
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Index PDF files into vector storage space
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

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3.5 rounded-xl bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
              <span>{error}</span>
            </div>
          )}

          {/* Dropzone */}
          <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-2xl p-6 text-center hover:border-slate-950 dark:hover:border-white transition-colors bg-slate-50/50 dark:bg-slate-900/40">
            <input
              type="file"
              id="file-upload"
              accept=".pdf,.md,.txt,.doc,.docx"
              onChange={handleFileChange}
              className="hidden"
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer flex flex-col items-center justify-center space-y-2"
            >
              <div className="p-3 rounded-2xl bg-white dark:bg-slate-800 shadow-sm border border-slate-200 dark:border-slate-700">
                <File className="w-8 h-8 text-slate-700 dark:text-slate-300" />
              </div>
              <span className="text-sm font-semibold text-slate-900 dark:text-white">
                {selectedFile ? selectedFile.name : 'Click to select or drag document'}
              </span>
              <span className="text-xs text-slate-400">
                PDF, MD, TXT up to 50MB
              </span>
            </label>
          </div>

          {/* Pages Input */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Page Count Estimate
            </label>
            <input
              type="number"
              min={1}
              value={pages}
              onChange={(e) => setPages(parseInt(e.target.value) || 1)}
              className="kairos-input w-full"
            />
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="kairos-btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUploading || !selectedFile}
              className="kairos-btn-primary text-xs disabled:opacity-40"
            >
              {isUploading ? 'Uploading...' : 'Confirm Upload'}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
