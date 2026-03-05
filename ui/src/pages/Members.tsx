import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { OrgData } from "../types";

export default function Members() {
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
    <div className="members">
      <h2>Members - {orgData.org.name}</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
          </tr>
        </thead>
        <tbody>
          {orgData.members.map((m) => (
            <tr key={m.id}>
              <td>{m.name}</td>
              <td>{m.email}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
