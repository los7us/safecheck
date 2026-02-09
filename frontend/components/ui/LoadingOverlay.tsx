/**
 * Loading Overlay Component
 * 
 * Full-screen loading indicator with blur backdrop.
 * Used during analysis to provide modern glassmorphism feedback.
 */

'use client';

import React from 'react';
import BlurredBackdrop from './BlurredBackdrop';

interface LoadingOverlayProps {
  show: boolean;
  message?: string;
}

export default function LoadingOverlay({
  show,
  message = 'Analyzing content...',
}: LoadingOverlayProps) {
  if (!show) return null;

  return (
    <>
      {/* Blurred Backdrop */}
      <BlurredBackdrop
        show={show}
        blurAmount="lg"
        opacity={0.3}
      />

      {/* Loading Card */}
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="
          bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl p-8
          flex flex-col items-center gap-4
          animate-in fade-in zoom-in-95 duration-300
        ">
          {/* Spinner */}
          <div className="relative w-16 h-16">
            <div className="absolute inset-0 border-4 border-gray-200 rounded-full" />
            <div className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin" />
          </div>

          {/* Message */}
          <p className="text-lg font-medium text-gray-700">{message}</p>
          <p className="text-sm text-gray-400">This may take a moment</p>
        </div>
      </div>
    </>
  );
}
