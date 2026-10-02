import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/useAuth";
import { accountsApi } from "../api/accounts";
import { transactionsApi } from "../api/transactions";
import { formatCurrency, formatDate, getStatusStyle } from "../utils/formatters";
import { Button } from "../components/common/Button";
import { Alert, Spinner, Badge } from "../components/common/Feedback";
import { BalanceCheckModal } from "../components/accounts/BalanceCheckModal";
import { CreateUPIProfileModal } from "../components/dashboard/CreateUPIProfileModal";

export function Dashboard({ onNavigate, onSelectTransaction }) {
  const { user, upiProfile, refreshUPIProfile } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [balances, setBalances] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedAccForBalance, setSelectedAccForBalance] = useState(null);
  const [isUpiModalOpen, setIsUpiModalOpen] = useState(false);

  const loadDashboardData = useCallback(async () => {
    try {
      const [accRes, txRes] = await Promise.allSettled([
        accountsApi.getLinkedAccounts(),
        transactionsApi.getTransactions({ limit: 5, offset: 0 }),
      ]);

      if (accRes.status === "fulfilled") {
        setAccounts(accRes.value.accounts || []);
      }

      if (txRes.status === "fulfilled") {
        setRecentTransactions(txRes.value.transactions || []);
      }
    } catch {
      setError("Failed to load dashboard overview.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;

    Promise.allSettled([
      accountsApi.getLinkedAccounts(),
      transactionsApi.getTransactions({ limit: 5, offset: 0 }),
    ]).then(([accRes, txRes]) => {
      if (!ignore) {
        if (accRes.status === "fulfilled") {
          setAccounts(accRes.value.accounts || []);
        }
        if (txRes.status === "fulfilled") {
          setRecentTransactions(txRes.value.transactions || []);
        }
        setLoading(false);
      }
    }).catch(() => {
      if (!ignore) {
        setError("Failed to load dashboard overview.");
        setLoading(false);
      }
    });

    return () => {
      ignore = true;
    };
  }, []);

  const primaryAccount = accounts.find((a) => a.is_primary) || accounts[0];
  const primaryBalance = primaryAccount ? balances[primaryAccount.account_id] : undefined;

  const handleBalanceUpdated = (accId, bal) => {
    setBalances((prev) => ({ ...prev, [accId]: bal }));
  };

  if (loading) {
    return <Spinner text="Loading your SecurePay dashboard..." />;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Welcome Banner */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <h2 style={{ fontSize: "24px", fontWeight: "800", color: "var(--color-text-main)" }}>
            Hello, {user?.name || "Member"} 👋
          </h2>
          <p style={{ color: "var(--color-text-muted)", fontSize: "14px" }}>
            Real-time payments protected by SecurePay fraud intelligence
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <Button variant="primary" onClick={() => onNavigate("send-money")}>
            <span>💸</span> Send Money
          </Button>
          <Button variant="secondary" onClick={() => onNavigate("accounts")}>
            <span>🏦</span> Manage Banks
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="danger" onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      {/* UPI Profile Prompt Banner if not setup */}
      {!upiProfile?.exists && (
        <div
          className="alert alert-warning"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div>
            <strong>UPI ID Setup Needed:</strong> You have not configured a UPI ID yet. Create one to send and receive money.
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsUpiModalOpen(true)}
          >
            Create UPI ID
          </Button>
        </div>
      )}

      {/* Hero Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "20px",
        }}
      >
        {/* UPI & Primary Bank Card */}
        <div className="bank-pass-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <span style={{ fontSize: "11px", letterSpacing: "1px", color: "#38bdf8", fontWeight: "700" }}>
                SECUREPAY UPI
              </span>
              <div
                style={{
                  fontSize: "18px",
                  fontWeight: "700",
                  fontFamily: "var(--font-mono)",
                  marginTop: "4px",
                }}
              >
                {upiProfile?.upi_id || "No UPI ID active"}
              </div>
            </div>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                background: "rgba(255, 255, 255, 0.15)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "18px",
              }}
            >
              ₹
            </div>
          </div>

          <div style={{ margin: "24px 0 16px" }}>
            <div style={{ fontSize: "12px", color: "#94a3b8" }}>
              Primary Funding Bank: {primaryAccount ? `${primaryAccount.bank_name} Bank` : "None linked"}
            </div>
            <div style={{ fontSize: "20px", fontFamily: "var(--font-mono)", letterSpacing: "2px", marginTop: "2px" }}>
              {primaryAccount ? primaryAccount.masked_account_number : "•••• •••• •••• ••••"}
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>Available Balance</div>
              <div style={{ fontSize: "20px", fontWeight: "700" }}>
                {primaryBalance !== undefined ? formatCurrency(primaryBalance) : "••••••••"}
              </div>
            </div>

            {primaryAccount && (
              <Button
                variant="outline-primary"
                size="sm"
                onClick={() => setSelectedAccForBalance(primaryAccount)}
                style={{
                  color: "#ffffff",
                  borderColor: "rgba(255, 255, 255, 0.4)",
                  backgroundColor: "rgba(255, 255, 255, 0.08)",
                }}
              >
                {primaryBalance !== undefined ? "Refresh" : "Check Balance"}
              </Button>
            )}
          </div>
        </div>

        {/* Quick Summary & Action Card */}
        <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <h3 className="card-title">Quick Actions</h3>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "12px",
                marginTop: "16px",
              }}
            >
              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: "16px 12px", display: "flex", flexDirection: "column", gap: "6px" }}
                onClick={() => onNavigate("send-money")}
              >
                <span style={{ fontSize: "22px" }}>💸</span>
                <span style={{ fontSize: "13px", fontWeight: "600" }}>Send Money</span>
              </button>

              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: "16px 12px", display: "flex", flexDirection: "column", gap: "6px" }}
                onClick={() => onNavigate("accounts")}
              >
                <span style={{ fontSize: "22px" }}>➕</span>
                <span style={{ fontSize: "13px", fontWeight: "600" }}>Link Bank</span>
              </button>

              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: "16px 12px", display: "flex", flexDirection: "column", gap: "6px" }}
                onClick={() => onNavigate("transactions")}
              >
                <span style={{ fontSize: "22px" }}>📜</span>
                <span style={{ fontSize: "13px", fontWeight: "600" }}>Passbook</span>
              </button>

              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: "16px 12px", display: "flex", flexDirection: "column", gap: "6px" }}
                onClick={() => {
                  if (primaryAccount) setSelectedAccForBalance(primaryAccount);
                  else onNavigate("accounts");
                }}
              >
                <span style={{ fontSize: "22px" }}>🔍</span>
                <span style={{ fontSize: "13px", fontWeight: "600" }}>Check Balance</span>
              </button>
            </div>
          </div>

          <div
            style={{
              marginTop: "16px",
              paddingTop: "14px",
              borderTop: "1px solid var(--color-border)",
              display: "flex",
              justifyContent: "space-between",
              fontSize: "13px",
              color: "var(--color-text-muted)",
            }}
          >
            <span>Linked Accounts: <strong>{accounts.length}</strong></span>
            <span>Security: <strong>Active</strong></span>
          </div>
        </div>
      </div>

      {/* Recent Transactions Section */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Recent Transactions</h3>
            <p style={{ color: "var(--color-text-muted)", fontSize: "13px", marginTop: "2px" }}>
              Latest credit and debit activity
            </p>
          </div>
          <Button variant="secondary" size="sm" onClick={() => onNavigate("transactions")}>
            View All
          </Button>
        </div>

        {recentTransactions.length === 0 ? (
          <div style={{ textAlign: "center", padding: "28px", color: "var(--color-text-muted)" }}>
            <div style={{ fontSize: "28px", marginBottom: "6px" }}>📜</div>
            <p style={{ fontSize: "14px" }}>No transactions recorded yet.</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="app-table">
              <thead>
                <tr>
                  <th>Recipient / Sender</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th style={{ textAlign: "right" }}>Amount</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {recentTransactions.map((tx) => {
                  const isDebit = tx.direction === "DEBIT";
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
                            {isDebit ? "↑" : "↓"}
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
                              {isDebit ? "Sent to" : "Received from"}
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
                        }}
                      >
                        <span className={isDebit ? "amount-debit" : "amount-credit"}>
                          {isDebit ? "-" : "+"} {formatCurrency(tx.amount)}
                        </span>
                      </td>

                      <td style={{ textAlign: "right" }}>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            if (onSelectTransaction) onSelectTransaction(tx.transaction_id);
                            onNavigate("transaction-detail");
                          }}
                        >
                          Details
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedAccForBalance && (
        <BalanceCheckModal
          isOpen={Boolean(selectedAccForBalance)}
          onClose={() => setSelectedAccForBalance(null)}
          account={selectedAccForBalance}
          upiProfileId={upiProfile?.id}
          onBalanceUpdated={handleBalanceUpdated}
        />
      )}

      {isUpiModalOpen && (
        <CreateUPIProfileModal
          isOpen={isUpiModalOpen}
          onClose={() => setIsUpiModalOpen(false)}
          onProfileCreated={() => {
            refreshUPIProfile();
            setLoading(true);
            loadDashboardData();
          }}
        />
      )}
    </div>
  );
}
