/**
 * Fact Checks List Component
 */

import type { FactCheck } from '@/lib/schemas';
import { FactCheckCard } from './FactCheckCard';

interface FactChecksListProps {
  factChecks: FactCheck[];
}

export function FactChecksList({ factChecks }: FactChecksListProps) {
  if (!factChecks || factChecks.length === 0) {
    return null;
  }
  
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
        Fact Checks
      </h3>
      
      <div className="space-y-3">
        {factChecks.map((factCheck, index) => (
          <FactCheckCard key={index} factCheck={factCheck} />
        ))}
      </div>
    </div>
  );
}
