import { NavLink } from "react-router-dom";

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <nav>
        <NavLink to="/" end>
          Dashboard
        </NavLink>
        <NavLink to="/funds">Funds</NavLink>
        <NavLink to="/properties">Properties</NavLink>
        <NavLink to="/command-center">Command Center</NavLink>
        <NavLink to="/balance-sheet">Balance Sheet</NavLink>
        <NavLink to="/members">Members</NavLink>
      </nav>
    </aside>
  );
}
