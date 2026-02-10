/**
 * Celtic Knot Loader
 *
 * Animated SVG path loader matching the reference design:
 * 4 interlocking U-shaped loops in a pinwheel/clover pattern
 * with stroke-dashoffset animation for a continuous draw effect.
 *
 * Uses CSS keyframes for smooth, GPU-accelerated animation.
 */

'use client';

import React from 'react';

interface CelticKnotLoaderProps {
  /** Pixel size of the loader (width & height) */
  size?: number;
  /** Stroke color — hex or CSS color */
  color?: string;
  /** Stroke thickness */
  strokeWidth?: number;
  /** Animation cycle in seconds */
  duration?: number;
  /** Show subtle outer glow */
  showGlow?: boolean;
  /** Extra CSS classes */
  className?: string;
}

export default function CelticKnotLoader({
  size = 120,
  color = '#4B5EFC',
  strokeWidth = 7,
  duration = 3,
  showGlow = true,
  className = '',
}: CelticKnotLoaderProps) {
  // Each arm is a U-shaped loop. 4 arms rotated 0°/90°/180°/270° form the knot.
  // The over/under weave is achieved by layering: draw bottom segments first,
  // then overdraw the "over" crossings on top.
  //
  // Viewbox: 200×200, center at (100,100)

  // The outer U-loop path (one arm pointing UP-LEFT)
  // We draw relative to center and rotate via <g transform="rotate(...)">
  const armPath =
    'M 56,100 L 56,56 Q 56,36 76,36 L 100,36 Q 120,36 120,56 L 120,100';

  // Inner parallel stroke for the layered railroad look
  const armPathInner =
    'M 66,100 L 66,60 Q 66,46 80,46 L 100,46 Q 114,46 114,60 L 114,100';

  const totalLen = 600; // approximate path length for dasharray

  const armStyle = {
    strokeDasharray: totalLen,
    strokeDashoffset: totalLen,
    animation: `knotDraw ${duration}s ease-in-out infinite`,
  };

  const armStyleDelayed = (delay: number) => ({
    ...armStyle,
    animationDelay: `${delay}s`,
  });

  const rotations = [0, 90, 180, 270];
  const delays = [0, duration * 0.1, duration * 0.2, duration * 0.3];

  return (
    <div
      className={`inline-flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Loading"
        role="img"
      >
        <defs>
          {showGlow && (
            <filter id="knotGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          )}
        </defs>

        {/* === BOTTOM LAYER: all 4 outer arms (will be partially hidden by crossings) === */}
        {rotations.map((rot, i) => (
          <g
            key={`outer-${i}`}
            transform={`rotate(${rot} 100 100)`}
            filter={showGlow ? 'url(#knotGlow)' : undefined}
          >
            <path
              d={armPath}
              stroke={color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              opacity={0.35}
            />
          </g>
        ))}

        {/* === TOP LAYER: animated strokes that draw on continuously === */}
        {rotations.map((rot, i) => (
          <g
            key={`anim-outer-${i}`}
            transform={`rotate(${rot} 100 100)`}
            filter={showGlow ? 'url(#knotGlow)' : undefined}
          >
            <path
              d={armPath}
              stroke={color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              style={armStyleDelayed(delays[i])}
            />
          </g>
        ))}

        {/* === INNER parallel tracks (thinner, slightly transparent) === */}
        {rotations.map((rot, i) => (
          <g key={`inner-bg-${i}`} transform={`rotate(${rot} 100 100)`}>
            <path
              d={armPathInner}
              stroke={color}
              strokeWidth={strokeWidth * 0.55}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              opacity={0.2}
            />
          </g>
        ))}

        {rotations.map((rot, i) => (
          <g key={`inner-anim-${i}`} transform={`rotate(${rot} 100 100)`}>
            <path
              d={armPathInner}
              stroke={color}
              strokeWidth={strokeWidth * 0.55}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              opacity={0.7}
              style={armStyleDelayed(delays[i])}
            />
          </g>
        ))}

        {/* === CENTER square element (from reference) === */}
        <rect
          x="94"
          y="94"
          width="12"
          height="12"
          rx="2"
          fill={color}
          opacity={0.8}
        />
      </svg>

      <style jsx>{`
        @keyframes knotDraw {
          0% {
            stroke-dashoffset: ${totalLen};
          }
          50% {
            stroke-dashoffset: 0;
          }
          100% {
            stroke-dashoffset: -${totalLen};
          }
        }
      `}</style>
    </div>
  );
}
