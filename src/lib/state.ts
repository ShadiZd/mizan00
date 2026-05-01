/* state.ts — single source of truth for client-side data.
 *
 * Components subscribe via the `useStateSlice` hook. When `setState` is
 * called, all subscribers re-render — so when api.ts swaps mock data for
 * real responses, every UI surface updates with zero rewiring.
 */
import { useEffect, useState } from "react";
import type {
  User,
  Transaction,
  SavingsConfig,
  Contract,
  InvestmentSuggestion,
} from "./mockData";

export type AppState = {
  user: User | null;
  balance: number | null;
  transactions: Transaction[];
  savings: SavingsConfig | null;
  contract: Contract | null;
  investments: InvestmentSuggestion[];
  nudgeCount: Record<string, number>;
  isLoading: boolean;
  error: string | null;
};

export const state: AppState = {
  user: null,
  balance: null,
  transactions: [],
  savings: null,
  contract: null,
  investments: [],
  nudgeCount: {},
  isLoading: false,
  error: null,
};

const EVENT = "stateChange";

export function setState<K extends keyof AppState>(key: K, value: AppState[K]) {
  state[key] = value;
  if (typeof document !== "undefined") {
    document.dispatchEvent(new CustomEvent(EVENT, { detail: { key, value } }));
  }
}

/* Subscribe a component to one key; returns the live value. */
export function useStateSlice<K extends keyof AppState>(key: K): AppState[K] {
  const [value, setValue] = useState<AppState[K]>(state[key]);
  useEffect(() => {
    function onChange(e: Event) {
      const detail = (e as CustomEvent<{ key: keyof AppState; value: unknown }>).detail;
      if (detail.key === key) setValue(detail.value as AppState[K]);
    }
    document.addEventListener(EVENT, onChange);
    return () => document.removeEventListener(EVENT, onChange);
  }, [key]);
  return value;
}
