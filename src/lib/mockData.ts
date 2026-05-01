/* mockData.ts — realistic Mizan fixtures.
 * Replace by real API responses later; shape is the contract.
 */

export type User = {
  id: string;
  name: string;
  monthlySalary: number;
  hourlyRate: number;
};

export type Transaction = {
  id: string;
  label: string;
  category: "Food" | "Shopping" | "Transit" | "Bills" | "Entertainment";
  amount: number;
  timestamp: string; // ISO
  balanceAfter: number;
};

export type SavingsConfig = {
  bucketTotal: number;
  percent: number;
  frequency: "daily" | "weekly" | "per-tx";
};

export type Contract = {
  cap: number;
  penalty: number;
  spentThisMonth: number;
  penaltyConfirmed: boolean;
};

export type InvestmentSuggestion = {
  id: string;
  type: string;
  why: string;
  expectedReturn: string;
};

export const mockUser: User = {
  id: "u_001",
  name: "Layla",
  monthlySalary: 5120,
  hourlyRate: 32,
};

export const mockBalance = 2400;

export const mockTransactions: Transaction[] = [
  { id: "t1", label: "Coffee", category: "Food", amount: 4.3, timestamp: "2026-04-30T08:14:00Z", balanceAfter: 2395.7 },
  { id: "t2", label: "Lunch", category: "Food", amount: 11.75, timestamp: "2026-04-30T12:42:00Z", balanceAfter: 2383.95 },
  { id: "t3", label: "Bookshop", category: "Shopping", amount: 22.1, timestamp: "2026-04-29T18:01:00Z", balanceAfter: 2361.85 },
  { id: "t4", label: "Bus fare", category: "Transit", amount: 2.4, timestamp: "2026-04-29T08:30:00Z", balanceAfter: 2359.45 },
  { id: "t5", label: "Subway", category: "Transit", amount: 0.6, timestamp: "2026-04-28T19:50:00Z", balanceAfter: 2358.85 },
  { id: "t6", label: "Groceries", category: "Food", amount: 38.25, timestamp: "2026-04-28T17:10:00Z", balanceAfter: 2320.6 },
  { id: "t7", label: "Streaming", category: "Entertainment", amount: 9.99, timestamp: "2026-04-27T09:00:00Z", balanceAfter: 2310.61 },
  { id: "t8", label: "Sneakers", category: "Shopping", amount: 84.0, timestamp: "2026-04-26T15:24:00Z", balanceAfter: 2226.61 },
  { id: "t9", label: "Phone bill", category: "Bills", amount: 35.0, timestamp: "2026-04-25T10:00:00Z", balanceAfter: 2191.61 },
  { id: "t10", label: "Cinema", category: "Entertainment", amount: 14.5, timestamp: "2026-04-24T20:30:00Z", balanceAfter: 2177.11 },
];

export const mockSavings: SavingsConfig = {
  bucketTotal: 286.4,
  percent: 5,
  frequency: "weekly",
};

export const mockContract: Contract = {
  cap: 800,
  penalty: 40,
  spentThisMonth: 620,
  penaltyConfirmed: true,
};

export const mockInvestments: InvestmentSuggestion[] = [
  {
    id: "i1",
    type: "Low-Risk Index Fund",
    why: "Based on your steady 12% monthly savings rate.",
    expectedReturn: "~7% / year · roughly $84 on your current savings",
  },
  {
    id: "i2",
    type: "Short-Term Bond ETF",
    why: "Fits your low-volatility preference.",
    expectedReturn: "~4% / year · roughly $48",
  },
  {
    id: "i3",
    type: "Diversified Equity",
    why: "Matches your 18-month horizon.",
    expectedReturn: "~9% / year · roughly $108",
  },
];
