import { useState } from "react";
import { accountsApi } from "../../api/accounts";
import { formatCurrency } from "../../utils/formatters";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import { Alert } from "../common/Feedback";

export function BalanceCheckModal({
  isOpen,
  onClose,
  account,
  upiProfileId,
  onBalanceUpdated,
}) {
  const [pin, setPin] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [balanceResult, setBalanceResult] = useState(null);

  const handleClose = () => {
    setPin("");
    setError("");
    setBalanceResult(null);
    onClose();
  };

  const handleCheckBalance = async (e) => {
    e.preventDefault();
    if (!pin || pin.length < 4 || pin.length > 6) {
      setError("Please enter your 4-6 digit UPI PIN");
      return;
    }

    if (!upiProfileId) {
      setError("Active UPI Profile required to check bank balance.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const res = await accountsApi.getBalance({
        upi_profile_id: upiProfileId,
        account_id: account.account_id,
        upi_pin: pin,
      });

      setBalanceResult(res);
      if (onBalanceUpdated) {
        onBalanceUpdated(account.account_id, res.balance);
      }
    } catch (err) {
      if (err.status === 403) {
        setError("Invalid UPI PIN. Please try again.");
      } else {
        setError(err.message || "Failed to check balance. Please check your UPI PIN.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={balanceResult ? "Account Balance" : "Enter UPI PIN"}
      maxWidth="420px"
    >
      {error && (
        <Alert variant="danger" onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      {balanceResult ? (
        <div style={{ textAlign: "center", padding: "16px 0" }}>
          <div
            style={{
              width: "60px",
              height: "60px",
              borderRadius: "50%",
              backgroundColor: "var(--color-success-bg)",
              color: "var(--color-success)",
              fontSize: "28px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
              border: "1px solid var(--color-success-border)",
            }}
          >
            ✓
          </div>
          <div style={{ fontSize: "14px", color: "var(--color-text-muted)" }}>
            Available Balance
          </div>
          <div
            style={{
              fontSize: "36px",
              fontWeight: "800",
              color: "var(--color-text-main)",
              fontFamily: "var(--font-sans)",
              margin: "8px 0 16px",
            }}
          >
            {formatCurrency(balanceResult.balance)}
          </div>
          <div
            style={{
              background: "#f8fafc",
              padding: "12px",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--color-border)",
              fontSize: "13px",
              color: "var(--color-text-muted)",
            }}
          >
            <div>Bank: <strong>{balanceResult.bank_name}</strong></div>
            <div>Account Type: <strong>{balanceResult.account_type}</strong></div>
          </div>
          <div style={{ marginTop: "24px" }}>
            <Button variant="primary" block onClick={handleClose}>
              Done
            </Button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleCheckBalance}>
          <div style={{ textAlign: "center", marginBottom: "16px" }}>
            <div style={{ fontWeight: "600", fontSize: "15px" }}>
              {account?.bank_name} Bank
            </div>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                color: "var(--color-text-muted)",
                fontSize: "13px",
              }}
            >
              Account ending in {account?.masked_account_number?.slice(-4)}
            </div>
          </div>

          <div className="form-group" style={{ textAlign: "center" }}>
            <label className="form-label" style={{ justifyContent: "center" }}>
              Enter 4 to 6 digit UPI PIN
            </label>
            <input
              type="password"
              inputMode="numeric"
              maxLength={6}
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))}
              className="form-input"
              style={{
                textAlign: "center",
                letterSpacing: "12px",
                fontSize: "24px",
                fontFamily: "var(--font-mono)",
                maxWidth: "220px",
                margin: "0 auto",
              }}
              autoFocus
              placeholder="••••"
            />
            <span className="form-hint" style={{ marginTop: "6px" }}>
              UPI PIN is never saved or logged
            </span>
          </div>

          <div style={{ marginTop: "24px", display: "flex", gap: "12px" }}>
            <Button variant="secondary" block onClick={handleClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" block loading={loading}>
              Check Balance
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
