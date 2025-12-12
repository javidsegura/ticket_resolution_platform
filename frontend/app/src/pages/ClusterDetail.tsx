import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Download,
  Check,
  MessageSquare,
  X,
  ArrowLeft,
  Layers,
  Send,
  Info,
  FlaskConical,
  Copy,
  CheckCircle2,
} from "lucide-react";
import {
  fetchClusterById,
  fetchLatestArticles,
  type Cluster,
} from "@/services/clusters";
import { approveArticle, iterateArticle } from "@/services/articles";
import ReactMarkdown from "react-markdown";

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getClusterStatusBadge = (status: string) => {
  const styles = {
    active: "bg-blue-100 text-blue-800",
    resolved: "bg-green-100 text-green-800",
    pending: "bg-yellow-100 text-yellow-800",
  };
  return (
    <span
      className={`px-3 py-1 rounded-full text-sm font-medium ${styles[status as keyof typeof styles] || "bg-gray-100 text-gray-800"}`}
    >
      {status}
    </span>
  );
};

// Note: These handlers will be updated to use articleIdFull from component state

// Note: Download handlers are defined inside the component to access article state

export default function ClusterDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [cluster, setCluster] = useState<Cluster | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [articleVersion, setArticleVersion] = useState<number | null>(null);
  const [articleIdFull, setArticleIdFull] = useState<number | null>(null);
  const [articleContent, setArticleContent] = useState<string | null>(null);
  const [articleStatus, setArticleStatus] = useState<string | null>(null);
  const [loadingArticle, setLoadingArticle] = useState(true);
  const [approving, setApproving] = useState(false);
  const [copied, setCopied] = useState(false);

  // Helper function to map article status to cluster status
  const getClusterStatusFromArticleStatus = (articleStatus: string | null): "pending" | "resolved" | "active" => {
    if (!articleStatus) return "active";
    if (articleStatus === "accepted") return "resolved";
    if (articleStatus === "iteration") return "pending";
    return "active"; // default fallback
  };

  // Check if article is accepted (buttons should be disabled)
  const isArticleAccepted = articleStatus === "accepted";

  useEffect(() => {
    const loadCluster = async () => {
      if (!id) return;

      try {
        setLoading(true);
        const data = await fetchClusterById(id);
        setCluster(data);
      } catch (error) {
        console.error("Error loading cluster:", error);
      } finally {
        setLoading(false);
      }
    };

    loadCluster();
  }, [id]);

  useEffect(() => {
    const loadArticle = async () => {
      if (!id) return;

      try {
        setLoadingArticle(true);
        const articlesData = await fetchLatestArticles(id);

        // Store version, article ID, and status for later use
        setArticleVersion(articlesData.version);
        setArticleIdFull(articlesData.article_id_full);
        setArticleStatus(articlesData.status);

        // Fetch and load the markdown content from the presigned URL
        if (articlesData.presigned_url_full) {
          try {
            const response = await fetch(articlesData.presigned_url_full);
            if (response.ok) {
              const markdownContent = await response.text();
              setArticleContent(markdownContent);
            } else {
              console.error("Failed to fetch article content from presigned URL");
              setArticleContent(null);
            }
          } catch (error) {
            console.error("Error fetching article content:", error);
            setArticleContent(null);
          }
        } else {
          setArticleContent(null);
        }
      } catch (error) {
        console.error("Error loading articles:", error);
        setArticleVersion(null);
        setArticleIdFull(null);
        setArticleStatus(null);
        setArticleContent(null);
      } finally {
        setLoadingArticle(false);
      }
    };

    loadArticle();
  }, [id]);

  // Handler functions
  const handleApprove = async () => {
    if (!articleIdFull) {
      alert("No article available to approve. Please wait for the article to load.");
    return;
  }

    try {
      setApproving(true);
      const result = await approveArticle(articleIdFull);
      alert(`Article approved successfully! ${result.message}`);
      
      // Reload article to get updated status
      const articlesData = await fetchLatestArticles(id!);
      setArticleVersion(articlesData.version);
      setArticleIdFull(articlesData.article_id_full);
      setArticleStatus(articlesData.status);
      
      if (articlesData.presigned_url_full) {
        const response = await fetch(articlesData.presigned_url_full);
        if (response.ok) {
          const markdownContent = await response.text();
          setArticleContent(markdownContent);
        }
      }
    } catch (error) {
      console.error("Error approving article:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to approve article. Please try again.";
      alert(errorMessage);
    } finally {
      setApproving(false);
    }
  };

  const handleSubmitFeedback = async (feedbackText: string) => {
    if (!articleIdFull) {
      alert("No article available to provide feedback on. Please wait for the article to load.");
    return false;
  }

    if (!feedbackText.trim()) {
      alert("Please provide feedback before submitting.");
      return false;
    }

    try {
      setSubmitting(true);
      const result = await iterateArticle(articleIdFull, feedbackText);
    alert(
        `Feedback submitted successfully! A new version (v${result.next_version}) is being generated. Job ID: ${result.job_id}`
    );
    return true;
  } catch (error) {
    console.error("Error submitting feedback:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to submit feedback. Please try again.";
      alert(errorMessage);
    return false;
    } finally {
      setSubmitting(false);
    }
  };

  // Download handlers
  const handleDownloadMarkdown = () => {
    if (!cluster) return;

    let markdown = `# ${cluster.title}\n\n`;
    
    // Metadata
    markdown += `## Cluster Information\n\n`;
    markdown += `- **Cluster ID:** ${cluster.id}\n`;
    markdown += `- **Created:** ${formatDate(cluster.createdAt)}\n`;
    markdown += `- **Last Updated:** ${formatDate(cluster.updatedAt)}\n`;
    
    if (articleVersion !== null) {
      markdown += `- **Article Version:** v${articleVersion}\n`;
    }
    
    const clusterStatus = getClusterStatusFromArticleStatus(articleStatus);
    markdown += `- **Status:** ${clusterStatus}\n`;
    
    if (articleStatus) {
      markdown += `- **Article Status:** ${articleStatus}\n`;
    }
    markdown += `\n`;

    // Main Topics
    if (cluster.mainTopics && cluster.mainTopics.length > 0) {
      markdown += `## Main Topics\n\n`;
      cluster.mainTopics.forEach((topic) => {
        markdown += `- ${topic}\n`;
      });
      markdown += `\n`;
    }

    // Categories
    if (cluster.categories) {
      const categories = [
        cluster.categories.level1,
        cluster.categories.level2,
        cluster.categories.level3,
      ].filter((cat): cat is { id: number; name: string } => Boolean(cat));
      
      if (categories.length > 0) {
        markdown += `## Categories\n\n`;
        categories.forEach((cat, idx) => {
          markdown += `- Level ${idx + 1}: ${cat.name}\n`;
        });
        markdown += `\n`;
      }
    }

    // Article Content
    if (articleContent) {
      markdown += `## AI Generated Article\n\n`;
      markdown += `${articleContent}\n`;
    } else {
      markdown += `## AI Generated Article\n\n`;
      markdown += `_No article content available._\n`;
  }

  const blob = new Blob([markdown], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
    a.download = `cluster-${cluster.id}-v${articleVersion || "draft"}.md`;
  a.click();
  URL.revokeObjectURL(url);
};

  const handleDownloadHTML = () => {
    if (!cluster) return;

    const clusterStatus = getClusterStatusFromArticleStatus(articleStatus);
    
    // Convert markdown content to HTML if available
    let articleHtml = "";
    if (articleContent) {
      // Basic markdown to HTML conversion
      articleHtml = articleContent
        .replace(/\n\n/g, "</p><p>")
        .replace(/\n/g, "<br>")
        .replace(/#{3} (.*)/g, "<h3>$1</h3>")
        .replace(/#{2} (.*)/g, "<h2>$1</h2>")
        .replace(/#{1} (.*)/g, "<h1>$1</h1>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>");
      articleHtml = `<div class="article-content"><p>${articleHtml}</p></div>`;
    } else {
      articleHtml = `<div class="article-content"><p><em>No article content available.</em></p></div>`;
    }

  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${cluster.title}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      background: #f5f5f5;
      padding: 40px 20px;
    }
    .container {
      max-width: 900px;
      margin: 0 auto;
      background: white;
      padding: 40px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    h1 { 
      color: #1a1a1a;
      font-size: 2em;
      margin-bottom: 20px;
      border-bottom: 3px solid #4a90e2;
      padding-bottom: 10px;
    }
    h2 {
      color: #2c3e50;
      font-size: 1.5em;
      margin-top: 30px;
      margin-bottom: 15px;
      border-bottom: 2px solid #e0e0e0;
      padding-bottom: 8px;
    }
    h3 {
      color: #34495e;
      font-size: 1.2em;
      margin-top: 20px;
      margin-bottom: 10px;
    }
    .metadata {
      background: #f8f9fa;
      padding: 20px;
      border-radius: 6px;
      margin-bottom: 30px;
      border-left: 4px solid #4a90e2;
    }
    .metadata-item {
      margin-bottom: 8px;
      font-size: 0.95em;
    }
    .metadata-item strong {
      color: #555;
      min-width: 140px;
      display: inline-block;
    }
    .summary {
      color: #666;
      line-height: 1.8;
      font-size: 1.05em;
      margin-bottom: 30px;
      padding: 15px;
      background: #fafafa;
      border-radius: 6px;
    }
    .topics {
      margin: 20px 0;
    }
    .topic {
      display: inline-block;
      background: #e8f4f8;
      color: #2c3e50;
      padding: 6px 12px;
      margin: 4px 8px 4px 0;
      border-radius: 20px;
      font-size: 0.9em;
      border: 1px solid #cce7f0;
    }
    .categories {
      margin: 20px 0;
    }
    .category {
      margin: 8px 0;
      padding: 8px 12px;
      background: #f0f7ff;
      border-left: 3px solid #4a90e2;
      border-radius: 4px;
    }
    .article-content {
      margin-top: 30px;
      line-height: 1.8;
    }
    .article-content p {
      margin-bottom: 16px;
    }
    .article-content ul, .article-content ol {
      margin: 16px 0;
      padding-left: 30px;
    }
    .article-content li {
      margin-bottom: 8px;
    }
    .article-content code {
      background: #f4f4f4;
      padding: 2px 6px;
      border-radius: 3px;
      font-family: 'Courier New', monospace;
      font-size: 0.9em;
    }
    .status-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 0.85em;
      font-weight: 600;
      text-transform: capitalize;
    }
    .status-pending { background: #fff3cd; color: #856404; }
    .status-resolved { background: #d4edda; color: #155724; }
    .status-active { background: #d1ecf1; color: #0c5460; }
  </style>
</head>
<body>
  <div class="container">
  <h1>${cluster.title}</h1>
    
    <div class="metadata">
      <div class="metadata-item"><strong>Cluster ID:</strong> ${cluster.id}</div>
      <div class="metadata-item"><strong>Created:</strong> ${formatDate(cluster.createdAt)}</div>
      <div class="metadata-item"><strong>Last Updated:</strong> ${formatDate(cluster.updatedAt)}</div>
      ${articleVersion !== null ? `<div class="metadata-item"><strong>Article Version:</strong> v${articleVersion}</div>` : ""}
      <div class="metadata-item"><strong>Status:</strong> <span class="status-badge status-${clusterStatus}">${clusterStatus}</span></div>
      ${articleStatus ? `<div class="metadata-item"><strong>Article Status:</strong> ${articleStatus}</div>` : ""}
    </div>

    ${cluster.mainTopics && cluster.mainTopics.length > 0 ? `
  <div class="topics">
    <h2>Main Topics</h2>
    ${cluster.mainTopics.map((t) => `<span class="topic">${t}</span>`).join("")}
    </div>
    ` : ""}

    ${cluster.categories && (cluster.categories.level1 || cluster.categories.level2 || cluster.categories.level3) ? `
    <div class="categories">
      <h2>Categories</h2>
      ${[cluster.categories.level1, cluster.categories.level2, cluster.categories.level3]
        .filter((cat): cat is { id: number; name: string } => Boolean(cat))
        .map((cat, idx) => `<div class="category"><strong>Level ${idx + 1}:</strong> ${cat.name}</div>`)
        .join("")}
    </div>
    ` : ""}

    <div class="article-content">
      <h2>AI Generated Article</h2>
      ${articleHtml}
    </div>
  </div>
</body>
</html>`;

  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
    a.download = `cluster-${cluster.id}-v${articleVersion || "draft"}.html`;
  a.click();
  URL.revokeObjectURL(url);
};

  const handleCopyReactComponent = async () => {
    if (!cluster) return;

    const componentCode = `<MicroAnswer intentId="${cluster.id}" />`;
    
    try {
      await navigator.clipboard.writeText(componentCode);
      setCopied(true);
      setTimeout(() => {
        setCopied(false);
      }, 2000);
      } catch (error) {
      console.error("Failed to copy to clipboard:", error);
      // Fallback for older browsers
      const textArea = document.createElement("textarea");
      textArea.value = componentCode;
      textArea.style.position = "fixed";
      textArea.style.opacity = "0";
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand("copy");
        setCopied(true);
        setTimeout(() => {
          setCopied(false);
        }, 2000);
      } catch (err) {
        console.error("Fallback copy failed:", err);
        alert("Failed to copy to clipboard");
      }
      document.body.removeChild(textArea);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading cluster...</p>
        </div>
      </div>
    );
  }

  if (!cluster) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <p className="text-lg text-gray-600">Cluster not found</p>
        <Button onClick={() => navigate("/dashboard")} className="mt-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Back Button and Title */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate("/dashboard")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900">{cluster.title}</h1>
          <p className="text-gray-600 mt-1">Cluster #{cluster.id}</p>
        </div>
      </div>

      {/* Key Information & A/B Testing */}
      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <Card className="lg:h-full flex flex-col">
          <CardHeader>
            <CardTitle>Key Information</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col gap-6">
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground font-medium">Status</p>
                <div className="mt-2">
                  {getClusterStatusBadge(getClusterStatusFromArticleStatus(articleStatus))}
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground font-medium">Version</p>
                <p className="font-semibold text-base">
                  {articleVersion !== null ? `v${articleVersion}` : "N/A"}
                </p>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground font-medium">Created</p>
                <p className="font-semibold text-base">
                  {formatDate(cluster.createdAt)}
                </p>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground font-medium">Last Updated</p>
                <p className="font-semibold text-base">
                  {formatDate(cluster.updatedAt)}
                </p>
              </div>
            </div>

            {/* Main Topics */}
            {cluster.mainTopics && cluster.mainTopics.length > 0 && (
              <div className="flex-1 flex flex-col pt-4 border-t">
                <p className="text-sm text-muted-foreground font-medium mb-3">
                  Main Topics
                </p>
                <div className="flex flex-wrap gap-2">
                  {cluster.mainTopics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="lg:h-full">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <FlaskConical className="h-4 w-4" />
                  A/B Testing Performance
                </CardTitle>
                <CardDescription className="text-xs mt-1">
                  Variant impressions, resolutions, and conversion rates
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0 space-y-5">
            <div className="space-y-3">
              {(["variantA", "variantB"] as const).map((variantKey) => {
                const label =
                  variantKey === "variantA" ? "Variant A" : "Variant B";
                const impressions =
                  cluster[
                    variantKey === "variantA"
                      ? "variantAImpressions"
                      : "variantBImpressions"
                  ] ?? 0;
                const resolutions =
                  cluster[
                    variantKey === "variantA"
                      ? "variantAResolutions"
                      : "variantBResolutions"
                  ] ?? 0;
                const conversion =
                  impressions === 0 ? 0 : (resolutions / impressions) * 100;

                return (
                  <div key={variantKey} className="rounded-lg border p-3">
                    <div className="flex items-center justify-between text-sm font-medium text-gray-900">
                      <span>{label}</span>
                      <span>{conversion.toFixed(1)}%</span>
                    </div>
                    <p className="text-xs text-gray-500">
                      {resolutions} resolutions / {impressions} impressions
                    </p>
                    <div className="mt-3 h-2 rounded-full bg-gray-100">
                      <div
                        className="h-full rounded-full bg-primary-500 transition-all"
                        style={{ width: `${Math.min(conversion, 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="rounded-lg bg-gray-50 p-4 text-xs text-gray-600">
              <p className="font-semibold text-gray-800 mb-1">Quick insights</p>
              <ul className="space-y-1">
                {(() => {
                  const variantAImpressions = cluster.variantAImpressions ?? 0;
                  const variantBImpressions = cluster.variantBImpressions ?? 0;
                  const variantAResolutions = cluster.variantAResolutions ?? 0;
                  const variantBResolutions = cluster.variantBResolutions ?? 0;
                  const variantAConversion =
                    variantAImpressions === 0
                      ? 0
                      : (variantAResolutions / variantAImpressions) * 100;
                  const variantBConversion =
                    variantBImpressions === 0
                      ? 0
                      : (variantBResolutions / variantBImpressions) * 100;
                  const conversionDifference =
                    variantAConversion - variantBConversion;

                  return (
                    <>
                      <li>
                        Variant A lift vs B:{" "}
                        <span
                          className={`font-semibold ${conversionDifference >= 0 ? "text-green-700" : "text-red-600"}`}
                        >
                          {conversionDifference >= 0 ? "+" : ""}
                          {conversionDifference.toFixed(1)} pp
                        </span>
                      </li>
                      <li>
                        Total impressions:{" "}
                        <span className="font-semibold text-gray-900">
                          {variantAImpressions + variantBImpressions}
                        </span>
                      </li>
                      <li>
                        Total resolutions:{" "}
                        <span className="font-semibold text-gray-900">
                          {variantAResolutions + variantBResolutions}
                        </span>
                      </li>
                    </>
                  );
                })()}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Resolution with Actions Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Generated Resolution - Scrollable */}
        <div className="lg:col-span-2">
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="h-5 w-5" />
                AI Generated Resolution
              </CardTitle>
              <CardDescription>
                Markdown-formatted recommendations and solutions
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden flex flex-col">
              {loadingArticle ? (
                <div className="flex-1 flex items-center justify-center py-12">
                  <div className="text-center text-gray-500">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-3"></div>
                    <p className="text-sm">Loading article...</p>
                  </div>
                </div>
              ) : articleContent ? (
                <div className="prose prose-sm max-w-none overflow-y-auto flex-1 pr-2">
                  <ReactMarkdown
                    components={{
                      h1: ({ node, ...props }) => (
                        <h1
                          className="text-2xl font-bold mt-6 mb-4 text-gray-900"
                          {...props}
                        />
                      ),
                      h2: ({ node, ...props }) => (
                        <h2
                          className="text-xl font-semibold mt-5 mb-3 text-gray-900"
                          {...props}
                        />
                      ),
                      h3: ({ node, ...props }) => (
                        <h3
                          className="text-lg font-semibold mt-4 mb-2 text-gray-900"
                          {...props}
                        />
                      ),
                      p: ({ node, ...props }) => (
                        <p
                          className="mb-4 text-gray-700 leading-relaxed"
                          {...props}
                        />
                      ),
                      ul: ({ node, ...props }) => (
                        <ul
                          className="list-disc pl-6 mb-4 space-y-1"
                          {...props}
                        />
                      ),
                      ol: ({ node, ...props }) => (
                        <ol
                          className="list-decimal pl-6 mb-4 space-y-1"
                          {...props}
                        />
                      ),
                      li: ({ node, ...props }) => (
                        <li className="text-gray-700" {...props} />
                      ),
                      strong: ({ node, ...props }) => (
                        <strong
                          className="font-semibold text-gray-900"
                          {...props}
                        />
                      ),
                      code: ({ node, ...props }) => (
                        <code
                          className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800"
                          {...props}
                        />
                      ),
                    }}
                  >
                    {articleContent}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center py-12">
                  <div className="text-center text-gray-500">
                    <Layers className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                    <p className="text-sm">No article available</p>
                    <p className="text-xs mt-1 text-gray-400">
                      The AI-generated article will appear here once available
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Actions Sidebar - Fixed (Always Visible) */}
        <div className="lg:col-span-1">
          <Card className="sticky top-4">
            <CardHeader>
              <CardTitle>Actions</CardTitle>
              <CardDescription>Manage this cluster</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Action Buttons */}
              <div className="space-y-3">
                <Button
                  onClick={handleApprove}
                  disabled={approving || !articleIdFull || isArticleAccepted}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title={isArticleAccepted ? "Article has already been accepted" : ""}
                >
                  {approving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Approving...
                    </>
                  ) : (
                    <>
                  <Check className="mr-2 h-4 w-4" />
                  Approve
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setFeedback("");
                    setShowFeedbackForm(true);
                  }}
                  disabled={isArticleAccepted}
                  className="w-full disabled:opacity-50 disabled:cursor-not-allowed"
                  title={isArticleAccepted ? "Article has already been accepted" : ""}
                >
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Give Feedback
                </Button>
              </div>

              {/* Accepted Notice */}
              {isArticleAccepted && (
                <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-md">
                  <p className="text-xs text-green-800 text-center">
                    ✓ This article has been accepted. No further actions are available.
                  </p>
                </div>
              )}

              {/* Download Options */}
              <div className="pt-4 border-t space-y-3">
                <p className="text-sm font-medium text-gray-700">Download</p>
                <Button
                  variant="outline"
                  onClick={handleDownloadMarkdown}
                  className="w-full"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download as Markdown
                </Button>
                <Button
                  variant="outline"
                  onClick={handleDownloadHTML}
                  className="w-full"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download as HTML
                </Button>
              </div>

              {/* Copy React Component */}
              <div className="pt-4 border-t space-y-3">
                <p className="text-sm font-medium text-gray-700">Code</p>
                <Button
                  variant="outline"
                  onClick={handleCopyReactComponent}
                  className="w-full"
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="mr-2 h-4 w-4" />
                      Copy React Component
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Feedback Form Modal */}
      {showFeedbackForm && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setShowFeedbackForm(false)}
        >
          <Card
            className="w-full max-w-2xl max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader className="border-b">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Give Feedback
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Provide feedback to improve the AI-generated resolution
                  </CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFeedbackForm(false)}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-4 flex-1 overflow-y-auto">
              {/* Instructions */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-sm text-blue-900 mb-2">
                      Tips for Effective Feedback
                    </h3>
                    <ul className="text-sm text-blue-800 space-y-1.5 list-disc list-inside">
                      <li>
                        <strong>Be specific:</strong> Clearly describe what
                        needs to be changed or improved
                      </li>
                      <li>
                        <strong>Be clear:</strong> Use straightforward language
                        to explain your requirements
                      </li>
                      <li>
                        <strong>Provide context:</strong> Explain why the change
                        is needed or what outcome you're seeking
                      </li>
                      <li>
                        <strong>Give examples:</strong> If possible, provide
                        examples of what you'd like to see
                      </li>
                      <li>
                        <strong>Focus on one area:</strong> Address specific
                        sections or aspects rather than everything at once
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Feedback Form */}
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (!feedback.trim()) {
                    alert("Please provide feedback before submitting");
                    return;
                  }

                  const success = await handleSubmitFeedback(feedback);

                  if (success) {
                    setShowFeedbackForm(false);
                    setFeedback("");
                    // Optionally reload article data after feedback is submitted
                    // The article will be regenerated in the background
                  }
                }}
                className="space-y-4"
              >
                <div>
                  <label
                    htmlFor="feedback"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Your Feedback
                  </label>
                  <textarea
                    id="feedback"
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Example: 'Please make the recommendations more technical and include specific implementation steps. Also, add a section about security considerations.'"
                    className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm min-h-[150px] resize-y"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {feedback.length} characters
                  </p>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowFeedbackForm(false);
                      setFeedback("");
                    }}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting || !feedback.trim()}
                    className="bg-primary-600 hover:bg-primary-700"
                  >
                    {submitting ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="mr-2 h-4 w-4" />
                        Submit Feedback
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

