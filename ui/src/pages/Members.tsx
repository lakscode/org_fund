import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import { Table } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { OrgData, OrgMember } from "../types";

export default function Members() {
  const { currentOrg } = useAuth();
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentOrg) {
      setLoading(true);
      api
        .get(`/orgs/${currentOrg.id}`)
        .then((res: { data: OrgData }) => setMembers(res.data.members))
        .catch(() => setMembers([]))
        .finally(() => setLoading(false));
    }
  }, [currentOrg]);

  if (!currentOrg) return <p>No organization selected.</p>;

  const columns: ColumnsType<OrgMember> = [
    { title: "Name", dataIndex: "name", key: "name" },
    { title: "Email", dataIndex: "email", key: "email" },
  ];

  return (
    <div className="members page-container">
      <h2 className="page-title">Members - {currentOrg.name}</h2>
      <p className="page-subtitle">{members.length} members</p>
      <div className="table-responsive">
        <Table
          columns={columns}
          dataSource={members}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, showSizeChanger: false }}
          size="small"
        />
      </div>
    </div>
  );
}
