import { api } from "./client";

export const paymentsApi = {
  /**
   * Check if current user has an active UPI profile
   */
  async getUPIProfile() {
    return api.get("/upi/get-profile");
  },

  /**
   * Create an initial UPI profile (@securepay) and set UPI PIN
   */
  async createUPIProfile({ upi_id, upi_pin }) {
    return api.post("/upi/create-profile", {
      upi_id,
      upi_pin,
    });
  },

  /**
   * Initiate a UPI payment with a mandatory Idempotency-Key
   */
  async makePayment(
    {
      receiver,
      sender_upi_profile_id,
      sender_account_id,
      amount,
      upi_pin,
    },
    idempotencyKey
  ) {
    if (!idempotencyKey) {
      throw new Error("Idempotency key is required to make a payment.");
    }

    return api.post(
      "/upi/pay",
      {
        receiver,
        sender_upi_profile_id: Number(sender_upi_profile_id),
        sender_account_id: Number(sender_account_id),
        amount: Math.round(Number(amount)),
        upi_pin,
      },
      {
        headers: {
          "Idempotency-Key": idempotencyKey,
        },
      }
    );
  },
};
