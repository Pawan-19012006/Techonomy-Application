import React, { useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  FileText,
  Loader2,
  AlertCircle,
  RefreshCw,
  Target,
  Maximize2,
} from 'lucide-react';
import * as pdfjsLib from 'pdfjs-dist';
import { getDocumentFileUrl } from '../services/api';
import { useDocuments } from '../hooks/useDocuments';

// Set up PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;

interface PageCanvasProps {
  pdfDoc: pdfjsLib.PDFDocumentProxy;
  pageNum: number;
  scale: number;
  isTargetPage: boolean;
  onVisible: (pageNum: number) => void;
}

const PageCanvas: React.FC<PageCanvasProps> = ({
  pdfDoc,
  pageNum,
  scale,
  isTargetPage,
  onVisible,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const renderTaskRef = useRef<any>(null);

  const [shouldRender, setShouldRender] = useState<boolean>(isTargetPage || pageNum <= 3);
  const [rendering, setRendering] = useState<boolean>(true);
  const [dimensions, setDimensions] = useState<{ width: number; height: number }>({
    width: 600,
    height: 800,
  });

  // Observe viewport visibility for lazy rendering
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setShouldRender(true);
            onVisible(pageNum);
          }
        });
      },
      {
        rootMargin: '500px 0px 500px 0px',
        threshold: 0.1,
      }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [pageNum, onVisible]);

  // High-DPI Retina PDF Page Renderer
  useEffect(() => {
    if (!shouldRender || !pdfDoc) return;

    let isMounted = true;

    const renderPage = async () => {
      try {
        setRendering(true);
        const page = await pdfDoc.getPage(pageNum);
        if (!isMounted) return;

        // Account for Retina / High-DPI displays (e.g. devicePixelRatio = 2)
        const outputScale = window.devicePixelRatio || 1;
        const viewport = page.getViewport({ scale });

        setDimensions({ width: viewport.width, height: viewport.height });

        const canvas = canvasRef.current;
        if (!canvas) return;

        const context = canvas.getContext('2d', { alpha: false });
        if (!context) return;

        // Canvas physical backing dimensions (scaled for high DPI)
        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);

        // Canvas logical CSS display size
        canvas.style.width = `${Math.floor(viewport.width)}px`;
        canvas.style.height = `${Math.floor(viewport.height)}px`;

        // Cancel previous render task if active
        if (renderTaskRef.current) {
          try {
            renderTaskRef.current.cancel();
          } catch (e) {
            // Ignore cancellation error
          }
        }

        const transform = outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null;

        const renderContext = {
          canvasContext: context,
          transform: transform,
          viewport: viewport,
          canvas: canvas,
        };

        const task = page.render(renderContext);
        renderTaskRef.current = task;
        await task.promise;

        if (isMounted) {
          setRendering(false);
        }
      } catch (err: any) {
        if (err?.name !== 'RenderingCancelledException' && isMounted) {
          console.error(`Page ${pageNum} render error:`, err);
          setRendering(false);
        }
      }
    };

    renderPage();

    return () => {
      isMounted = false;
      if (renderTaskRef.current) {
        try {
          renderTaskRef.current.cancel();
        } catch (e) {
          // Ignore
        }
      }
    };
  }, [pdfDoc, pageNum, scale, shouldRender]);

  return (
    <div
      id={`pdf-page-${pageNum}`}
      ref={containerRef}
      data-page-number={pageNum}
      className={`relative my-6 mx-auto rounded-xl transition-all ${
        isTargetPage
          ? 'ring-4 ring-indigo-500 shadow-2xl shadow-indigo-500/20'
          : 'shadow-xl border border-slate-200 dark:border-slate-800'
      }`}
      style={{
        width: dimensions.width ? `${dimensions.width}px` : 'auto',
        minHeight: dimensions.height ? `${dimensions.height}px` : '600px',
      }}
    >
      {/* Page Badge */}
      <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-slate-950/90 text-white font-mono text-[11px] font-bold z-10 flex items-center gap-1.5 shadow-md">
        <span>Page {pageNum}</span>
        {isTargetPage && (
          <span className="text-amber-400 font-extrabold flex items-center gap-1">
            <Target className="w-3.5 h-3.5" /> CITATION SOURCE
          </span>
        )}
      </div>

      {/* Loading Overlay */}
      {rendering && (
        <div
          className="absolute inset-0 bg-slate-100 dark:bg-slate-900/80 rounded-xl flex items-center justify-center z-0 backdrop-blur-xs"
          style={{ minHeight: `${dimensions.height || 600}px` }}
        >
          <div className="flex items-center gap-2 text-slate-500 font-mono text-xs font-bold">
            <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
            <span>Rendering Page {pageNum}...</span>
          </div>
        </div>
      )}

      <canvas ref={canvasRef} className="mx-auto block rounded-xl bg-white" />
    </div>
  );
};

