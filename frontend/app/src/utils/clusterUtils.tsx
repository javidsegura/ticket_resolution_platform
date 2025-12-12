/**
 * Utility functions for cluster-related operations
 */

/**
 * Format a date string to a human-readable format
 */
export const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

/**
 * Get the cluster status badge component with appropriate styling
 */
export const getClusterStatusBadge = (status: string) => {
  const styles = {
    active: "bg-blue-100 text-blue-800",
    resolved: "bg-green-100 text-green-800",
    pending: "bg-yellow-100 text-yellow-800",
  };
  return (
    <span
      className={`px-3 py-1 rounded-full text-sm font-medium ${
        styles[status as keyof typeof styles] || "bg-gray-100 text-gray-800"
      }`}
    >
      {status}
    </span>
  );
};

/**
 * Map article status to cluster status
 * @param articleStatus - Article status from API
 * @returns Cluster status string (pending or resolved only)
 */
export const getClusterStatusFromArticleStatus = (
  articleStatus: string | null,
): "pending" | "resolved" => {
  if (articleStatus === "accepted") return "resolved";
  // All other cases (null, "iteration", unknown) should be "pending"
  return "pending";
};

