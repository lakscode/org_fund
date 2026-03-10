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
    <div className="dashboard page-container">
      <h2 className="page-title">{orgData.org?.name ?? "—"}</h2>
      <p className="page-subtitle">Status: {orgData.org?.status ?? "—"}</p>
      <div className="row g-3">
        <div className="col-12 col-sm-6 col-lg-3">
          <div className="stat-card h-100">
            <h3>Members</h3>
            <p className="stat-value">{orgData.members?.length ?? 0}</p>
          </div>
        </div>
        <div className="col-12 col-sm-6 col-lg-3">
          <div className="stat-card h-100">
            <h3>Organization</h3>
            <p className="stat-value">{orgData.org?.name ?? "—"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
