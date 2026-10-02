import { useAuth } from "../../context/useAuth";

export function Sidebar({ currentRoute, onNavigate }) {
  const { user, upiProfile, logout } = useAuth();

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: "📊" },
    { id: "send-money", label: "Send Money", icon: "💸" },
    { id: "accounts", label: "Bank Accounts", icon: "🏦" },
    { id: "transactions", label: "Transactions", icon: "📜" },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-logo-badge">₹</div>
        <div className="brand-text">
          <h1>SecurePay</h1>
          <span>UPI Network</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`nav-item ${currentRoute === item.id ? "active" : ""}`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile-pill">
          <div className="user-avatar-circle">
            {user?.name ? user.name[0].toUpperCase() : "U"}
          </div>
          <div className="user-info-text">
            <div className="user-name-title">{user?.name || "SecurePay User"}</div>
            <div className="user-upi-handle">
              {upiProfile?.upi_id || user?.mobile_no || "User"}
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={logout}
          style={{
            background: "transparent",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: "var(--radius-md)",
            color: "#94a3b8",
            padding: "8px 12px",
            fontSize: "12px",
            fontWeight: 500,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "6px",
            transition: "all 0.2s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "#f87171";
            e.currentTarget.style.borderColor = "rgba(248, 113, 113, 0.3)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = "#94a3b8";
            e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.1)";
          }}
        >
          <span>🚪</span>
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
