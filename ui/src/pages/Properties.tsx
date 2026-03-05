import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { Property } from "../types";

export default function Properties() {
  const { currentOrg } = useAuth();
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);

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

  if (!currentOrg) return <p>No organization selected.</p>;
  if (loading) return <p>Loading...</p>;

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
          {properties.map((prop) => (
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
    </div>
  );
}
