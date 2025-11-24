import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Ticket, TrendingUp, Clock, CheckCircle, Upload, Layers, AlertCircle, ChevronDown, ChevronUp, Maximize2, X, Search } from "lucide-react"
import { fetchClusters, type Cluster } from "@/services/clusters"

// Dummy data - will be replaced with API calls
const dummyTickets = [
  {
    id: "1",
    title: "How do I reset my password?",
    status: "pending",
    priority: "high",
    createdAt: "2024-01-15T10:30:00Z",
    customer: "john.doe@example.com"
  },
  {
    id: "2",
    title: "Where can I find my order history?",
    status: "resolved",
    priority: "medium",
    createdAt: "2024-01-14T14:20:00Z",
    customer: "jane.smith@example.com"
  },
  {
    id: "3",
    title: "What is your return policy?",
    status: "pending",
    priority: "low",
    createdAt: "2024-01-15T09:15:00Z",
    customer: "bob.johnson@example.com"
  },
  {
    id: "4",
    title: "How do I contact customer support?",
    status: "in_review",
    priority: "medium",
    createdAt: "2024-01-13T16:45:00Z",
    customer: "alice.brown@example.com"
  },
]

const dummyStats = {
  totalTickets: 24,
  pendingTickets: 8,
  resolvedTickets: 12,
  avgResolutionTime: "2.5 hours"
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  })
}

const getStatusBadge = (status: string) => {
  const styles = {
    pending: "bg-yellow-100 text-yellow-800",
    resolved: "bg-green-100 text-green-800",
    in_review: "bg-blue-100 text-blue-800",
    declined: "bg-red-100 text-red-800"
  }
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status as keyof typeof styles] || "bg-gray-100 text-gray-800"}`}>
      {status.replace("_", " ")}
    </span>
  )
}

const getPriorityBadge = (priority: string) => {
  const styles = {
    high: "text-red-600 font-semibold",
    medium: "text-yellow-600 font-semibold",
    low: "text-green-600 font-semibold"
  }
  return (
    <span className={styles[priority as keyof typeof styles] || "text-gray-600"}>
      {priority}
    </span>
  )
}

// Dummy API call handler for CSV upload
const handleTicketDropIn = () => {
  console.log("API Call: Ticket Drop In (CSV)")
  // TODO: Replace with actual API call
  // This would typically open a file picker and upload the CSV
  alert("Ticket Drop In (CSV) - API call placeholder. This will upload a CSV file with tickets.")
}

const getClusterStatusBadge = (status: string) => {
  const styles = {
    active: "bg-blue-100 text-blue-800",
    resolved: "bg-green-100 text-green-800",
    pending: "bg-yellow-100 text-yellow-800"
  }
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status as keyof typeof styles] || "bg-gray-100 text-gray-800"}`}>
      {status}
    </span>
  )
}

const getClusterPriorityBadge = (priority: string) => {
  const styles = {
    high: "text-red-600 font-semibold",
    medium: "text-yellow-600 font-semibold",
    low: "text-green-600 font-semibold"
  }
  return (
    <span className={styles[priority as keyof typeof styles] || "text-gray-600"}>
      {priority}
    </span>
  )
}

