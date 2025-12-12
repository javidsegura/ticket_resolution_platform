// Cluster API service
import { config } from "@/core/config";

type CategoryRef = {
  id: number;
  name: string;
};

export interface Cluster {
  id: string;
  title: string;
  summary: string;
  createdAt: string;
  updatedAt: string;
  mainTopics: string[];
  status: "active" | "resolved" | "pending";
  resolution?: string; // AI-generated resolution in markdown format
  area?: string | null;
  categories?: {
    level1?: CategoryRef;
    level2?: CategoryRef;
    level3?: CategoryRef;
  };
  variantAImpressions?: number;
  variantBImpressions?: number;
  variantAResolutions?: number;
  variantBResolutions?: number;
}

type IntentResponse = {
  id: number;
  name: string;
  area: string | null;
  is_processed: boolean;
  created_at: string;
  updated_at: string;
  category_level_1?: CategoryRef;
  category_level_2?: CategoryRef;
  category_level_3?: CategoryRef;
  variant_a_impressions?: number;
  variant_b_impressions?: number;
  variant_a_resolutions?: number;
  variant_b_resolutions?: number;
  article_version?: number | null;
  article_status?: string | null;
};

const buildApiBaseUrl = () => {
  const baseUrl = config.BASE_API_URL?.replace(/\/+$/, "");

  if (!baseUrl) {
    return null;
  }

  const needsApiPrefix = !/\/api(\/|$)/.test(baseUrl);
  return needsApiPrefix ? `${baseUrl}/api` : baseUrl;
};

const mapIntentToCluster = (intent: IntentResponse): Cluster => {
  const categoryNames = [
    intent.category_level_1?.name,
    intent.category_level_2?.name,
    intent.category_level_3?.name,
  ].filter((name): name is string => Boolean(name));

  return {
    id: String(intent.id),
    title: intent.name,
    summary: intent.area ?? "No area specified",
    createdAt: intent.created_at,
    updatedAt: intent.updated_at,
    mainTopics: categoryNames,
    status: "pending", // Default to pending, will be updated based on article_status
    area: intent.area,
    categories: {
      level1: intent.category_level_1,
      level2: intent.category_level_2,
      level3: intent.category_level_3,
    },
    variantAImpressions: intent.variant_a_impressions ?? 0,
    variantBImpressions: intent.variant_b_impressions ?? 0,
    variantAResolutions: intent.variant_a_resolutions ?? 0,
    variantBResolutions: intent.variant_b_resolutions ?? 0,
  };
};

