"use client";

import { useState, useTransition } from "react";

import type { RecommendationResponse } from "@soil/shared-types";

import { NutrientHeatmap } from "@/components/nutrient-heatmap";

const starterRequest = {
  location: {
    state: "Karnataka",
    district: "Tumkur",
    agroRegionCode: "AER-12",
    lat: 13.34,
    lon: 77.1,
  },
  weatherProvider: "both",
  soilSample: {
    nValue: 180,
    pValue: 24,
    kValue: 210,
    phValue: 6.7,
    ocValue: 0.82,
    nutrientBasis: "N-P-K",
  },
  season: "kharif",
  targetYieldValue: 50,
  targetYieldUnit: "q/ha",
  candidateCropCodes: [],
  localAdoptionOverrides: {},
  marketSignalOverrides: {},
  organicContributions: {},
  fetchWeather: true,
  includeRetrieval: true,
  ragMode: "hybrid",
  retrievalQuery: "karnataka kharif maize fertilizer",
  soilNpkOffsets: [
    { label: "N-5", n: -5, p: 0, k: 0 },
    { label: "baseline", n: 0, p: 0, k: 0 },
    { label: "N+5", n: 5, p: 0, k: 0 },
  ],
};

export function RecommendationProbe() {
  const [requestText, setRequestText] = useState(JSON.stringify(starterRequest, null, 2));
  const [response, setResponse] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const runProbe = () => {
    startTransition(() => {
      void (async () => {
        setError(null);
        setResponse(null);

        try {
          const parsedRequest = JSON.parse(requestText) as Record<string, unknown>;
          const result = await fetch("/api/recommend", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(parsedRequest),
          });

          if (!result.ok) {
            const text = await result.text();
            throw new Error(text || "Probe request failed.");
          }

          const payload = (await result.json()) as RecommendationResponse;
          setResponse(payload);
        } catch (caughtError) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Unable to run recommendation probe.",
          );
        }
      })();
    });
  };

  return (
    <section className="probe-card">
      <div className="probe-header">
        <div>
          <p className="eyebrow">Deterministic API</p>
          <h2>Recommendation probe</h2>
        </div>
        <button
          className="probe-button"
          disabled={isPending}
          onClick={runProbe}
          type="button"
        >
          {isPending ? "Running..." : "Run /recommend"}
        </button>
      </div>

      <p className="panel-copy">
        This panel exercises the REST contract directly. With no Postgres URL, the API uses the bundled Karnataka
        demo catalog. Set `DATABASE_URL` to load crops/rules from `db/schema.sql` + `db/seed.sql` instead.
      </p>

      <textarea
        className="probe-editor"
        onChange={(event) => setRequestText(event.target.value)}
        spellCheck={false}
        value={requestText}
      />

      {error ? <p className="probe-error">{error}</p> : null}

      {response ? (
        <div className="probe-results">
          <div className="probe-metadata">
            <span>Run: {response.runId}</span>
            <span>Scoring: {response.scoringVersion}</span>
            <span>Options: {response.options.length}</span>
          </div>

          {response.weatherProfile ? (
            <div className="weather-banner">
              <p className="eyebrow">Weather profile used</p>
              <p>
                Short-range: <strong>{formatScore(response.weatherProfile.shortRangeScore)}</strong> · Seasonal
                prior: <strong>{formatScore(response.weatherProfile.seasonalPriorScore)}</strong> · Source:{" "}
                <strong>{response.weatherProfile.sourceName ?? "—"}</strong>
              </p>
              {response.weatherProfile.notes?.length ? (
                <ul className="weather-notes">
                  {response.weatherProfile.notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}

          {response.retrievalChunks?.length ? (
            <div className="retrieval-panel">
              <p className="eyebrow">Retrieved agronomy chunks</p>
              <div className="retrieval-grid">
                {response.retrievalChunks.map((chunk) => (
                  <article className="retrieval-card" key={chunk.chunkId}>
                    <header>
                      <h4>{chunk.title}</h4>
                      <span className="retrieval-type">{chunk.chunkType}</span>
                    </header>
                    <p className="retrieval-meta">
                      Match: <strong>{chunk.matchType ?? "—"}</strong>
                      {chunk.score != null ? (
                        <>
                          {" "}
                          · score <strong>{chunk.score.toFixed(4)}</strong>
                        </>
                      ) : null}
                    </p>
                    <p>{chunk.chunkText}</p>
                  </article>
                ))}
              </div>
            </div>
          ) : null}

          <div className="result-grid">
            {response.options.length > 0 ? (
              response.options.map((option) => (
                <article className="result-card" key={option.cropId}>
                  <div className="result-card-header">
                    <h3>{option.cropName}</h3>
                    <span
                      className={`confidence confidence-${option.confidenceBand.toLowerCase()}`}
                    >
                      {option.confidenceBand}
                    </span>
                  </div>
                  <p>
                    Score <strong>{option.finalScore.toFixed(2)}</strong> in {option.nutrientBasis}
                  </p>
                  <p>
                    N/P/K: {option.recommendedN ?? "-"} / {option.recommendedP ?? "-"} /{" "}
                    {option.recommendedK ?? "-"}
                  </p>
                </article>
              ))
            ) : (
              <article className="result-card empty-state">
                <h3>No crop options</h3>
                <p>Check season/location against available rules, or load seed data into Postgres.</p>
              </article>
            )}
          </div>

          <NutrientHeatmap rows={response.heatmap} />

          {response.whatIfRuns?.length ? (
            <div className="whatif-stack">
              <p className="eyebrow">What-if scenarios</p>
              {response.whatIfRuns.map((run, index) => (
                <details className="whatif-details" key={`${run.label ?? "scenario"}-${index}`} open={index === 0}>
                  <summary>
                    {run.label ?? `Scenario ${index + 1}`} · top score{" "}
                    {run.options[0] ? run.options[0].finalScore.toFixed(2) : "—"}
                  </summary>
                  <NutrientHeatmap rows={run.heatmap} />
                </details>
              ))}
            </div>
          ) : null}

          <pre className="probe-response">{JSON.stringify(response, null, 2)}</pre>
        </div>
      ) : null}
    </section>
  );
}

function formatScore(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return value.toFixed(2);
}
