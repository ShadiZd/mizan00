// ── Auth ──────────────────────────────────
export interface RegisterResponse {
  user_id: string
  name: string
  email: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

// ── Classify ──────────────────────────────
export interface ClassifyResponse {
  category: string
  confidence: number
  source: string
  should_intercept: boolean
  nudge_type: string | null
  nudge_message: string
  real_cost_hours: number | null
  flags: string[]
}

// ── Transaction Pipeline ──────────────────
export interface NudgeOut {
  nudge_type: string
  title: string
  message: string
  severity: "warning" | "critical"
  cta: string
  source: string
  progress: {
    spent: number
    limit: number
    remaining: number
    pct_used: number
    currency: string
  } | null
  contract_context: {
    id: string
    category: string
    period_start: string
    period_end: string
  } | null
  roundup_amount: number
  roundup_message: string | null
}

export interface ViolationOut {
  contract_id: string
  triggering_tx_id: string
  overage_amount: number
  penalty_amount: number
}

export interface ProcessTransactionResponse {
  transaction_id: string
  category: string
  confidence: number
  classification_source: string
  real_cost_hours: number | null
  flags: string[]
  should_intercept: boolean
  nudge: NudgeOut | null
  contract_state: string | null
  total_spent: number | null
  violation: ViolationOut | null
  penalty_amount: number
  roundup_amount: number
  roundup_message: string | null
  investment_nudge: Record<string, unknown> | null
}

// ── Contracts ─────────────────────────────
export interface ContractIn {
  contract_id: string
  user_id: string
  category: string
  monthly_limit: number
  penalty_rate: number
  penalty_bucket_id: string
  period_start: string
  period_end: string
  currency?: string
}

export interface TransactionHistoryItem {
  transaction_id: string
  amount: number
  category: string
  occurred_at: string
}

// ── Investments ───────────────────────────
export interface Platform {
  name: string
  description: string
  min_investment_sar: number
  risk_levels: string[]
  regions: string[]
  shariah_compliant: boolean
  asset_types: string[]
  app_store_url: string
  deep_link: string
}

export interface RecommendationItem {
  rank: number
  platform: string
  score: number
  recommendation_reason: string
  suggested_amount_sar: number
  urgency: string
  app_store_url: string
  deep_link: string
  asset_types: string[]
  min_investment_sar: number
}

export interface RecommendResponse {
  recommendations: RecommendationItem[]
  total_available_to_invest: number
  suggested_keep_as_emergency: number
  suggested_invest: number
}

export interface InvestmentSuggestion {
  title: string
  rationale: string
  risk_level: string
  expected_return_pct: number
}

// ── API Class ─────────────────────────────
const BASE_URL = import.meta.env.VITE_API_URL ?? "https://clammy-stank-whenever.ngrok-free.dev"
const TOKEN_KEY = "mizan_token"

class MizanAPI {
  private getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  }