export default function Dashboard() {
  const [clusters, setClusters] = useState<Cluster[]>([])
  const [clustersLoading, setClustersLoading] = useState(true)
  const [clustersExpanded, setClustersExpanded] = useState(false)
  const [clustersExpandedModal, setClustersExpandedModal] = useState(false)
  const [ticketsExpandedModal, setTicketsExpandedModal] = useState(false)
  
  // Filter states for compact view clusters
  const [clusterSearch, setClusterSearch] = useState("")
  const [clusterPriorityFilter, setClusterPriorityFilter] = useState<string>("all")
  const [clusterStatusFilter, setClusterStatusFilter] = useState<string>("all")
  
  // Filter states for modal clusters (separate from compact view)
  const [clusterModalSearch, setClusterModalSearch] = useState("")
  const [clusterModalPriorityFilter, setClusterModalPriorityFilter] = useState<string>("all")
  const [clusterModalStatusFilter, setClusterModalStatusFilter] = useState<string>("all")
  
  // Filter states for compact view tickets
  const [ticketSearch, setTicketSearch] = useState("")
  
  // Filter states for modal tickets (separate from compact view)
  const [ticketModalSearch, setTicketModalSearch] = useState("")
  
  // Global search state
  const [globalSearch, setGlobalSearch] = useState("")
  const [showGlobalSearchResults, setShowGlobalSearchResults] = useState(false)
  
  // Reset modal filters when modal closes
  const handleCloseClustersModal = () => {
    setClustersExpandedModal(false)
    setClusterModalSearch("")
    setClusterModalPriorityFilter("all")
    setClusterModalStatusFilter("all")
  }
  
  const handleCloseTicketsModal = () => {
    setTicketsExpandedModal(false)
    setTicketModalSearch("")
  }

  useEffect(() => {
    const loadClusters = async () => {
      try {
        setClustersLoading(true)
        const data = await fetchClusters()
        setClusters(data)
      } catch (error) {
        console.error("Error loading clusters:", error)
      } finally {
        setClustersLoading(false)
      }
    }

    loadClusters()
  }, [])

  const CLUSTERS_PREVIEW_COUNT = 6
  
  // Filter clusters for compact view
  const filteredClusters = clusters.filter(cluster => {
    const matchesSearch = clusterSearch === "" || 
      cluster.title.toLowerCase().includes(clusterSearch.toLowerCase()) ||
      cluster.summary.toLowerCase().includes(clusterSearch.toLowerCase())
    const matchesPriority = clusterPriorityFilter === "all" || cluster.priority === clusterPriorityFilter
    const matchesStatus = clusterStatusFilter === "all" || cluster.status === clusterStatusFilter
    return matchesSearch && matchesPriority && matchesStatus
  })
  
  // Filter clusters for modal view (separate filters)
  const filteredClustersModal = clusters.filter(cluster => {
    const matchesSearch = clusterModalSearch === "" || 
      cluster.title.toLowerCase().includes(clusterModalSearch.toLowerCase()) ||
      cluster.summary.toLowerCase().includes(clusterModalSearch.toLowerCase())
    const matchesPriority = clusterModalPriorityFilter === "all" || cluster.priority === clusterModalPriorityFilter
    const matchesStatus = clusterModalStatusFilter === "all" || cluster.status === clusterModalStatusFilter
    return matchesSearch && matchesPriority && matchesStatus
  })
  
  // Filter tickets for compact view
  const filteredTickets = dummyTickets.filter(ticket => {
    const matchesSearch = ticketSearch === "" || 
      ticket.title.toLowerCase().includes(ticketSearch.toLowerCase())
    return matchesSearch
  })
  
  // Filter tickets for modal view (separate filters)
  const filteredTicketsModal = dummyTickets.filter(ticket => {
    const matchesSearch = ticketModalSearch === "" || 
      ticket.title.toLowerCase().includes(ticketModalSearch.toLowerCase())
    return matchesSearch
  })
  
  // Apply search filter to compact view clusters
  const displayedClusters = clustersExpanded ? filteredClusters : filteredClusters.slice(0, CLUSTERS_PREVIEW_COUNT)
  const hasMoreClusters = filteredClusters.length > CLUSTERS_PREVIEW_COUNT
  
  // Apply search filter to compact view tickets (for consistency, though we can show all in compact view)
  const displayedTickets = filteredTickets
  
  // Global search across tickets and clusters
  const globalSearchResults = {
    clusters: globalSearch === "" ? [] : clusters.filter(cluster => 
      cluster.title.toLowerCase().includes(globalSearch.toLowerCase()) ||
      cluster.summary.toLowerCase().includes(globalSearch.toLowerCase()) ||
      cluster.mainTopics.some(topic => topic.toLowerCase().includes(globalSearch.toLowerCase()))
    ).slice(0, 5), // Limit to 5 results
    tickets: globalSearch === "" ? [] : dummyTickets.filter(ticket => 
      ticket.title.toLowerCase().includes(globalSearch.toLowerCase()) ||
      ticket.customer.toLowerCase().includes(globalSearch.toLowerCase())
    ).slice(0, 5) // Limit to 5 results
  }
  
  const totalGlobalResults = globalSearchResults.clusters.length + globalSearchResults.tickets.length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Overview of tickets and statistics</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Global Search Bar */}
          <div className="relative">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search dashboard..."
                value={globalSearch}
                onChange={(e) => {
                  setGlobalSearch(e.target.value)
                  setShowGlobalSearchResults(e.target.value.length > 0)
                }}
                onFocus={() => {
                  if (globalSearch.length > 0) {
                    setShowGlobalSearchResults(true)
                  }
                }}
                onBlur={() => {
                  // Delay hiding to allow clicks on results
                  setTimeout(() => setShowGlobalSearchResults(false), 200)
                }}
                className="w-64 pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
              />
            </div>
            
            {/* Search Results Dropdown */}
            {showGlobalSearchResults && totalGlobalResults > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
                <div className="p-2">
                  {/* Clusters Results */}
                  {globalSearchResults.clusters.length > 0 && (
                    <div className="mb-2">
                      <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-2">
                        <Layers className="h-3 w-3" />
                        Clusters ({globalSearchResults.clusters.length})
                      </div>
                      {globalSearchResults.clusters.map((cluster) => (
                        <Link
                          key={cluster.id}
                          to={`/cluster/${cluster.id}`}
                          onClick={() => {
                            setGlobalSearch("")
                            setShowGlobalSearchResults(false)
                          }}
                          className="block px-3 py-2 hover:bg-gray-50 rounded transition-colors border-b last:border-b-0"
                        >
                          <div className="font-medium text-sm text-gray-900">{cluster.title}</div>
                          <div className="text-xs text-gray-500 mt-1 line-clamp-1">{cluster.summary}</div>
                          <div className="flex items-center gap-2 mt-2">
                            {getClusterStatusBadge(cluster.status)}
                            {getClusterPriorityBadge(cluster.priority)}
                            <span className="text-xs text-gray-500">
                              {cluster.ticketCount} tickets
                            </span>
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                  
                  {/* Tickets Results */}
                  {globalSearchResults.tickets.length > 0 && (
                    <div>
                      <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-2">
                        <Ticket className="h-3 w-3" />
                        Tickets ({globalSearchResults.tickets.length})
                      </div>
                      {globalSearchResults.tickets.map((ticket) => (
                        <Link
                          key={ticket.id}
                          to={`/ticket/${ticket.id}`}
                          onClick={() => {
                            setGlobalSearch("")
                            setShowGlobalSearchResults(false)
                          }}
                          className="block px-3 py-2 hover:bg-gray-50 rounded transition-colors border-b last:border-b-0"
                        >
                          <div className="font-medium text-sm text-gray-900">{ticket.title}</div>
                          <div className="text-xs text-gray-500 mt-1">{ticket.customer}</div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* No Results Message */}
            {showGlobalSearchResults && globalSearch.length > 0 && totalGlobalResults === 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 p-4">
                <div className="text-center text-sm text-gray-500">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p>No results found for "{globalSearch}"</p>
                </div>
              </div>
            )}
          </div>
          
        <Button onClick={handleTicketDropIn} variant="outline">
          <Upload className="mr-2 h-4 w-4" />
          Ticket Drop In (CSV)
        </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tickets</CardTitle>
            <Ticket className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dummyStats.totalTickets}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dummyStats.pendingTickets}</div>
            <p className="text-xs text-muted-foreground">Awaiting review</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolved</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dummyStats.resolvedTickets}</div>
            <p className="text-xs text-muted-foreground">Completed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Resolution</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dummyStats.avgResolutionTime}</div>
            <p className="text-xs text-muted-foreground">Time to resolve</p>
          </CardContent>
        </Card>
      </div>

      {/* Clusters and Tickets Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative">
        {/* Clusters Section */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Layers className="h-4 w-4" />
                  Ticket Clusters
                </CardTitle>
                <CardDescription className="text-xs mt-1">
                  Main topics where multiple tickets are summarized
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                {!clustersLoading && clusters.length > CLUSTERS_PREVIEW_COUNT && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setClustersExpanded(!clustersExpanded)}
                    className="flex items-center gap-1 h-7 text-xs"
                  >
                    {clustersExpanded ? (
                      <>
                        <ChevronUp className="h-3 w-3" />
                        Collapse
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-3 w-3" />
                        Expand ({clusters.length})
                      </>
                    )}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setClustersExpandedModal(true)
                    // Reset modal filters when opening
                    setClusterModalSearch("")
                    setClusterModalPriorityFilter("all")
                    setClusterModalStatusFilter("all")
                  }}
                  className="flex items-center gap-1 h-7 text-xs"
                  title="Expand with filters"
                >
                  <Maximize2 className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0 space-y-3">
            {/* Search Bar */}
            {!clustersLoading && clusters.length > 0 && (
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search clusters..."
                  value={clusterSearch}
                  onChange={(e) => setClusterSearch(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                />
              </div>
            )}
            
            {clustersLoading ? (
              <div className="flex items-center justify-center py-4">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600 text-xs">Loading clusters...</p>
                </div>
              </div>
            ) : clusters.length === 0 ? (
              <div className="text-center py-4 text-gray-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-xs">No clusters found</p>
              </div>
            ) : filteredClusters.length === 0 ? (
              <div className="text-center py-4 text-gray-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-xs">No clusters match your search</p>
              </div>
            ) : (
              <div className="space-y-0.5 max-h-96 overflow-y-auto">
                {displayedClusters.map((cluster) => (
                  <Link
                    key={cluster.id}
                    to={`/cluster/${cluster.id}`}
                    className="flex items-center justify-between p-2.5 hover:bg-gray-50 rounded transition-colors border-b last:border-b-0"
                  >
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <h4 className="font-medium text-sm text-gray-900 truncate hover:text-primary-600 transition-colors">
                        {cluster.title}
                      </h4>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                      <span className="text-xs text-gray-600 flex items-center gap-1">
                        <Ticket className="h-3 w-3" />
                        {cluster.ticketCount}
                      </span>
                      {getClusterStatusBadge(cluster.status)}
                      {getClusterPriorityBadge(cluster.priority)}
                    </div>
                  </Link>
                ))}
                {hasMoreClusters && !clustersExpanded && (
                  <div className="text-center pt-2">
                    <p className="text-xs text-muted-foreground">
                      Showing {displayedClusters.length} of {filteredClusters.length} clusters
                    </p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Tickets Section */}
      <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Ticket className="h-4 w-4" />
                  Recent Tickets
                </CardTitle>
                <CardDescription className="text-xs mt-1">
                  List of tickets requiring attention
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setTicketsExpandedModal(true)
                  // Reset modal filters when opening
                  setTicketModalSearch("")
                  setTicketModalPriorityFilter("all")
                  setTicketModalStatusFilter("all")
                }}
                className="flex items-center gap-1 h-7 text-xs"
                title="Expand with filters"
              >
                <Maximize2 className="h-3 w-3" />
              </Button>
            </div>
        </CardHeader>
          <CardContent className="pt-0 space-y-3">
            {/* Search Bar */}
            {dummyTickets.length > 0 && (
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search tickets..."
                  value={ticketSearch}
                  onChange={(e) => setTicketSearch(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                />
              </div>
            )}
            
            {dummyTickets.length === 0 ? (
              <div className="text-center py-4 text-gray-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-xs">No tickets found</p>
              </div>
            ) : filteredTickets.length === 0 ? (
              <div className="text-center py-4 text-gray-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-xs">No tickets match your search</p>
              </div>
            ) : (
            <div className="space-y-0.5 max-h-96 overflow-y-auto">
              {displayedTickets.map((ticket) => (
                    <Link 
                  key={ticket.id}
                      to={`/ticket/${ticket.id}`}
                  className="flex items-center justify-between p-2.5 hover:bg-gray-50 rounded transition-colors border-b last:border-b-0"
                    >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <h4 className="font-medium text-sm text-gray-900 truncate hover:text-primary-600 transition-colors">
                      {ticket.title}
                    </h4>
                  </div>
                </Link>
              ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Clusters Expanded Modal */}
      {clustersExpandedModal && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={handleCloseClustersModal}
        >
          <Card 
            className="w-full max-w-4xl max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader className="pb-3 border-b">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <Layers className="h-5 w-5" />
                    Ticket Clusters
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Filter and search through all clusters
                  </CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCloseClustersModal}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-4 space-y-4 flex-1 overflow-hidden flex flex-col">
              {/* Filters */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search clusters..."
                    value={clusterModalSearch}
                    onChange={(e) => setClusterModalSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                  />
                </div>
                <select
                  value={clusterModalPriorityFilter}
                  onChange={(e) => setClusterModalPriorityFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                >
                  <option value="all">All Priorities</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
                <select
                  value={clusterModalStatusFilter}
                  onChange={(e) => setClusterModalStatusFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                >
                  <option value="all">All Statuses</option>
                  <option value="active">Active</option>
                  <option value="pending">Pending</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>

              {/* Results Count */}
              <div className="text-sm text-gray-600">
                Showing {filteredClustersModal.length} of {clusters.length} clusters
              </div>

              {/* Clusters List */}
              <div className="space-y-1 overflow-y-auto flex-1">
                {filteredClustersModal.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <AlertCircle className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                    <p>No clusters found matching your filters</p>
                  </div>
                ) : (
                  filteredClustersModal.map((cluster) => (
                    <Link
                      key={cluster.id}
                      to={`/cluster/${cluster.id}`}
                      onClick={handleCloseClustersModal}
                      className="flex items-center justify-between p-3 hover:bg-gray-50 rounded transition-colors border-b last:border-b-0"
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <h4 className="font-medium text-sm text-gray-900 hover:text-primary-600 transition-colors">
                          {cluster.title}
                        </h4>
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0 ml-4">
                        <span className="text-xs text-gray-600 flex items-center gap-1">
                          <Ticket className="h-3 w-3" />
                          {cluster.ticketCount}
                        </span>
                        {getClusterStatusBadge(cluster.status)}
                        {getClusterPriorityBadge(cluster.priority)}
                      </div>
                    </Link>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tickets Expanded Modal */}
      {ticketsExpandedModal && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={handleCloseTicketsModal}
        >
          <Card 
            className="w-full max-w-4xl max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader className="pb-3 border-b">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <Ticket className="h-5 w-5" />
                    Recent Tickets
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Filter and search through all tickets
                  </CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCloseTicketsModal}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-4 space-y-4 flex-1 overflow-hidden flex flex-col">
              {/* Filters */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search tickets..."
                  value={ticketModalSearch}
                  onChange={(e) => setTicketModalSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                />
              </div>

              {/* Results Count */}
              <div className="text-sm text-gray-600">
                Showing {filteredTicketsModal.length} of {dummyTickets.length} tickets
              </div>

              {/* Tickets List */}
              <div className="space-y-1 overflow-y-auto flex-1">
                {filteredTicketsModal.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <AlertCircle className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                    <p>No tickets found matching your filters</p>
                  </div>
                ) : (
                  filteredTicketsModal.map((ticket) => (
                    <Link 
                      key={ticket.id}
                      to={`/ticket/${ticket.id}`}
                      onClick={handleCloseTicketsModal}
                      className="flex items-center justify-between p-3 hover:bg-gray-50 rounded transition-colors border-b last:border-b-0"
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <h4 className="font-medium text-sm text-gray-900 hover:text-primary-600 transition-colors">
                          {ticket.title}
                        </h4>
                      </div>
                    </Link>
                  ))
                )}
              </div>
        </CardContent>
      </Card>
        </div>
      )}
    </div>
  )
}

