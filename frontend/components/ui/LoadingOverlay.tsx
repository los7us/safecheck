/**
 * Loading Overlay Component
 *
 * Full-screen loading indicator with blur backdrop
 * and animated Celtic knot loader.
 */

'use client';

import React from 'react';
import BlurredBackdrop from './BlurredBackdrop';
import CelticKnotLoader from './CelticKnotLoader';

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
      <BlurredBackdrop show={show} blurAmount="lg" opacity={0.3} />

      {/* Loading Card */}
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div
          className="
            bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl
            px-10 py-8
            flex flex-col items-center gap-5
          "
        >
          <CelticKnotLoader size={80} duration={3} showGlow />

          <p className="text-lg font-medium text-gray-700">{message}</p>
          <p className="text-sm text-gray-400">This may take a moment</p>
        </div>
      </div>
    </>
  );
}
