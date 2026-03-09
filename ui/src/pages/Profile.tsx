import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import type { OrgMember } from "../types";

const PAGE_SIZE = 10;

type ModalMode = "add" | "edit" | "resetpw" | null;

export default function Profile() {
  const { user, currentOrg } = useAuth();
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [modal, setModal] = useState<ModalMode>(null);
  const [editTarget, setEditTarget] = useState<OrgMember | null>(null);
  const [form, setForm] = useState({ name: "", email: "", role: "member" });
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const fetchMembers = () => {
    if (currentOrg) {
      setLoading(true);
      api
        .get(`/orgs/${currentOrg.id}`)
        .then((res) => {
          setMembers(res.data.members);
          setPage(0);
        })
        .catch(() => setMembers([]))
        .finally(() => setLoading(false));
    }
  };

  useEffect(fetchMembers, [currentOrg]);

  if (!user) return null;

  const totalPages = Math.ceil(members.length / PAGE_SIZE);
  const paginated = members.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const openAdd = () => {
    setForm({ name: "", email: "", role: "member" });
    setError("");
    setModal("add");
  };

  const openEdit = (m: OrgMember) => {
    setEditTarget(m);
    setForm({ name: m.name, email: m.email, role: m.role });
    setError("");
    setModal("edit");
  };

  const openResetPw = (m: OrgMember) => {
    setEditTarget(m);
    setPassword("");
    setError("");
    setModal("resetpw");
  };

  const closeModal = () => {
    setModal(null);
    setEditTarget(null);
    setError("");
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.post(`/orgs/${currentOrg!.id}/members`, form);
      closeModal();
      fetchMembers();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to add user");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.put(`/orgs/${currentOrg!.id}/members/${editTarget!.id}`, form);
      closeModal();
      fetchMembers();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to update user");
    } finally {
      setSaving(false);
    }
  };

  const handleResetPw = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.post(`/orgs/${currentOrg!.id}/members/${editTarget!.id}/reset-password`, { password });
      closeModal();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to reset password");
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (iso: string) => {
    if (!iso) return "-";
    return new Date(iso).toLocaleDateString("en-US");
  };

  return (
    <div className="settings">
      <div className="settings-section">
        <div className="settings-section-header">
          <h2>Users</h2>
          <button className="btn-primary" onClick={openAdd}>
            + Add User
          </button>
        </div>

        {loading ? (
          <p>Loading...</p>
        ) : (
          <>
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Company</th>
                  <th>Roles</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginated.map((m) => (
                  <tr key={m.id}>
                    <td className="td-bold">{m.name}</td>
                    <td>{m.email}</td>
                    <td>{currentOrg?.name}</td>
                    <td>
                      <span className="role-badge">{m.role}</span>
                    </td>
                    <td>{formatDate(m.createdAt)}</td>
                    <td className="actions-cell">
                      <button className="action-btn" title="Edit" onClick={() => openEdit(m)}>
                        &#9998;
                      </button>
                      <button className="action-btn" title="Reset Password" onClick={() => openResetPw(m)}>
                        &#128274;
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {totalPages > 1 && (
              <div className="cc-pagination">
                <button disabled={page === 0} onClick={() => setPage(page - 1)}>
                  &laquo;
                </button>
                <span>
                  {page + 1} / {totalPages}
                </span>
                <button disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>
                  &raquo;
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Add User Modal */}
      {modal === "add" && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Add User</h3>
            <form onSubmit={handleAdd}>
              {error && <p className="error">{error}</p>}
              <label>Name</label>
              <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              <label>Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              <label>Role</label>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                <option value="admin">Admin</option>
                <option value="portfolio_manager">Portfolio Manager</option>
                <option value="analyst">Analyst</option>
                <option value="member">Member</option>
              </select>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={closeModal}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Adding..." : "Add User"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {modal === "edit" && editTarget && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Edit User</h3>
            <form onSubmit={handleEdit}>
              {error && <p className="error">{error}</p>}
              <label>Name</label>
              <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              <label>Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              <label>Role</label>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                <option value="admin">Admin</option>
                <option value="portfolio_manager">Portfolio Manager</option>
                <option value="analyst">Analyst</option>
                <option value="member">Member</option>
              </select>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={closeModal}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving..." : "Save"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reset Password Modal */}
      {modal === "resetpw" && editTarget && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Reset Password</h3>
            <p className="modal-subtitle">Reset password for {editTarget.name} ({editTarget.email})</p>
            <form onSubmit={handleResetPw}>
              {error && <p className="error">{error}</p>}
              <label>New Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required />
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={closeModal}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Resetting..." : "Reset Password"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
