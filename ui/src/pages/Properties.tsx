import { useEffect, useState, useMemo } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { Property } from "../types";

const PAGE_SIZE = 10;

function fmt(v?: number): string {
  if (v == null) return "$0";
  const sign = v < 0 ? "-" : "";
  return `${sign}$${Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

export default function Properties() {
  const { currentOrg } = useAuth();
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [marketFilter, setMarketFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  useEffect(() => {
    if (currentOrg) {
      setLoading(true);
      setPage(0);
      api
        .get(`/orgs/${currentOrg.id}/properties`)
        .then((res) => setProperties(res.data))
        .catch(() => setProperties([]))
        .finally(() => setLoading(false));
    }
  }, [currentOrg]);

  // Extract unique markets and types from data
  const markets = useMemo(() => {
    const set = new Set<string>();
    properties.forEach((p) => {
      const m = typeof p.market === "string" ? p.market : "";
      if (m) set.add(m);
    });
    return Array.from(set).sort();
  }, [properties]);

  const types = useMemo(() => {
    const set = new Set<string>();
    properties.forEach((p) => {
      if (p.propertyType) set.add(p.propertyType);
    });
    return Array.from(set).sort();
  }, [properties]);

  // Filter properties
  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return properties.filter((p) => {
      if (marketFilter && (typeof p.market === "string" ? p.market : "") !== marketFilter) return false;
      if (typeFilter && p.propertyType !== typeFilter) return false;
      if (q) {
        const name = (p.propertyName || "").toLowerCase();
        const code = (p.propertyCode || "").toLowerCase();
        const city = (p.address?.city || "").toLowerCase();
        const state = (p.address?.state || "").toLowerCase();
        if (!name.includes(q) && !code.includes(q) && !city.includes(q) && !state.includes(q)) return false;
      }
      return true;
    });
  }, [properties, search, marketFilter, typeFilter]);

  // Reset page when filters change
  useEffect(() => {
    setPage(0);
  }, [search, marketFilter, typeFilter]);

  if (!currentOrg) return <p>No organization selected.</p>;
  if (loading) return <p>Loading...</p>;

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="properties">
      <h2>Assets</h2>
      <p className="list-count">{filtered.length} properties</p>

      <div className="assets-filters">
        <div className="assets-search">
          <span className="assets-search-icon">&#128269;</span>
          <input
            type="text"
            placeholder="Search property name, city..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="assets-select"
          value={marketFilter}
          onChange={(e) => setMarketFilter(e.target.value)}
        >
          <option value="">All Markets</option>
          {markets.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
        <select
          className="assets-select"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All Types</option>
          {types.map((t) => (
            <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
          ))}
        </select>
      </div>

      <table className="assets-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Market</th>
            <th>Type</th>
            <th className="text-right">NOI YTD</th>
            <th className="text-right">NOI vs Budget</th>
            <th className="text-right">Occupancy</th>
            <th className="text-right">DSCR</th>
            <th>Rent Expiring</th>
            <th>Risk</th>
            <th>Month-End</th>
          </tr>
        </thead>
        <tbody>
          {paginated.map((prop) => {
            const budgetPct = prop.noiVsBudgetPct ?? 0;
            const occ = prop.occupancy ?? 0;
            return (
              <tr key={prop.id}>
                <td>
                  <div className="asset-name">{prop.propertyName}</div>
                 {/*  <div className="asset-code">{prop.propertyCode}</div> */}
                </td>
                <td>{typeof prop.market === "string" ? prop.market : ""}</td>
                <td className="capitalize">{prop.propertyType}</td>
                <td className="text-right">{fmt(prop.noiActual)}</td>
                <td className="text-right">
                  <span className={budgetPct >= 0 ? "text-green" : "text-red"}>
                    {budgetPct >= 0 ? "+" : ""}{budgetPct.toFixed(1)}%
                  </span>
                </td>
                <td className="text-right">{occ.toFixed(1)}%</td>
                <td className="text-right">{(prop.dscr ?? 0).toFixed(2)}x</td>
                <td>—</td>
                <td>
                  <span className={`risk-badge risk-${occ >= 80 ? "low" : occ >= 50 ? "medium" : "high"}`}>
                    {occ >= 80 ? "Low" : occ >= 50 ? "Medium" : "High"}
                  </span>
                </td>
                <td>
                  <span className={`status-badge status-${prop.status}`}>
                    {prop.status}
                  </span>
                </td>
              </tr>
            );
          })}
          {paginated.length === 0 && (
            <tr><td colSpan={10} style={{ textAlign: "center", padding: "2rem", color: "#888" }}>No properties match your filters.</td></tr>
          )}
        </tbody>
      </table>
      {totalPages > 1 && (
        <div className="cc-pagination">
          <button disabled={page === 0} onClick={() => setPage(page - 1)}>&laquo;</button>
          <span>{page + 1} / {totalPages}</span>
          <button disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>&raquo;</button>
        </div>
      )}
    </div>
  );
}
