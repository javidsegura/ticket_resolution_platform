import { config } from "@/core/config";

export interface Ticket {
  id: number;
  subject: string;
  body: string;
  intent_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface TicketListResponse {
  total: number;
  skip: number;
  limit: number;
  tickets: Ticket[];
}

type FetchTicketsParams = {
  skip?: number;
  limit?: number;
};

const buildTicketsBaseUrl = () => {
  const baseUrl = config.BASE_API_URL?.replace(/\/+$/, "");

  if (!baseUrl) {
    return null;
  }

  const needsApiPrefix = !/\/api(\/|$)/.test(baseUrl);
  return needsApiPrefix ? `${baseUrl}/api` : baseUrl;
};

/**
 * Fetch tickets from the backend API using the paginated endpoint.
 * Falls back to an empty list when the API URL is not configured.
 */
export const fetchTickets = async ({
  skip = 0,
  limit = 50,
}: FetchTicketsParams = {}): Promise<TicketListResponse> => {
  const apiBase = buildTicketsBaseUrl();

  if (!apiBase) {
    console.warn("BASE_API_URL not configured; returning empty ticket list");
    return {
      total: 0,
      skip,
      limit,
      tickets: [],
    };
  }

  const url = new URL(`${apiBase}/tickets/`);
  url.searchParams.set("skip", String(skip));
  url.searchParams.set("limit", String(limit));

  const response = await fetch(url.toString(), {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(
      `Failed to fetch tickets: ${response.status} ${response.statusText}`,
    );
  }

  const data = await response.json();
  return data as TicketListResponse;
};

/**
 * Fetch a single ticket by ID.
 */
export const fetchTicketById = async (
  ticketId: number | string,
): Promise<Ticket> => {
  const apiBase = buildTicketsBaseUrl();

  if (!apiBase) {
    throw new Error("BASE_API_URL not configured; cannot fetch ticket");
  }

  const normalizedId = String(ticketId).trim();
  if (!normalizedId) {
    throw new Error("Ticket ID is required");
  }

  const response = await fetch(`${apiBase}/tickets/${normalizedId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Ticket not found");
    }
    throw new Error(
      `Failed to fetch ticket: ${response.status} ${response.statusText}`,
    );
  }

  const data = await response.json();
  return data as Ticket;
};
