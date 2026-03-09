import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { Property } from "../types";

const PAGE_SIZE = 10;

export default function Properties() {
  const { currentOrg } = useAuth();
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);

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

  if (!currentOrg) return <p>No organization selected.</p>;
  if (loading) return <p>Loading...</p>;

  const totalPages = Math.ceil(properties.length / PAGE_SIZE);
  const paginated = properties.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="properties">
      <h2>Properties</h2>
      <p className="list-count">{properties.length} properties</p>
      <table>
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>City</th>
            <th>State</th>
            <th>Type</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {paginated.map((prop) => (
            <tr key={prop.id}>
              <td>{prop.propertyCode}</td>
              <td>{prop.propertyName}</td>
              <td>{prop.address?.city}</td>
              <td>{prop.address?.state}</td>
              <td className="capitalize">{prop.propertyType}</td>
              <td>
                <span className={`status-badge status-${prop.status}`}>
                  {prop.status}
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
