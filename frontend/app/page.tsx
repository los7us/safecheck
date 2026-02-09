/**
 * SafetyCheck Main Page
 */

'use client';

import { AnalysisInput } from '@/components/analysis/AnalysisInput';
import { AnalysisModal } from '@/components/analysis/AnalysisModal';
import { useAnalysis } from '@/hooks/useAnalysis';
import { ShieldCheck, Search, CheckCircle, Eye } from 'lucide-react';

export default function HomePage() {
  const {
    isLoading,
    result,
    error,
    isModalOpen,
    analyze,
    analyzeImage,
    closeModal,
  } = useAnalysis();
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-8 h-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">
              SafetyCheck
            </h1>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Analyze Social Media Posts for Scams
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Paste a URL, text, or upload a screenshot from social media to check for potential scams,
            misleading claims, and safety concerns. Powered by AI.
          </p>
        </div>
        
        {/* Input Form Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-200">
          <AnalysisInput
            onSubmit={analyze}
            onSubmitImage={analyzeImage}
            isLoading={isLoading}
          />
        </div>
        
        {/* Features Grid */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">
              AI-Powered Analysis
            </h3>
            <p className="text-sm text-gray-600">
              Advanced AI detects scams, phishing, and misleading content
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">
              Fact-Checking
            </h3>
            <p className="text-sm text-gray-600">
              Verifies claims against credible sources with citations
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Eye className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">
              Multimodal Support
            </h3>
            <p className="text-sm text-gray-600">
              Analyzes text, images, and metadata for comprehensive results
            </p>
          </div>
        </div>
        
        {/* Disclaimer */}
        <div className="mt-12 text-center">
          <p className="text-xs text-gray-500 max-w-2xl mx-auto">
            SafetyCheck is a decision-support tool and should not be considered
            a definitive authority. Always exercise your own judgment when
            evaluating online content.
          </p>
        </div>
      </main>
      
      {/* Analysis Modal */}
      <AnalysisModal
        isOpen={isModalOpen}
        onClose={closeModal}
        analysisState={{ isLoading, result, error }}
        onRetry={() => closeModal()}
      />
    </div>
  );
}
