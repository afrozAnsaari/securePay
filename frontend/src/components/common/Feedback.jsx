export function Alert({ variant = "danger", children, onClose, className = "" }) {
  if (!children) return null;

  const iconMap = {
    danger: "⚠️",
    success: "✓",
    info: "ℹ️",
    warning: "⚡",
  };

  return (
    <div className={`alert alert-${variant} ${className}`.trim()}>
      <span style={{ fontSize: "16px", lineHeight: 1 }}>{iconMap[variant] || "•"}</span>
      <div style={{ flex: 1 }}>{children}</div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "inherit",
            opacity: 0.7,
            padding: "0 4px",
            fontSize: "16px",
          }}
          aria-label="Dismiss alert"
        >
          ✕
        </button>
      )}
    </div>
  );
}

export function Badge({ variant = "neutral", children, className = "" }) {
  return (
    <span className={`badge badge-${variant} ${className}`.trim()}>
      {children}
    </span>
  );
}

export function Spinner({ size = "md", text = null }) {
  const dimension = size === "sm" ? "18px" : size === "lg" ? "36px" : "24px";
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        gap: "12px",
      }}
    >
      <div
        style={{
          width: dimension,
          height: dimension,
          border: "3px solid #e2e8f0",
          borderTopColor: "var(--color-primary)",
          borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
        }}
      />
      {text && <span style={{ color: "var(--color-text-muted)", fontSize: "13px" }}>{text}</span>}
    </div>
  );
}
