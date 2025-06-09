'use client';

import { useState, useEffect } from 'react';
import PDFViewer from './PDFViewer';

interface ExtractResponse {
  task_id: string;
  status: string;
  message: string;
}

interface StatusResponse {
  task_id: string;
  status: string;
  message: string;
  file_path?: string;
}

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api' 
  : 'http://localhost:8000';

export default function DocumentExtractor() {
  const [url, setUrl] = useState('');
  const [mode, setMode] = useState<'pdf' | 'txt'>('pdf');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [restoredFromStorage, setRestoredFromStorage] = useState(false);

  // Load saved state from localStorage on component mount
  useEffect(() => {
    const savedState = localStorage.getItem('document-extractor-state');
    if (savedState) {
      try {
        const state = JSON.parse(savedState);
        if (state.taskId && state.status && state.pdfUrl) {
          setTaskId(state.taskId);
          setStatus(state.status);
          setPdfUrl(state.pdfUrl);
          setUrl(state.url || '');
          setMode(state.mode || 'pdf');
          setRestoredFromStorage(true);
          console.log('Restored state from localStorage:', state);
        }
      } catch (error) {
        console.error('Failed to load saved state:', error);
        localStorage.removeItem('document-extractor-state');
      }
    }
  }, []);

  // Save state to localStorage whenever important state changes
  useEffect(() => {
    if (taskId && status) {
      const stateToSave = {
        taskId,
        status,
        pdfUrl,
        url,
        mode,
        timestamp: Date.now(),
        savedAt: new Date().toLocaleString()
      };
      localStorage.setItem('document-extractor-state', JSON.stringify(stateToSave));
    }
  }, [taskId, status, pdfUrl, url, mode]);

  const startExtraction = async () => {
    if (!url.trim()) {
      alert('Please enter a URL');
      return;
    }

    setLoading(true);
    setPdfUrl(null);
    setStatus(null);

    try {
      const response = await fetch(`${API_BASE_URL}/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, mode }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ExtractResponse = await response.json();
      setTaskId(data.task_id);
    } catch (error) {
      console.error('Error starting extraction:', error);
      alert('Failed to start extraction. Make sure the API server is running.');
    } finally {
      setLoading(false);
    }
  };

  const checkStatus = async (id: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/status/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: StatusResponse = await response.json();
      setStatus(data);

      if (data.status === 'completed' && data.file_path && mode === 'pdf') {
        setPdfUrl(`${API_BASE_URL}/view/${id}`);
      }
    } catch (error) {
      console.error('Error checking status:', error);
    }
  };

  useEffect(() => {
    if (taskId && status?.status !== 'completed' && status?.status !== 'failed') {
      const interval = setInterval(() => {
        checkStatus(taskId);
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [taskId, status?.status]);

  const downloadFile = () => {
    if (taskId) {
      window.open(`${API_BASE_URL}/download/${taskId}`, '_blank');
    }
  };

  const scrollToPDF = () => {
    const pdfElement = document.getElementById('pdf-viewer');
    if (pdfElement) {
      pdfElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const resetExtraction = () => {
    setUrl('');
    setTaskId(null);
    setStatus(null);
    setPdfUrl(null);
    setLoading(false);
    setRestoredFromStorage(false);
    localStorage.removeItem('document-extractor-state');
  };

  return (
    <div className="space-y-8">
      {/* PDF Viewer - Now displayed first */}
      {pdfUrl && mode === 'pdf' && (
        <div id="pdf-viewer" className="bg-white rounded-lg shadow-md p-6">
          <PDFViewer url={pdfUrl} />
        </div>
      )}

      {/* Input Form */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Extract Documents</h2>
        
                  <div className="space-y-4">
          {pdfUrl && mode === 'pdf' && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <p className="text-sm text-blue-800">
                📄 PDF preview is displayed above. You can scroll up to view it.
              </p>
              <p className="text-xs text-blue-600 mt-1">
                💾 State automatically saved - PDF will persist after page reload
              </p>
              {restoredFromStorage && (
                <p className="text-xs text-green-600 mt-1">
                  ✨ Restored from previous session
                </p>
              )}
            </div>
          )}
          <div>
            <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-1">
              Archive URL
            </label>
            <input
              type="url"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/archive.zip"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Output Format
            </label>
            <div className="flex space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="outputFormat"
                  value="pdf"
                  checked={mode === 'pdf'}
                  onChange={(e) => setMode(e.target.value as 'pdf' | 'txt')}
                  className="mr-2"
                />
                PDF
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="outputFormat"
                  value="txt"
                  checked={mode === 'txt'}
                  onChange={(e) => setMode(e.target.value as 'pdf' | 'txt')}
                  className="mr-2"
                />
                Text
              </label>
            </div>
          </div>

          <button
            onClick={startExtraction}
            disabled={loading || !url.trim() || (status?.status === 'processing')}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading || status?.status === 'processing' ? 'Processing...' : 'Extract Documents'}
          </button>
        </div>
      </div>

      {/* Status Display */}
      {status && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-2">Status</h3>
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              status.status === 'completed' ? 'bg-green-500' :
              status.status === 'failed' ? 'bg-red-500' :
              'bg-yellow-500 animate-pulse'
            }`}></div>
            <span className="text-sm font-medium capitalize">{status.status}</span>
            {status.status === 'processing' && (
              <span className="text-xs text-gray-500">
                (This may take a few minutes...)
              </span>
            )}
          </div>
          <p className="text-gray-600 mt-2">{status.message}</p>
          
          {status.status === 'processing' && mode === 'pdf' && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-sm text-blue-800">
                💡 PDF will appear at the top of the page when ready. No need to download manually!
              </p>
            </div>
          )}
          
          {status.status === 'completed' && (
            <div className="mt-4">
              <div className="flex flex-wrap gap-3 mb-3">
                <button
                  onClick={downloadFile}
                  className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700"
                >
                  Download File
                </button>
                {mode === 'pdf' && pdfUrl && (
                  <button
                    onClick={scrollToPDF}
                    className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
                  >
                    View PDF Above
                  </button>
                )}
                <button
                  onClick={resetExtraction}
                  className="bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700"
                >
                  New Extraction
                </button>
              </div>
              {mode === 'pdf' && pdfUrl && (
                <span className="text-sm text-green-600">
                  ✅ PDF preview is shown above
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
} 