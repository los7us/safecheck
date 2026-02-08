/**
 * Key Signals Component
 */

import { XCircle } from 'lucide-react';

interface KeySignalsProps {
  signals: string[];
}

export function KeySignals({ signals }: KeySignalsProps) {
  if (!signals || signals.length === 0) {
    return null;
  }
  
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
        Key Signals Detected
      </h3>
      
      <ul className="space-y-2">
        {signals.map((signal, index) => (
          <li
            key={index}
            className="flex items-start gap-2 text-sm text-gray-700"
          >
            <XCircle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
            <span>{signal}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
