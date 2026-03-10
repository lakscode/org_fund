import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import { Table } from "antd";
import type { ColumnsType } from "antd/es/table";
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
  budget_vs_actual: number;
  noi_vs_budget: number;
  budgetVsActual_details: {
    actual: number;
    budget: number;
    variance: number;
  };
  ytdReturn: number;
}

interface Property {
  id: string;
  propertyName: string;
  market: string;
  noiActual: number;
  noiBudget: number;
  noiVariance: number;
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
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(false);
  const [fundsLoading, setFundsLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("Daily Brief");

  useEffect(() => {
    if (currentOrg) {
      setFundsLoading(true);
      api
        .get(`/orgs/${currentOrg.id}/funds`)
        .then((res) => {
          setFunds(res.data);
          if (res.data.length > 0 && !selectedFundId) {
            setSelectedFundId(res.data[0].id);
          }
        })
        .catch(() => setFunds([]))
        .finally(() => setFundsLoading(false));

      api
        .get(`/orgs/${currentOrg.id}/properties`)
        .then((res) => setProperties(res.data))
        .catch(() => setProperties([]));
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

  const filteredProperties = properties
    .filter((p) => p.noiActual !== 0 || p.noiBudget !== 0)
    .sort((a, b) => b.noiActual - a.noiActual);

  const assetsColumns: ColumnsType<Property> = [
    { title: "Asset Name", dataIndex: "propertyName", key: "propertyName" },
    { title: "Market", dataIndex: "market", key: "market", render: (v: string) => v || "—" },
    { title: "NOI vs Budget", key: "noiBudget", render: (_: unknown, r: Property) => fmtCompact(r.noiActual) },
    { title: "NOI Trend", key: "noiTrend", render: () => "-" },
    { title: "Lease Risk", key: "leaseRisk", render: () => "-" },
  ];

  const rankColumns: ColumnsType<Property> = [
    { title: "Asset Name", dataIndex: "propertyName", key: "propertyName" },
    { title: "NOI", key: "noi", render: (_: unknown, r: Property) => fmtCompact(r.noiActual) },
    {
      title: "Variance",
      key: "variance",
      render: (_: unknown, r: Property) => (
        <span style={{ color: r.noiVariance >= 0 ? "#4caf50" : "#ef5350" }}>
          {fmtCompact(r.noiVariance)}
        </span>
      ),
    },
    { title: "Occupancy", key: "occupancy", render: () => "-" },
    { title: "Expense Ratio", key: "expenseRatio", render: () => "-" },
    { title: "DSCR", key: "dscr", render: () => "-" },
  ];

  return (
    <div className="command-center page-container">
      {/* Title */}
      <div className="cc-title-row">
        <h2 className="page-title">Command Center</h2>
        <span className="cc-live-badge">LIVE</span>
        <div className="select-wrapper">
          <select
            className="cc-fund-select app-select"
            value={selectedFundId}
            onChange={(e) => setSelectedFundId(e.target.value)}
            disabled={fundsLoading}
          >
            {fundsLoading ? (
              <option>Loading funds...</option>
            ) : funds.length === 0 ? (
              <option>No funds available</option>
            ) : (
              funds.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.fundCode} - {f.fundName}
                </option>
              ))
            )}
          </select>
          {fundsLoading && <span className="select-spinner" />}
        </div>
      </div>
      <p className="page-subtitle">
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
              value={fmtCompact((data.noi ?? 0) + Math.abs(data.budget_vs_actual ?? 0))}
              subtitle="-1.8% vs Budget"
              subtitleColor="yellow"
              sources="GL \u00B7 RECENCY"
            />
            <MetricCard
              title="EXPENSE RATIO"
              icon="%"
              value={`${((data.expenseRatio ?? 0) * 100).toFixed(1)}%`}
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
              value={`${(data.dscr ?? 0).toFixed(2)}x`}
              subtitle={(data.dscr ?? 0) >= 1.25 ? "Above 1.25x covenant" : "Below 1.25x covenant"}
              subtitleColor={(data.dscr ?? 0) >= 1.25 ? "green" : "red"}
              sources="GL + DEBT"
            />
            <MetricCard
              title="BUDGET VS ACTUAL"
              icon="&#9776;"
              value={fmtCompact(data.budgetVsActual_details?.variance ?? 0)}
              valueColor={(data.budgetVsActual_details?.variance ?? 0) < 0 ? "#ef5350" : undefined}
              subtitle={(data.budgetVsActual_details?.variance ?? 0) < 0 ? "NOI shortfall YTD" : "Favorable variance YTD"}
              subtitleColor={(data.budgetVsActual_details?.variance ?? 0) >= 0 ? "green" : "red"}
              sources="GL"
            />
            <MetricCard
              title="YTD RETURN"
              icon="&#8599;"
              value={`${(data.ytdReturn ?? 0).toFixed(1)}%`}
              subtitle="Levered \u00B7 Net"
              subtitleColor={(data.ytdReturn ?? 0) >= 0 ? "green" : "red"}
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
                <div className="table-responsive">
                  <Table
                    columns={assetsColumns}
                    dataSource={filteredProperties}
                    rowKey="id"
                    pagination={{ pageSize: 5, showSizeChanger: false, size: "small" }}
                    size="small"
                  />
                </div>
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

              {/* Asset Performance Ranking */}
              <div className="cc-assets-panel cc-ranking-panel">
                <h3>Asset Performance Ranking</h3>
                <div className="table-responsive">
                  <Table
                    columns={rankColumns}
                    dataSource={filteredProperties}
                    rowKey="id"
                    pagination={{ pageSize: 5, showSizeChanger: false, size: "small" }}
                    size="small"
                  />
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
