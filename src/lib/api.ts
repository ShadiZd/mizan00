/* api.ts — THE ONLY file allowed to make backend HTTP calls.
 *
 * Every function below is currently a MOCK that resolves with fixtures
 * after a short, realistic latency. To go live, swap each function body
 * for a real `fetch(`${API_BASE}/...`)` call. No other file changes needed.
 */

import {
  mockUser,
  mockBalance,
  mockTransactions,
  mockSavings,
  mockContract,
  mockInvestments,
  type User,
  type Transaction,
  type SavingsConfig,
  type Contract,
  type InvestmentSuggestion,
} from "./mockData";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const API_BASE = "http://localhost:3000"; // swap to production URL later

/* Realistic latency band so loading skeletons are visible. */
function latency() {
  return 200 + Math.random() * 400;
}
function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), latency()));
}

/* ─────────────── GET ─────────────── */

// MOCK — replace with real endpoint: GET /me
export const getUser = async (): Promise<User> => delay(mockUser);

// MOCK — replace with real endpoint: GET /balance
export const getUserBalance = async (): Promise<number> => delay(mockBalance);

// MOCK — replace with real endpoint: GET /savings/total
export const getSavingsTotal = async (): Promise<SavingsConfig> => delay(mockSavings);

// MOCK — replace with real endpoint: GET /contracts
export const getSpendingContracts = async (): Promise<Contract> => delay(mockContract);

// MOCK — replace with real endpoint: GET /transactions
export const getTransactions = async (): Promise<Transaction[]> => delay(mockTransactions);

// MOCK — replace with real endpoint: GET /investments/suggestions
export const getInvestmentSuggestions = async (): Promise<InvestmentSuggestion[]> =>
  delay(mockInvestments);

/* ─────────────── POST ─────────────── */

export type NudgeDecision = "confirm" | "delay" | "cancel";

// MOCK — replace with real endpoint: POST /nudges/decision
export const postNudgeDecision = async (
  decision: NudgeDecision
): Promise<{ ok: true; decision: NudgeDecision }> => delay({ ok: true, decision });

// MOCK — replace with real endpoint: POST /savings/config
export const postSavingsConfig = async (
  percent: number,
  frequency: SavingsConfig["frequency"]
): Promise<{ ok: true }> => {
  void percent;
  void frequency;
  return delay({ ok: true });
};

// MOCK — replace with real endpoint: POST /contracts
export const postContractSetup = async (
  cap: number,
  penalty: number
): Promise<{ ok: true }> => {
  void cap;
  void penalty;
  return delay({ ok: true });
};

// MOCK — replace with real endpoint: POST /privacy/export
export const exportUserData = async (): Promise<{ ok: true; filename: string }> =>
  delay({ ok: true, filename: "mizan-export.json" });
