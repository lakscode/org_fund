import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { Fund } from "../types";

interface BalanceSheetData {
  fundId: string;
  fundCode: string;
  fundName: string;
  propertyCount: number;
  aum: {
    investmentsLP: number;
    investmentsCorp: number;
    aggregateInvestmentValue: number;
  };
  eum: {
    aggregateInvestmentValue: number;
    totalMortgageDebt: number;
    equityUnderManagement: number;
  };
  noi: {
    revenue: number;
    operatingExpenses: number;
    netOperatingIncome: number;
  };
  expenseRatio: number;
  cash: number;
  dscr: {
    noi: number;
    totalDebtExpenses: number;
    debtServiceCoverageRatio: number;
  };
  budgetVsActual: {
    actual: number;
    budget: number;
    variance: number;
  };
  ytdReturn: {
    netIncome: number;
    totalEquity: number;
    returnPct: number;
  };
}

function fmt(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function pct(value: number): string {
  return `${value.toFixed(2)}%`;
}

export default function BalanceSheet() {
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
            setSelectedFundId(res.data[0].id);
          }
        })
        .catch(() => setFunds([]));
    }
  }, [currentOrg]);

  useEffect(() => {
    if (selectedFundId) {
      setLoading(true);
      setError("");
      api
        .get(`/funds/69a97849cad17ccef75cb4ab/balancesheet`)
        .then((res) => setData(res.data))
        .catch(() => {
          setData(null);
          setError("Failed to load balance sheet data.");
        })
        .finally(() => setLoading(false));
    }
  }, [selectedFundId]);

  if (!currentOrg) return <p>No organization selected.</p>;

  return (
    <div className="balance-sheet">
      <div className="bs-header">
        <h2>Balance Sheet</h2>
        <select
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

      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}

      {data && !loading && (
        <>
          <p className="bs-subtitle">
            {data.fundName} &middot; {data.propertyCount} properties
          </p>

          <div className="bs-grid">
            <div className="bs-card">
              <h3>Assets Under Management</h3>
              <div className="bs-value">{fmt(data.aum.aggregateInvestmentValue)}</div>
              <div className="bs-breakdown">
                <span>Investments LP: {fmt(data.aum.investmentsLP)}</span>
                <span>Investments Corp: {fmt(data.aum.investmentsCorp)}</span>
              </div>
            </div>

            <div className="bs-card">
              <h3>Equity Under Management</h3>
              <div className="bs-value">{fmt(data.eum.equityUnderManagement)}</div>
              <div className="bs-breakdown">
                <span>AUM: {fmt(data.eum.aggregateInvestmentValue)}</span>
                <span>Mortgage Debt: {fmt(data.eum.totalMortgageDebt)}</span>
              </div>
            </div>

            <div className="bs-card">
              <h3>Portfolio NOI</h3>
              <div className="bs-value">{fmt(data.noi.netOperatingIncome)}</div>
              <div className="bs-breakdown">
                <span>Revenue: {fmt(data.noi.revenue)}</span>
                <span>Op. Expenses: {fmt(data.noi.operatingExpenses)}</span>
              </div>
            </div>

            <div className="bs-card">
              <h3>Expense Ratio</h3>
              <div className="bs-value">{pct(data.expenseRatio * 100)}</div>
            </div>

            <div className="bs-card">
              <h3>Cash</h3>
              <div className="bs-value">{fmt(data.cash)}</div>
            </div>

            <div className="bs-card">
              <h3>Portfolio DSCR</h3>
              <div className="bs-value">{data.dscr.debtServiceCoverageRatio.toFixed(2)}x</div>
              <div className="bs-breakdown">
                <span>NOI: {fmt(data.dscr.noi)}</span>
                <span>Debt Expenses: {fmt(data.dscr.totalDebtExpenses)}</span>
              </div>
            </div>

            <div className="bs-card">
              <h3>Budget vs Actual</h3>
              <div className="bs-value">{fmt(data.budgetVsActual.variance)}</div>
              <div className="bs-breakdown">
                <span>Actual: {fmt(data.budgetVsActual.actual)}</span>
                <span>Budget: {fmt(data.budgetVsActual.budget)}</span>
              </div>
            </div>

            <div className="bs-card">
              <h3>YTD Return (Fund Level)</h3>
              <div className="bs-value">{pct(data.ytdReturn.returnPct)}</div>
              <div className="bs-breakdown">
                <span>Net Income: {fmt(data.ytdReturn.netIncome)}</span>
                <span>Total Equity: {fmt(data.ytdReturn.totalEquity)}</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
