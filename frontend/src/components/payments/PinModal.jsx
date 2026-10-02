import { useState } from "react";
import { formatCurrency } from "../../utils/formatters";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";

export function PinModal({
  isOpen,
  onClose,
  amount,
  receiver,
  bankName,
  onSubmit,
  loading,
}) {
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");

  const handleClose = () => {
    setPin("");
    setError("");
    if (onClose) onClose();
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!pin || pin.length < 4 || pin.length > 6) {
      setError("Please enter your 4 to 6 digit UPI PIN");
      return;
    }
    setError("");
    onSubmit(pin);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={loading ? undefined : handleClose}
      title="Authorize Payment"
      maxWidth="420px"
    >
      <div style={{ textAlign: "center", marginBottom: "20px" }}>
        <div style={{ fontSize: "13px", color: "var(--color-text-muted)" }}>
          Paying to
        </div>
        <div
          style={{
            fontSize: "17px",
            fontWeight: "700",
            color: "var(--color-text-main)",
            margin: "2px 0 8px",
          }}
        >
          {receiver}
        </div>
        <div
          style={{
            fontSize: "32px",
            fontWeight: "800",
            color: "var(--color-primary-dark)",
            fontFamily: "var(--font-sans)",
          }}
        >
          {formatCurrency(amount)}
        </div>
        <div
          style={{
            fontSize: "12px",
            color: "var(--color-text-muted)",
            marginTop: "4px",
          }}
        >
          Debiting from <strong>{bankName} Bank</strong>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group" style={{ textAlign: "center" }}>
          <label className="form-label" style={{ justifyContent: "center" }}>
            Enter UPI PIN
          </label>
          <input
            type="password"
            inputMode="numeric"
            maxLength={6}
            value={pin}
            onChange={(e) => {
              setPin(e.target.value.replace(/\D/g, ""));
              if (error) setError("");
            }}
            disabled={loading}
            className="form-input"
            style={{
              textAlign: "center",
              letterSpacing: "14px",
              fontSize: "26px",
              fontFamily: "var(--font-mono)",
              maxWidth: "200px",
              margin: "0 auto",
            }}
            autoFocus
            placeholder="••••"
          />
          {error && <span className="form-error" style={{ display: "block", marginTop: "8px" }}>{error}</span>}
          <span className="form-hint" style={{ marginTop: "6px" }}>
            UPI PIN will be encrypted and verified by NPCI Secure Server
          </span>
        </div>

        <div style={{ marginTop: "24px", display: "flex", gap: "12px" }}>
          <Button
            variant="secondary"
            block
            onClick={handleClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            block
            loading={loading}
          >
            Pay Now
          </Button>
        </div>
      </form>
    </Modal>
  );
}
