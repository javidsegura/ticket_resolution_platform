import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, Check, MessageSquare, X, ArrowLeft, Layers, Send, Info, FlaskConical } from "lucide-react"
import { fetchClusterById, type Cluster } from "@/services/clusters"
import ReactMarkdown from "react-markdown"

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  })
}

const getClusterStatusBadge = (status: string) => {
  const styles = {
    active: "bg-blue-100 text-blue-800",
    resolved: "bg-green-100 text-green-800",
    pending: "bg-yellow-100 text-yellow-800"
  }
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${styles[status as keyof typeof styles] || "bg-gray-100 text-gray-800"}`}>
      {status}
    </span>
  )
}

// Helper function to check if cluster is resolved
const isClusterResolved = (cluster: Cluster | null) => {
  return cluster?.status === "resolved"
}

// Dummy API call handlers
const handleApprove = (cluster: Cluster | null) => {
  if (isClusterResolved(cluster)) {
    alert("This cluster has already been resolved. No further actions can be taken.")
    return
  }
  console.log("API Call: Approve cluster", cluster?.id)
  // TODO: Replace with actual API call
  alert(`Cluster ${cluster?.id} approved (dummy action)`)
}

const handleSubmitFeedback = async (cluster: Cluster | null, feedback: string) => {
  if (isClusterResolved(cluster)) {
    alert("This cluster has already been resolved. No further actions can be taken.")
    return false
  }
  
  // TODO: Replace with actual API call - this will reprompt the AI assistant in the backend
  // Expected endpoint: POST /api/clusters/:id/feedback
  // Body: { feedback: string }
  try {
    console.log("API Call: Submit feedback for cluster", cluster?.id, feedback)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    alert(`Feedback submitted for cluster ${cluster?.id}. The AI assistant will regenerate the resolution based on your feedback.`)
    return true
  } catch (error) {
    console.error("Error submitting feedback:", error)
    alert("Failed to submit feedback. Please try again.")
    return false
  }
}

const handleDecline = (cluster: Cluster | null) => {
  if (isClusterResolved(cluster)) {
    alert("This cluster has already been resolved. No further actions can be taken.")
    return
  }
  console.log("API Call: Decline/Delete cluster", cluster?.id)
  // TODO: Replace with actual API call
  if (confirm(`Are you sure you want to decline/delete cluster ${cluster?.id}?`)) {
    alert(`Cluster ${cluster?.id} declined/deleted (dummy action)`)
  }
}

const handleDownloadMarkdown = (cluster: Cluster) => {
  console.log("Download as Markdown:", cluster.id)
  let markdown = `# ${cluster.title}\n\n## Summary\n${cluster.summary}\n\n## Main Topics\n${cluster.mainTopics.map(t => `- ${t}`).join('\n')}`
  
  if (cluster.resolution) {
    markdown += `\n\n## AI Generated Resolution\n\n${cluster.resolution}`
  }
  
  const blob = new Blob([markdown], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cluster-${cluster.id}.md`
  a.click()
  URL.revokeObjectURL(url)
}

const handleDownloadHTML = (cluster: Cluster) => {
  console.log("Download as HTML:", cluster.id)
  // TODO: Implement HTML download
  const html = `<!DOCTYPE html>
<html>
<head>
  <title>${cluster.title}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
    h1 { color: #333; }
    .summary { color: #666; line-height: 1.6; }
    .topics { margin-top: 20px; }
    .topic { display: inline-block; background: #f0f0f0; padding: 5px 10px; margin: 5px; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>${cluster.title}</h1>
  <div class="summary">${cluster.summary}</div>
  <div class="topics">
    <h2>Main Topics</h2>
    ${cluster.mainTopics.map(t => `<span class="topic">${t}</span>`).join('')}
  </div>
</body>
</html>`
  const blob = new Blob([html], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cluster-${cluster.id}.html`
  a.click()
  URL.revokeObjectURL(url)
}

export default function ClusterDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [cluster, setCluster] = useState<Cluster | null>(null)
  const [loading, setLoading] = useState(true)
  const [showFeedbackForm, setShowFeedbackForm] = useState(false)
  const [feedback, setFeedback] = useState("")
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const loadCluster = async () => {
      if (!id) return
      
      try {
        setLoading(true)
        const data = await fetchClusterById(id)
        setCluster(data)
      } catch (error) {
        console.error("Error loading cluster:", error)
      } finally {
        setLoading(false)
      }
    }

    loadCluster()
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading cluster...</p>
        </div>
      </div>
    )
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
    )
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
        <Card>
          <CardHeader>
            <CardTitle>Key Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <div className="mt-1">{getClusterStatusBadge(cluster.status)}</div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Created</p>
                <p className="font-medium text-sm">{formatDate(cluster.createdAt)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Last Updated</p>
                <p className="font-medium text-sm">{formatDate(cluster.updatedAt)}</p>
              </div>
            </div>
            
            {/* Area */}
            <div className="mt-4 pt-4 border-t">
              <p className="text-sm text-muted-foreground mb-2">Area</p>
              <p className="text-gray-700 leading-relaxed">{cluster.area ?? cluster.summary}</p>
            </div>

            {/* Main Topics */}
            {cluster.mainTopics && cluster.mainTopics.length > 0 && (
              <div className="mt-4 pt-4 border-t">
                <p className="text-sm text-muted-foreground mb-2">Main Topics</p>
                <div className="flex flex-wrap gap-2">
                  {cluster.mainTopics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md text-sm font-medium"
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
                const label = variantKey === "variantA" ? "Variant A" : "Variant B"
                const impressions = cluster[variantKey === "variantA" ? "variantAImpressions" : "variantBImpressions"] ?? 0
                const resolutions = cluster[variantKey === "variantA" ? "variantAResolutions" : "variantBResolutions"] ?? 0
                const conversion = impressions === 0 ? 0 : (resolutions / impressions) * 100

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
                )
              })}
            </div>

            <div className="rounded-lg bg-gray-50 p-4 text-xs text-gray-600">
              <p className="font-semibold text-gray-800 mb-1">Quick insights</p>
              <ul className="space-y-1">
                {(() => {
                  const variantAImpressions = cluster.variantAImpressions ?? 0
                  const variantBImpressions = cluster.variantBImpressions ?? 0
                  const variantAResolutions = cluster.variantAResolutions ?? 0
                  const variantBResolutions = cluster.variantBResolutions ?? 0
                  const variantAConversion = variantAImpressions === 0 ? 0 : (variantAResolutions / variantAImpressions) * 100
                  const variantBConversion = variantBImpressions === 0 ? 0 : (variantBResolutions / variantBImpressions) * 100
                  const conversionDifference = variantAConversion - variantBConversion

                  return (
                    <>
                      <li>
                        Variant A lift vs B:{" "}
                        <span className={`font-semibold ${conversionDifference >= 0 ? "text-green-700" : "text-red-600"}`}>
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
                  )
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
              <CardDescription>Markdown-formatted recommendations and solutions</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden flex flex-col">
              {cluster.resolution ? (
                <div className="prose prose-sm max-w-none overflow-y-auto flex-1 pr-2">
                  <ReactMarkdown
                    components={{
                      h1: ({node, ...props}) => <h1 className="text-2xl font-bold mt-6 mb-4 text-gray-900" {...props} />,
                      h2: ({node, ...props}) => <h2 className="text-xl font-semibold mt-5 mb-3 text-gray-900" {...props} />,
                      h3: ({node, ...props}) => <h3 className="text-lg font-semibold mt-4 mb-2 text-gray-900" {...props} />,
                      p: ({node, ...props}) => <p className="mb-4 text-gray-700 leading-relaxed" {...props} />,
                      ul: ({node, ...props}) => <ul className="list-disc pl-6 mb-4 space-y-1" {...props} />,
                      ol: ({node, ...props}) => <ol className="list-decimal pl-6 mb-4 space-y-1" {...props} />,
                      li: ({node, ...props}) => <li className="text-gray-700" {...props} />,
                      strong: ({node, ...props}) => <strong className="font-semibold text-gray-900" {...props} />,
                      code: ({node, ...props}) => <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800" {...props} />,
                    }}
                  >
                    {cluster.resolution}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center py-12">
                  <div className="text-center text-gray-500">
                    <Layers className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                    <p className="text-sm">Resolution is being generated...</p>
                    <p className="text-xs mt-1 text-gray-400">The AI-generated resolution will appear here once available</p>
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
                  onClick={() => handleApprove(cluster)}
                  disabled={isClusterResolved(cluster)}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title={isClusterResolved(cluster) ? "Cluster has already been resolved" : ""}
                >
                  <Check className="mr-2 h-4 w-4" />
                  Approve
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => {
                    if (isClusterResolved(cluster)) {
                      alert("This cluster has already been resolved. No further actions can be taken.")
                      return
                    }
                    setFeedback("")
                    setShowFeedbackForm(true)
                  }}
                  disabled={isClusterResolved(cluster)}
                  className="w-full disabled:opacity-50 disabled:cursor-not-allowed"
                  title={isClusterResolved(cluster) ? "Cluster has already been resolved" : ""}
                >
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Give Feedback
                </Button>
                <Button 
                  variant="destructive"
                  onClick={() => handleDecline(cluster)}
                  disabled={isClusterResolved(cluster)}
                  className="w-full disabled:opacity-50 disabled:cursor-not-allowed"
                  title={isClusterResolved(cluster) ? "Cluster has already been resolved" : ""}
                >
                  <X className="mr-2 h-4 w-4" />
                  Decline/Delete
                </Button>
              </div>
              
              {/* Resolved Notice */}
              {isClusterResolved(cluster) && (
                <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-md">
                  <p className="text-xs text-green-800 text-center">
                    ✓ This cluster has been resolved. No further actions are available.
                  </p>
                </div>
              )}

              {/* Download Options */}
              <div className="pt-4 border-t space-y-3">
                <p className="text-sm font-medium text-gray-700">Download</p>
                <Button 
                  variant="outline"
                  onClick={() => handleDownloadMarkdown(cluster)}
                  className="w-full"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download as Markdown
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => handleDownloadHTML(cluster)}
                  className="w-full"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download as HTML
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
                    <h3 className="font-semibold text-sm text-blue-900 mb-2">Tips for Effective Feedback</h3>
                    <ul className="text-sm text-blue-800 space-y-1.5 list-disc list-inside">
                      <li><strong>Be specific:</strong> Clearly describe what needs to be changed or improved</li>
                      <li><strong>Be clear:</strong> Use straightforward language to explain your requirements</li>
                      <li><strong>Provide context:</strong> Explain why the change is needed or what outcome you're seeking</li>
                      <li><strong>Give examples:</strong> If possible, provide examples of what you'd like to see</li>
                      <li><strong>Focus on one area:</strong> Address specific sections or aspects rather than everything at once</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Feedback Form */}
              <form
                onSubmit={async (e) => {
                  e.preventDefault()
                  if (!feedback.trim()) {
                    alert("Please provide feedback before submitting")
                    return
                  }
                  
                  if (isClusterResolved(cluster)) {
                    alert("This cluster has already been resolved. No further actions can be taken.")
                    setShowFeedbackForm(false)
                    setFeedback("")
                    return
                  }
                  
                  setSubmitting(true)
                  const success = await handleSubmitFeedback(cluster, feedback)
                  setSubmitting(false)
                  
                  if (success) {
                    setShowFeedbackForm(false)
                    setFeedback("")
                    // Optionally reload cluster data to show updated resolution
                    // await loadCluster()
                  }
                }}
                className="space-y-4"
              >
                <div>
                  <label htmlFor="feedback" className="block text-sm font-medium text-gray-700 mb-2">
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
                      setShowFeedbackForm(false)
                      setFeedback("")
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
  )
}

