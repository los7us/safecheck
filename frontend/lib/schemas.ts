/**
 * Canonical Data Schemas v1 (TypeScript/Zod)
 * 
 * These schemas mirror the Python Pydantic schemas exactly.
 * They provide type safety and runtime validation in the frontend.
 */

import { z } from 'zod';

// ============================================================================
// ENUMERATIONS
// ============================================================================

export const PlatformNameSchema = z.enum([
  'reddit',
  'twitter',
  'tiktok',
  'facebook',
  'instagram',
  'youtube',
  'unknown',
]);
export type PlatformName = z.infer<typeof PlatformNameSchema>;

export const MediaTypeSchema = z.enum(['image', 'video', 'gif', 'none']);
export type MediaType = z.infer<typeof MediaTypeSchema>;

export const AuthorTypeSchema = z.enum([
  'individual',
  'organization',
  'bot',
  'verified',
  'unknown',
]);
export type AuthorType = z.infer<typeof AuthorTypeSchema>;

export const AccountAgeBucketSchema = z.enum([
  'new',
  'recent',
  'established',
  'veteran',
  'unknown',
]);
export type AccountAgeBucket = z.infer<typeof AccountAgeBucketSchema>;

export const RiskLevelSchema = z.enum([
  'Minimal',
  'Low',
  'Moderate',
  'High',
  'Critical',
]);
export type RiskLevel = z.infer<typeof RiskLevelSchema>;

export const ClaimVerdictSchema = z.enum([
  'True',
  'False',
  'Misleading',
  'Unverifiable',
  'Lacks Context',
]);
export type ClaimVerdict = z.infer<typeof ClaimVerdictSchema>;

// ============================================================================
// MEDIA SCHEMAS
// ============================================================================

export const MediaMetadataSchema = z.object({
  media_type: MediaTypeSchema,
  url: z.string().url(),
  hash: z.string().optional(),
  width: z.number().int().optional(),
  height: z.number().int().optional(),
  size_bytes: z.number().int().optional(),
  thumbnail_url: z.string().url().optional(),
});
export type MediaMetadata = z.infer<typeof MediaMetadataSchema>;

export const MediaFeaturesSchema = z.object({
  caption: z.string().optional(),
  ocr_text: z.string().optional(),
  detected_objects: z.array(z.string()).optional(),
  nsfw_score: z.number().min(0).max(1).optional(),
  face_detected: z.boolean().optional(),
});
export type MediaFeatures = z.infer<typeof MediaFeaturesSchema>;

// ============================================================================
// METADATA SCHEMAS
// ============================================================================

export const EngagementMetricsSchema = z.object({
  likes: z.number().int().nonnegative().optional(),
  shares: z.number().int().nonnegative().optional(),
  replies: z.number().int().nonnegative().optional(),
  views: z.number().int().nonnegative().optional(),
});
export type EngagementMetrics = z.infer<typeof EngagementMetricsSchema>;

export const AuthorMetadataSchema = z.object({
  author_type: AuthorTypeSchema.default('unknown'),
  account_age_bucket: AccountAgeBucketSchema.default('unknown'),
  is_verified: z.boolean().optional(),
  follower_count_bucket: z.string().optional(),
});
export type AuthorMetadata = z.infer<typeof AuthorMetadataSchema>;

// ============================================================================
// CANONICAL POST SCHEMA
// ============================================================================

export const CanonicalPostSchema = z.object({
  post_id: z.string(),
  post_text: z.string(),
  platform_name: PlatformNameSchema,
  timestamp: z.string().datetime().optional(),
  language: z.string().optional(),
  author_metadata: AuthorMetadataSchema.optional(),
  engagement_metrics: EngagementMetricsSchema.optional(),
  media_items: z.array(MediaMetadataSchema).optional().default([]),
  media_features: MediaFeaturesSchema.optional(),
  external_links: z.array(z.string()).optional().default([]),
  hashtags: z.array(z.string()).optional().default([]),
  mentions: z.array(z.string()).optional().default([]),
  sampled_comments: z.array(z.string()).max(5).optional().default([]),
  reply_context: z.string().optional(),
  raw_url: z.string().optional(),
  adapter_version: z.string().default('1.0'),
});
export type CanonicalPost = z.infer<typeof CanonicalPostSchema>;

// ============================================================================
// ANALYSIS OUTPUT SCHEMAS
// ============================================================================

export const CitationSchema = z.object({
  source_name: z.string(),
  url: z.string().url(),
  excerpt: z.string().max(200).optional(),
});
export type Citation = z.infer<typeof CitationSchema>;

export const FactCheckSchema = z.object({
  claim: z.string(),
  verdict: ClaimVerdictSchema,
  explanation: z.string().max(500),
  citations: z.array(CitationSchema).min(1).max(3),
});
export type FactCheck = z.infer<typeof FactCheckSchema>;

export const SafetyAnalysisResultSchema = z.object({
  risk_score: z.number().min(0).max(1),
  risk_level: RiskLevelSchema,
  summary: z.string().max(500),
  key_signals: z.array(z.string()).min(2).max(5),
  fact_checks: z.array(FactCheckSchema).default([]),
  analysis_timestamp: z.string().datetime(),
  model_version: z.string().default('gemini-1.5-pro'),
});
export type SafetyAnalysisResult = z.infer<typeof SafetyAnalysisResultSchema>;

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export function getRiskColor(level: RiskLevel): string {
  switch (level) {
    case 'Minimal':
      return 'green';
    case 'Low':
      return 'blue';
    case 'Moderate':
      return 'yellow';
    case 'High':
      return 'orange';
    case 'Critical':
      return 'red';
  }
}

export function getRiskLevelFromScore(score: number): RiskLevel {
  if (score < 0.25) return 'Minimal';
  if (score < 0.5) return 'Low';
  if (score < 0.7) return 'Moderate';
  if (score < 0.9) return 'High';
  return 'Critical';
}

export const SCHEMA_VERSION = '1.0.0';
