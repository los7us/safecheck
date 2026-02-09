/**
 * SafetyCheck Main Page
 */

'use client';

import { AnalysisInput } from '@/components/analysis/AnalysisInput';
import { AnalysisModal } from '@/components/analysis/AnalysisModal';
import { useAnalysis } from '@/hooks/useAnalysis';
import { Search, CheckCircle, Eye } from 'lucide-react';

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
    <div className="min-h-screen bg-gray-50 relative">
      {/* Background Image */}
      <div 
        className="fixed inset-0 z-0 opacity-30"
        style={{
          backgroundImage: `url(/background.jpeg)`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      />
      
      {/* Content Wrapper */}
      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-gray-200 bg-white/90 backdrop-blur-sm">
          <div className="flex items-center gap-3 px-6 py-4">
            <img src="/logo.png" alt="SafetyCheck Logo" className="w-9 h-9" />
            <h1 className="text-xl font-semibold text-gray-900">
              SafetyCheck
            </h1>
          </div>
        </header>
        
        {/* Main Content */}
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* Hero Section */}
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-3 sm:mb-4 px-4">
              Analyze Your Posts for Misleading Content
            </h2>
            <p className="text-sm sm:text-base text-gray-600 max-w-2xl mx-auto px-4">
              Paste a URL, text, or upload a screenshot from social media to check for potential
              scams, misleading claims, and safety concerns. Powered by Gemini.
            </p>
          </div>
          
          {/* Input Card */}
          <div className="bg-white shadow-sm border border-gray-200 p-4 sm:p-6 lg:p-8 mb-12 sm:mb-16">
            <AnalysisInput
              onSubmit={analyze}
              onSubmitImage={analyzeImage}
              isLoading={isLoading}
            />
          </div>
          
          {/* Features Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 sm:gap-10 lg:gap-12 mb-12 px-4">
            <div className="text-center">
              <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
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
              <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
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
              <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
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
          <div className="text-center px-4">
            <p className="text-xs text-gray-500 max-w-2xl mx-auto">
              SafetyCheck is a decision-support tool and should not be considered a definitive authority. Always exercise your own judgment when evaluating online content.
            </p>
          </div>
        </main>
      </div>
      
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
