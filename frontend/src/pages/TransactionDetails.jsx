import { useState, useEffect } from "react";
import { transactionsApi } from "../api/transactions";
import { formatCurrency, formatDate, getStatusStyle } from "../utils/formatters";
import { Button } from "../components/common/Button";
import { Alert, Spinner, Badge } from "../components/common/Feedback";

export function TransactionDetails({ transactionId, onNavigate }) {
  const [transaction, setTransaction] = useState(null);
  const [loading, setLoading] = useState(Boolean(transactionId));
  const [error, setError] = useState(transactionId ? "" : "No transaction selected.");

  useEffect(() => {
    if (!transactionId) return;

    let ignore = false;

    transactionsApi
      .getTransactionById(transactionId)
      .then((res) => {
        if (!ignore) {
          setTransaction(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          setError(err.message || "Failed to load transaction details.");
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [transactionId]);

  if (loading) {
    return <Spinner text="Loading transaction details..." />;
  }

  if (error || !transaction) {
    return (
      <div style={{ maxWidth: "520px", margin: "0 auto" }}>
        <Alert variant="danger">{error || "Transaction not found."}</Alert>
        <Button variant="secondary" onClick={() => onNavigate("transactions")}>
          ← Back to Transactions
        </Button>
      </div>
    );
  }

  const isDebit = transaction.direction === "DEBIT";
  const statusStyle = getStatusStyle(transaction.status);

  return (
    <div style={{ maxWidth: "560px", margin: "0 auto" }}>
      <div style={{ marginBottom: "16px" }}>
        <button
          type="button"
          onClick={() => onNavigate("transactions")}
          style={{
            background: "none",
            border: "none",
            color: "var(--color-primary)",
            fontWeight: "600",
            fontSize: "14px",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "4px 0",
          }}
        >
          ← Back to Transactions
        </button>
      </div>

      <div className="card" style={{ padding: "36px 28px" }}>
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div
            style={{
              width: "64px",
              height: "64px",
              borderRadius: "50%",
              backgroundColor: isDebit ? "var(--color-danger-bg)" : "var(--color-success-bg)",
              color: isDebit ? "var(--color-danger)" : "var(--color-success)",
              fontSize: "30px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 14px",
              border: `1px solid ${isDebit ? "var(--color-danger-border)" : "var(--color-success-border)"}`,
            }}
          >
            {isDebit ? "↑" : "↓"}
          </div>

          <Badge variant={statusStyle.badgeClass.replace("badge-", "")}>
            {statusStyle.label}
          </Badge>

          <h2
            style={{
              fontSize: "34px",
              fontWeight: "800",
              margin: "12px 0 4px",
              fontFamily: "var(--font-sans)",
            }}
          >
            <span className={isDebit ? "amount-debit" : "amount-credit"}>
              {isDebit ? "-" : "+"} {formatCurrency(transaction.amount)}
            </span>
          </h2>

          <div style={{ fontSize: "14px", color: "var(--color-text-muted)" }}>
            {isDebit ? (
              <>Paid to <strong>{transaction.receiver}</strong></>
            ) : (
              <>Received from <strong>{transaction.sender}</strong></>
            )}
          </div>
        </div>

        <div
          style={{
            background: "#f8fafc",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--color-border)",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "14px",
            fontSize: "13px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--color-text-muted)" }}>Transaction ID</span>
            <span style={{ fontFamily: "var(--font-mono)", fontWeight: "600", wordBreak: "break-all" }}>
              {transaction.transaction_id}
            </span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--color-text-muted)" }}>Payment Type</span>
            <span style={{ fontWeight: "600" }}>{transaction.transaction_type} (Unified Payments Interface)</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--color-text-muted)" }}>Sender UPI</span>
            <span style={{ fontFamily: "var(--font-mono)", fontWeight: "600" }}>
              {transaction.sender}
            </span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--color-text-muted)" }}>Receiver UPI</span>
            <span style={{ fontFamily: "var(--font-mono)", fontWeight: "600" }}>
              {transaction.receiver}
            </span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--color-text-muted)" }}>Direction</span>
            <span style={{ fontWeight: "600" }}>{transaction.direction}</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "var(--color-text-muted)" }}>Date & Time</span>
            <span>{formatDate(transaction.created_at)}</span>
          </div>
        </div>

        <div style={{ marginTop: "28px", display: "flex", gap: "12px" }}>
          <Button variant="secondary" block onClick={() => onNavigate("transactions")}>
            Back to List
          </Button>
          <Button variant="primary" block onClick={() => onNavigate("send-money")}>
            Send Again
          </Button>
        </div>
      </div>
    </div>
  );
}
