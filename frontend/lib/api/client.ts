/**
 * API Client for SafetyCheck Backend
 */

import type { SafetyAnalysisResult } from '../schemas';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export interface AnalysisRequest {
  url?: string;
  text?: string;
  platform_hint?: string;
}

export interface AnalysisResponse {
  success: boolean;
  data?: SafetyAnalysisResult;
  error?: string;
}

export class APIClient {
  private baseUrl: string;
  
  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }
  
  async analyze(request: AnalysisRequest): Promise<AnalysisResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const message = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
        throw new APIError(
          message,
          response.status,
          errorData
        );
      }
      
      return await response.json();
      
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      
      throw new APIError(
        `Failed to analyze: ${error instanceof Error ? error.message : 'Unknown error'}`,
        undefined,
        error
      );
    }
  }
  
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new APIError('Health check failed', response.status);
    }
    return response.json();
  }
}

export const apiClient = new APIClient();
