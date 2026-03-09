import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrator",
  portfolio_manager: "Portfolio Manager",
  analyst: "Analyst",
  member: "Member",
};

function formatRole(role: string): string {
  return ROLE_LABELS[role] || role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function Sidebar() {
  const {currentOrg } = useAuth();
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <img src="/images/logo.png" alt="Logo" className="sidebar-logo-img" /> REstackAI
      </div>

      <div className="sidebar-fund-info">
        <div className="sidebar-fund-label">FUND ADMINISTRATOR</div>
        <div className="sidebar-fund-aum">
          {currentOrg ? currentOrg.name : "No org selected"}
        </div>
        {currentOrg?.role && (
          <div className="sidebar-fund-access">{formatRole(currentOrg.role)}</div>
        )}
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/command-center">
          <span className="sidebar-icon">&#9632;</span>
          Command Center
        </NavLink>
        <NavLink to="/funds">
          <span className="sidebar-icon">&#9960;</span>
          Funds
        </NavLink>
        <NavLink to="/properties">
          <span className="sidebar-icon">&#9827;</span>
          Assets
        </NavLink>
        <NavLink to="/balance-sheet">
          <span className="sidebar-icon">&#9633;</span>
          Balance Sheet
        </NavLink>
        <NavLink to="/members">
          <span className="sidebar-icon">&#9679;</span>
          Members
        </NavLink>
        <NavLink to="/chat">
          <span className="sidebar-icon">&#9993;</span>
          REstackAI Chat
        </NavLink>
      </nav>

      <div className="sidebar-bottom">
        <div className="sidebar-admin-label">ADMIN</div>
        <NavLink to="/profile">
          <span className="sidebar-icon">&#9881;</span>
          Settings
        </NavLink>
      </div>
    </aside>
  );
}
