# SafetyCheck Architecture (v1)

## Overview

SafetyCheck is a modular, multimodal safety analysis system for social media content.

## Key Design Decisions

### 1. Platform-Neutral Canonical Schema

**Decision**: All platform adapters normalize to a single `CanonicalPost` schema.

**Rationale**:
- Enables true platform-neutrality
- Analysis pipeline doesn't need platform-specific logic
- Easy to add new platforms
- Graceful degradation when data is missing

**Trade-offs**:
- Some platform-specific nuances may be lost
- Requires thoughtful schema design

### 2. Adapter Pattern for Platforms

**Decision**: Each platform has a dedicated adapter implementing `PlatformAdapter` interface.

**Rationale**:
- Separation of concerns
- Easy to maintain and test
- Platform-specific quirks isolated
- Can swap or disable adapters independently

**Trade-offs**:
- More code than a monolithic approach
- Requires discipline to maintain interface

### 3. Gemini for Analysis (Not Classification)

**Decision**: Use Gemini as a reasoning engine, not a statistical classifier.

**Rationale**:
- Multimodal capabilities (text + images)
- Can provide explanations
- Can fact-check and cite sources
- Better at nuanced context

**Trade-offs**:
- Higher cost per analysis than simple ML
- Latency considerations
- Requires careful prompt engineering

### 4. Optional Fields with Graceful Degradation

**Decision**: Only `post_id`, `post_text`, and `platform_name` are required.

**Rationale**:
- Not all platforms provide same data
- API access varies by platform
- Works even with minimal data (paste mode)

**Trade-offs**:
- Analysis quality varies with data availability
- Must handle missing data throughout pipeline

### 5. No PII Collection

**Decision**: Never collect personally identifiable information.

**Rationale**:
- Privacy by design
- Reduces legal risk
- Aligns with ethical principles
- Account age/follower count in buckets, not exact values

**Trade-offs**:
- Can't analyze user history patterns
- Can't build user profiles (which is good!)

## Data Flow

```
User Input (URL or Text)
        ↓
Platform Adapter (extract + normalize)
        ↓
CanonicalPost Schema
        ↓
Media Processor (download + extract features)
        ↓
Gemini Service (analyze + fact-check)
        ↓
SafetyAnalysisResult
        ↓
Frontend UI (display)
```

## Module Boundaries

- `adapters/`: Platform-specific extraction logic
- `core/`: Shared schemas and types
- `services/`: Business logic (Gemini, media processing)
- `utils/`: Utilities and helpers

## Error Handling Philosophy

- Fail fast on schema violations
- Graceful degradation on missing optional data
- Retry on transient errors (rate limits, network)
- Clear error messages to users

## Versioning Strategy

- All schemas versioned (currently v1.0.0)
- Adapter versions tracked
- Gemini prompt versions tracked
- Breaking changes = new major version
