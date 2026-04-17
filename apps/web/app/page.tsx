import { AssistantPanel } from "@/components/assistant-panel";
import { RecommendationProbe } from "@/components/recommendation-probe";
import { SchemaCard } from "@/components/schema-card";

export default function Home() {
  return (
    <main className="page-shell">
      <section className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">Soil-to-Crop Intelligence Advisor</p>
          <h1>Equation-first agronomy, not prompt-made fertilizer math.</h1>
          <p className="hero-text">
            This starter scaffold keeps citations, confidence bands, and scoring traces first-class. RAG retrieves verified rules. Deterministic services compute fertilizer need and rank crops.
          </p>
        </div>
        <div className="hero-stats">
          <div className="stat-tile">
            <span>Math</span>
            <strong>Structured code</strong>
          </div>
          <div className="stat-tile">
            <span>Sources</span>
            <strong>Audit-ready registry</strong>
          </div>
          <div className="stat-tile">
            <span>UI</span>
            <strong>assistant-ui + probe</strong>
          </div>
        </div>
      </section>

      <section className="workspace-grid">
        <AssistantPanel />
        <div className="side-stack">
          <SchemaCard />
          <RecommendationProbe />
        </div>
      </section>
    </main>
  );
}
