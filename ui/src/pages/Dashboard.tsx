import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { OrgData } from "../types";

export default function Dashboard() {
  const { currentOrg } = useAuth();
  const [orgData, setOrgData] = useState<OrgData | null>(null);

  useEffect(() => {
    if (currentOrg) {
      api.get(`/orgs/${currentOrg.id}`).then((res) => setOrgData(res.data));
    }
  }, [currentOrg]);

  if (!currentOrg) return <p>No organization selected.</p>;
  if (!orgData) return <p>Loading...</p>;

  return (
    <div className="dashboard">
      <h2>{orgData.org.name}</h2>
      <p className="org-status">Status: {orgData.org.status}</p>
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Members</h3>
          <p className="stat-value">{orgData.members.length}</p>
        </div>
        <div className="stat-card">
          <h3>Organization</h3>
          <p className="stat-value">{orgData.org.name}</p>
        </div>
      </div>
    </div>
  );
}
