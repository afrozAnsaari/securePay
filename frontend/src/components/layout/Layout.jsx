import { useState } from "react";
import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";
import { MobileNav } from "./MobileNav";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import { useAuth } from "../../context/useAuth";

export function Layout({ currentRoute, onNavigate, title, children }) {
  const [showSignOutConfirm, setShowSignOutConfirm] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);
  const { logout } = useAuth();

  const handleConfirmSignOut = async () => {
    try {
      setIsSigningOut(true);
      await logout();
    } finally {
      setIsSigningOut(false);
      setShowSignOutConfirm(false);
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        currentRoute={currentRoute}
        onNavigate={onNavigate}
        onSignOut={() => setShowSignOutConfirm(true)}
      />
      <div className="main-wrapper">
        <Navbar
          title={title}
          onNavigate={onNavigate}
          onSignOut={() => setShowSignOutConfirm(true)}
        />
        <main className="page-content">{children}</main>
        <MobileNav currentRoute={currentRoute} onNavigate={onNavigate} />
      </div>

      <Modal
        isOpen={showSignOutConfirm}
        onClose={isSigningOut ? undefined : () => setShowSignOutConfirm(false)}
        title="Confirm Sign Out"
        maxWidth="400px"
        footer={
          <div
            style={{
              display: "flex",
              gap: "10px",
              justifyContent: "flex-end",
              width: "100%",
            }}
          >
            <Button
              variant="secondary"
              onClick={() => setShowSignOutConfirm(false)}
              disabled={isSigningOut}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleConfirmSignOut}
              loading={isSigningOut}
            >
              Yes, Sign Out
            </Button>
          </div>
        }
      >
        <div style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
          <div
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "50%",
              backgroundColor: "#fee2e2",
              color: "#dc2626",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "22px",
              flexShrink: 0,
            }}
          >
            🚪
          </div>
          <div>
            <h4
              style={{
                margin: "0 0 6px 0",
                fontSize: "15px",
                fontWeight: 600,
                color: "var(--color-text-main, #0f172a)",
              }}
            >
              Are you sure you want to sign out?
            </h4>
            <p
              style={{
                margin: 0,
                fontSize: "13px",
                color: "var(--color-text-muted, #64748b)",
                lineHeight: "1.5",
              }}
            >
              Your active session will be ended. You will need to log in again with your mobile number and password.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
}

