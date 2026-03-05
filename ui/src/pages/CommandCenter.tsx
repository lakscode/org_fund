import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { Fund } from "../types";

interface BalanceSheetData {
  fundId: string;
  fundCode: string;
  fundName: string;
  aum: number;
  eum: number;
  noi: number;
  expenseRatio: number;
  cash: number;
  dscr: number;
  budgetVsActual: {
    actual: number;
    budget: number;
    variance: number;
  };
  ytdReturn: number;
}

function fmtCompact(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1_000_000_000) return `${sign}$${(abs / 1_000_000_000).toFixed(1)}B`;
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(0)}K`;
  return `${sign}$${abs.toFixed(0)}`;
}

interface CardProps {
  title: string;
  icon: string;
  value: string;
  subtitle: string;
  subtitleColor: "green" | "yellow" | "red";
  sources: { label: string; color: "green" | "yellow" | "red" }[];
  accent?: "green" | "red";
}

function MetricCard({ title, icon, value, subtitle, subtitleColor, sources, accent }: CardProps) {
  const dotColors = { green: "#4caf50", yellow: "#ff9800", red: "#ef5350" };
  const accentBorder = accent === "red" ? "#ffcdd2" : accent === "green" ? "#c8e6c9" : undefined;

  return (
    <div
      className="cc-card"
      style={accentBorder ? { borderLeft: `3px solid ${accentBorder}` } : undefined}
    >
      <div className="cc-card-header">
        <span className="cc-card-title">{title}</span>
        <span className="cc-card-icon">{icon}</span>
      </div>
      <div className="cc-card-value">{value}</div>
      <div className="cc-card-subtitle">
        <span
          className="cc-dot"
          style={{ background: dotColors[subtitleColor] }}
        />
        {subtitle}
      </div>
      <div className="cc-card-sources">
        {sources.map((s, i) => (
          <span key={i} className="cc-source">
            <span className="cc-dot-sm" style={{ background: dotColors[s.color] }} />
            {s.label}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function CommandCenter() {
  const { currentOrg } = useAuth();
  const [funds, setFunds] = useState<Fund[]>([]);
  const [selectedFundId, setSelectedFundId] = useState("");
  const [data, setData] = useState<BalanceSheetData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (currentOrg) {
      api
        .get(`/orgs/${currentOrg.id}/funds`)
        .then((res) => {
          setFunds(res.data);
          if (res.data.length > 0 && !selectedFundId) {
            setSelectedFundId(res.data[0].fundId);
          }
        })
        .catch(() => setFunds([]));
    }
  }, [currentOrg]);

  const fetchBalanceSheet = () => {
    console.log("fetchBalanceSheet selectedFundId ", selectedFundId)
    if (!selectedFundId) return;
    setLoading(true);
    setError("");
    api
      .get(`/funds/${selectedFundId}/balancesheet`)
      .then((res) => setData(res.data))
      .catch(() => {
        setData(null);
        setError("Failed to load data.");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchBalanceSheet();
  }, [selectedFundId]);

  if (!currentOrg) return <p>No organization selected.</p>;

  const selectedFund = funds.find((f) => f.id === selectedFundId);

  return (
    <div className="command-center">
      <div className="cc-title-row">
        <h2>Command Center</h2>
        <span className="cc-live-badge">Live</span>
        <button
          className="cc-refresh-btn"
          onClick={fetchBalanceSheet}
          disabled={loading || !selectedFundId}
          title="Refresh data"
        >
          &#x21bb;
        </button>
        <select
          className="cc-fund-select"
          value={selectedFundId}
          onChange={(e) => setSelectedFundId(e.target.value)}
        >
          {funds.map((f) => (
            <option key={f.id} value={f.id}>
              {f.fundCode} - {f.fundName}
            </option>
          ))}
        </select>
      </div>
      <p className="cc-subtitle">
        Executive portfolio-wide visibility
        {selectedFund ? ` \u00B7 ${selectedFund.fundName}` : ""}
      </p>

      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}

      {data && !loading && (
        <>
          {/* Top row */}
          <div className="cc-row cc-row-top">
            <MetricCard
              title="AUM"
              icon="$"
              value={fmtCompact(data.aum)}
              subtitle="Assets Under Management"
              subtitleColor="green"
              sources={[
                { label: "Appraisal + Book", color: "green" },
                { label: "Recency", color: "green" },
                { label: "Quality", color: "green" },
              ]}
            />
            <MetricCard
              title="PORTFOLIO NOI"
              icon="\u2261"
              value={fmtCompact(data.noi)}
              subtitle="Net Operating Income"
              subtitleColor={data.noi >= 0 ? "green" : "yellow"}
              sources={[
                { label: "GL", color: "green" },
                { label: "Recency", color: "green" },
                { label: "Quality", color: "green" },
              ]}
            />
            <MetricCard
              title="EXPENSE RATIO"
              icon="%"
              value={`${(data.expenseRatio * 100).toFixed(1)}%`}
              subtitle="Expenses / Revenue"
              subtitleColor={data.expenseRatio <= 0.4 ? "green" : "yellow"}
              sources={[
                { label: "GL", color: "green" },
                { label: "Recency", color: "green" },
                { label: "Quality", color: "green" },
              ]}
            />
            <MetricCard
              title="CASH"
              icon="$"
              value={fmtCompact(data.cash)}
              subtitle="Cash balance"
              subtitleColor="green"
              sources={[
                { label: "Bank Feeds", color: "green" },
                { label: "Recency", color: "green" },
                { label: "Quality", color: "green" },
              ]}
            />
          </div>

          {/* Bottom row */}
          <div className="cc-row cc-row-bottom">
            <MetricCard
              title="EUM"
              icon="\u25CE"
              value={fmtCompact(data.eum)}
              subtitle="Equity Under Management"
              subtitleColor="green"
              accent="green"
              sources={[
                { label: "GL + Appraisal", color: "green" },
                { label: "Recency", color: "green" },
                { label: "Quality", color: "green" },
              ]}
            />
            <MetricCard
              title="PORTFOLIO DSCR"
              icon="\u25D1"
              value={`${data.dscr.toFixed(2)}x`}
              subtitle={data.dscr >= 1.25 ? "Above 1.25x covenant" : "Below 1.25x covenant"}
              subtitleColor={data.dscr >= 1.25 ? "green" : "red"}
              accent="green"
              sources={[
                { label: "GL + Debt Schedule", color: "green" },
                { label: "Recency", color: "green" },
                { label: "Quality", color: "green" },
              ]}
            />
            <MetricCard
              title="BUDGET VS ACTUAL"
              icon="\u2261"
              value={fmtCompact(data.budgetVsActual.variance)}
              subtitle={data.budgetVsActual.variance < 0 ? "NOI shortfall YTD" : "Favorable variance YTD"}
              subtitleColor={data.budgetVsActual.variance >= 0 ? "green" : "red"}
              accent={data.budgetVsActual.variance >= 0 ? "green" : "red"}
              sources={[
                { label: "GL", color: "green" },
                { label: "Recency", color: "green" },
                { label: "Quality", color: "green" },
              ]}
            />
            <MetricCard
              title="YTD RETURN"
              icon="\u2197"
              value={`${data.ytdReturn.toFixed(1)}%`}
              subtitle="Levered \u00B7 Net"
              subtitleColor={data.ytdReturn >= 0 ? "green" : "red"}
              accent={data.ytdReturn >= 0 ? "green" : "red"}
              sources={[
                { label: "Calculated", color: "green" },
                { label: "Recency", color: "green" },
                { label: "Quality", color: "green" },
              ]}
            />
            <MetricCard
              title="TOTAL FUND EXPENSES"
              icon="$"
              value={fmtCompact(data.budgetVsActual.actual)}
              subtitle="Before Depreciation & Tax"
              subtitleColor="green"
              sources={[
                { label: "GL", color: "green" },
                { label: "Recency", color: "green" },
                { label: "Quality", color: "green" },
              ]}
            />
          </div>
        </>
      )}
    </div>
  );
}
