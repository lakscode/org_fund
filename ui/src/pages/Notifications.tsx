import { useState } from "react";
import { useAuth } from "../context/AuthContext";

interface Notification {
  id: string;
  type: "info" | "warning" | "success" | "error";
  title: string;
  message: string;
  date: string;
  read: boolean;
}

const DUMMY_NOTIFICATIONS: Notification[] = [
  {
    id: "1",
    type: "success",
    title: "Fund Import Complete",
    message: "Successfully imported 24 funds from table_fund_data.csv.",
    date: "2026-03-10T09:15:00Z",
    read: false,
  },
  {
    id: "2",
    type: "info",
    title: "New Member Added",
    message: "John Smith was added to Koncord Capital as an Analyst.",
    date: "2026-03-09T16:42:00Z",
    read: false,
  },
  {
    id: "3",
    type: "warning",
    title: "Balance Sheet Review",
    message: "Q4 2025 balance sheet for Fund LAKE-01 has variances exceeding 5%.",
    date: "2026-03-09T11:30:00Z",
    read: false,
  },
  {
    id: "4",
    type: "error",
    title: "Import Failed",
    message: "Property CSV import failed — missing required column SADDR1.",
    date: "2026-03-08T14:20:00Z",
    read: true,
  },
  {
    id: "5",
    type: "info",
    title: "System Maintenance",
    message: "Scheduled maintenance window on March 15, 2026 from 2:00 AM to 4:00 AM EST.",
    date: "2026-03-08T09:00:00Z",
    read: true,
  },
  {
    id: "6",
    type: "success",
    title: "Property Valuation Updated",
    message: "Market valuations refreshed for 12 properties in the NE region.",
    date: "2026-03-07T17:45:00Z",
    read: true,
  },
  {
    id: "7",
    type: "info",
    title: "Quarterly Report Ready",
    message: "Q4 2025 quarterly report is now available for download.",
    date: "2026-03-07T10:00:00Z",
    read: true,
  },
  {
    id: "8",
    type: "warning",
    title: "Expiring Lease",
    message: "Lease for tenant Apex Corp at 200 Main St expires in 30 days.",
    date: "2026-03-06T13:10:00Z",
    read: true,
  },
];

const TYPE_ICONS: Record<string, string> = {
  info: "\u2139",
  warning: "\u26A0",
  success: "\u2714",
  error: "\u2718",
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function Notifications() {
  const { currentOrg } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>(DUMMY_NOTIFICATIONS);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  if (!currentOrg) return <p>No organization selected.</p>;

  const filtered = filter === "unread" ? notifications.filter((n) => !n.read) : notifications;
  const unreadCount = notifications.filter((n) => !n.read).length;

  const toggleRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: !n.read } : n))
    );
  };

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const dismiss = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <div className="notifications-page">
      <div className="notifications-header">
        <h2>Notifications</h2>
        <div className="notifications-actions">
          <div className="notifications-filter">
            <button
              className={`notif-filter-btn ${filter === "all" ? "active" : ""}`}
              onClick={() => setFilter("all")}
            >
              All ({notifications.length})
            </button>
            <button
              className={`notif-filter-btn ${filter === "unread" ? "active" : ""}`}
              onClick={() => setFilter("unread")}
            >
              Unread ({unreadCount})
            </button>
          </div>
          {unreadCount > 0 && (
            <button className="notif-mark-all" onClick={markAllRead}>
              Mark all as read
            </button>
          )}
        </div>
      </div>

      <div className="notifications-list">
        {filtered.length === 0 ? (
          <div className="notif-empty">
            <span className="notif-empty-icon">&#128276;</span>
            <p>No {filter === "unread" ? "unread " : ""}notifications</p>
          </div>
        ) : (
          filtered.map((n) => (
            <div
              key={n.id}
              className={`notif-card ${n.read ? "read" : "unread"} notif-${n.type}`}
            >
              <div className="notif-icon">{TYPE_ICONS[n.type]}</div>
              <div className="notif-body">
                <div className="notif-title-row">
                  <span className="notif-title">{n.title}</span>
                  <span className="notif-time">{timeAgo(n.date)}</span>
                </div>
                <p className="notif-message">{n.message}</p>
              </div>
              <div className="notif-card-actions">
                <button
                  className="notif-btn-read"
                  title={n.read ? "Mark unread" : "Mark read"}
                  onClick={() => toggleRead(n.id)}
                >
                  {n.read ? "\u25CB" : "\u25CF"}
                </button>
                <button
                  className="notif-btn-dismiss"
                  title="Dismiss"
                  onClick={() => dismiss(n.id)}
                >
                  &times;
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
