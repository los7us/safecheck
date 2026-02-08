/**
 * useAnalysis Hook
 * 
 * Manages analysis state and API calls.
 */

'use client';

import { useState, useCallback } from 'react';
import type { SafetyAnalysisResult } from '@/lib/schemas';
import { apiClient, type AnalysisRequest } from '@/lib/api/client';

export interface AnalysisState {
  isLoading: boolean;
  result: SafetyAnalysisResult | null;
  error: string | null;
}

export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>({
    isLoading: false,
    result: null,
    error: null,
  });
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const analyze = useCallback(async (url?: string, text?: string) => {
    // Reset state
    setState({
      isLoading: true,
      result: null,
      error: null,
    });
    
    // Open modal
    setIsModalOpen(true);
    
    try {
      const request: AnalysisRequest = {};
      
      if (url) {
        request.url = url;
      } else if (text) {
        request.text = text;
      } else {
        throw new Error('Either URL or text must be provided');
      }
      
      const response = await apiClient.analyze(request);
      
      if (!response.success || !response.data) {
        throw new Error(response.error || 'Analysis failed');
      }
      
      setState({
        isLoading: false,
        result: response.data,
        error: null,
      });
      
    } catch (error) {
      console.error('Analysis error:', error);
      
      setState({
        isLoading: false,
        result: null,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      });
    }
  }, []);
  
  const reset = useCallback(() => {
    setState({
      isLoading: false,
      result: null,
      error: null,
    });
  }, []);
  
  const closeModal = useCallback(() => {
    setIsModalOpen(false);
  }, []);
  
  return {
    ...state,
    isModalOpen,
    analyze,
    reset,
    closeModal,
  };
}
