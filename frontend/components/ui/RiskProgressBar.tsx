/**
 * Risk Progress Bar Component
 */

import { formatRiskScore, getRiskProgressColor } from '@/lib/risk-utils';

interface RiskProgressBarProps {
  score: number;
  showPercentage?: boolean;
}

export function RiskProgressBar({
  score,
  showPercentage = true,
}: RiskProgressBarProps) {
  const barColor = getRiskProgressColor(score);
  const percentage = score * 100;
  
  return (
    <div className="w-full">
      {showPercentage && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            Risk Score
          </span>
          <span className="text-sm font-bold text-gray-900">
            {formatRiskScore(score)}
          </span>
        </div>
      )}
      
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full ${barColor} transition-all duration-1000 ease-out rounded-full`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
