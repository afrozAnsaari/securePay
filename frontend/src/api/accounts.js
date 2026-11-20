import { api } from "./client";

export const accountsApi = {
  /**
   * Fetch all linked bank accounts for current user
   */
  async getLinkedAccounts() {
    return api.get("/upi/accounts/linked");
  },

  /**
   * Check balance of a specific linked account with verified UPI PIN
   */
  async getBalance({ upi_profile_id, account_id, upi_pin }) {
    return api.post("/accounts/get-balance", {
      upi_profile_id,
      account_id,
      upi_pin,
    });
  },

  /**
   * Link a new bank account by validating debit card details
   */
  async linkBankAccount({
    bank_name,
    card_number,
    expiry_month,
    expiry_year,
    card_pin,
  }) {
    return api.post("/upi/link-bank", {
      bank_name,
      card_number,
      expiry_month: Number(expiry_month),
      expiry_year: Number(expiry_year),
      card_pin,
    });
  },

  /**
   * Discover bank accounts registered to the logged-in user's mobile number
   */
  async discoverAccounts() {
    return api.post("/discover-accounts");
  },
};
