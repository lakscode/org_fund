import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { Fund } from "../types";

const PAGE_SIZE = 10;

export default function Funds() {
  const { currentOrg } = useAuth();
  const [funds, setFunds] = useState<Fund[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);

  useEffect(() => {
    if (currentOrg) {
      setLoading(true);
      setPage(0);
      api
        .get(`/orgs/${currentOrg.id}/funds`)
        .then((res) => setFunds(res.data))
        .catch(() => setFunds([]))
        .finally(() => setLoading(false));
    }
  }, [currentOrg]);

  if (!currentOrg) return <p>No organization selected.</p>;
  if (loading) return <p>Loading...</p>;

  const totalPages = Math.ceil(funds.length / PAGE_SIZE);
  const paginated = funds.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="funds">
      <h2>Funds</h2>
      <p className="list-count">{funds.length} funds</p>
      <table>
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Type</th>
            <th>Currency</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {paginated.map((fund) => (
            <tr key={fund.id}>
              <td>{fund.fundCode}</td>
              <td>{fund.fundName}</td>
              <td className="capitalize">{fund.fundType}</td>
              <td>{fund.baseCurrency}</td>
              <td>
                <span className={`status-badge status-${fund.status}`}>
                  {fund.status}
                </span>
              </td>
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
