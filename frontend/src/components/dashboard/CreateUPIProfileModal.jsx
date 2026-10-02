import { useState } from "react";
import { paymentsApi } from "../../api/payments";
import { useAuth } from "../../context/useAuth";
import { validateUpiPin } from "../../utils/validators";
import { Modal } from "../common/Modal";
import { Input } from "../common/Input";
import { Button } from "../common/Button";
import { Alert } from "../common/Feedback";

export function CreateUPIProfileModal({ isOpen, onClose, onProfileCreated }) {
  const { refreshUPIProfile } = useAuth();
  const [upiId, setUpiId] = useState("");
  const [upiPin, setUpiPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const trimmedId = upiId.trim().toLowerCase();
    if (!trimmedId) {
      setError("Please choose a UPI ID username");
      return;
    }

    const pinErr = validateUpiPin(upiPin);
    if (pinErr) {
      setError(pinErr);
      return;
    }

    if (upiPin !== confirmPin) {
      setError("UPI PINs do not match.");
      return;
    }

    setLoading(true);

    try {
      const fullUpiId = trimmedId.endsWith("@securepay")
        ? trimmedId
        : `${trimmedId}@securepay`;

      await paymentsApi.createUPIProfile({
        upi_id: fullUpiId,
        upi_pin: upiPin,
      });

      await refreshUPIProfile();
      if (onProfileCreated) onProfileCreated();
      onClose();
    } catch (err) {
      setError(err.message || "Failed to create UPI profile. Username may be taken.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={loading ? undefined : onClose}
      title="Create Your UPI ID"
      maxWidth="460px"
    >
      {error && (
        <Alert variant="danger" onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Choose UPI Handle</label>
          <div style={{ display: "flex", alignItems: "center" }}>
            <input
              type="text"
              placeholder="e.g. rahul"
              value={upiId}
              onChange={(e) =>
                setUpiId(e.target.value.toLowerCase().replace(/[^a-z0-9._]/g, ""))
              }
              className="form-input"
              style={{
                borderTopRightRadius: 0,
                borderBottomRightRadius: 0,
                flex: 1,
              }}
              required
            />
            <span
              style={{
                padding: "12px 14px",
                backgroundColor: "#f1f5f9",
                border: "1.5px solid var(--color-border)",
                borderLeft: "none",
                borderTopRightRadius: "var(--radius-md)",
                borderBottomRightRadius: "var(--radius-md)",
                color: "var(--color-primary-dark)",
                fontWeight: "700",
                fontSize: "14px",
                fontFamily: "var(--font-mono)",
              }}
            >
              @securepay
            </span>
          </div>
          <span className="form-hint" style={{ marginTop: "4px" }}>
            Letters, numbers, '.', and '_' allowed (max 16 characters)
          </span>
        </div>

        <Input
          label="Set UPI PIN (4-6 digits)"
          type="password"
          maxLength={6}
          placeholder="••••"
          value={upiPin}
          onChange={(e) => setUpiPin(e.target.value.replace(/\D/g, ""))}
          hint="Used to authorize all future transfers & balance checks"
        />

        <Input
          label="Confirm UPI PIN"
          type="password"
          maxLength={6}
          placeholder="••••"
          value={confirmPin}
          onChange={(e) => setConfirmPin(e.target.value.replace(/\D/g, ""))}
        />

        <div style={{ marginTop: "24px", display: "flex", gap: "12px" }}>
          <Button variant="secondary" block onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" block loading={loading}>
            Create Profile
          </Button>
        </div>
      </form>
    </Modal>
  );
}
