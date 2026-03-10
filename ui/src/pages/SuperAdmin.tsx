import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { Org, SAUser } from "../types";

type Tab = "orgs" | "users";

const ROLES = ["admin", "portfolio_manager", "analyst", "member"];

export default function SuperAdmin() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("orgs");

  // --- Orgs ---
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [orgsLoading, setOrgsLoading] = useState(false);
  const [newOrgName, setNewOrgName] = useState("");
  const [orgMsg, setOrgMsg] = useState("");

  // --- Users ---
  const [users, setUsers] = useState<SAUser[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUser, setNewUser] = useState({ email: "", name: "", password: "changeme123" });
  const [newUserOrgs, setNewUserOrgs] = useState<{ org_id: string; role: string }[]>([]);
  const [userMsg, setUserMsg] = useState("");

  // --- Map user modal ---
  const [mapModal, setMapModal] = useState<SAUser | null>(null);
  const [mapOrgId, setMapOrgId] = useState("");
  const [mapRole, setMapRole] = useState("member");
  const [mapMsg, setMapMsg] = useState("");

  if (!user?.isSuperAdmin) {
    return <div className="sa-restricted">Super Admin access required.</div>;
  }

  const fetchOrgs = () => {
    setOrgsLoading(true);
    api.get("/sa/orgs").then((r) => setOrgs(r.data)).catch(() => {}).finally(() => setOrgsLoading(false));
  };

  const fetchUsers = () => {
    setUsersLoading(true);
    api.get("/sa/users").then((r) => setUsers(r.data)).catch(() => {}).finally(() => setUsersLoading(false));
  };

  useEffect(() => {
    fetchOrgs();
    fetchUsers();
  }, []);

  // --- Org actions ---
  const createOrg = async () => {
    if (!newOrgName.trim()) return;
    try {
      await api.post("/sa/orgs", { name: newOrgName.trim() });
      setNewOrgName("");
      setOrgMsg("Organization created");
      fetchOrgs();
    } catch (e: any) {
      setOrgMsg(e.response?.data?.detail || "Failed");
    }
  };

  const deleteOrg = async (id: string) => {
    if (!confirm("Delete this organization?")) return;
    try {
      await api.delete(`/sa/orgs/${id}`);
      setOrgMsg("Organization deleted");
      fetchOrgs();
    } catch (e: any) {
      setOrgMsg(e.response?.data?.detail || "Failed");
    }
  };

  // --- User actions ---
  const createUser = async () => {
    if (!newUser.email || !newUser.name) { setUserMsg("Email and name required"); return; }
    try {
      await api.post("/sa/users", { ...newUser, orgs: newUserOrgs });
      setNewUser({ email: "", name: "", password: "changeme123" });
      setNewUserOrgs([]);
      setShowCreateUser(false);
      setUserMsg("User created");
      fetchUsers();
    } catch (e: any) {
      setUserMsg(e.response?.data?.detail || "Failed");
    }
  };

  const addOrgToNewUser = () => {
    if (orgs.length === 0) return;
    setNewUserOrgs([...newUserOrgs, { org_id: orgs[0].id, role: "member" }]);
  };

  const removeOrgFromNewUser = (idx: number) => {
    setNewUserOrgs(newUserOrgs.filter((_, i) => i !== idx));
  };

  // --- Map user to org ---
  const openMapModal = (u: SAUser) => {
    setMapModal(u);
    setMapOrgId("");
    setMapRole("member");
    setMapMsg("");
  };

  const mapUser = async () => {
    if (!mapModal || !mapOrgId) return;
    try {
      await api.post("/sa/map-user", {
        userId: mapModal.id,
        orgs: [{ org_id: mapOrgId, role: mapRole }],
      });
      setMapMsg("User mapped successfully");
      fetchUsers();
    } catch (e: any) {
      setMapMsg(e.response?.data?.detail || "Failed");
    }
  };

  const unmapUser = async (userId: string, orgId: string) => {
    if (!confirm("Remove user from this organization?")) return;
    try {
      await api.post("/sa/unmap-user", { userId, orgId });
      setUserMsg("User removed from org");
      fetchUsers();
    } catch (e: any) {
      setUserMsg(e.response?.data?.detail || "Failed");
    }
  };

  const orgNameById = (id: string) => orgs.find((o) => o.id === id)?.name || id;

  // Available orgs for mapping (not already assigned)
  const availableOrgsForMap = mapModal
    ? orgs.filter((o) => !mapModal.org_roles.some((r) => r.org_id === o.id))
    : [];

  return (
    <div className="sa-page">
      <h2>Super Admin</h2>

      <div className="sa-tabs">
        <button className={`sa-tab ${tab === "orgs" ? "active" : ""}`} onClick={() => setTab("orgs")}>
          Organizations ({orgs.length})
        </button>
        <button className={`sa-tab ${tab === "users" ? "active" : ""}`} onClick={() => setTab("users")}>
          Users ({users.length})
        </button>
      </div>

      {/* ─── ORGS TAB ─── */}
      {tab === "orgs" && (
        <div className="sa-section">
          <div className="sa-create-row">
            <input
              className="sa-input"
              placeholder="New organization name"
              value={newOrgName}
              onChange={(e) => setNewOrgName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && createOrg()}
            />
            <button className="sa-btn sa-btn-primary" onClick={createOrg}>Create Org</button>
          </div>
          {orgMsg && <p className="sa-msg">{orgMsg}</p>}

          {orgsLoading ? (
            <p className="sa-loading">Loading organizations...</p>
          ) : (
            <table className="sa-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {orgs.map((o) => (
                  <tr key={o.id}>
                    <td>{o.name}</td>
                    <td><span className={`sa-badge sa-badge-${o.status}`}>{o.status}</span></td>
                    <td>{o.createdAt ? new Date(o.createdAt).toLocaleDateString() : ""}</td>
                    <td>
                      <button className="sa-btn sa-btn-danger sa-btn-sm" onClick={() => deleteOrg(o.id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ─── USERS TAB ─── */}
      {tab === "users" && (
        <div className="sa-section">
          <div className="sa-create-row">
            <button className="sa-btn sa-btn-primary" onClick={() => setShowCreateUser(!showCreateUser)}>
              {showCreateUser ? "Cancel" : "+ New User"}
            </button>
          </div>
          {userMsg && <p className="sa-msg">{userMsg}</p>}

          {showCreateUser && (
            <div className="sa-create-form">
              <h4>Create New User</h4>
              <div className="sa-form-grid">
                <input className="sa-input" placeholder="Email" value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} />
                <input className="sa-input" placeholder="Name" value={newUser.name}
                  onChange={(e) => setNewUser({ ...newUser, name: e.target.value })} />
                <input className="sa-input" placeholder="Password" value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} />
              </div>

              <div className="sa-org-mappings">
                <h5>Org Mappings</h5>
                {newUserOrgs.map((m, i) => (
                  <div key={i} className="sa-map-row">
                    <select className="app-select" value={m.org_id}
                      onChange={(e) => {
                        const updated = [...newUserOrgs];
                        updated[i].org_id = e.target.value;
                        setNewUserOrgs(updated);
                      }}>
                      {orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
                    </select>
                    <select className="app-select" value={m.role}
                      onChange={(e) => {
                        const updated = [...newUserOrgs];
                        updated[i].role = e.target.value;
                        setNewUserOrgs(updated);
                      }}>
                      {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                    </select>
                    <button className="sa-btn sa-btn-danger sa-btn-sm" onClick={() => removeOrgFromNewUser(i)}>&times;</button>
                  </div>
                ))}
                <button className="sa-btn sa-btn-secondary sa-btn-sm" onClick={addOrgToNewUser}>+ Add Org</button>
              </div>

              <button className="sa-btn sa-btn-primary" onClick={createUser}>Create User</button>
            </div>
          )}

          {usersLoading ? (
            <p className="sa-loading">Loading users...</p>
          ) : (
            <table className="sa-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Organizations</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>
                      {u.name}
                      {u.isSuperAdmin && <span className="sa-badge sa-badge-super">SA</span>}
                    </td>
                    <td>{u.email}</td>
                    <td>
                      <div className="sa-user-orgs">
                        {u.org_roles.map((r) => (
                          <span key={r.org_id} className="sa-org-chip">
                            {orgNameById(r.org_id)} <em>({r.role})</em>
                            <button className="sa-chip-remove" title="Remove from org"
                              onClick={() => unmapUser(u.id, r.org_id)}>&times;</button>
                          </span>
                        ))}
                        {u.org_roles.length === 0 && <em className="sa-muted">No orgs</em>}
                      </div>
                    </td>
                    <td>
                      <button className="sa-btn sa-btn-secondary sa-btn-sm" onClick={() => openMapModal(u)}>
                        + Map Org
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ─── MAP USER MODAL ─── */}
      {mapModal && (
        <div className="sa-modal-overlay" onClick={() => setMapModal(null)}>
          <div className="sa-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Map User to Organization</h3>
            <p className="sa-modal-sub">{mapModal.name} ({mapModal.email})</p>

            {availableOrgsForMap.length === 0 ? (
              <p className="sa-muted">User is already in all organizations.</p>
            ) : (
              <>
                <div className="sa-form-grid">
                  <select className="app-select" value={mapOrgId}
                    onChange={(e) => setMapOrgId(e.target.value)}>
                    <option value="">Select organization</option>
                    {availableOrgsForMap.map((o) => (
                      <option key={o.id} value={o.id}>{o.name}</option>
                    ))}
                  </select>
                  <select className="app-select" value={mapRole}
                    onChange={(e) => setMapRole(e.target.value)}>
                    {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
                <button className="sa-btn sa-btn-primary" onClick={mapUser} disabled={!mapOrgId}>
                  Map User
                </button>
              </>
            )}
            {mapMsg && <p className="sa-msg">{mapMsg}</p>}
            <button className="sa-btn sa-btn-secondary" onClick={() => setMapModal(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
