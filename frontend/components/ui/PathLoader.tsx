/**
 * Simple Path Loader
 *
 * Lightweight single-path infinity loop animation.
 * Good for inline loading states and buttons.
 */

'use client';

import React from 'react';

interface PathLoaderProps {
  size?: number;
  color?: string;
  strokeWidth?: number;
  duration?: number;
  className?: string;
}

export default function PathLoader({
  size = 48,
  color = '#4B5EFC',
  strokeWidth = 3,
  duration = 2,
  className = '',
}: PathLoaderProps) {
  const pathLen = 320;

  return (
    <div className={`inline-block ${className}`} style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 60"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Loading"
        role="img"
      >
        {/* Infinity / figure-8 path */}
        <path
          d="
            M 30,30
            C 30,10 50,10 50,30
            C 50,50 70,50 70,30
            C 70,10 50,10 50,30
            C 50,50 30,50 30,30
            Z
          "
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          fill="none"
          opacity={0.2}
        />
        <path
          d="
            M 30,30
            C 30,10 50,10 50,30
            C 50,50 70,50 70,30
            C 70,10 50,10 50,30
            C 50,50 30,50 30,30
            Z
          "
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          fill="none"
          style={{
            strokeDasharray: pathLen,
            strokeDashoffset: pathLen,
            animation: `infinityDraw ${duration}s linear infinite`,
          }}
        />
      </svg>

      <style jsx>{`
        @keyframes infinityDraw {
          to {
            stroke-dashoffset: 0;
          }
        }
      `}</style>
    </div>
  );
}
