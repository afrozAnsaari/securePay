import { useState, useEffect } from "react";
import { transactionsApi } from "../api/transactions";
import { formatCurrency, formatDate, getStatusStyle } from "../utils/formatters";
import { Button } from "../components/common/Button";
import { Alert, Spinner, Badge } from "../components/common/Feedback";

export function Transactions({ onNavigate, onSelectTransaction }) {
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(15);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    transactionsApi
      .getTransactions({ limit, offset })
      .then((res) => {
        if (!ignore) {
          setTransactions(res.transactions || []);
          setTotal(res.total || 0);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          setError(err.message || "Failed to load transaction history.");
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [limit, offset]);

  const handleRefresh = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await transactionsApi.getTransactions({ limit, offset });
      setTransactions(res.transactions || []);
      setTotal(res.total || 0);
    } catch (err) {
      setError(err.message || "Failed to load transaction history.");
    } finally {
      setLoading(false);
    }
  };

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit) || 1;

  const handleNextPage = () => {
    if (offset + limit < total) {
      setLoading(true);
      setOffset((prev) => prev + limit);
    }
  };

  const handlePrevPage = () => {
    if (offset - limit >= 0) {
      setLoading(true);
      setOffset((prev) => prev - limit);
    }
  };

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <h2 style={{ fontSize: "20px", fontWeight: "700" }}>Transaction History</h2>
          <p style={{ color: "var(--color-text-muted)", fontSize: "14px" }}>
            Complete audit record of your UPI transfers ({total} total)
          </p>
        </div>

        <Button variant="secondary" onClick={handleRefresh} size="sm">
          🔄 Refresh
        </Button>
      </div>

      {error && (
        <Alert variant="danger" onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        {loading ? (
          <Spinner text="Loading transaction records..." />
        ) : transactions.length === 0 ? (
          <div style={{ textAlign: "center", padding: "48px 20px", color: "var(--color-text-muted)" }}>
            <div style={{ fontSize: "36px", marginBottom: "8px" }}>📜</div>
            <h3 style={{ fontSize: "16px", color: "var(--color-text-main)", marginBottom: "4px" }}>
              No Transactions Found
            </h3>
            <p style={{ fontSize: "14px", maxWidth: "340px", margin: "0 auto 16px" }}>
              When you send or receive money via SecurePay, transaction records will appear here.
            </p>
            <Button variant="primary" size="sm" onClick={() => onNavigate("send-money")}>
              Send Money Now
            </Button>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table className="app-table">
                <thead>
                  <tr>
                    <th>Type / Parties</th>
                    <th>Date & Time</th>
                    <th>Status</th>
                    <th style={{ textAlign: "right" }}>Amount</th>
                    <th style={{ textAlign: "center" }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx) => {
                    const isDebit = tx.direction === "DEBIT";
                    const isSelf = tx.direction === "SELF";
                    const style = getStatusStyle(tx.status);

                    return (
                      <tr key={tx.transaction_id}>
                        <td>
                          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                            <div
                              style={{
                                width: "34px",
                                height: "34px",
                                borderRadius: "50%",
                                backgroundColor: isDebit
                                  ? "var(--color-danger-bg)"
                                  : "var(--color-success-bg)",
                                color: isDebit ? "var(--color-danger)" : "var(--color-success)",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontWeight: "700",
                                fontSize: "16px",
                              }}
                            >
                              {isDebit ? "↑" : isSelf ? "⇄" : "↓"}
                            </div>
                            <div>
                              <div style={{ fontWeight: "600" }}>
                                {isDebit ? tx.receiver : tx.sender}
                              </div>
                              <div
                                style={{
                                  fontSize: "12px",
                                  color: "var(--color-text-muted)",
                                  fontFamily: "var(--font-mono)",
                                }}
                              >
                                {isDebit ? "Sent to" : isSelf ? "Self Transfer" : "Received from"}
                              </div>
                            </div>
                          </div>
                        </td>

                        <td style={{ color: "var(--color-text-muted)", fontSize: "13px" }}>
                          {formatDate(tx.created_at)}
                        </td>

                        <td>
                          <Badge variant={style.badgeClass.replace("badge-", "")}>
                            {style.label}
                          </Badge>
                        </td>

                        <td
                          style={{
                            textAlign: "right",
                            fontWeight: "700",
                            fontFamily: "var(--font-mono)",
                            fontSize: "15px",
                          }}
                        >
                          <span className={isDebit ? "amount-debit" : "amount-credit"}>
                            {isDebit ? "-" : "+"} {formatCurrency(tx.amount)}
                          </span>
                        </td>

                        <td style={{ textAlign: "center" }}>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              if (onSelectTransaction) onSelectTransaction(tx.transaction_id);
                              onNavigate("transaction-detail");
                            }}
                          >
                            Receipt
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "16px 20px",
                borderTop: "1px solid var(--color-border)",
                backgroundColor: "#f8fafc",
                fontSize: "13px",
                color: "var(--color-text-muted)",
              }}
            >
              <div>
                Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong> ({total} items)
              </div>

              <div style={{ display: "flex", gap: "8px" }}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handlePrevPage}
                  disabled={offset === 0 || loading}
                >
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleNextPage}
                  disabled={offset + limit >= total || loading}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
