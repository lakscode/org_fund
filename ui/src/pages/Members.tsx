import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { OrgData } from "../types";

const PAGE_SIZE = 10;

export default function Members() {
  const { currentOrg } = useAuth();
  const [orgData, setOrgData] = useState<OrgData | null>(null);
  const [page, setPage] = useState(0);

  useEffect(() => {
    if (currentOrg) {
      setPage(0);
      api.get(`/orgs/${currentOrg.id}`).then((res) => setOrgData(res.data));
    }
  }, [currentOrg]);

  if (!currentOrg) return <p>No organization selected.</p>;
  if (!orgData) return <p>Loading...</p>;

  const members = orgData.members;
  const totalPages = Math.ceil(members.length / PAGE_SIZE);
  const paginated = members.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="members">
      <h2>Members - {orgData.org.name}</h2>
      <p className="list-count">{members.length} members</p>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
          </tr>
        </thead>
        <tbody>
          {paginated.map((m) => (
            <tr key={m.id}>
              <td>{m.name}</td>
              <td>{m.email}</td>
            </tr>
          ))}
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
