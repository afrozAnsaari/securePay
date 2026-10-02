/**
 * SecurePay Idempotency Key Generator & Manager
 * Generates standards-compliant UUIDv4 keys and allows reusing
 * the same key across network retries of the exact same payment attempt.
 */

export function generateIdempotencyKey() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // Fallback RFC4122 compliant UUID v4
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Creates an idempotency tracker for a payment session.
 * Reuses the existing key on retry until explicitly reset for a new payment.
 */
export function createIdempotencyManager() {
  let currentKey = null;

  return {
    getKey: () => {
      if (!currentKey) {
        currentKey = generateIdempotencyKey();
      }
      return currentKey;
    },
    resetKey: () => {
      currentKey = generateIdempotencyKey();
      return currentKey;
    },
    clear: () => {
      currentKey = null;
    },
  };
}
