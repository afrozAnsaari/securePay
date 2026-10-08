import { useState } from "react";
import { useAuth } from "../context/useAuth";
import {
  validateMobile,
  validateEmail,
  validatePassword,
} from "../utils/validators";
import { Input } from "../components/common/Input";
import { Button } from "../components/common/Button";
import { Alert } from "../components/common/Feedback";
import { PasswordToggle } from "../components/common/PasswordToggle";

export function Register({ onNavigate }) {
  const { register, login } = useAuth();
  const [name, setName] = useState("");
  const [mobileNo, setMobileNo] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError("");
    setSuccessMsg("");

    const newErrors = {};
    if (!name.trim()) newErrors.name = "Full name is required.";
    const mobileErr = validateMobile(mobileNo);
    if (mobileErr) newErrors.mobileNo = mobileErr;
    const emailErr = validateEmail(email);
    if (emailErr) newErrors.email = emailErr;
    const passErr = validatePassword(password);
    if (passErr) newErrors.password = passErr;

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setLoading(true);

    try {
      await register({
        name: name.trim(),
        mobile_no: mobileNo.trim(),
        email: email.trim(),
        password,
      });

      setSuccessMsg("Account created successfully! Logging you in...");

      // Automatically sign in the user
      await login({
        mobile_no: mobileNo.trim(),
        password,
      });

      setTimeout(() => {
        onNavigate("dashboard");
      }, 600);
    } catch (err) {
      setApiError(err.message || "Registration failed. Please check your information.");
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
        backgroundImage: "radial-gradient(circle at 50% 20%, rgba(37, 99, 235, 0.15) 0%, transparent 60%)",
      }}
    >
      <div
        className="card"
        style={{
          width: "100%",
          maxWidth: "460px",
          padding: "36px 32px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.4)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          backgroundColor: "#ffffff",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "24px" }}>
          <div
            className="brand-logo-badge"
            style={{
              margin: "0 auto 14px",
              width: "48px",
              height: "48px",
              fontSize: "24px",
            }}
          >
            ₹
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: "700", color: "#0f172a" }}>
            Register on SecurePay
          </h2>
          <p style={{ color: "#64748b", fontSize: "14px", marginTop: "4px" }}>
            Fast, secure UPI payments backed by neural fraud detection
          </p>
        </div>

        {apiError && (
          <Alert variant="danger" onClose={() => setApiError("")}>
            {apiError}
          </Alert>
        )}

        {successMsg && <Alert variant="success">{successMsg}</Alert>}

        <form onSubmit={handleSubmit}>
          <Input
            label="Full Name"
            placeholder="e.g. Rahul Sharma"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              if (errors.name) setErrors((prev) => ({ ...prev, name: null }));
            }}
            error={errors.name}
          />

          <Input
            label="Mobile Number"
            type="tel"
            placeholder="10-digit number"
            maxLength={10}
            value={mobileNo}
            onChange={(e) => {
              const val = e.target.value.replace(/\D/g, "").slice(0, 10);
              setMobileNo(val);
              if (errors.mobileNo) setErrors((prev) => ({ ...prev, mobileNo: null }));
            }}
            error={errors.mobileNo}
            hint="Must be a valid 10-digit mobile number"
          />

          <Input
            label="Email Address"
            type="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (errors.email) setErrors((prev) => ({ ...prev, email: null }));
            }}
            error={errors.email}
          />

          <Input
            label="Password"
            type={showPassword ? "text" : "password"}
            placeholder="At least 6 characters"
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
              Create Account
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
          Already registered?{" "}
          <button
            type="button"
            onClick={() => onNavigate("login")}
            style={{
              background: "none",
              border: "none",
              color: "var(--color-primary)",
              fontWeight: "600",
              cursor: "pointer",
              padding: 0,
            }}
          >
            Sign In Here
          </button>
        </div>
      </div>
    </div>
  );
}
