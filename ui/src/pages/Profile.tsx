import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <div className="profile">
      <h2>User Profile</h2>
      <div className="profile-card">
        <div className="profile-avatar">
          {user.name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2)}
        </div>
        <div className="profile-details">
          <div className="profile-field">
            <label>Name</label>
            <p>{user.name}</p>
          </div>
          <div className="profile-field">
            <label>Email</label>
            <p>{user.email}</p>
          </div>
          <div className="profile-field">
            <label>Organizations</label>
            <ul className="profile-orgs">
              {user.orgs.map((org) => (
                <li key={org.id}>
                  <span className="profile-org-name">{org.name}</span>
                  <span className="profile-org-status">{org.status}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
