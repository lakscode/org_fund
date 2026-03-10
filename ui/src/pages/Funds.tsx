import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import { Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { Fund, Property } from "../types";

interface FundProperties {
  [fundId: string]: { data: Property[]; loading: boolean };
}

export default function Funds() {
  const { currentOrg } = useAuth();
  const [funds, setFunds] = useState<Fund[]>([]);
  const [loading, setLoading] = useState(true);
  const [fundProps, setFundProps] = useState<FundProperties>({});

  useEffect(() => {
    if (currentOrg) {
      setLoading(true);
      api
        .get(`/orgs/${currentOrg.id}/funds`)
        .then((res) => setFunds(res.data))
        .catch(() => setFunds([]))
        .finally(() => setLoading(false));
    }
  }, [currentOrg]);

  const fetchFundProperties = (fundId: string) => {
    if (fundProps[fundId]) return;
    setFundProps((prev) => ({ ...prev, [fundId]: { data: [], loading: true } }));
    api
      .get(`/funds/${fundId}/properties`)
      .then((res) =>
        setFundProps((prev) => ({ ...prev, [fundId]: { data: res.data, loading: false } }))
      )
      .catch(() =>
        setFundProps((prev) => ({ ...prev, [fundId]: { data: [], loading: false } }))
      );
  };

  if (!currentOrg) return <p>No organization selected.</p>;

  const fmtCompact = (value: number): string => {
    const abs = Math.abs(value);
    const sign = value < 0 ? "-" : "";
    if (abs >= 1_000_000_000) return `${sign}$${(abs / 1_000_000_000).toFixed(1)}B`;
    if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
    if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(0)}K`;
    return `${sign}$${abs.toFixed(0)}`;
  };

  const columns: ColumnsType<Fund> = [
    { title: "Name", dataIndex: "fundName", key: "fundName" },
    {
      title: "AUM",
      dataIndex: "aum",
      key: "aum",
      render: (v: number) => fmtCompact(v || 0),
    },
    {
      title: "EUM",
      dataIndex: "eum",
      key: "eum",
      render: (v: number) => fmtCompact(v || 0),
    },
    {
      title: "Cash",
      dataIndex: "cash",
      key: "cash",
      render: (v: number) => fmtCompact(v || 0),
    },
    {
      title: "Properties",
      dataIndex: "propertyCount",
      key: "propertyCount",
      render: (v: number) => v ?? 0,
    },
    {
      title: "YTD Return",
      dataIndex: "ytdReturn",
      key: "ytdReturn",
      render: (v: number) => {
        const val = v || 0;
        return (
          <span style={{ color: val >= 0 ? "#4caf50" : "#ef5350" }}>
            {val.toFixed(1)}%
          </span>
        );
      },
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      render: (status: string) => (
        <Tag color={status === "active" ? "green" : status === "closed" ? "red" : "default"}>
          {status}
        </Tag>
      ),
    },
  ];

  const propColumns: ColumnsType<Property> = [
    { title: "Code", dataIndex: "propertyCode", key: "propertyCode" },
    { title: "Name", dataIndex: "propertyName", key: "propertyName" },
    { title: "Market", dataIndex: "market", key: "market", render: (v: string) => v || "—" },
    { title: "Type", dataIndex: "propertyType", key: "propertyType", render: (v: string) => v || "—" },
    {
      title: "Status",
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
    <div className="funds">
      <h2>Funds</h2>
      <p className="list-count">{funds.length} funds</p>
      <Table
        columns={columns}
        dataSource={funds}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10, showSizeChanger: false }}
        size="small"
        expandable={{
          expandedRowRender: (record) => {
            const fp = fundProps[record.id];
            if (!fp || fp.loading) return <p>Loading properties...</p>;
            if (fp.data.length === 0) return <p className="sa-muted">No properties linked to this fund.</p>;
            return (
              <Table
                columns={propColumns}
                dataSource={fp.data}
                rowKey="id"
                pagination={false}
                size="small"
              />
            );
          },
          onExpand: (expanded, record) => {
            if (expanded) fetchFundProperties(record.id);
          },
        }}
      />
    </div>
  );
}
