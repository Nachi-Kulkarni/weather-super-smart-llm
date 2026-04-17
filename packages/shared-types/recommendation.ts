export type ConfidenceBand = "A" | "B" | "C";

export interface CitationRef {
  sourceDocId: string;
  title: string;
  snippet?: string;
}

export interface CropOption {
  cropId: string;
  cropName: string;
  rank: number;
  targetYieldValue?: number;
  targetYieldUnit?: string;
  recommendedN: number | null;
  recommendedP: number | null;
  recommendedK: number | null;
  nutrientBasis: "N-P-K" | "N-P2O5-K2O";
  nutrientFitScore: number;
  weatherFeasibilityScore: number;
  agroRegionFitScore: number;
  localAdoptionScore: number;
  marketSignalScore: number;
  inputBurdenScore: number;
  finalScore: number;
  confidenceBand: ConfidenceBand;
  reasons: string[];
  cautions: string[];
  citations: CitationRef[];
  tracePayload: Record<string, unknown>;
}

export interface HeatmapCell {
  cropId: string;
  cropName: string;
  deltaN: number | null;
  deltaP: number | null;
  deltaK: number | null;
  score: number;
  confidenceBand: ConfidenceBand;
}

export interface RetrievalChunk {
  chunkId: string;
  sourceDocId: string;
  title: string;
  chunkType: string;
  chunkText: string;
  cropTags: string[];
  matchType?: "keyword" | "vector" | "hybrid" | null;
  score?: number | null;
}

export interface WhatIfScenario {
  label?: string | null;
  soilSample: Record<string, unknown>;
  options: CropOption[];
  heatmap: HeatmapCell[];
  rejectedCrops: Array<{
    cropName: string;
    reason: string;
  }>;
}

export interface RecommendationResponse {
  runId: string;
  scoringVersion: string;
  location: {
    state?: string;
    district?: string;
    lat?: number;
    lon?: number;
  };
  soilSample: Record<string, unknown>;
  options: CropOption[];
  heatmap: HeatmapCell[];
  rejectedCrops: Array<{
    cropName: string;
    reason: string;
  }>;
  weatherProfile?: {
    shortRangeScore?: number | null;
    seasonalPriorScore?: number | null;
    sourceName?: string | null;
    notes: string[];
  } | null;
  retrievalChunks?: RetrievalChunk[] | null;
  whatIfRuns?: WhatIfScenario[] | null;
}
