'use client';

import { useState } from 'react';
import DocumentExtractor from './components/DocumentExtractor';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <DocumentExtractor />
      </div>
    </div>
  );
}
