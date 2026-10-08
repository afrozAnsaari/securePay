/**
 * SecurePay Form & Data Validators
 * Matches FastAPI / Pydantic schema validation rules.
 */

export const PHONE_REGEX = /^[0-9]{10}$/;
export const UPI_ID_SUFFIX = "@securepay";
export const UPI_USERNAME_REGEX = /^[a-z](?:[a-z0-9]|[_.(?!_.)](?![_.]))*[a-z0-9]$/i;

export function validateMobile(mobile) {
  if (!mobile || typeof mobile !== "string") {
    return "Mobile number is required.";
  }
  const cleaned = mobile.trim();
  if (!PHONE_REGEX.test(cleaned)) {
    return "Mobile number must be exactly 10 digits.";
  }
  return null;
}

export function validateEmail(email) {
  if (!email || typeof email !== "string") {
    return "Email address is required.";
  }
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!re.test(email.trim())) {
    return "Please enter a valid email address.";
  }
  return null;
}

export function validatePassword(password) {
  if (!password || typeof password !== "string") {
    return "Password is required.";
  }
  if (password.length < 4 || password.length > 6) {
    return "Password must be at least 4-6 characters long.";
  }
  return null;
}

export function validateUpiPin(pin) {
  if (!pin || typeof pin !== "string") {
    return "UPI PIN is required.";
  }
  const cleaned = pin.trim();
  if (!/^\d+$/.test(cleaned) || cleaned.length < 4 || cleaned.length > 6) {
    return "UPI PIN must be 4 to 6 digits.";
  }
  return null;
}

export function validateCardPin(pin) {
  if (!pin || typeof pin !== "string") {
    return "Card ATM PIN is required.";
  }
  const cleaned = pin.trim();
  if (!/^\d+$/.test(cleaned) || cleaned.length < 4 || cleaned.length > 6) {
    return "Card PIN must be 4 to 6 digits.";
  }
  return null;
}

export function validateCardNumber(cardNumber) {
  if (!cardNumber) return "Card number is required.";
  const cleaned = cardNumber.replace(/[\s-]/g, "");
  if (!/^\d{16}$/.test(cleaned)) {
    return "Card number must be exactly 16 digits.";
  }
  return null;
}

export function validateCardExpiry(month, year) {
  const m = Number(month);
  const y = Number(year);
  if (!m || m < 1 || m > 12) {
    return "Valid expiry month (1-12) is required.";
  }
  if (!y || y < 2024 || y > 2099) {
    return "Valid 4-digit expiry year is required.";
  }
  return null;
}

export function validateAmount(amount) {
  const num = Number(amount);
  if (isNaN(num) || num <= 0) {
    return "Amount must be a positive integer greater than ₹0.";
  }
  if (!Number.isInteger(num)) {
    return "Amount must be a whole number in rupees.";
  }
  return null;
}

export function validateReceiver(receiver) {
  if (!receiver || typeof receiver !== "string") {
    return "Receiver UPI ID or 10-digit mobile is required.";
  }
  const trimmed = receiver.trim().toLowerCase();
  if (/^[6-9]\d{9}$/.test(trimmed)) {
    return null; // Valid mobile number
  }

  let username = trimmed;
  if (trimmed.endsWith(UPI_ID_SUFFIX)) {
    username = trimmed.slice(0, -UPI_ID_SUFFIX.length);
  } else if (trimmed.includes("@")) {
    return "Invalid handle. Only @securepay is supported.";
  }

  if (!username) {
    return "UPI ID username cannot be empty.";
  }
  if (username.length > 16) {
    return "UPI ID username cannot be more than 16 characters.";
  }
  if (!/^[a-z]/.test(username)) {
    return "UPI ID must start with a letter.";
  }
  if (/[._]{2,}/.test(username)) {
    return "UPI ID cannot contain consecutive '.' or '_'.";
  }
  if (/[._]$/.test(username)) {
    return "UPI ID cannot end with '.' or '_'.";
  }
  return null;
}
