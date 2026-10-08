import { useState } from "react";
import { useAuth } from "../context/useAuth";
import { validateMobile, validatePassword } from "../utils/validators";
import { Input } from "../components/common/Input";
import { Button } from "../components/common/Button";
import { Alert } from "../components/common/Feedback";
import { PasswordToggle } from "../components/common/PasswordToggle";

export function Login({ onNavigate }) {
  const { login } = useAuth();
  const [mobileNo, setMobileNo] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError("");

    const mobileErr = validateMobile(mobileNo);
    const passErr = validatePassword(password);

    if (mobileErr || passErr) {
      setErrors({
        mobileNo: mobileErr,
        password: passErr,
      });
      return;
    }

    setErrors({});
    setLoading(true);

    try {
      await login({
        mobile_no: mobileNo.trim(),
        password,
      });
      onNavigate("dashboard");
    } catch (err) {
      setApiError(err.message || "Failed to log in. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#0a1128",
        padding: "20px",
        backgroundImage: "radial-gradient(circle at 50% 20%, rgba(2, 132, 199, 0.15) 0%, transparent 60%)",
      }}
    >
      <div
        className="card"
        style={{
          width: "100%",
          maxWidth: "420px",
          padding: "36px 32px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.4)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          backgroundColor: "#ffffff",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div
            className="brand-logo-badge"
            style={{
              margin: "0 auto 16px",
              width: "48px",
              height: "48px",
              fontSize: "24px",
            }}
          >
            ₹
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: "700", color: "#0f172a" }}>
            Welcome to SecurePay
          </h2>
          <p style={{ color: "#64748b", fontSize: "14px", marginTop: "4px" }}>
            Login with your registered 10-digit mobile number
          </p>
        </div>

        {apiError && (
          <Alert variant="danger" onClose={() => setApiError("")}>
            {apiError}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Input
            label="Mobile Number"
            type="tel"
            placeholder="e.g. 9876543210"
            maxLength={10}
            value={mobileNo}
            onChange={(e) => {
              const val = e.target.value.replace(/\D/g, "").slice(0, 10);
              setMobileNo(val);
              if (errors.mobileNo) setErrors((prev) => ({ ...prev, mobileNo: null }));
            }}
            error={errors.mobileNo}
            hint="10-digit Indian phone number"
            autoFocus
          />

          <Input
            label="Password"
            type={showPassword ? "text" : "password"}
            placeholder="••••••••"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (errors.password) setErrors((prev) => ({ ...prev, password: null }));
            }}
            error={errors.password}
            rightElement={
              <PasswordToggle
                isVisible={showPassword}
                onToggle={() => setShowPassword((prev) => !prev)}
              />
            }
          />

          <div style={{ marginTop: "24px" }}>
            <Button
              type="submit"
              variant="primary"
              block
              size="lg"
              loading={loading}
            >
              Sign In
            </Button>
          </div>
        </form>

        <div
          style={{
            marginTop: "24px",
            textAlign: "center",
            fontSize: "13px",
            color: "#64748b",
            borderTop: "1px solid #f1f5f9",
            paddingTop: "20px",
          }}
        >
          Don't have an account?{" "}
          <button
            type="button"
            onClick={() => onNavigate("register")}
            style={{
              background: "none",
              border: "none",
              color: "var(--color-primary)",
              fontWeight: "600",
              cursor: "pointer",
              padding: 0,
            }}
          >
            Create an Account
          </button>
        </div>
      </div>
    </div>
  );
}
