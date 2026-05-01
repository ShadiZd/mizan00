import { useState, useEffect, useCallback } from "react"
import { mizanAPI } from "@/lib/api"
import type {
  ProcessTransactionResponse,
  Platform,
  RecommendResponse,
  ContractIn,
  TransactionHistoryItem,
} from "@/lib/api"

// ── Mock fallbacks ────────────────────────────────────────────────────────────
const MOCK_SAFE_RESULT: ProcessTransactionResponse = {
  transaction_id: "mock-tx",
  category: "food",
  confidence: 1.0,
  classification_source: "mock",
  real_cost_hours: null,
  flags: [],
  should_intercept: false,
  nudge: null,
  contract_state: "safe",
  total_spent: 0,
  violation: null,
  penalty_amount: 0,
  roundup_amount: 0,
  roundup_message: null,
  investment_nudge: null,
}

function getMockNudge(amount: number): ProcessTransactionResponse {
  if (amount > 400) {
    return {
      ...MOCK_SAFE_RESULT,
      should_intercept: true,
      contract_state: "exceeded",
      nudge: {
        nudge_type: "budget_exceeded",
        title: "Your limit has been reached.",
        message: `You've gone ${(amount - 400).toFixed(2)} SAR over your budget.`,
        severity: "critical",
        cta: "See what was saved",
        source: "mock",
        progress: {
          spent: amount,
          limit: 400,
          remaining: 0,
          pct_used: 100,
          currency: "SAR",
        },
        contract_context: null,
        roundup_amount: 0,
        roundup_message: null,
      },
    }
  }
  if (amount > 100) {
    return {
      ...MOCK_SAFE_RESULT,
      should_intercept: true,
      contract_state: "warning",
      nudge: {
        nudge_type: "budget_warning",
        title: "You're almost there.",
        message: `You've used ${Math.round((amount / 400) * 100)}% of your budget.`,
        severity: "warning",
        cta: "View my contract",
        source: "mock",
        progress: {
          spent: amount,
          limit: 400,
          remaining: 400 - amount,
          pct_used: (amount / 400) * 100,
          currency: "SAR",
        },
        contract_context: null,
        roundup_amount: 0,
        roundup_message: null,
      },
    }
  }
  return MOCK_SAFE_RESULT
}

const MOCK_PLATFORMS: Platform[] = [
  {
    name: "Wahed Invest",
    description: "Shariah-compliant halal investing",
    min_investment_sar: 100,
    risk_levels: ["low", "medium"],
    regions: ["SA", "AE", "global"],
    shariah_compliant: true,
    asset_types: ["ETFs", "sukuk", "gold"],
    app_store_url: "https://wahed.com",
    deep_link: "wahed://invest",
  },
  {
    name: "Aghaz Invest",
    description: "Saudi micro-investing made simple",
    min_investment_sar: 10,
    risk_levels: ["low", "medium"],
    regions: ["SA"],
    shariah_compliant: true,
    asset_types: ["mutual funds", "sukuk"],
    app_store_url: "https://aghazinvest.com",
    deep_link: "aghaz://invest",
  },
  {
    name: "Nester",
    description: "Fractional real estate investment",
    min_investment_sar: 1000,
    risk_levels: ["medium", "high"],
    regions: ["SA", "AE"],
    shariah_compliant: true,
    asset_types: ["real estate", "REITs"],
    app_store_url: "https://nester.sa",
    deep_link: "nester://invest",
  },
  {
    name: "Sarwa",
    description: "Automated low-fee investing",
    min_investment_sar: 500,
    risk_levels: ["low", "medium", "high"],
    regions: ["AE", "global"],
    shariah_compliant: false,
    asset_types: ["ETFs", "stocks", "bonds"],
    app_store_url: "https://sarwa.co",
    deep_link: "sarwa://invest",
  },
  {
    name: "Baraka",
    description: "US stocks and ETFs",
    min_investment_sar: 50,
    risk_levels: ["medium", "high"],
    regions: ["AE", "global"],
    shariah_compliant: false,
    asset_types: ["US stocks", "ETFs"],
    app_store_url: "https://getbaraka.com",
    deep_link: "baraka://invest",
  },
  {
    name: "Sharia Portfolio Global",
    description: "Globally diversified halal portfolios",
    min_investment_sar: 200,
    risk_levels: ["low", "medium", "high"],
    regions: ["SA", "global"],
    shariah_compliant: true,
    asset_types: ["global ETFs", "sukuk"],
    app_store_url: "https://shariaportfolio.com",
    deep_link: "shariaportfolio://invest",
  },
]

// ── Hook ──────────────────────────────────────────────────────────────────────
export function useMizan() {
  const [isBackendOnline, setIsBackendOnline] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(
    mizanAPI.isAuthenticated()
  )

  useEffect(() => {
    mizanAPI.healthCheck().then(setIsBackendOnline)
  }, [])

  const processTransaction = useCallback(
    async (params: {
      description: string
      amount: number
      hourly_wage?: number
      contract?: ContractIn | null
      transaction_history?: TransactionHistoryItem[]
      total_saved?: number
      risk_level?: string
    }): Promise<ProcessTransactionResponse> => {
      setIsLoading(true)
      setError(null)
      try {
        if (!isBackendOnline) {
          console.warn("Mizan: backend offline, using mock data")
          return getMockNudge(params.amount)
        }
        const result = await mizanAPI.processTransaction({
          transaction_id: crypto.randomUUID(),
          occurred_at: new Date().toISOString().split("T")[0],
          use_ai: false,
          ...params,
        })
        return result ?? getMockNudge(params.amount)
      } finally {
        setIsLoading(false)
      }
    },
    [isBackendOnline]
  )

  const getPlatforms = useCallback(async (): Promise<Platform[]> => {
    if (!isBackendOnline) {
      console.warn("Mizan: backend offline, using mock platforms")
      return MOCK_PLATFORMS
    }
    const result = await mizanAPI.getPlatforms()
    return result.length > 0 ? result : MOCK_PLATFORMS
  }, [isBackendOnline])

  const getRecommendations = useCallback(
    async (params: {
      user_id: string
      risk_level: string
      total_saved: number
      shariah_preference?: boolean
    }): Promise<RecommendResponse | null> => {
      if (!isBackendOnline) return null
      return mizanAPI.getRecommendations(params)
    },
    [isBackendOnline]
  )

  const login = useCallback(
    async (email: string, password: string): Promise<boolean> => {
      setIsLoading(true)
      setError(null)
      try {
        const result = await mizanAPI.login(email, password)
        if (result) {
          setIsAuthenticated(true)
          return true
        }
        setError("Invalid email or password")
        return false
      } finally {
        setIsLoading(false)
      }
    },
    []
  )

  const register = useCallback(
    async (
      name: string,
      email: string,
      password: string
    ): Promise<boolean> => {
      setIsLoading(true)
      setError(null)
      try {
        const result = await mizanAPI.register(name, email, password)
        if (result) return true
        setError("Registration failed. Email may already be in use.")
        return false
      } finally {
        setIsLoading(false)
      }
    },
    []
  )

  const logout = useCallback(() => {
    mizanAPI.logout()
    setIsAuthenticated(false)
  }, [])

  return {
    isBackendOnline,
    isLoading,
    error,
    isAuthenticated,
    processTransaction,
    getPlatforms,
    getRecommendations,
    login,
    register,
    logout,
  }
}
