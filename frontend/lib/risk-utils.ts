/**
 * Risk Level Utilities
 * 
 * Color mappings and utilities for risk visualization.
 */

import type { RiskLevel } from './schemas';

export interface RiskLevelConfig {
  color: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
  progressColor: string;
  emoji: string;
  description: string;
}

export const RISK_LEVEL_CONFIG: Record<RiskLevel, RiskLevelConfig> = {
  Minimal: {
    color: 'green',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-700',
    progressColor: 'bg-green-500',
    emoji: '✅',
    description: 'Very low risk detected',
  },
  Low: {
    color: 'blue',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-700',
    progressColor: 'bg-blue-500',
    emoji: 'ℹ️',
    description: 'Minor concerns present',
  },
  Moderate: {
    color: 'yellow',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-700',
    progressColor: 'bg-yellow-500',
    emoji: '⚠️',
    description: 'Significant concerns detected',
  },
  High: {
    color: 'orange',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    textColor: 'text-orange-700',
    progressColor: 'bg-orange-500',
    emoji: '🚨',
    description: 'Strong indicators of risk',
  },
  Critical: {
    color: 'red',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-700',
    progressColor: 'bg-red-500',
    emoji: '🛑',
    description: 'Extremely high risk',
  },
};

/**
 * Get Tailwind color class for risk score
 */
export function getRiskScoreColor(score: number): string {
  if (score < 0.25) return 'text-green-600';
  if (score < 0.5) return 'text-blue-600';
  if (score < 0.7) return 'text-yellow-600';
  if (score < 0.9) return 'text-orange-600';
  return 'text-red-600';
}

/**
 * Get progress bar color for risk score
 */
export function getRiskProgressColor(score: number): string {
  if (score < 0.25) return 'bg-green-500';
  if (score < 0.5) return 'bg-blue-500';
  if (score < 0.7) return 'bg-yellow-500';
  if (score < 0.9) return 'bg-orange-500';
  return 'bg-red-500';
}

/**
 * Format risk score as percentage
 */
export function formatRiskScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}
