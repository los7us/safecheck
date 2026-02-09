/**
 * Blurred Backdrop Component
 * 
 * Creates a modern blur effect for modals and overlays.
 * Uses backdrop-filter for glassmorphism effect.
 */

'use client';

import React from 'react';

interface BlurredBackdropProps {
  show: boolean;
  onClick?: () => void;
  blurAmount?: 'sm' | 'md' | 'lg';
  opacity?: number;
  className?: string;
  zIndex?: number;
}

export default function BlurredBackdrop({
  show,
  onClick,
  blurAmount = 'md',
  opacity = 0.4,
  zIndex = 40,
  className = '',
}: BlurredBackdropProps) {
  if (!show) return null;

  const blurMap = {
    sm: 'backdrop-blur-sm',
    md: 'backdrop-blur-md',
    lg: 'backdrop-blur-lg',
  };

  const opacityMap: Record<number, string> = {
    0.2: 'bg-black/20',
    0.3: 'bg-black/30',
    0.4: 'bg-black/40',
    0.5: 'bg-black/50',
    0.6: 'bg-black/60',
    0.7: 'bg-black/70',
  };

  const opacityClass = opacityMap[opacity] ?? `bg-black/40`;

  return (
    <div
      className={`
        fixed inset-0
        ${blurMap[blurAmount]}
        ${opacityClass}
        transition-all duration-300 ease-in-out
        ${className}
      `}
      style={{ zIndex }}
      onClick={onClick}
      aria-hidden="true"
    />
  );
}
