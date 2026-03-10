import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import { Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { Fund } from "../types";

export default function Funds() {
  const { currentOrg } = useAuth();
  const [funds, setFunds] = useState<Fund[]>([]);
  const [loading, setLoading] = useState(true);

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

  if (!currentOrg) return <p>No organization selected.</p>;

  const columns: ColumnsType<Fund> = [
    { title: "Code", dataIndex: "fundCode", key: "fundCode" },
    { title: "Name", dataIndex: "fundName", key: "fundName" },
    {
      title: "Type",
      dataIndex: "fundType",
      key: "fundType",
      render: (v: string) => <span className="capitalize">{v}</span>,
    },
    { title: "Currency", dataIndex: "baseCurrency", key: "baseCurrency" },
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
      />
    </div>
  );
}
