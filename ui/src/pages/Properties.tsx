import { useEffect, useState, useMemo } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import { Table, Input, Select, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { Property } from "../types";

const { Search } = Input;

function fmt(v?: number): string {
  if (v == null) return "$0";
  const sign = v < 0 ? "-" : "";
  return `${sign}$${Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

export default function Properties() {
  const { currentOrg } = useAuth();
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [marketFilter, setMarketFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  useEffect(() => {
    if (currentOrg) {
      setLoading(true);
      api
        .get(`/orgs/${currentOrg.id}/properties`)
        .then((res) => setProperties(res.data))
        .catch(() => setProperties([]))
        .finally(() => setLoading(false));
    }
  }, [currentOrg]);

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

  if (!currentOrg) return <p>No organization selected.</p>;

  const columns: ColumnsType<Property> = [
    {
      title: "Name",
      dataIndex: "propertyName",
      key: "propertyName",
      render: (name: string) => <span className="asset-name">{name}</span>,
    },
    {
      title: "Market",
      dataIndex: "market",
      key: "market",
      render: (v: unknown) => (typeof v === "string" ? v : ""),
    },
    {
      title: "Type",
      dataIndex: "propertyType",
      key: "propertyType",
      render: (v: string) => <span className="capitalize">{v}</span>,
    },
    {
      title: "NOI YTD",
      dataIndex: "noiActual",
      key: "noiActual",
      align: "right",
      render: (v: number) => fmt(v),
    },
    {
      title: "NOI vs Budget",
      dataIndex: "noiVsBudgetPct",
      key: "noiVsBudgetPct",
      align: "right",
      render: (v: number) => {
        const pct = v ?? 0;
        return (
          <span style={{ color: pct >= 0 ? "#4caf50" : "#ef5350" }}>
            {pct >= 0 ? "+" : ""}{pct.toFixed(1)}%
          </span>
        );
      },
    },
    {
      title: "Occupancy",
      dataIndex: "occupancy",
      key: "occupancy",
      align: "right",
      render: (v: number) => `${(v ?? 0).toFixed(1)}%`,
    },
    {
      title: "DSCR",
      dataIndex: "dscr",
      key: "dscr",
      align: "right",
      render: (v: number) => `${(v ?? 0).toFixed(2)}x`,
    },
    {
      title: "Rent Expiring",
      key: "rentExpiring",
      render: () => "—",
    },
    {
      title: "Risk",
      key: "risk",
      render: (_: unknown, record: Property) => {
        const occ = record.occupancy ?? 0;
        const level = occ >= 80 ? "Low" : occ >= 50 ? "Medium" : "High";
        const color = occ >= 80 ? "green" : occ >= 50 ? "orange" : "red";
        return <Tag color={color}>{level}</Tag>;
      },
    },
    {
      title: "Month-End",
      dataIndex: "status",
      key: "status",
      render: (status: string) => (
        <Tag color={status === "active" ? "green" : status === "closed" ? "red" : "default"}>
          {status}
        </Tag>
      ),
    },
  ];

  return (
    <div className="properties">
      <h2>Assets</h2>
      <p className="list-count">{filtered.length} properties</p>

      <div className="assets-filters">
        <Search
          placeholder="Search property name, city..."
          allowClear
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 280 }}
        />
        <Select
          value={marketFilter || undefined}
          placeholder="All Markets"
          allowClear
          onChange={(v) => setMarketFilter(v || "")}
          style={{ width: 180 }}
          options={markets.map((m) => ({ label: m, value: m }))}
        />
        <Select
          value={typeFilter || undefined}
          placeholder="All Types"
          allowClear
          onChange={(v) => setTypeFilter(v || "")}
          style={{ width: 180 }}
          options={types.map((t) => ({ label: t.charAt(0).toUpperCase() + t.slice(1), value: t }))}
        />
      </div>

      <Table
        columns={columns}
        dataSource={filtered}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10, showSizeChanger: false }}
        size="small"
      />
    </div>
  );
}
