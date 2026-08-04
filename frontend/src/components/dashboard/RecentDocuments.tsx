import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, ChevronRight } from 'lucide-react';
import { DocumentMetadata } from '../../types';

interface RecentDocumentsProps {
  documents?: DocumentMetadata[];
  onViewDoc?: (doc: DocumentMetadata) => void;
}

export const RecentDocuments: React.FC<RecentDocumentsProps> = ({ documents = [], onViewDoc }) => {
  const defaultDocs: Partial<DocumentMetadata>[] = [
    { id: 1, filename: 'Annual_Report_2024.pdf', pages: 102, uploaded_at: '09:15 AM' },
    { id: 2, filename: 'Financial_Statements_Q4.pdf', pages: 84, uploaded_at: '09:10 AM' },
    { id: 3, filename: 'Market_Research_Report.pdf', pages: 67, uploaded_at: '09:05 AM' },
    { id: 4, filename: 'Competitor_Analysis.pdf', pages: 45, uploaded_at: '09:00 AM' },
  ];

  const docsToDisplay = documents.length > 0 ? documents.slice(0, 4) : defaultDocs;

  return (
    <div className="enterprise-card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Recent Documents
        </h3>
        <Link
          to="/documents"
          className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
        >
          View All
        </Link>
      </div>

      <div className="space-y-2">
        {docsToDisplay.map((doc) => (
          <div
            key={doc.id}
            onClick={() => onViewDoc && onViewDoc(doc as DocumentMetadata)}
            className="flex items-center justify-between p-3 rounded-lg border border-slate-100 dark:border-slate-800 hover:border-indigo-200 dark:hover:border-indigo-900 hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400">
                <FileText className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                  {doc.filename}
                </span>
                <span className="text-[11px] text-slate-500 dark:text-slate-400">
                  {doc.pages ? `${doc.pages} pages • ` : ''}Uploaded {doc.uploaded_at}
                </span>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors" />
          </div>
        ))}
      </div>
    </div>
  );
};
