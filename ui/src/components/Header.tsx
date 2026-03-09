import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrator",
  portfolio_manager: "Portfolio Manager",
  analyst: "Analyst",
  member: "Member",
};

export default function Header() {
  const { user, currentOrg, logout, setCurrentOrg } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!user) return null;

  const initials = user.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <header className="header">
      <div className="header-left">
        <div className="select-wrapper">
          <select
            className="header-org-select app-select"
            value={currentOrg?.id ?? ""}
            onChange={(e) => {
              const org = user.orgs.find((o) => o.id === e.target.value);
              if (org) setCurrentOrg(org);
            }}
          >
            {user && user.orgs && user.orgs.length === 0 ? (
              <option>No organizations</option>
            ) : (
              user.orgs.map((org) => (
                <option key={org.id} value={org.id}>
                  {org.name}
                </option>
              ))
            )}
          </select>
        </div>
      </div>
      <div className="header-right">
        <button className="header-icon-btn" title="Notifications">
          &#128276;
        </button>
        <button className="header-icon-btn" title="Settings">
          &#9776;
        </button>
        <div className="header-user-info">
          <span className="header-user-name">{user.name}</span>
          <span className="header-user-role">{currentOrg?.role ? (ROLE_LABELS[currentOrg.role] || currentOrg.role) : ""}</span>
        </div>
        <div className="avatar-wrapper" ref={menuRef}>
          <button
            className="avatar"
            onClick={() => setMenuOpen(!menuOpen)}
            title={user.name}
          >
            {initials}
          </button>
          {menuOpen && (
            <div className="avatar-menu">
              <div className="avatar-menu-header">
                <span className="avatar-menu-name">{user.name}</span>
                <span className="avatar-menu-email">{user.email}</span>
              </div>
              <div className="avatar-menu-divider" />
              <button
                className="avatar-menu-item"
                onClick={() => {
                  setMenuOpen(false);
                  navigate("/profile");
                }}
              >
                Profile
              </button>
              <button
                className="avatar-menu-item avatar-menu-logout"
                onClick={() => {
                  setMenuOpen(false);
                  logout();
                }}
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
