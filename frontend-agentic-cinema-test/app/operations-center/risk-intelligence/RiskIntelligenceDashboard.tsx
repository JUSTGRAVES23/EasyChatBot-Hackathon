import { useCallback, useEffect, useState } from "react";
import {
  getRiskIntelligence,
  type RiskIntelligenceResponse,
} from "../../lib/api/riskIntelligence";

function MetricCard({
  label,
  metric,
}: {
  label: string;
  metric: RiskIntelligenceResponse["total_item_years"];
}) {
  const available = metric.availability === "AVAILABLE";

  return (
    <section>
      <h2>{label}</h2>
      <p>
        {available && metric.value !== null
          ? metric.value
          : "Not available"}
      </p>
      <small>{metric.availability}</small>
    </section>
  );
}

export default function RiskIntelligenceDashboard() {
  const [data, setData] = useState<RiskIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await getRiskIntelligence();
      setData(result);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Risk Intelligence is temporarily unavailable.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  if (loading) {
    return <p>Loading Risk Intelligence…</p>;
  }

  if (error) {
    return (
      <section role="alert">
        <h1>Risk & Compliance Intelligence</h1>
        <p>{error}</p>
        <button type="button" onClick={() => void loadData()}>
          Retry
        </button>
      </section>
    );
  }

  if (!data) {
    return <p>Risk Intelligence is not available.</p>;
  }

  return (
    <section>
      <header>
        <h1>Risk & Compliance Intelligence</h1>
        <p>
          Lifecycle: {data.lifecycle_id}
        </p>
        <p>
          As of: {new Date(data.as_of).toLocaleString()}
        </p>
      </header>

      <section aria-label="Key metrics">
        <MetricCard
          label="Monitoring Item-Years"
          metric={data.total_item_years}
        />
        <MetricCard
          label="Distinct Controls"
          metric={data.distinct_controls}
        />
        <MetricCard
          label="Distinct Domains"
          metric={data.distinct_domains}
        />
      </section>

      <section>
        <h2>Yearly Population</h2>
        {Object.keys(data.yearly_population).length === 0 ? (
          <p>Not available</p>
        ) : (
          <ul>
            {Object.entries(data.yearly_population).map(([year, count]) => (
              <li key={year}>
                {year}: {count}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Risk Distribution</h2>
        {Object.keys(data.risk_distribution).length === 0 ? (
          <p>Not available</p>
        ) : (
          <ul>
            {Object.entries(data.risk_distribution).map(([risk, count]) => (
              <li key={risk}>
                {risk}: {count}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Compliance Domains</h2>
        {Object.keys(data.domain_distribution).length === 0 ? (
          <p>Not available</p>
        ) : (
          <ul>
            {Object.entries(data.domain_distribution).map(
              ([domain, count]) => (
                <li key={domain}>
                  {domain}: {count}
                </li>
              ),
            )}
          </ul>
        )}
      </section>

      <footer>
        <small>Source: {data.source}</small>
      </footer>
    </section>
  );
}

