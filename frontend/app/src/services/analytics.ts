import { config } from "@/core/config"

export interface ABTestingTotals {
  variant_a_impressions: number
  variant_b_impressions: number
  variant_a_resolutions: number
  variant_b_resolutions: number
}

const dummyABTestingTotals: ABTestingTotals = {
  variant_a_impressions: 6,
  variant_b_impressions: 12,
  variant_a_resolutions: 3,
  variant_b_resolutions: 10
}

export const fetchABTestingTotals = async (): Promise<ABTestingTotals> => {
  const baseUrl = config.BASE_API_URL

  if (!baseUrl) {
    console.warn("BASE_API_URL not configured, using dummy AB testing data")
    return dummyABTestingTotals
  }

  const normalizedBaseUrl = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl

  try {
    const response = await fetch(`${normalizedBaseUrl}/external/analytics/totals`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch AB testing totals: ${response.statusText}`)
    }

    const data = await response.json()
    return data as ABTestingTotals
  } catch (error) {
    console.error("Error fetching AB testing totals:", error)
    console.warn("Falling back to dummy AB testing data due to API error")
    return dummyABTestingTotals
  }
}


