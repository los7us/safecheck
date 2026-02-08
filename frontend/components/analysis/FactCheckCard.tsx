/**
 * Fact Check Card Component
 */

import type { FactCheck, ClaimVerdict } from '@/lib/schemas';
import { CheckCircle, XCircle, AlertTriangle, HelpCircle } from 'lucide-react';

interface FactCheckCardProps {
  factCheck: FactCheck;
}

const VERDICT_CONFIG: Record<ClaimVerdict, {
  icon: typeof CheckCircle;
  color: string;
  bgColor: string;
  borderColor: string;
  label: string;
}> = {
  'True': {
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    label: 'True',
  },
  'False': {
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    label: 'False',
  },
  'Misleading': {
    icon: AlertTriangle,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    label: 'Misleading',
  },
  'Unverifiable': {
    icon: HelpCircle,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    label: 'Unverifiable',
  },
  'Lacks Context': {
    icon: AlertTriangle,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    label: 'Lacks Context',
  },
};

export function FactCheckCard({ factCheck }: FactCheckCardProps) {
  const config = VERDICT_CONFIG[factCheck.verdict];
  const Icon = config.icon;
  
  return (
    <div className={`border rounded-lg p-4 ${config.bgColor} ${config.borderColor}`}>
      {/* Verdict badge */}
      <div className="flex items-start gap-3 mb-3">
        <Icon className={`w-6 h-6 ${config.color} flex-shrink-0 mt-0.5`} />
        <div className="flex-1">
          <div className={`text-sm font-semibold ${config.color} mb-1`}>
            {config.label}
          </div>
          <div className="text-sm font-medium text-gray-900">
            &ldquo;{factCheck.claim}&rdquo;
          </div>
        </div>
      </div>
      
      {/* Explanation */}
      <p className="text-sm text-gray-700 mb-3">
        {factCheck.explanation}
      </p>
      
      {/* Inline citations */}
      {factCheck.citations && factCheck.citations.length > 0 && (
        <div className="space-y-1.5">
          {factCheck.citations.map((citation, index) => (
            <div key={index} className="text-xs text-gray-600">
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
              >
                {citation.source_name} ↗
              </a>
              {citation.excerpt && (
                <span className="ml-2 italic">
                  &ldquo;{citation.excerpt}&rdquo;
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
