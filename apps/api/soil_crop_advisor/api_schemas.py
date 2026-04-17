from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class LocationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: str | None = None
    district: str | None = None
    agroRegionCode: str | None = None
    lat: float | None = None
    lon: float | None = None


class SoilSampleInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    nValue: float | None = None
    pValue: float | None = None
    kValue: float | None = None
    phValue: float | None = None
    ecValue: float | None = None
    ocValue: float | None = None
    nutrientBasis: Literal["N-P-K", "N-P2O5-K2O"] = "N-P-K"
    extras: dict[str, Any] = Field(default_factory=dict)


class WeatherInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shortRangeScore: float | None = None
    seasonalPriorScore: float | None = None
    sourceName: str | None = None
    notes: list[str] = Field(default_factory=list)


class SoilNpkOffset(BaseModel):
    """Perturb soil test values (same units as the incoming soil sample) for what-if exploration."""

    model_config = ConfigDict(extra="forbid")

    label: str | None = None
    n: float = 0.0
    p: float = 0.0
    k: float = 0.0


class RecommendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: LocationInput
    soilSample: SoilSampleInput
    season: str = "next_90_days"
    targetYieldValue: float | None = None
    targetYieldUnit: str | None = None
    candidateCropCodes: list[str] = Field(default_factory=list)
    localAdoptionOverrides: dict[str, float] = Field(default_factory=dict)
    marketSignalOverrides: dict[str, float] = Field(default_factory=dict)
    organicContributions: dict[str, float] = Field(default_factory=dict)
    weather: WeatherInput | None = None
    fetchWeather: bool = False
    weatherProvider: Literal["open_meteo", "imd", "both"] = Field(
        default="open_meteo",
        description="Forecast source when fetchWeather=true and lat/lon are set.",
    )
    includeRetrieval: bool = False
    retrievalQuery: str | None = None
    ragMode: Literal["keyword", "vector", "hybrid"] = Field(
        default="hybrid",
        description="keyword=ILIKE; vector=pgvector; hybrid=RRF fusion.",
    )
    soilNpkOffsets: list[SoilNpkOffset] = Field(default_factory=list)


class ChatMessageInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str
    content: list[dict[str, Any]] | str


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessageInput]
    threadId: str | None = None


class ToolEventModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: str
    phase: Literal["start", "end", "error"]
    detail: str | None = None
    at: str | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    toolEvents: list[ToolEventModel] = Field(default_factory=list)


class CitationRefModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sourceDocId: str
    title: str
    snippet: str | None = None


class CropOptionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cropId: str
    cropName: str
    rank: int
    targetYieldValue: float | None = None
    targetYieldUnit: str | None = None
    recommendedN: float | None = None
    recommendedP: float | None = None
    recommendedK: float | None = None
    nutrientBasis: Literal["N-P-K", "N-P2O5-K2O"]
    nutrientFitScore: float
    weatherFeasibilityScore: float
    agroRegionFitScore: float
    localAdoptionScore: float
    marketSignalScore: float
    inputBurdenScore: float
    finalScore: float
    confidenceBand: Literal["A", "B", "C"]
    reasons: list[str]
    cautions: list[str]
    citations: list[CitationRefModel]
    tracePayload: dict[str, Any]


class HeatmapCellModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cropId: str
    cropName: str
    deltaN: float | None = None
    deltaP: float | None = None
    deltaK: float | None = None
    score: float
    confidenceBand: Literal["A", "B", "C"]


class RejectedCropModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cropName: str
    reason: str


class RetrievalChunkModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunkId: str
    sourceDocId: str
    title: str
    chunkType: str
    chunkText: str
    cropTags: list[str] = Field(default_factory=list)
    matchType: Literal["keyword", "vector", "hybrid"] | None = None
    score: float | None = None


class WhatIfScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = None
    soilSample: dict[str, Any]
    options: list[CropOptionModel]
    heatmap: list[HeatmapCellModel]
    rejectedCrops: list[RejectedCropModel]


class RecommendationResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runId: str
    scoringVersion: str
    location: dict[str, Any]
    soilSample: dict[str, Any]
    options: list[CropOptionModel]
    heatmap: list[HeatmapCellModel]
    rejectedCrops: list[RejectedCropModel]
    weatherProfile: dict[str, Any] | None = Field(default=None)
    retrievalChunks: list[RetrievalChunkModel] | None = Field(default=None)
    whatIfRuns: list[WhatIfScenarioModel] | None = Field(default=None)