// Dummy clusters data - will be replaced with API calls
const dummyClusters: Cluster[] = [
  {
    id: "cluster-1",
    title: "Password Reset Issues",
    summary:
      "Multiple customers are experiencing difficulties with password reset functionality. Common issues include missing reset links, unclear instructions, and login page discoverability problems.",
    createdAt: "2024-01-10T08:00:00Z",
    updatedAt: "2024-01-15T14:30:00Z",
    mainTopics: [
      "Password reset link location",
      "Email delivery issues",
      "Reset instructions clarity",
    ],
    status: "active",
    resolution: `**Website Improvement Recommendation:**

Add a prominent "Forgot Password?" link directly on the login page, positioned below the password input field. Currently, users are having difficulty locating this feature. The link should be clearly visible and use a color that stands out from the rest of the form elements.

**FAQ Addition:**
Create a new FAQ entry titled "How to Reset Your Password" with the following content:

1. Click the "Forgot Password?" link on the login page
2. Enter your registered email address
3. Check your inbox (and spam folder) for the reset link
4. Click the link and follow the prompts to create a new password

**Layout Enhancement:**
Consider adding a visual indicator (icon or highlighted text) next to the "Forgot Password?" link to improve discoverability. Additionally, add a "Resend Reset Link" option if the email doesn't arrive within 5 minutes. The link should be positioned prominently but not interfere with the main login flow.

**Additional Recommendations:**

- Implement a password strength indicator to help users create secure passwords
- Add multi-factor authentication (MFA) options for enhanced security
- Create a dedicated password reset page with clear instructions
- Consider adding a "Remember me" option to reduce password reset requests

**User Experience Improvements:**

The current password reset process has multiple pain points that contribute to support ticket volume:

1. **Email Delivery Issues**: Many users report not receiving reset emails. Consider implementing:
   - Immediate email confirmation with alternative methods (SMS, security questions)
   - Clear messaging about checking spam folders
   - Email delivery status notifications
   - Ability to use backup email addresses

2. **Link Expiration**: Reset links expire too quickly (currently 1 hour). Recommendations:
   - Extend expiration to 24 hours for better user convenience
   - Add a "Request New Link" option that doesn't require starting over
   - Clear messaging about link expiration time

3. **Mobile Experience**: The password reset flow on mobile devices needs improvement:
   - Larger tap targets for links and buttons
   - Simplified form fields
   - Better keyboard handling for email input
   - Touch-friendly interface elements

**Security Considerations:**

While improving user experience, we must maintain security standards:

- Implement rate limiting on password reset requests (max 3 per hour per email)
- Add CAPTCHA after multiple failed attempts
- Log all password reset attempts for security monitoring
- Send confirmation emails when password is successfully changed
- Require email verification before allowing password change

**A/B Testing Recommendations:**

Before implementing all changes at once, consider testing:

1. Test different positions for the "Forgot Password?" link
2. Test different colors and styles for the link
3. Test email templates to improve open rates
4. Test different expiration times for reset links
5. Test mobile vs desktop experiences separately

**Implementation Priority:**

1. **High Priority** (Implement immediately):
   - Add prominent "Forgot Password?" link on login page
   - Create FAQ entry for password reset
   - Add "Resend Reset Link" functionality

2. **Medium Priority** (Implement within 2 weeks):
   - Extend link expiration time
   - Improve email delivery notifications
   - Mobile experience improvements

3. **Low Priority** (Implement within 1 month):
   - Password strength indicator
   - MFA options
   - A/B testing framework

**Metrics to Track:**

After implementation, monitor these metrics to measure success:

- Reduction in password reset support tickets
- Time to complete password reset process
- Email delivery rates
- Link click-through rates
- Success rate of password resets
- User satisfaction scores

**Long-term Vision:**

The ultimate goal is to create a self-service password reset experience that is:
- Intuitive and easy to find
- Fast and efficient
- Secure and reliable
- Accessible on all devices
- Well-documented and discoverable

By implementing these recommendations, we expect to see a 60-80% reduction in password reset-related support tickets, freeing up support staff to handle more complex issues.`,
  },
  {
    id: "cluster-2",
    title: "Order History Navigation",
    summary:
      "Users frequently cannot locate their order history. The feature appears to be buried in submenus and lacks prominent placement in the account dashboard.",
    createdAt: "2024-01-08T10:15:00Z",
    updatedAt: "2024-01-14T09:20:00Z",
    mainTopics: [
      "Account dashboard layout",
      "Navigation menu structure",
      "Order tracking visibility",
    ],
    status: "active",
  },
  {
    id: "cluster-3",
    title: "Return Policy Inquiries",
    summary:
      "High volume of questions about return policies, refund timelines, and return process. Customers are seeking clear, accessible information about returns and exchanges.",
    createdAt: "2024-01-05T12:00:00Z",
    updatedAt: "2024-01-13T16:45:00Z",
    mainTopics: [
      "Return policy documentation",
      "Refund process clarity",
      "Return window information",
    ],
    status: "pending",
  },
  {
    id: "cluster-4",
    title: "Customer Support Contact",
    summary:
      "Customers cannot find contact information for customer support. Missing phone numbers, email addresses, and support links are causing frustration and delays.",
    createdAt: "2024-01-03T09:30:00Z",
    updatedAt: "2024-01-12T11:00:00Z",
    mainTopics: [
      "Contact page visibility",
      "Support information placement",
      "Multiple contact methods",
    ],
    status: "active",
  },
  {
    id: "cluster-5",
    title: "Shipping Information Access",
    summary:
      "Users are asking about shipping options, delivery times, and tracking information. This information needs to be more prominently displayed during checkout and order process.",
    createdAt: "2024-01-12T14:00:00Z",
    updatedAt: "2024-01-15T10:00:00Z",
    mainTopics: [
      "Shipping policy visibility",
      "Delivery time estimates",
      "Order tracking integration",
    ],
    status: "active",
  },
  {
    id: "cluster-6",
    title: "Payment Method Issues",
    summary:
      "Customers experiencing problems with payment processing, including declined cards, missing payment options, and unclear error messages during checkout.",
    createdAt: "2024-01-09T11:20:00Z",
    updatedAt: "2024-01-14T15:30:00Z",
    mainTopics: [
      "Payment error messaging",
      "Accepted payment methods",
      "Checkout process clarity",
    ],
    status: "resolved",
  },
];

