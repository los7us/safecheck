/**
 * Image Upload Component
 * 
 * Allows users to upload screenshots for analysis.
 * Features:
 * - Drag and drop
 * - File picker
 * - Clipboard paste (Ctrl+V)
 * - Image preview
 * - File validation
 */

'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';

interface ImageUploadProps {
  onImageSelected: (file: File) => void;
  onClear: () => void;
  maxSizeMB?: number;
  selectedFile?: File | null;
}

export default function ImageUpload({
  onImageSelected,
  onClear,
  maxSizeMB = 10,
  selectedFile,
}: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pasteHint, setPasteHint] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);
  
  const validateAndSelectFile = useCallback((file: File) => {
    setError(null);
    
    // Check file type
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file');
      return;
    }
    
    // Check file size
    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > maxSizeMB) {
      setError(`File too large. Maximum size: ${maxSizeMB}MB`);
      return;
    }
    
    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
    
    // Notify parent
    onImageSelected(file);
  }, [maxSizeMB, onImageSelected]);
  
  // Handle clipboard paste (Ctrl+V)
  const handlePaste = useCallback((e: ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file) {
          validateAndSelectFile(file);
        }
        return;
      }
    }
  }, [validateAndSelectFile]);
  
  // Add global paste listener when component is focused/visible
  useEffect(() => {
    const handleGlobalPaste = (e: ClipboardEvent) => {
      // Only handle paste if no other input is focused
      const activeElement = document.activeElement;
      const isInputFocused = activeElement instanceof HTMLInputElement || 
                             activeElement instanceof HTMLTextAreaElement;
      
      // If user is typing in an input, don't intercept paste
      if (isInputFocused && activeElement !== dropZoneRef.current) {
        return;
      }
      
      handlePaste(e);
    };
    
    document.addEventListener('paste', handleGlobalPaste);
    return () => document.removeEventListener('paste', handleGlobalPaste);
  }, [handlePaste]);
  
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);
  
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const file = e.dataTransfer.files?.[0];
    if (file) {
      validateAndSelectFile(file);
    }
  }, [validateAndSelectFile]);
  
  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndSelectFile(file);
    }
  }, [validateAndSelectFile]);
  
  const handleClear = useCallback(() => {
    setPreview(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onClear();
  }, [onClear]);
  
  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);
  
  // Show paste hint on focus
  const handleFocus = useCallback(() => {
    setPasteHint(true);
  }, []);
  
  const handleBlur = useCallback(() => {
    setPasteHint(false);
  }, []);
  
  if (preview || selectedFile) {
    return (
      <div className="relative">
        {preview && (
          <img
            src={preview}
            alt="Upload preview"
            className="w-full rounded-xl border-2 border-gray-300 max-h-80 object-contain bg-gray-100"
          />
        )}
        <button
          onClick={handleClear}
          className="absolute top-3 right-3 bg-red-500/90 text-white p-2.5 rounded-full hover:bg-red-600 transition-colors shadow-lg backdrop-blur-sm"
          type="button"
          aria-label="Remove image"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        {selectedFile && (
          <p className="text-sm text-gray-500 mt-2 text-center">
            {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
          </p>
        )}
      </div>
    );
  }
  
  return (
    <div>
      <div
        ref={dropZoneRef}
        className={`
          border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
          transition-all duration-200 outline-none
          ${dragActive 
            ? 'border-blue-500 bg-blue-50' 
            : pasteHint
              ? 'border-blue-400 bg-blue-50/50'
              : 'border-gray-300 hover:border-gray-400 bg-gray-50'
          }
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
        onFocus={handleFocus}
        onBlur={handleBlur}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && handleClick()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileInput}
          className="hidden"
          aria-label="Upload image file"
        />
        
        <div className="flex flex-col items-center gap-4">
          <div className="p-5 bg-gradient-to-br from-blue-100 to-purple-100 rounded-2xl">
            <svg className="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          
          <div>
            <p className="text-lg font-medium text-gray-700">
              {pasteHint ? 'Press Ctrl+V to paste' : 'Drop, paste, or click to upload'}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              PNG, JPG, GIF, WebP up to {maxSizeMB}MB
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Tip: Copy a screenshot and press <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-600 font-mono text-xs">Ctrl+V</kbd>
            </p>
          </div>
        </div>
      </div>
      
      {error && (
        <div className="mt-3 flex items-center gap-2 text-red-500 text-sm">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}

