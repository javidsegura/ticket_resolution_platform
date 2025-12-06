import { config } from "@/core/config";

export interface DocumentUploadResult {
  filename: string;
  success: boolean;
  error?: string;
}

export interface DocumentUploadResponse {
  total_processed: number;
  successful: number;
  failed: number;
  results: DocumentUploadResult[];
}

const buildDocumentsBaseUrl = () => {
  const baseUrl = config.BASE_API_URL?.replace(/\/+$/, "");

  if (!baseUrl) {
    return null;
  }

  const needsApiPrefix = !/\/api(\/|$)/.test(baseUrl);
  return needsApiPrefix ? `${baseUrl}/api` : baseUrl;
};

/**
 * Upload one or more company documents (PDF) to the backend.
 */
export const uploadCompanyDocuments = async (
  files: File[],
): Promise<DocumentUploadResponse> => {
  if (!files.length) {
    throw new Error("Select at least one PDF before uploading");
  }

  const apiBase = buildDocumentsBaseUrl();
  if (!apiBase) {
    throw new Error("BASE_API_URL is not configured");
  }

  const formData = new FormData();
  files.forEach((file) => formData.append("files", file, file.name));

  const response = await fetch(`${apiBase}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(
      message || `Failed to upload documents: ${response.statusText}`,
    );
  }

  const data = await response.json();
  return data as DocumentUploadResponse;
};
