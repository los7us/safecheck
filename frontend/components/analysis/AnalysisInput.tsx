/**
 * Analysis Input Component
 */

'use client';

import { useState } from 'react';
import { Link, FileText } from 'lucide-react';

interface AnalysisInputProps {
  onSubmit: (url?: string, text?: string) => void;
  isLoading: boolean;
}

export function AnalysisInput({ onSubmit, isLoading }: AnalysisInputProps) {
  const [inputType, setInputType] = useState<'url' | 'text'>('url');
  const [url, setUrl] = useState('');
  const [text, setText] = useState('');
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (inputType === 'url' && url.trim()) {
      onSubmit(url.trim(), undefined);
    } else if (inputType === 'text' && text.trim()) {
      onSubmit(undefined, text.trim());
    }
  };
  
  const isValid = inputType === 'url' ? url.trim().length > 0 : text.trim().length > 0;
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Input type tabs */}
      <div className="flex gap-2 p-1 bg-gray-100 rounded-lg">
        <button
          type="button"
          onClick={() => setInputType('url')}
          className={`
            flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md
            text-sm font-medium transition-colors
            ${inputType === 'url'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
            }
          `}
        >
          <Link className="w-4 h-4" />
          URL
        </button>
        
        <button
          type="button"
          onClick={() => setInputType('text')}
          className={`
            flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md
            text-sm font-medium transition-colors
            ${inputType === 'text'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
            }
          `}
        >
          <FileText className="w-4 h-4" />
          Text
        </button>
      </div>
      
      {/* Input field */}
      {inputType === 'url' ? (
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
            Post or Message URL
          </label>
          <input
            id="url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://reddit.com/r/..."
            disabled={isLoading}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
        </div>
      ) : (
        <div>
          <label htmlFor="text" className="block text-sm font-medium text-gray-700 mb-2">
            Post or Message Text
          </label>
          <textarea
            id="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste the content you want to analyze..."
            rows={6}
            disabled={isLoading}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
          />
        </div>
      )}
      
      {/* Submit button */}
      <button
        type="submit"
        disabled={!isValid || isLoading}
        className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? 'Analyzing...' : 'Analyze Content'}
      </button>
    </form>
  );
}
