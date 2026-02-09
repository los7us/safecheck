/**
 * Analysis Modal Component
 */

'use client';

import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { X } from 'lucide-react';
import type { SafetyAnalysisResult } from '@/lib/schemas';
import { AnalysisResult } from './AnalysisResult';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

interface AnalysisState {
  isLoading: boolean;
  result: SafetyAnalysisResult | null;
  error: string | null;
}

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysisState: AnalysisState;
  onRetry?: () => void;
}

export function AnalysisModal({
  isOpen,
  onClose,
  analysisState,
  onRetry,
}: AnalysisModalProps) {
  const { isLoading, result, error } = analysisState;
  
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 backdrop-blur-md bg-black/30 transition-all duration-300" />
        </Transition.Child>
        
        {/* Modal Container */}
        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 shadow-xl transition-all">
                {/* Header */}
                <div className="flex items-start justify-between mb-6">
                  <Dialog.Title
                    as="h2"
                    className="text-2xl font-bold text-gray-900"
                  >
                    Safety Analysis
                  </Dialog.Title>
                  
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>
                
                {/* Content */}
                <div className="min-h-[300px]">
                  {isLoading && (
                    <div className="flex flex-col items-center justify-center py-12">
                      <LoadingSpinner size="lg" />
                      <p className="mt-4 text-sm text-gray-600">
                        Analyzing content...
                      </p>
                    </div>
                  )}
                  
                  {error && !isLoading && (
                    <ErrorMessage
                      message={error}
                      onRetry={onRetry}
                    />
                  )}
                  
                  {result && !isLoading && !error && (
                    <AnalysisResult result={result} useGauge={true} />
                  )}
                  
                  {!isLoading && !error && !result && (
                    <div className="text-center py-12 text-gray-500">
                      No analysis yet. Submit a URL or text to analyze.
                    </div>
                  )}
                </div>
                
                {/* Footer */}
                <div className="mt-6 pt-4 border-t border-gray-200 flex justify-end">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
