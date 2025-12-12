// Article API service
import { config } from "@/core/config";

const buildApiBaseUrl = () => {
  const baseUrl = config.BASE_API_URL?.replace(/\/+$/, "");

  if (!baseUrl) {
    return null;
  }

  const needsApiPrefix = !/\/api(\/|$)/.test(baseUrl);
  return needsApiPrefix ? `${baseUrl}/api` : baseUrl;
};

export interface ApproveArticleResponse {
  status: string;
  message: string;
  article_id: number;
  intent_id?: number;
  version?: number;
  new_status?: string;
  approved_types?: string[];
}

export interface IterateArticleResponse {
  status: string;
  message: string;
  article_id: number;
  intent_id: number;
  current_version: number;
  next_version: number;
  feedback_saved: boolean;
  job_id: string;
}

/**
 * Approve an article by ID
 * @param articleId - The ID of the article to approve
 * @returns Promise<ApproveArticleResponse> Approval response
 */
export const approveArticle = async (
  articleId: number,
): Promise<ApproveArticleResponse> => {
  const apiBase = buildApiBaseUrl();

  if (!apiBase) {
    throw new Error("BASE_API_URL not configured; cannot approve article");
  }

  const response = await fetch(`${apiBase}/articles/${articleId}/approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // TODO: Add authorization header when auth is implemented
      // "Authorization": `Bearer ${token}`
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `Failed to approve article: ${response.status} ${response.statusText}`;
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  const data = await response.json();
  return data as ApproveArticleResponse;
};

/**
 * Submit feedback to iterate on an article
 * @param articleId - The ID of the article to iterate
 * @param feedback - Feedback text for regeneration
 * @returns Promise<IterateArticleResponse> Iteration response
 */
export const iterateArticle = async (
  articleId: number,
  feedback: string,
): Promise<IterateArticleResponse> => {
  const apiBase = buildApiBaseUrl();

  if (!apiBase) {
    throw new Error("BASE_API_URL not configured; cannot iterate article");
  }

  if (!feedback || !feedback.trim()) {
    throw new Error("Feedback is required");
  }

  const response = await fetch(`${apiBase}/articles/${articleId}/iterate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // TODO: Add authorization header when auth is implemented
      // "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ feedback }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `Failed to submit feedback: ${response.status} ${response.statusText}`;
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  const data = await response.json();
  return data as IterateArticleResponse;
};

