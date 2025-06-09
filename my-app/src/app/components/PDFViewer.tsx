'use client';

import { useState, useEffect } from 'react';

interface PDFViewerProps {
  url: string;
}

export default function PDFViewer({ url }: PDFViewerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  // Reset state when URL changes
  useEffect(() => {
    setLoading(true);
    setError(false);
    setIsFullscreen(false);
    setShowHelp(false);
  }, [url]);

  const handleLoad = () => {
    setLoading(false);
    setError(false);
  };

  const handleError = () => {
    setLoading(false);
    setError(true);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const exitFullscreen = () => {
    setIsFullscreen(false);
  };

  const enterBrowserFullscreen = () => {
    if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen();
    }
  };

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isFullscreen) {
        exitFullscreen();
        return;
      }
      
      // Handle fullscreen toggle
      if ((e.key === 'f' || e.key === 'F') && (isFullscreen || document.activeElement?.closest('.pdf-viewer'))) {
        e.preventDefault();
        toggleFullscreen();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen]);

  const PDFContent = () => (
    <div className={`relative ${isFullscreen ? 'h-screen' : 'h-[calc(100vh-100px)]'} bg-gray-50`}>
      {/* Controls */}
      <div className={`bg-gray-100 p-3 border-b border-gray-300 ${isFullscreen ? 'sticky top-0 z-50' : ''}`}>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-medium text-gray-700">PDF Viewer</h3>
            {loading && (
              <span className="text-xs text-blue-600">Loading...</span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {isFullscreen ? (
              <button
                onClick={exitFullscreen}
                className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
              >
                ✕ Exit Fullscreen
              </button>
            ) : (
              <button
                onClick={toggleFullscreen}
                className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 text-sm"
              >
                ⛶ Fullscreen
              </button>
            )}
            
            <button
              onClick={enterBrowserFullscreen}
              className="px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm"
              title="Enter browser fullscreen mode"
            >
              📺 Browser Full
            </button>
            
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 text-sm"
              title="Keyboard shortcuts"
            >
              ❓ Help
            </button>
            
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
            >
              Open ↗
            </a>
          </div>
        </div>
      </div>

      {/* Help Modal */}
      {showHelp && (
        <div className="absolute top-16 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 z-40 max-w-xs">
          <div className="flex justify-between items-center mb-3">
            <h4 className="font-semibold text-gray-800">Keyboard Shortcuts</h4>
            <button
              onClick={() => setShowHelp(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
          <div className="text-sm text-gray-600 space-y-1">
            <div><kbd className="bg-gray-100 px-1 rounded">F</kbd> Toggle fullscreen</div>
            <div><kbd className="bg-gray-100 px-1 rounded">Esc</kbd> Exit fullscreen</div>
            <div className="mt-2 text-xs text-gray-500">
              Use browser PDF controls for navigation and zoom
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
          <div className="flex flex-col items-center space-y-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="text-gray-600">Loading PDF...</span>
          </div>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
          <div className="text-center p-6">
            <div className="text-red-500 text-xl mb-4">📄❌</div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Failed to load PDF</h3>
            <p className="text-sm text-gray-600 mb-4">
              The PDF could not be displayed in this browser.
            </p>
            <div className="space-x-3">
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 inline-block"
              >
                Open in New Tab
              </a>
              <button
                onClick={() => window.location.reload()}
                className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PDF iframe */}
      <iframe
        src={url + `?t=${Date.now()}#toolbar=1&navpanes=0&scrollbar=1&page=1&zoom=100`}
        className={`w-full border-0 ${isFullscreen ? 'h-[calc(100vh-60px)]' : 'h-[calc(100vh-160px)]'}`}
        onLoad={handleLoad}
        onError={handleError}
        title="PDF Viewer"
        style={{ display: loading || error ? 'none' : 'block' }}
        allow="fullscreen"
      />
    </div>
  );

  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-white">
        <PDFContent />
      </div>
    );
  }

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden bg-white pdf-viewer" tabIndex={0}>
      <PDFContent />
    </div>
  );
} 