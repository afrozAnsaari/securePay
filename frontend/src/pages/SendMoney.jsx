import { useState, useEffect, useRef } from "react";
import { accountsApi } from "../api/accounts";
import { paymentsApi } from "../api/payments";
import { useAuth } from "../context/useAuth";
import { createIdempotencyManager } from "../utils/idempotency";
import { validateReceiver, validateAmount } from "../utils/validators";
import { formatCurrency, formatDate } from "../utils/formatters";
import { Input } from "../components/common/Input";
import { Button } from "../components/common/Button";
import { Alert, Spinner } from "../components/common/Feedback";
import { PinModal } from "../components/payments/PinModal";

export function SendMoney({ onNavigate }) {
  const { upiProfile } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [loadingAccounts, setLoadingAccounts] = useState(true);

  // Form inputs
  const [receiver, setReceiver] = useState("");
  const [amount, setAmount] = useState("");
  const [selectedAccountId, setSelectedAccountId] = useState("");
  const [errors, setErrors] = useState({});

  // Payment states
  const [isPinModalOpen, setIsPinModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [paymentError, setPaymentError] = useState("");
  const [paymentSuccess, setPaymentSuccess] = useState(null);

  const idempotencyManager = useRef(createIdempotencyManager()).current;

  useEffect(() => {
    let ignore = false;

    accountsApi
      .getLinkedAccounts()
      .then((res) => {
        if (!ignore) {
          const accList = res.accounts || [];
          setAccounts(accList);
          if (accList.length > 0) {
            const primary = accList.find((a) => a.is_primary) || accList[0];
            setSelectedAccountId(String(primary.account_id));
          }
          setLoadingAccounts(false);
        }
      })
      .catch(() => {
        if (!ignore) {
          setLoadingAccounts(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  const handleReviewPayment = (e) => {
    e.preventDefault();
    setPaymentError("");
    setPaymentSuccess(null);

    const newErrors = {};
    const receiverErr = validateReceiver(receiver);
    if (receiverErr) newErrors.receiver = receiverErr;

    const amountErr = validateAmount(amount);
    if (amountErr) newErrors.amount = amountErr;

    if (!selectedAccountId) {
      newErrors.account = "Please select a funding bank account.";
    }

    if (!upiProfile?.exists) {
      setPaymentError("You must setup a UPI profile before sending money.");
      return;
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    idempotencyManager.getKey();
    setIsPinModalOpen(true);
  };

  const handleExecutePayment = async (pin) => {
    setSubmitting(true);
    setPaymentError("");

    const key = idempotencyManager.getKey();

    try {
      const payload = {
        receiver: receiver.trim().toLowerCase(),
        sender_upi_profile_id: upiProfile.id,
        sender_account_id: Number(selectedAccountId),
        amount: Math.round(Number(amount)),
        upi_pin: pin,
      };

      const result = await paymentsApi.makePayment(payload, key);
      idempotencyManager.resetKey();
      setIsPinModalOpen(false);
      setPaymentSuccess(result);
    } catch (err) {
      if (err.status === 403) {
        if (err.message && err.message.toLowerCase().includes("pin")) {
          setPaymentError("Invalid UPI PIN. Please check your PIN and try again.");
        } else {
          setPaymentError(
            "Transaction declined by SecurePay security and fraud risk engine. Your account was not debited."
          );
        }
      } else if (err.status === 400) {
        if (err.message && err.message.includes("Insufficient Balance")) {
          setPaymentError("Insufficient balance in your selected bank account.");
        } else if (err.message && err.message.includes("same bank account")) {
          setPaymentError("Cannot transfer funds to the same bank account.");
        } else {
          setPaymentError(err.message || "Invalid transfer request.");
        }
      } else if (err.status === 404) {
        setPaymentError(
          "Recipient not found. Please verify the mobile number or UPI ID (@securepay)."
        );
      } else if (err.status === 409) {
        setPaymentError(
          "This payment is already processing. Please check transaction history before retrying."
        );
      } else if (err.status === 429) {
        setPaymentError("Payment rate limit exceeded. Please wait a moment.");
      } else {
        setPaymentError(
          err.message || "Payment could not be processed. You can safely retry without double-debiting."
        );
      }
      setIsPinModalOpen(false);
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartNewPayment = () => {
    setReceiver("");
    setAmount("");
    setPaymentSuccess(null);
    setPaymentError("");
    idempotencyManager.resetKey();
  };

  const selectedBank = accounts.find((a) => String(a.account_id) === String(selectedAccountId));

  if (loadingAccounts) {
    return <Spinner text="Loading payment options..." />;
  }

  if (accounts.length === 0) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "48px 20px" }}>
        <div style={{ fontSize: "40px", marginBottom: "12px" }}>⚠️</div>
        <h3 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "8px" }}>
          No Bank Account Available
        </h3>
        <p style={{ color: "var(--color-text-muted)", fontSize: "14px", maxWidth: "420px", margin: "0 auto 20px" }}>
          You need at least one linked bank account to transfer money via UPI.
        </p>
        <Button variant="primary" onClick={() => onNavigate("accounts")}>
          Link Bank Account
        </Button>
      </div>
    );
  }

  if (paymentSuccess) {
    return (
      <div style={{ maxWidth: "520px", margin: "0 auto" }}>
        <div
          className="card"
          style={{
            textAlign: "center",
            padding: "40px 28px",
            borderTop: "6px solid var(--color-success)",
          }}
        >
          <div
            style={{
              width: "72px",
              height: "72px",
              borderRadius: "50%",
              backgroundColor: "var(--color-success-bg)",
              color: "var(--color-success)",
              fontSize: "36px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
              border: "1px solid var(--color-success-border)",
            }}
          >
            ✓
          </div>

          <span className="badge badge-success" style={{ marginBottom: "12px" }}>
            Payment Successful
          </span>

          <h2 style={{ fontSize: "38px", fontWeight: "800", color: "var(--color-text-main)", margin: "8px 0" }}>
            {formatCurrency(paymentSuccess.amount)}
          </h2>

          <p style={{ color: "var(--color-text-muted)", fontSize: "14px", marginBottom: "24px" }}>
            Sent successfully to <strong>{paymentSuccess.receiver}</strong>
          </p>

          <div
            style={{
              background: "#f8fafc",
              borderRadius: "var(--radius-md)",
              padding: "16px",
              border: "1px solid var(--color-border)",
              textAlign: "left",
              fontSize: "13px",
              marginBottom: "28px",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--color-text-muted)" }}>Transaction ID:</span>
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: "600" }}>
                {paymentSuccess.transaction_id}
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--color-text-muted)" }}>Date & Time:</span>
              <span>{formatDate(paymentSuccess.created_at)}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--color-text-muted)" }}>Payment Method:</span>
              <span>UPI (P2P Transfer)</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--color-text-muted)" }}>Debited From:</span>
              <span>{selectedBank?.bank_name} Bank ({selectedBank?.masked_account_number})</span>
            </div>
          </div>

          <div style={{ display: "flex", gap: "12px" }}>
            <Button variant="secondary" block onClick={() => onNavigate("transactions")}>
              View History
            </Button>
            <Button variant="primary" block onClick={handleStartNewPayment}>
              Send Another
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: "540px", margin: "0 auto" }}>
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Send Money via UPI</h2>
            <p style={{ color: "var(--color-text-muted)", fontSize: "13px", marginTop: "2px" }}>
              Instant transfer to any UPI ID or phone number
            </p>
          </div>
        </div>

        {paymentError && (
          <Alert variant="danger" onClose={() => setPaymentError("")}>
            {paymentError}
          </Alert>
        )}

        <form onSubmit={handleReviewPayment}>
          <Input
            label="Recipient UPI ID or Mobile Number"
            type="text"
            placeholder="e.g. rahul@securepay or 9876543210"
            value={receiver}
            onChange={(e) => {
              setReceiver(e.target.value);
              if (errors.receiver) setErrors((prev) => ({ ...prev, receiver: null }));
            }}
            error={errors.receiver}
            hint="Supports 10-digit mobile or username@securepay"
          />

          <Input
            label="Amount (in Rupees)"
            type="number"
            placeholder="₹ 0"
            min={1}
            step={1}
            value={amount}
            onChange={(e) => {
              setAmount(e.target.value);
              if (errors.amount) setErrors((prev) => ({ ...prev, amount: null }));
            }}
            error={errors.amount}
          />

          <div className="form-group">
            <label className="form-label">Pay From Bank Account</label>
            <select
              className="form-input"
              value={selectedAccountId}
              onChange={(e) => setSelectedAccountId(e.target.value)}
            >
              {accounts.map((acc) => (
                <option key={acc.account_id} value={acc.account_id}>
                  {acc.bank_name} Bank ({acc.masked_account_number})
                  {acc.is_primary ? " — Primary" : ""}
                </option>
              ))}
            </select>
            {errors.account && <span className="form-error">{errors.account}</span>}
          </div>

          <div style={{ marginTop: "28px" }}>
            <Button
              type="submit"
              variant="primary"
              block
              size="lg"
              disabled={submitting}
            >
              Proceed to Pay
            </Button>
          </div>
        </form>
      </div>

      {isPinModalOpen && (
        <PinModal
          isOpen={isPinModalOpen}
          onClose={() => setIsPinModalOpen(false)}
          amount={Number(amount)}
          receiver={receiver}
          bankName={selectedBank?.bank_name}
          onSubmit={handleExecutePayment}
          loading={submitting}
        />
      )}
    </div>
  );
}
