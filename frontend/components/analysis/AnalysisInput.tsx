/**
 * Analysis Input Component
 * 
 * Supports three input modes:
 * - URL: Paste a social media post URL
 * - Text: Paste text content
 * - Image: Upload a screenshot (NEW)
 */

'use client';

import { useState } from 'react';
import { Link, FileText, Image as ImageIcon } from 'lucide-react';
import ImageUpload from '@/components/ui/ImageUpload';

interface AnalysisInputProps {
  onSubmit: (url?: string, text?: string) => void;
  onSubmitImage?: (file: File, context?: string) => void;
  isLoading: boolean;
}

type InputType = 'url' | 'text' | 'image';

export function AnalysisInput({ onSubmit, onSubmitImage, isLoading }: AnalysisInputProps) {
  const [inputType, setInputType] = useState<InputType>('url');
  const [url, setUrl] = useState('');
  const [text, setText] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageContext, setImageContext] = useState('');
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (inputType === 'url' && url.trim()) {
      onSubmit(url.trim(), undefined);
    } else if (inputType === 'text' && text.trim()) {
      onSubmit(undefined, text.trim());
    } else if (inputType === 'image' && imageFile && onSubmitImage) {
      onSubmitImage(imageFile, imageContext.trim() || undefined);
    }
  };
  
  const isValid = () => {
    if (inputType === 'url') return url.trim().length > 0;
    if (inputType === 'text') return text.trim().length > 0;
    if (inputType === 'image') return imageFile !== null && onSubmitImage !== undefined;
    return false;
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Input type tabs */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-lg">
        <button
          type="button"
          onClick={() => setInputType('url')}
          className={`
            flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-md
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
            flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-md
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
        
        <button
          type="button"
          onClick={() => setInputType('image')}
          className={`
            flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-md
            text-sm font-medium transition-colors
            ${inputType === 'image'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
            }
          `}
        >
          <ImageIcon className="w-4 h-4" />
          Image
        </button>
      </div>
      
      {/* Input field - URL */}
      {inputType === 'url' && (
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
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
        </div>
      )}
      
      {/* Input field - Text */}
      {inputType === 'text' && (
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
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
          />
        </div>
      )}
      
      {/* Input field - Image (NEW) */}
      {inputType === 'image' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Screenshot
            </label>
            <ImageUpload
              onImageSelected={setImageFile}
              onClear={() => setImageFile(null)}
              selectedFile={imageFile}
            />
          </div>
          
          {imageFile && (
            <div>
              <label htmlFor="imageContext" className="block text-sm font-medium text-gray-700 mb-2">
                Additional Context (Optional)
              </label>
              <textarea
                id="imageContext"
                value={imageContext}
                onChange={(e) => setImageContext(e.target.value)}
                placeholder="Provide any additional context about this screenshot..."
                rows={3}
                disabled={isLoading}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
              />
            </div>
          )}
          
          {!onSubmitImage && (
            <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">
              Image upload is not yet configured. Please use URL or Text mode.
            </p>
          )}
        </div>
      )}
      
      {/* Submit button */}
      <div className="flex justify-center">
        <button
          type="submit"
          disabled={!isValid() || isLoading}
          className={`
            px-6 py-2 text-sm font-medium rounded-full transition-all
            ${isValid() 
              ? 'bg-blue-600 text-white hover:bg-blue-700' 
              : 'bg-blue-600/10 text-blue-700'
            }
            disabled:cursor-not-allowed
          `}
        >
          {isLoading ? 'Analyzing...' : 'Analyze Content'}
        </button>
      </div>
    </form>
  );
}
