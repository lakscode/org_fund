import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";
import { Table, Tag, Button, Space } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { OrgMember } from "../types";

type ModalMode = "add" | "edit" | "resetpw" | null;

export default function Profile() {
  const { user, currentOrg } = useAuth();
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [loading, setLoading] = useState(true);
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
        .then((res) => setMembers(res.data.members))
        .catch(() => setMembers([]))
        .finally(() => setLoading(false));
    }
  };

  useEffect(fetchMembers, [currentOrg]);

  if (!user) return null;

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

  const columns: ColumnsType<OrgMember> = [
    { title: "Name", dataIndex: "name", key: "name", render: (v: string) => <strong>{v}</strong> },
    { title: "Email", dataIndex: "email", key: "email" },
    { title: "Company", key: "company", render: () => currentOrg?.name },
    {
      title: "Roles",
      dataIndex: "role",
      key: "role",
      render: (role: string) => <Tag>{role}</Tag>,
    },
    {
      title: "Created",
      dataIndex: "createdAt",
      key: "createdAt",
      render: (v: string) => formatDate(v),
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: OrgMember) => (
        <Space>
          <Button type="link" size="small" onClick={() => openEdit(record)} title="Edit">
            &#9998;
          </Button>
          <Button type="link" size="small" onClick={() => openResetPw(record)} title="Reset Password">
            &#128274;
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="settings page-container">
      <div className="settings-section">
        <div className="settings-section-header">
          <h2 className="page-title">Users</h2>
          <button className="btn-primary" onClick={openAdd}>
            + Add User
          </button>
        </div>

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
