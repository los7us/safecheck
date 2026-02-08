/**
 * Risk Score Gauge Component
 */

'use client';

import { useMemo } from 'react';
import { formatRiskScore, getRiskScoreColor } from '@/lib/risk-utils';

interface RiskScoreGaugeProps {
  score: number;
  size?: number;
}

export function RiskScoreGauge({ score, size = 120 }: RiskScoreGaugeProps) {
  const radius = size / 2 - 8;
  const circumference = 2 * Math.PI * radius;
  
  const offset = useMemo(() => {
    return circumference - (score * circumference);
  }, [score, circumference]);
  
  const colorClass = getRiskScoreColor(score);
  
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          className="transform -rotate-90"
          width={size}
          height={size}
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            className="text-gray-200"
          />
          
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={`transition-all duration-1000 ease-out ${colorClass}`}
          />
        </svg>
        
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className={`text-2xl font-bold ${colorClass}`}>
            {formatRiskScore(score)}
          </div>
          <div className="text-xs text-gray-500">Risk Score</div>
        </div>
      </div>
    </div>
  );
}