  private saveToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
  }

  private removeToken(): void {
    localStorage.removeItem(TOKEN_KEY)
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T | null> {
    const token = this.getToken()
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    }
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
    try {
      const res = await fetch(`${BASE_URL}${path}`, {
        ...options,
        headers,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        console.error(`Mizan API error ${res.status}:`, err)
        return null
      }
      return res.json() as Promise<T>
    } catch (e) {
      console.error("Mizan API network error:", e)
      return null
    }
  }

  async healthCheck(): Promise<boolean> {
    const result = await this.request<{ status: string }>("/health")
    return result?.status === "ok"
  }

  async register(
    name: string,
    email: string,
    password: string
  ): Promise<RegisterResponse | null> {
    return this.request<RegisterResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    })
  }

  async login(
    email: string,
    password: string
  ): Promise<TokenResponse | null> {
    const result = await this.request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    if (result?.access_token) {
      this.saveToken(result.access_token)
    }
    return result
  }

  logout(): void {
    this.removeToken()
  }

  isAuthenticated(): boolean {
    return !!this.getToken()
  }

  async processTransaction(params: {
    transaction_id: string
    description: string
    amount: number
    occurred_at: string
    hourly_wage?: number
    use_ai?: boolean
    contract?: ContractIn | null
    transaction_history?: TransactionHistoryItem[]
    total_saved?: number
    risk_level?: string
    region?: string
    shariah_preference?: boolean
    monthly_savings_rate?: number
  }): Promise<ProcessTransactionResponse | null> {
    return this.request<ProcessTransactionResponse>("/transaction", {
      method: "POST",
      body: JSON.stringify({
        use_ai: false,
        region: "SA",
        shariah_preference: false,
        monthly_savings_rate: 0,
        transaction_history: [],
        ...params,
      }),
    })
  }

  async classifyTransaction(
    description: string,
    amount: number,
    hourly_wage?: number
  ): Promise<ClassifyResponse | null> {
    return this.request<ClassifyResponse>("/classify", {
      method: "POST",
      body: JSON.stringify({ description, amount, hourly_wage, use_ai: false }),
    })
  }

  async getRecommendations(params: {
    user_id: string
    risk_level: string
    region?: string
    shariah_preference?: boolean
    total_saved: number
    monthly_savings_rate?: number
  }): Promise<RecommendResponse | null> {
    return this.request<RecommendResponse>("/recommend-investments", {
      method: "POST",
      body: JSON.stringify({
        region: "SA",
        shariah_preference: false,
        monthly_savings_rate: 0,
        ...params,
      }),
    })
  }

  async getPlatforms(): Promise<Platform[]> {
    const result = await this.request<Platform[]>("/platforms")
    return result ?? []
  }

  async trackReferral(
    user_id: string,
    platform_name: string,
    suggested_amount: number,
    action: "recommendation_shown" | "app_opened" | "invested" = "app_opened"
  ): Promise<void> {
    await this.request("/track-referral", {
      method: "POST",
      body: JSON.stringify({ user_id, platform_name, suggested_amount, action }),
    })
  }

  async getInvestmentSuggestions(
    user_id: string
  ): Promise<InvestmentSuggestion[] | null> {
    const result = await this.request<{
      suggestions: InvestmentSuggestion[]
    }>(`/investment-suggestions/${user_id}`)
    return result?.suggestions ?? null
  }
}

export const mizanAPI = new MizanAPI()

// ── Legacy mock exports — keeps existing demo components working ──────────────
import {
  mockUser,
  mockBalance,
  mockTransactions,
  mockSavings,
  mockContract,
  type User,
  type Transaction,
  type SavingsConfig,
  type Contract,
} from "./mockData"

function _delay<T>(value: T): Promise<T> {
  const ms = 200 + Math.random() * 400
  return new Promise((res) => setTimeout(() => res(value), ms))
}

export type NudgeDecision = "confirm" | "delay" | "cancel"
export const getUser = async (): Promise<User> => _delay(mockUser)
export const getUserBalance = async (): Promise<number> => _delay(mockBalance)
export const getSavingsTotal = async (): Promise<SavingsConfig> => _delay(mockSavings)
export const getSpendingContracts = async (): Promise<Contract> => _delay(mockContract)
export const getTransactions = async (): Promise<Transaction[]> => _delay(mockTransactions)
export const postNudgeDecision = async (
  decision: NudgeDecision
): Promise<{ ok: true; decision: NudgeDecision }> => _delay({ ok: true, decision })
export const postSavingsConfig = async (
  _percent: number,
  _frequency: SavingsConfig["frequency"]
): Promise<{ ok: true }> => _delay({ ok: true })
export const postContractSetup = async (
  _cap: number,
  _penalty: number
): Promise<{ ok: true }> => _delay({ ok: true })
export const exportUserData = async (): Promise<{ ok: true; filename: string }> =>
  _delay({ ok: true, filename: "mizan-export.json" })
