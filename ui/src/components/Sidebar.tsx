import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Sidebar() {
  const { currentOrg } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span className="sidebar-logo-icon">=</span>
        <span className="sidebar-logo-text">REstackAI</span>
      </div>

      <div className="sidebar-fund-info">
        <div className="sidebar-fund-label">FUND ADMINISTRATOR</div>
        <div className="sidebar-fund-aum">
          {currentOrg ? currentOrg.name : "No org selected"}
        </div>
        <div className="sidebar-fund-access">READ-ONLY ACCESS</div>
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
