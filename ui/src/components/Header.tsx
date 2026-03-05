import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

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
        <h1>Org Fund</h1>
      </div>
      <div className="header-right">
        <select
          value={currentOrg?.id ?? ""}
          onChange={(e) => {
            const org = user.orgs.find((o) => o.id === e.target.value);
            if (org) setCurrentOrg(org);
          }}
        >
          {user && user.orgs && user.orgs.map((org) => (
            <option key={org.id} value={org.id}>
              {org.name}
            </option>
          ))}
        </select>
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
