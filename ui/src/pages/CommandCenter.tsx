import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { Fund } from "../types";

interface BalanceSheetData {
  fundId: string;
  fundCode: string;
  fundName: string;
  propertyCount?: number;
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
  valueColor?: string;
  subtitle: string;
  subtitleColor: "green" | "yellow" | "red";
  sources: string;
}

function MetricCard({ title, icon, value, valueColor, subtitle, subtitleColor, sources }: CardProps) {
  const dotColors = { green: "#4caf50", yellow: "#ff9800", red: "#ef5350" };

  return (
    <div className="cc-card">
      <div className="cc-card-header">
        <span className="cc-card-title">{title}</span>
        <span className="cc-card-icon">{icon}</span>
      </div>
      <div className="cc-card-value" style={valueColor ? { color: valueColor } : undefined}>
        {value}
      </div>
      <div className="cc-card-subtitle">
        <span className="cc-dot" style={{ background: dotColors[subtitleColor] }} />
        {subtitle}
      </div>
      <div className="cc-card-sources-row">
        {sources.split(" \u00B7 ").map((s, i) => (
          <span key={i} className="cc-source-tag">
            <span className="cc-dot-sm" style={{ background: "#4caf50" }} />
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}

const TABS = [
  "Daily Brief",
  "Performance Summary",
  "Liquidity & Cash",
  "Risk & Valuation",
  "Month-End Control",
  "Data Health",
];

export default function CommandCenter() {
  const { currentOrg } = useAuth();
  const [funds, setFunds] = useState<Fund[]>([]);
  const [selectedFundId, setSelectedFundId] = useState("");
  const [data, setData] = useState<BalanceSheetData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("Daily Brief");

  useEffect(() => {
    if (currentOrg) {
     
      api
        .get(`/orgs/${currentOrg.id}/funds`)
        .then((res) => {
          setFunds(res.data);
          if (res.data.length > 0 && !selectedFundId) {
            setSelectedFundId(res.data[0].id);
          }
        })
        .catch(() => setFunds([]));
    }
  }, [currentOrg]);

  const fetchBalanceSheet = () => {
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
      {/* Title */}
      <div className="cc-title-row">
        <h2>Command Center</h2>
        <span className="cc-live-badge">LIVE</span>
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

      {loading && <p className="cc-loading">Loading...</p>}
      {error && <p className="error">{error}</p>}

      {data && !loading && (
        <>
          {/* Top row - 6 cards */}
          <div className="cc-row cc-row-6">
            <MetricCard
              title="AUM"
              icon="$"
              value={fmtCompact(data.aum)}
              subtitle="+3.2% vs Prior Year"
              subtitleColor="green"
              sources="APPRAISAL + BOOK"
            />
            <MetricCard
              title="PORTFOLIO NOI"
              icon="&#9636;"
              value={fmtCompact(data.noi)}
              subtitle={data.noi >= 0 ? "Net Operating Income" : "-2.4% vs Budget"}
              subtitleColor={data.noi >= 0 ? "green" : "yellow"}
              sources="GL \u00B7 RECENCY \u00B7 QUALITY"
            />
            <MetricCard
              title="OCCUPANCY"
              icon="&#9634;"
              value="--"
              subtitle="Portfolio-Wide"
              subtitleColor="green"
              sources="LEASE DATA \u00B7 RECENCY"
            />
            <MetricCard
              title="REVENUE"
              icon="$"
              value={fmtCompact(data.noi + Math.abs(data.budgetVsActual.actual))}
              subtitle="-1.8% vs Budget"
              subtitleColor="yellow"
              sources="GL \u00B7 RECENCY"
            />
            <MetricCard
              title="EXPENSE RATIO"
              icon="%"
              value={`${(data.expenseRatio * 100).toFixed(1)}%`}
              subtitle="+2.1pp vs Budget"
              subtitleColor="yellow"
              sources="GL \u00B7 RECENCY"
            />
            <MetricCard
              title="CASH"
              icon="&#9783;"
              value={fmtCompact(data.cash)}
              subtitle="+$285K MTD"
              subtitleColor="green"
              sources="BANK FEEDS \u00B7 RECENCY"
            />
          </div>

          {/* Bottom row - 5 cards */}
          <div className="cc-row cc-row-5">
            <MetricCard
              title="EUM"
              icon="&#9678;"
              value={fmtCompact(data.eum)}
              subtitle="Equity Under Management"
              subtitleColor="green"
              sources="GL + APPRAISAL"
            />
            <MetricCard
              title="PORTFOLIO DSCR"
              icon="&#9684;"
              value={`${data.dscr.toFixed(2)}x`}
              subtitle={data.dscr >= 1.25 ? "Above 1.25x covenant" : "Below 1.25x covenant"}
              subtitleColor={data.dscr >= 1.25 ? "green" : "red"}
              sources="GL + DEBT"
            />
            <MetricCard
              title="BUDGET VS ACTUAL"
              icon="&#9776;"
              value={fmtCompact(data.budgetVsActual.variance)}
              valueColor={data.budgetVsActual.variance < 0 ? "#ef5350" : undefined}
              subtitle={data.budgetVsActual.variance < 0 ? "NOI shortfall YTD" : "Favorable variance YTD"}
              subtitleColor={data.budgetVsActual.variance >= 0 ? "green" : "red"}
              sources="GL"
            />
            <MetricCard
              title="YTD RETURN"
              icon="&#8599;"
              value={`${data.ytdReturn.toFixed(1)}%`}
              subtitle="Levered \u00B7 Net"
              subtitleColor={data.ytdReturn >= 0 ? "green" : "red"}
              sources="CALCULATED"
            />
            <MetricCard
              title="AT-RISK ASSETS"
              icon="&#9651;"
              value="--"
              subtitle="Below budget threshold"
              subtitleColor="red"
              sources="GL + LEASES"
            />
          </div>

          {/* Returns bar */}
          <div className="cc-returns-bar">
            <span className="cc-returns-label">RETURNS</span>
            <span className="cc-returns-period">1Y</span>
            <span className="cc-returns-val cc-returns-up">12.4%</span>
            <span className="cc-returns-val cc-returns-sm">7.8%</span>
            <span className="cc-returns-period">3Y</span>
            <span className="cc-returns-val cc-returns-up">10.1%</span>
            <span className="cc-returns-val cc-returns-sm">6.5%</span>
            <span className="cc-returns-period">5Y</span>
            <span className="cc-returns-val cc-returns-up">11.8%</span>
            <span className="cc-returns-val cc-returns-sm">7.2%</span>
          </div>

          {/* Tabs */}
          <div className="cc-tabs">
            {TABS.map((tab) => (
              <button
                key={tab}
                className={`cc-tab ${activeTab === tab ? "cc-tab-active" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {activeTab === "Daily Brief" && (
            <div className="cc-daily-brief">
              {/* Assets table */}
              <div className="cc-assets-panel">
                <h3>Assets Ranked by Performance and Risk</h3>
                <table className="cc-assets-table">
                  <thead>
                    <tr>
                      <th>ASSET NAME</th>
                      <th>YTD YIELD</th>
                      <th>OCCUPANCY</th>
                      <th>WALE</th>
                      <th>RISK SCORE</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Oakwood Corporate Plaza</td>
                      <td className="cc-yield-green">11.2%</td>
                      <td>98.5%</td>
                      <td>4.2 yrs</td>
                      <td><span className="cc-risk-badge cc-risk-low">Low</span></td>
                    </tr>
                    <tr>
                      <td>The Meridian Industrial Park</td>
                      <td className="cc-yield-green">9.8%</td>
                      <td>94.0%</td>
                      <td>6.5 yrs</td>
                      <td><span className="cc-risk-badge cc-risk-low">Low</span></td>
                    </tr>
                    <tr>
                      <td>Summit Retail Collective</td>
                      <td>6.1%</td>
                      <td>82.3%</td>
                      <td>2.1 yrs</td>
                      <td><span className="cc-risk-badge cc-risk-high">High</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Action queue */}
              <div className="cc-action-panel">
                <div className="cc-action-header">
                  <h3>ACTION QUEUE</h3>
                  <span className="cc-action-count">3</span>
                </div>
                <div className="cc-action-card cc-action-overdue">
                  <div className="cc-action-card-top">
                    <span className="cc-action-tag cc-action-tag-overdue">OVERDUE</span>
                    <span className="cc-action-time">2h ago</span>
                  </div>
                  <p className="cc-action-title">Reconcile Q3 Variance - Summit Retail</p>
                  <a className="cc-action-link" href="#">View Details &rsaquo;</a>
                </div>
                <div className="cc-action-card cc-action-pending">
                  <div className="cc-action-card-top">
                    <span className="cc-action-tag cc-action-tag-pending">PENDING APPROVAL</span>
                    <span className="cc-action-time">Yesterday</span>
                  </div>
                  <p className="cc-action-title">Capital Call Notice #42 Distribution</p>
                </div>
              </div>
            </div>
          )}

          {activeTab !== "Daily Brief" && (
            <div className="cc-tab-placeholder">
              <p>{activeTab} content coming soon.</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
