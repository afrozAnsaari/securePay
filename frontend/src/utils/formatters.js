/**
 * SecurePay Data & UI Formatters
 */

export function formatCurrency(amount) {
  if (amount === undefined || amount === null || isNaN(amount)) return "₹0.00";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(dateString) {
  if (!dateString) return "";
  const d = new Date(dateString);
  if (isNaN(d.getTime())) return dateString;

  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  }).format(d);
}

export function formatMaskedAccount(masked) {
  if (!masked) return "";
  // If backend returns *******1234, format as •••• 1234
  const last4 = masked.slice(-4);
  return `•••• ${last4}`;
}

export function getBankColor(bankName) {
  switch ((bankName || "").toUpperCase()) {
    case "SBI":
      return {
        bg: "rgba(14, 116, 144, 0.12)",
        text: "#0891b2",
        border: "rgba(14, 116, 144, 0.3)",
      };
    case "HDFC":
      return {
        bg: "rgba(2, 132, 199, 0.12)",
        text: "#0284c7",
        border: "rgba(2, 132, 199, 0.3)",
      };
    case "ICICI":
      return {
        bg: "rgba(217, 119, 6, 0.12)",
        text: "#d97706",
        border: "rgba(217, 119, 6, 0.3)",
      };
    default:
      return {
        bg: "rgba(99, 102, 241, 0.12)",
        text: "#6366f1",
        border: "rgba(99, 102, 241, 0.3)",
      };
  }
}

export function getStatusStyle(status) {
  const normalized = (status || "").toUpperCase();
  switch (normalized) {
    case "SUCCESS":
    case "APPROVED":
    case "ACTIVE":
      return {
        badgeClass: "badge-success",
        label: "Success",
        icon: "✓",
      };
    case "PENDING":
    case "PROCESSING":
      return {
        badgeClass: "badge-warning",
        label: "Pending",
        icon: "⏳",
      };
    case "DECLINED":
    case "FRAUD_BLOCKED":
    case "BLOCKED":
      return {
        badgeClass: "badge-danger",
        label: normalized === "FRAUD_BLOCKED" ? "Security Declined" : "Declined",
        icon: "✕",
      };
    default:
      return {
        badgeClass: "badge-neutral",
        label: status || "Unknown",
        icon: "•",
      };
  }
}
