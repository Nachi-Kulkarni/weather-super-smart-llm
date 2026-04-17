export function SchemaCard() {
  return (
    <section className="info-card">
      <div className="info-card-header">
        <p className="eyebrow">Response Contract</p>
        <h2>Recommendation payload shape</h2>
      </div>

      <div className="schema-grid">
        <div>
          <h3>Per crop option</h3>
          <ul className="schema-list">
            <li>`cropId`, `cropName`, `rank`</li>
            <li>`recommendedN`, `recommendedP`, `recommendedK`</li>
            <li>`nutrientBasis`, `finalScore`, `confidenceBand`</li>
            <li>`reasons`, `cautions`, `citations`, `tracePayload`</li>
          </ul>
        </div>
        <div>
          <h3>Guardrails</h3>
          <ul className="schema-list">
            <li>Agronomy math lives in Python, not in prompts.</li>
            <li>Every option carries citations and a scoring trace.</li>
            <li>Low-confidence fallbacks are explicit, never hidden.</li>
          </ul>
        </div>
      </div>
    </section>
  );
}
