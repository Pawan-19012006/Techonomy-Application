import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Check, Copy } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  isStreaming?: boolean;
}

const CodeBlock: React.FC<{ language?: string; value: string }> = ({ language, value }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-3 rounded-lg overflow-hidden border border-slate-700/60 bg-slate-900 shadow-md">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-800/80 border-b border-slate-700/60 text-xs text-slate-400 font-mono">
        <span>{language || 'code'}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 hover:text-slate-200 transition-colors py-0.5 px-1.5 rounded hover:bg-slate-700/50"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-3.5 overflow-x-auto text-xs text-slate-100 font-mono leading-relaxed">
        <code>{value}</code>
      </pre>
    </div>
  );
};

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, isStreaming }) => {
  return (
    <div className="markdown-body prose dark:prose-invert max-w-none text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-4 mb-2 tracking-tight border-b border-slate-200 dark:border-slate-800 pb-1.5">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-3.5 mb-2 tracking-tight">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100 mt-3 mb-1.5">
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p className="text-sm leading-relaxed mb-3 text-slate-800 dark:text-slate-200 last:mb-0">
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-slate-900 dark:text-white">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-slate-800 dark:text-slate-200">
              {children}
            </em>
          ),
          ul: ({ children }) => (
            <ul className="list-disc list-outside ml-5 mb-3 space-y-1 text-sm text-slate-800 dark:text-slate-200">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-outside ml-5 mb-3 space-y-1 text-sm text-slate-800 dark:text-slate-200">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed pl-1">
              {children}
            </li>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-indigo-500 bg-slate-50 dark:bg-slate-900/60 pl-4 py-2 my-3 rounded-r text-slate-700 dark:text-slate-300 italic text-sm">
              {children}
            </blockquote>
          ),
          hr: () => (
            <hr className="my-4 border-slate-200 dark:border-slate-700" />
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
            >
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="my-3 overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm max-w-full">
              <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700 text-sm">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-slate-100 dark:bg-slate-800/80">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-900/40">
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className="px-3.5 py-2 text-left text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3.5 py-2 text-sm text-slate-800 dark:text-slate-200 whitespace-nowrap sm:whitespace-normal">
              {children}
            </td>
          ),
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const isInline = !match && !String(children).includes('\n');

            if (isInline) {
              return (
                <code
                  className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-indigo-600 dark:text-indigo-300 font-mono text-[0.825rem] border border-slate-200 dark:border-slate-700/60"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            return (
              <CodeBlock
                language={match ? match[1] : undefined}
                value={String(children).replace(/\n$/, '')}
              />
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>

      {isStreaming && (
        <span className="inline-block w-2 h-4 ml-1 bg-indigo-500 animate-pulse rounded-xs align-middle" />
      )}
    </div>
  );
};
