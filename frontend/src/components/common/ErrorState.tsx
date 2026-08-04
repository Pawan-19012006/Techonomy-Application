import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to load data',
  message = 'An error occurred while communicating with the Techonomy backend server.',
  onRetry,
  className = '',
}) => {
  return (
    <div className={`enterprise-card p-8 border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-950/20 text-center flex flex-col items-center justify-center ${className}`}>
      <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-400 flex items-center justify-center mb-3">
        <AlertCircle className="w-5 h-5" />
      </div>
      <h4 className="text-base font-semibold text-red-900 dark:text-red-200 mb-1">
        {title}
      </h4>
      <p className="text-xs text-red-700 dark:text-red-300 max-w-md mb-4">
        {message}
      </p>
      {onRetry && (
        <button onClick={onRetry} className="enterprise-btn-secondary text-xs py-2 px-3">
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Connection
        </button>
      )}
    </div>
  );
};
