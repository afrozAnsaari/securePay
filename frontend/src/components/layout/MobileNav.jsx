export function MobileNav({ currentRoute, onNavigate }) {
  const navItems = [
    { id: "dashboard", label: "Home", icon: "📊" },
    { id: "send-money", label: "Pay", icon: "💸" },
    { id: "accounts", label: "Banks", icon: "🏦" },
    { id: "transactions", label: "History", icon: "📜" },
  ];

  return (
    <nav className="mobile-nav">
      <div className="mobile-nav-items">
        {navItems.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`mobile-nav-btn ${currentRoute === item.id ? "active" : ""}`}
            onClick={() => onNavigate(item.id)}
          >
            <span style={{ fontSize: "18px" }}>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
