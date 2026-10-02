import { api } from "./client";

export const transactionsApi = {
  /**
   * Fetch paginated transactions for the current user
   */
  async getTransactions({ limit = 20, offset = 0 } = {}) {
    return api.get(`/upi/transactions?limit=${limit}&offset=${offset}`);
  },

  /**
   * Fetch a single transaction's details by its transaction ID (UUID)
   */
  async getTransactionById(transactionId) {
    if (!transactionId) throw new Error("Transaction ID is required");
    return api.get(`/upi/transactions/${encodeURIComponent(transactionId)}`);
  },
};
