import { useAuth } from "../../context/useAuth";
import { Button } from "../common/Button";

export function Navbar({ title, onNavigate, onSignOut }) {
  const { upiProfile, logout } = useAuth();
  const handleSignOut = onSignOut || logout;

  return (
    <header className="topbar">
      <div className="topbar-title">
        <span>{title}</span>
      </div>

      <div className="topbar-actions">
        {upiProfile?.exists ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              background: "var(--color-primary-light)",
              padding: "6px 12px",
              borderRadius: "var(--radius-full)",
              fontSize: "12px",
              color: "var(--color-primary-dark)",
              fontWeight: 600,
            }}
          >
            <span>⚡</span>
            <span>{upiProfile.upi_id}</span>
          </div>
        ) : (
          <button
            onClick={() => onNavigate("dashboard")}
            style={{
              background: "#fffbeb",
              border: "1px solid #fde68a",
              color: "#b45309",
              padding: "4px 10px",
              borderRadius: "var(--radius-full)",
              fontSize: "11px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            ⚠️ Setup UPI ID
          </button>
        )}

        <Button
          variant="secondary"
          size="sm"
          onClick={handleSignOut}
          title="Sign out of SecurePay"
        >
          Sign Out
        </Button>
      </div>
    </header>
  );
}