export const DocumentViewerPage: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const isAdminContext = location.pathname.startsWith('/admin');

  const handleBack = () => {
    if (isAdminContext) {
      navigate('/admin/documents');
    } else {
      navigate('/documents');
    }
  };

  const { data: documents = [] } = useDocuments();

  const initialPage = parseInt(searchParams.get('page') || '1', 10);
  const [targetPage] = useState<number>(initialPage > 0 ? initialPage : 1);
  const [currentPage, setCurrentPage] = useState<number>(initialPage > 0 ? initialPage : 1);
  const [scale, setScale] = useState<number>(1.2);

  const [pdfDoc, setPdfDoc] = useState<pdfjsLib.PDFDocumentProxy | null>(null);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const documentName = docId ? decodeURIComponent(docId) : 'Document.pdf';

  // Load PDF Document via ArrayBuffer from Backend API
  useEffect(() => {
    let isSubscribed = true;

    const loadPdf = async () => {
      try {
        setLoading(true);
        setError(null);

        const fileUrl = getDocumentFileUrl(documentName);
        const response = await fetch(fileUrl);

        if (!response.ok) {
          throw new Error(`Failed to fetch document (${response.status} ${response.statusText})`);
        }

        const arrayBuffer = await response.arrayBuffer();
        if (!isSubscribed) return;

        const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
        const loadedPdf = await loadingTask.promise;

        if (!isSubscribed) return;

        setPdfDoc(loadedPdf);
        setTotalPages(loadedPdf.numPages);
        setLoading(false);
      } catch (err: any) {
        console.error('PDF Loading Error:', err);
        if (isSubscribed) {
          setError(err?.message || 'Unable to render PDF document.');
          setLoading(false);
        }
      }
    };

    loadPdf();

    return () => {
      isSubscribed = false;
    };
  }, [documentName]);

  // Jump to target page on initial load
  useEffect(() => {
    if (!loading && pdfDoc && targetPage > 0) {
      setTimeout(() => {
        const el = document.getElementById(`pdf-page-${targetPage}`);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          setCurrentPage(targetPage);
        }
      }, 350);
    }
  }, [loading, pdfDoc, targetPage]);

  const handleJumpToPage = (pageNum: number) => {
    if (pageNum >= 1 && pageNum <= totalPages) {
      setCurrentPage(pageNum);
      const el = document.getElementById(`pdf-page-${pageNum}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  };

  const handlePageVisible = (pageNum: number) => {
    setCurrentPage(pageNum);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-4 select-none">
      
      {/* TOOLBAR & NAVIGATION HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-2xl bg-white dark:bg-[#0F172A] border border-slate-200/90 dark:border-slate-800 shadow-sm transition-colors">
        
        {/* Left: Back Button & Title */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleBack}
            className="kairos-btn-secondary p-2.5 text-xs font-bold flex items-center gap-2"
            title="Back to Library"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Back to Library</span>
          </button>

          <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 hidden sm:block" />

          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-base font-extrabold text-slate-950 dark:text-white truncate max-w-md">
                {documentName}
              </h1>
              <p className="text-[11px] font-mono text-slate-400">
                Official KAIROS Challenge Source Document
              </p>
            </div>
          </div>
        </div>

        {/* Center: Page Navigation Controls */}
        <div className="flex items-center justify-center gap-2 p-1 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
          <button
            onClick={() => handleJumpToPage(currentPage - 1)}
            disabled={currentPage <= 1}
            className="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white dark:hover:bg-slate-800 disabled:opacity-30 transition-colors"
            title="Previous Page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-1.5 text-xs font-mono font-bold px-2 text-slate-900 dark:text-slate-100">
            <span>Page</span>
            <input
              type="number"
              min={1}
              max={totalPages || 1}
              value={currentPage}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                if (!isNaN(val)) handleJumpToPage(val);
              }}
              className="w-12 text-center py-0.5 px-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-xs font-mono font-bold text-slate-950 dark:text-white focus:outline-none focus:border-indigo-500"
            />
            <span className="text-slate-400">/ {totalPages || 1}</span>
          </div>

          <button
            onClick={() => handleJumpToPage(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white dark:hover:bg-slate-800 disabled:opacity-30 transition-colors"
            title="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Right: High-Res Zoom Controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800 text-xs font-mono">
            <button
              onClick={() => setScale((s) => Math.max(0.6, s - 0.2))}
              className="p-1.5 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="px-2 text-slate-700 dark:text-slate-300 font-bold">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={() => setScale((s) => Math.min(2.5, s + 0.2))}
              className="p-1.5 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

      </div>

      {/* DOCUMENT VIEWER CANVAS WORKSPACE */}
      <div
        ref={containerRef}
        className="relative rounded-2xl bg-slate-950/90 dark:bg-[#070A10] border border-slate-800 p-4 sm:p-6 shadow-2xl h-[780px] overflow-y-auto space-y-8 scroll-smooth"
      >
        {loading ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-3">
            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            <p className="text-xs font-mono uppercase tracking-wider">Rendering High-Resolution PDF Document...</p>
          </div>
        ) : error ? (
          <div className="h-full flex flex-col items-center justify-center text-red-400 space-y-3 p-6 text-center">
            <AlertCircle className="w-10 h-10 text-red-500" />
            <div className="space-y-1">
              <h3 className="text-base font-bold text-white">Unable to render PDF document</h3>
              <p className="text-xs font-mono text-slate-400 max-w-md">{error}</p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="kairos-btn-secondary py-2 px-4 text-xs font-bold flex items-center gap-2 mt-2"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Loading</span>
            </button>
          </div>
        ) : pdfDoc ? (
          <div className="space-y-8 py-2">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((pNum) => (
              <PageCanvas
                key={pNum}
                pdfDoc={pdfDoc}
                pageNum={pNum}
                scale={scale}
                isTargetPage={pNum === targetPage}
                onVisible={handlePageVisible}
              />
            ))}
          </div>
        ) : null}
      </div>

    </div>
  );
};
