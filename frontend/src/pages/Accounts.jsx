import { useState, useEffect } from "react";
import { accountsApi } from "../api/accounts";
import { useAuth } from "../context/useAuth";
import { formatCurrency, getBankColor } from "../utils/formatters";
import { Button } from "../components/common/Button";
import { Alert, Spinner, Badge } from "../components/common/Feedback";
import { BalanceCheckModal } from "../components/accounts/BalanceCheckModal";
import { LinkAccountModal } from "../components/accounts/LinkAccountModal";

export function Accounts() {
  const { upiProfile } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [balances, setBalances] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedAccForBalance, setSelectedAccForBalance] = useState(null);
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);

  useEffect(() => {
    let ignore = false;

    accountsApi
      .getLinkedAccounts()
      .then((res) => {
        if (!ignore) {
          setAccounts(res.accounts || []);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          setError(err.message || "Failed to load linked bank accounts.");
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await accountsApi.getLinkedAccounts();
      setAccounts(res.accounts || []);
    } catch (err) {
      setError(err.message || "Failed to load linked bank accounts.");
    } finally {
      setLoading(false);
    }
  };

  const handleBalanceUpdated = (accountId, balance) => {
    setBalances((prev) => ({ ...prev, [accountId]: balance }));
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
          <h2 style={{ fontSize: "20px", fontWeight: "700" }}>Linked Bank Accounts</h2>
          <p style={{ color: "var(--color-text-muted)", fontSize: "14px" }}>
            Accounts registered for UPI payments and instant transfers
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <Button variant="secondary" onClick={handleRefresh} size="sm">
            🔄 Refresh
          </Button>
          <Button
            variant="primary"
            onClick={() => setIsLinkModalOpen(true)}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <span>➕</span>
            <span>Link New Bank</span>
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="danger" onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Spinner text="Loading linked bank accounts..." />
      ) : accounts.length === 0 ? (
        <div
          className="card"
          style={{
            textAlign: "center",
            padding: "48px 20px",
            color: "var(--color-text-muted)",
          }}
        >
          <div style={{ fontSize: "40px", marginBottom: "12px" }}>🏦</div>
          <h3 style={{ fontSize: "17px", color: "var(--color-text-main)", marginBottom: "6px" }}>
            No Bank Accounts Linked Yet
          </h3>
          <p style={{ fontSize: "14px", maxWidth: "380px", margin: "0 auto 20px" }}>
            Link your savings or current account using your debit card to start sending and receiving UPI payments.
          </p>
          <Button variant="primary" onClick={() => setIsLinkModalOpen(true)}>
            Link Your Bank Account
          </Button>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: "18px",
          }}
        >
          {accounts.map((acc) => {
            const colors = getBankColor(acc.bank_name);
            const balance = balances[acc.account_id];

            return (
              <div
                key={acc.account_id}
                className="card"
                style={{
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  position: "relative",
                  borderTop: `4px solid ${colors.text}`,
                }}
              >
                <div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: "12px",
                    }}
                  >
                    <div
                      style={{
                        padding: "4px 8px",
                        borderRadius: "var(--radius-sm)",
                        background: colors.bg,
                        color: colors.text,
                        fontWeight: "700",
                        fontSize: "12px",
                        letterSpacing: "0.5px",
                      }}
                    >
                      {acc.bank_name} BANK
                    </div>

                    {acc.is_primary && (
                      <Badge variant="primary">Primary Account</Badge>
                    )}
                  </div>

                  <div
                    style={{
                      fontSize: "18px",
                      fontWeight: "700",
                      fontFamily: "var(--font-mono)",
                      color: "var(--color-text-main)",
                      letterSpacing: "2px",
                      margin: "12px 0 8px",
                    }}
                  >
                    {acc.masked_account_number}
                  </div>

                  <div
                    style={{
                      fontSize: "12px",
                      color: "var(--color-text-muted)",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <span>Account ID: #{acc.account_id}</span>
                  </div>
                </div>

                <div
                  style={{
                    marginTop: "20px",
                    paddingTop: "14px",
                    borderTop: "1px solid var(--color-border)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <div style={{ fontSize: "11px", color: "var(--color-text-muted)" }}>
                      Account Balance
                    </div>
                    <div style={{ fontSize: "15px", fontWeight: "700" }}>
                      {balance !== undefined ? formatCurrency(balance) : "••••••••"}
                    </div>
                  </div>

                  <Button
                    variant="outline-primary"
                    size="sm"
                    onClick={() => setSelectedAccForBalance(acc)}
                  >
                    {balance !== undefined ? "Refresh" : "Check Balance"}
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedAccForBalance && (
        <BalanceCheckModal
          isOpen={Boolean(selectedAccForBalance)}
          onClose={() => setSelectedAccForBalance(null)}
          account={selectedAccForBalance}
          upiProfileId={upiProfile?.id}
          onBalanceUpdated={handleBalanceUpdated}
        />
      )}

      {isLinkModalOpen && (
        <LinkAccountModal
          isOpen={isLinkModalOpen}
          onClose={() => setIsLinkModalOpen(false)}
          onAccountLinked={() => {
            handleRefresh();
          }}
        />
      )}
    </div>
  );
}
