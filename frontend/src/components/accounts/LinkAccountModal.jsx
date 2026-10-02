import { useState } from "react";
import { accountsApi } from "../../api/accounts";
import {
  validateCardNumber,
  validateCardExpiry,
  validateCardPin,
} from "../../utils/validators";
import { Modal } from "../common/Modal";
import { Input } from "../common/Input";
import { Button } from "../common/Button";
import { Alert } from "../common/Feedback";

export function LinkAccountModal({ isOpen, onClose, onAccountLinked }) {
  const [bankName, setBankName] = useState("HDFC");
  const [cardNumber, setCardNumber] = useState("");
  const [expiryMonth, setExpiryMonth] = useState("");
  const [expiryYear, setExpiryYear] = useState("");
  const [cardPin, setCardPin] = useState("");
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);

  const resetForm = () => {
    setBankName("HDFC");
    setCardNumber("");
    setExpiryMonth("");
    setExpiryYear("");
    setCardPin("");
    setErrors({});
    setApiError("");
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError("");

    const newErrors = {};
    const cardErr = validateCardNumber(cardNumber);
    if (cardErr) newErrors.cardNumber = cardErr;

    const expiryErr = validateCardExpiry(expiryMonth, expiryYear);
    if (expiryErr) newErrors.expiry = expiryErr;

    const pinErr = validateCardPin(cardPin);
    if (pinErr) newErrors.cardPin = pinErr;

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setLoading(true);

    try {
      const res = await accountsApi.linkBankAccount({
        bank_name: bankName,
        card_number: cardNumber.replace(/[\s-]/g, ""),
        expiry_month: Number(expiryMonth),
        expiry_year: Number(expiryYear),
        card_pin: cardPin,
      });

      resetForm();
      if (onAccountLinked) {
        onAccountLinked(res);
      }
      onClose();
    } catch (err) {
      setApiError(err.message || "Failed to link bank account. Please verify debit card details.");
    } finally {
      setLoading(false);
    }
  };

  // Format card number with spaces every 4 digits
  const handleCardNumberChange = (e) => {
    const raw = e.target.value.replace(/\D/g, "").slice(0, 16);
    const formatted = raw.match(/.{1,4}/g)?.join(" ") || raw;
    setCardNumber(formatted);
    if (errors.cardNumber) setErrors((prev) => ({ ...prev, cardNumber: null }));
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Link Bank Account"
      maxWidth="480px"
    >
      {apiError && (
        <Alert variant="danger" onClose={() => setApiError("")}>
          {apiError}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Select Bank</label>
          <select
            className="form-input"
            value={bankName}
            onChange={(e) => setBankName(e.target.value)}
          >
            <option value="HDFC">HDFC Bank</option>
            <option value="SBI">State Bank of India (SBI)</option>
            <option value="ICICI">ICICI Bank</option>
          </select>
        </div>

        <Input
          label="Debit Card Number"
          type="text"
          placeholder="4111 2222 3333 4444"
          maxLength={19}
          value={cardNumber}
          onChange={handleCardNumberChange}
          error={errors.cardNumber}
          hint="16-digit debit card linked to your account"
        />

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <Input
            label="Expiry Month"
            type="number"
            placeholder="MM (01-12)"
            min={1}
            max={12}
            value={expiryMonth}
            onChange={(e) => {
              setExpiryMonth(e.target.value);
              if (errors.expiry) setErrors((prev) => ({ ...prev, expiry: null }));
            }}
          />

          <Input
            label="Expiry Year"
            type="number"
            placeholder="YYYY (e.g. 2028)"
            min={2024}
            max={2099}
            value={expiryYear}
            onChange={(e) => {
              setExpiryYear(e.target.value);
              if (errors.expiry) setErrors((prev) => ({ ...prev, expiry: null }));
            }}
          />
        </div>
        {errors.expiry && (
          <div className="form-error" style={{ marginBottom: "12px" }}>
            {errors.expiry}
          </div>
        )}

        <Input
          label="ATM PIN (4-6 digits)"
          type="password"
          maxLength={6}
          placeholder="••••"
          value={cardPin}
          onChange={(e) => {
            setCardPin(e.target.value.replace(/\D/g, ""));
            if (errors.cardPin) setErrors((prev) => ({ ...prev, cardPin: null }));
          }}
          error={errors.cardPin}
          hint="Used by NPCI to securely verify account ownership"
        />

        <div style={{ marginTop: "24px", display: "flex", gap: "12px" }}>
          <Button variant="secondary" block onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" block loading={loading}>
            Link Account
          </Button>
        </div>
      </form>
    </Modal>
  );
}