/**
 * Helper function to map article status to cluster status
 * @param articleStatus - Article status from API
 * @returns Cluster status string (pending or resolved only)
 */
const getClusterStatusFromArticleStatus = (
  articleStatus: string | null,
): "pending" | "resolved" => {
  if (articleStatus === "accepted") return "resolved";
  // All other cases (null, "iteration", unknown) should be "pending"
  return "pending";
};

/**
 * Fetch all clusters from the backend API with their article statuses
 * @returns Promise<Cluster[]> Array of clusters with correct status based on article status
 */
export const fetchClusters = async (): Promise<Cluster[]> => {
  const apiBase = buildApiBaseUrl();

  // If no API URL is configured, return dummy data
  if (!apiBase) {
    console.warn("BASE_API_URL not configured, using dummy cluster data");
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 300));
    return dummyClusters;
  }

  try {
    const response = await fetch(`${apiBase}/intents/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        // TODO: Add authorization header when auth is implemented
        // "Authorization": `Bearer ${token}`
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch clusters: ${response.statusText}`);
    }

    const data = (await response.json()) as IntentResponse[];
    // Map intents to clusters, using article_status from the API response
    const clusters = data.map((intent) => {
      const cluster = mapIntentToCluster(intent);
      // Set cluster status based on article status from API response
      // This will always be either "pending" or "resolved"
      cluster.status = getClusterStatusFromArticleStatus(intent.article_status);
      return cluster;
    });

    return clusters;
  } catch (error) {
    console.error("Error fetching clusters:", error);
    // Fallback to dummy data on error
    console.warn("Falling back to dummy cluster data due to API error");
    return dummyClusters;
  }
};

/**
 * Fetch a single cluster by ID
 * @param clusterId - The ID of the cluster to fetch
 * @returns Promise<Cluster | null> The cluster or null if not found
 */
export const fetchClusterById = async (
  clusterId: string,
): Promise<Cluster | null> => {
  const apiBase = buildApiBaseUrl();

  // If no API URL is configured, return dummy data
  if (!apiBase) {
    console.warn("BASE_API_URL not configured, using dummy cluster data");
    await new Promise((resolve) => setTimeout(resolve, 300));
    return dummyClusters.find((c) => c.id === clusterId) || null;
  }

  try {
    const response = await fetch(`${apiBase}/intents/${clusterId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        // TODO: Add authorization header when auth is implemented
        // "Authorization": `Bearer ${token}`
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`Failed to fetch cluster: ${response.statusText}`);
    }

    const data = (await response.json()) as IntentResponse;
    return mapIntentToCluster(data);
  } catch (error) {
    console.error("Error fetching cluster:", error);
    // Fallback to dummy data on error
    const cluster = dummyClusters.find((c) => c.id === clusterId);
    return cluster || null;
  }
};

export interface LatestArticlesResponse {
  intent_id: number;
  version: number | null;
  status: string | null;
  article_id_micro: number | null;
  article_id_full: number | null;
  presigned_url_micro: string | null;
  presigned_url_full: string | null;
}

/**
 * Fetch the latest articles for a specific intent/cluster
 * @param intentId - The ID of the intent/cluster
 * @returns Promise<LatestArticlesResponse> The latest articles information
 */
export const fetchLatestArticles = async (
  intentId: string | number,
): Promise<LatestArticlesResponse> => {
  const apiBase = buildApiBaseUrl();

  if (!apiBase) {
    throw new Error("BASE_API_URL not configured; cannot fetch articles");
  }

  const response = await fetch(`${apiBase}/intents/${intentId}/articles/latest`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      // TODO: Add authorization header when auth is implemented
      // "Authorization": `Bearer ${token}`
    },
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Intent not found");
    }
    throw new Error(
      `Failed to fetch articles: ${response.status} ${response.statusText}`,
    );
  }

  const data = await response.json();
  return data as LatestArticlesResponse;
};
