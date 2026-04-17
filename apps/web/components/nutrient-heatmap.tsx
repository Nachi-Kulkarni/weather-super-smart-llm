"use client";

import type { HeatmapCell } from "@soil/shared-types";

/**
 * Maps fertilizer recommendation magnitudes (N/P/K) to heat levels.
 * These thresholds are UI scaffolding — tune against agronomy + product policy.
 */
function burdenLevel(value: number | null): "low" | "mid" | "high" | "na" {
  if (value === null || Number.isNaN(value)) {
    return "na";
  }
  const magnitude = Math.abs(value);
  if (magnitude < 80) {
    return "low";
  }
  if (magnitude < 160) {
    return "mid";
  }
  return "high";
}

export function NutrientHeatmap({ rows }: { rows: HeatmapCell[] }) {
  if (!rows.length) {
    return null;
  }

  return (
    <div className="heatmap-wrap">
      <div className="heatmap-header">
        <p className="eyebrow">Nutrient burden heat map</p>
        <h3>N / P / K (recommendation basis)</h3>
        <p className="panel-copy">
          Cell colors reflect suggested fertilizer addition magnitude per nutrient — not raw soil chemistry alone.
        </p>
      </div>

      <div className="heatmap-table" role="table" aria-label="Nutrient heat map">
        <div className="heatmap-row heatmap-row-head" role="row">
          <div className="heatmap-cell heatmap-sticky" role="columnheader">
            Crop
          </div>
          <div className="heatmap-cell" role="columnheader">
            ΔN
          </div>
          <div className="heatmap-cell" role="columnheader">
            ΔP
          </div>
          <div className="heatmap-cell" role="columnheader">
            ΔK
          </div>
          <div className="heatmap-cell" role="columnheader">
            Score
          </div>
        </div>

        {rows.map((row) => (
          <div className="heatmap-row" key={`${row.cropId}-${row.cropName}`} role="row">
            <div className="heatmap-cell heatmap-sticky" role="cell">
              <span className="heatmap-crop">{row.cropName}</span>
              <span className={`heatmap-confidence heatmap-confidence-${row.confidenceBand.toLowerCase()}`}>
                {row.confidenceBand}
              </span>
            </div>
            <HeatCell value={row.deltaN} />
            <HeatCell value={row.deltaP} />
            <HeatCell value={row.deltaK} />
            <div className="heatmap-cell heatmap-score" role="cell">
              {row.score.toFixed(2)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function HeatCell({ value }: { value: number | null }) {
  const level = burdenLevel(value);
  return (
    <div className={`heatmap-cell heatmap-heat heat-${level}`} role="cell">
      {value === null ? "—" : value.toFixed(1)}
    </div>
  );
}
