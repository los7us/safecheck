/**
 * Risk Badge Component
 */

import type { RiskLevel } from '@/lib/schemas';
import { RISK_LEVEL_CONFIG } from '@/lib/risk-utils';

interface RiskBadgeProps {
  riskLevel: RiskLevel;
  size?: 'sm' | 'md' | 'lg';
}

export function RiskBadge({ riskLevel, size = 'md' }: RiskBadgeProps) {
  const config = RISK_LEVEL_CONFIG[riskLevel];
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  };
  
  return (
    <div
      className={`
        inline-flex items-center gap-1.5 rounded-full font-medium
        ${config.bgColor} ${config.textColor} ${config.borderColor}
        border ${sizeClasses[size]}
      `}
    >
      <span>{config.emoji}</span>
      <span>{riskLevel}</span>
    </div>
  );
}
