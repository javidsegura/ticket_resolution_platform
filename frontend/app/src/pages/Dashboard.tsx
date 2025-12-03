import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Ticket,
  TrendingUp,
  Clock,
  CheckCircle,
  Upload,
  Layers,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Maximize2,
  X,
  Search,
  FlaskConical,
} from "lucide-react";
import { fetchClusters, type Cluster } from "@/services/clusters";
import {
  fetchABTestingTotals,
  type ABTestingTotals,
} from "@/services/analytics";
import { fetchTickets, type Ticket as ApiTicket } from "@/services/tickets";

const dummyStats = {
  totalTickets: 24,
  pendingTickets: 8,
  resolvedTickets: 12,
  avgResolutionTime: "2.5 hours",
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// Dummy handlers for manual uploads
const handleTicketDropIn = () => {
  console.log("API Call: Ticket Drop In (CSV)");
  // TODO: Replace with actual API call
  alert("Ticket Drop In (CSV) - This will upload a CSV file with tickets.");
};

const handleCompanyDocsDropIn = () => {
  console.log("API Call: Company Docs Drop In (PDF only)");
  // TODO: Replace with actual API call and PDF file picker restriction
  alert("Company Docs Drop In - Only PDF files are accepted in this upload.");
};

const getClusterStatusBadge = (status: string) => {
  const styles = {
    active: "bg-blue-100 text-blue-800",
    resolved: "bg-green-100 text-green-800",
    pending: "bg-yellow-100 text-yellow-800",
  };
  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status as keyof typeof styles] || "bg-gray-100 text-gray-800"}`}
    >
      {status}
    </span>
  );
};

export default function Dashboard() {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [clustersLoading, setClustersLoading] = useState(true);
  const [clustersExpanded, setClustersExpanded] = useState(false);
  const [clustersExpandedModal, setClustersExpandedModal] = useState(false);
  const [ticketsExpandedModal, setTicketsExpandedModal] = useState(false);

  // Filter states for compact view clusters
  const [clusterSearch, setClusterSearch] = useState("");
  const clusterStatusFilter = "all";

  // Filter states for modal clusters (separate from compact view)
  const [clusterModalSearch, setClusterModalSearch] = useState("");
  const [clusterModalStatusFilter, setClusterModalStatusFilter] =
    useState<string>("all");

  // Filter states for compact view tickets
  const [ticketSearch, setTicketSearch] = useState("");

  // Filter states for modal tickets (separate from compact view)
  const [ticketModalSearch, setTicketModalSearch] = useState("");

  // Global search state
  const [globalSearch, setGlobalSearch] = useState("");
  const [showGlobalSearchResults, setShowGlobalSearchResults] = useState(false);
  const [abTestingTotals, setAbTestingTotals] =
    useState<ABTestingTotals | null>(null);
  const [abTestingLoading, setAbTestingLoading] = useState(true);
  const [abTestingError, setAbTestingError] = useState<string | null>(null);
  const [tickets, setTickets] = useState<ApiTicket[]>([]);
  const [ticketsLoading, setTicketsLoading] = useState(true);
  const [ticketsError, setTicketsError] = useState<string | null>(null);

  // Reset modal filters when modal closes
  const handleCloseClustersModal = () => {
    setClustersExpandedModal(false);
    setClusterModalSearch("");
    setClusterModalStatusFilter("all");
  };

  const handleCloseTicketsModal = () => {
    setTicketsExpandedModal(false);
    setTicketModalSearch("");
  };

  useEffect(() => {
    const loadClusters = async () => {
      try {
        setClustersLoading(true);
        const data = await fetchClusters();
        setClusters(data);
      } catch (error) {
        console.error("Error loading clusters:", error);
      } finally {
        setClustersLoading(false);
      }
    };

    const loadABTestingTotals = async () => {
      try {
        setAbTestingLoading(true);
        const data = await fetchABTestingTotals();
        setAbTestingTotals(data);
        setAbTestingError(null);
      } catch (error) {
        console.error("Error loading AB testing data:", error);
        setAbTestingError("Unable to load A/B test performance right now.");
      } finally {
        setAbTestingLoading(false);
      }
    };

    loadClusters();
    loadABTestingTotals();
    const loadTickets = async () => {
      try {
        setTicketsLoading(true);
        const data = await fetchTickets();
        setTickets(data.tickets);
        setTicketsError(null);
      } catch (error) {
        console.error("Error loading tickets:", error);
        setTicketsError("Unable to load tickets right now.");
      } finally {
        setTicketsLoading(false);
      }
    };
    loadTickets();
  }, []);

  const CLUSTERS_PREVIEW_COUNT = 6;

  // Filter clusters for compact view
  const filteredClusters = clusters.filter((cluster) => {
    const matchesSearch =
      clusterSearch === "" ||
      cluster.title.toLowerCase().includes(clusterSearch.toLowerCase()) ||
      cluster.summary.toLowerCase().includes(clusterSearch.toLowerCase());
    const matchesStatus =
      clusterStatusFilter === "all" || cluster.status === clusterStatusFilter;
    return matchesSearch && matchesStatus;
  });

  // Filter clusters for modal view (separate filters)
  const filteredClustersModal = clusters.filter((cluster) => {
    const matchesSearch =
      clusterModalSearch === "" ||
      cluster.title.toLowerCase().includes(clusterModalSearch.toLowerCase()) ||
      cluster.summary.toLowerCase().includes(clusterModalSearch.toLowerCase());
    const matchesStatus =
      clusterModalStatusFilter === "all" ||
      cluster.status === clusterModalStatusFilter;
    return matchesSearch && matchesStatus;
  });

  // Filter tickets for compact view
  const filteredTickets = tickets.filter((ticket) => {
    const matchesSearch =
      ticketSearch === "" ||
      ticket.subject.toLowerCase().includes(ticketSearch.toLowerCase()) ||
      (ticket.body?.toLowerCase().includes(ticketSearch.toLowerCase()) ??
        false);
    return matchesSearch;
  });

  // Filter tickets for modal view (separate filters)
  const filteredTicketsModal = tickets.filter((ticket) => {
    const matchesSearch =
      ticketModalSearch === "" ||
      ticket.subject.toLowerCase().includes(ticketModalSearch.toLowerCase()) ||
      (ticket.body?.toLowerCase().includes(ticketModalSearch.toLowerCase()) ??
        false);
    return matchesSearch;
  });

  // Apply search filter to compact view clusters
  const displayedClusters = clustersExpanded
    ? filteredClusters
    : filteredClusters.slice(0, CLUSTERS_PREVIEW_COUNT);
  const hasMoreClusters = filteredClusters.length > CLUSTERS_PREVIEW_COUNT;

  // Apply search filter to compact view tickets (for consistency, though we can show all in compact view)
  const displayedTickets = filteredTickets;

  // Global search across tickets and clusters
  const globalSearchResults = {
    clusters:
      globalSearch === ""
        ? []
        : clusters
            .filter(
              (cluster) =>
                cluster.title
                  .toLowerCase()
                  .includes(globalSearch.toLowerCase()) ||
                cluster.summary
                  .toLowerCase()
                  .includes(globalSearch.toLowerCase()) ||
                cluster.mainTopics.some((topic) =>
                  topic.toLowerCase().includes(globalSearch.toLowerCase()),
                ),
            )
            .slice(0, 5), // Limit to 5 results
    tickets:
      globalSearch === ""
        ? []
        : tickets
            .filter(
              (ticket) =>
                ticket.subject
                  .toLowerCase()
                  .includes(globalSearch.toLowerCase()) ||
                (ticket.body
                  ?.toLowerCase()
                  .includes(globalSearch.toLowerCase()) ??
                  false),
            )
            .slice(0, 5), // Limit to 5 results
  };

  const totalGlobalResults =
    globalSearchResults.clusters.length + globalSearchResults.tickets.length;

  const variantAConversion = abTestingTotals
    ? abTestingTotals.variant_a_impressions === 0
      ? 0
      : (abTestingTotals.variant_a_resolutions /
          abTestingTotals.variant_a_impressions) *
        100
    : 0;

  const variantBConversion = abTestingTotals
    ? abTestingTotals.variant_b_impressions === 0
      ? 0
      : (abTestingTotals.variant_b_resolutions /
          abTestingTotals.variant_b_impressions) *
        100
    : 0;

  const conversionDifference = abTestingTotals
    ? variantAConversion - variantBConversion
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Overview of tickets and statistics
          </p>
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
                  setGlobalSearch(e.target.value);
                  setShowGlobalSearchResults(e.target.value.length > 0);
                }}
                onFocus={() => {
                  if (globalSearch.length > 0) {
                    setShowGlobalSearchResults(true);
                  }
                }}
                onBlur={() => {
                  // Delay hiding to allow clicks on results
                  setTimeout(() => setShowGlobalSearchResults(false), 200);
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
                            setGlobalSearch("");
                            setShowGlobalSearchResults(false);
                          }}
                          className="block px-3 py-2 hover:bg-gray-50 rounded transition-colors border-b last:border-b-0"
                        >
                          <div className="font-medium text-sm text-gray-900">
                            {cluster.title}
                          </div>
                          <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                            {cluster.summary}
                          </div>
                          <div className="flex items-center gap-2 mt-2">
                            {getClusterStatusBadge(cluster.status)}
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
                            setGlobalSearch("");
                            setShowGlobalSearchResults(false);
                          }}
                          className="block px-3 py-2 hover:bg-gray-50 rounded transition-colors border-b last:border-b-0"
                        >
                          <div className="font-medium text-sm text-gray-900">
                            {ticket.subject}
                          </div>
                          <div className="text-xs text-gray-500 mt-1 line-clamp-1">
                            {ticket.body}
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* No Results Message */}
            {showGlobalSearchResults &&
              globalSearch.length > 0 &&
              totalGlobalResults === 0 && (
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
          <Button onClick={handleCompanyDocsDropIn} variant="outline">
            <Upload className="mr-2 h-4 w-4" />
            Company Docs (PDF)
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
            <div className="text-2xl font-bold">
              {dummyStats.pendingTickets}
            </div>
            <p className="text-xs text-muted-foreground">Awaiting review</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolved</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dummyStats.resolvedTickets}
            </div>
            <p className="text-xs text-muted-foreground">Completed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Avg Resolution
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dummyStats.avgResolutionTime}
            </div>
            <p className="text-xs text-muted-foreground">Time to resolve</p>
          </CardContent>
        </Card>
      </div>

      {/* Clusters, AB Testing and Tickets */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.2fr_1fr_0.5fr] relative">
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
                {!clustersLoading &&
                  clusters.length > CLUSTERS_PREVIEW_COUNT && (
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
                    setClustersExpandedModal(true);
                    // Reset modal filters when opening
                    setClusterModalSearch("");
                    setClusterModalStatusFilter("all");
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
                  <p className="mt-2 text-gray-600 text-xs">
                    Loading clusters...
                  </p>
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
                      {getClusterStatusBadge(cluster.status)}
                    </div>
                  </Link>
                ))}
                {hasMoreClusters && !clustersExpanded && (
                  <div className="text-center pt-2">
                    <p className="text-xs text-muted-foreground">
                      Showing {displayedClusters.length} of{" "}
                      {filteredClusters.length} clusters
                    </p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* AB Testing Section */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <FlaskConical className="h-4 w-4" />
                  A/B Testing Performance
                </CardTitle>
                <CardDescription className="text-xs mt-1">
                  Impressions, resolutions, and conversion rates
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {abTestingLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600 text-xs">
                    Loading experiment data...
                  </p>
                </div>
              </div>
            ) : abTestingError ? (
              <div className="text-center py-8 text-gray-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-xs">{abTestingError}</p>
              </div>
            ) : abTestingTotals ? (
              <div className="space-y-5">
                <div className="grid grid-cols-1 gap-4">
                  {(["variant_a", "variant_b"] as const).map((variantKey) => {
                    const label =
                      variantKey === "variant_a" ? "Variant A" : "Variant B";
                    const impressions =
                      abTestingTotals[`${variantKey}_impressions` as const];
                    const resolutions =
                      abTestingTotals[`${variantKey}_resolutions` as const];
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
                  <p className="font-semibold text-gray-800 mb-1">
                    Quick insights
                  </p>
                  <ul className="space-y-1">
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
                        {abTestingTotals.variant_a_impressions +
                          abTestingTotals.variant_b_impressions}
                      </span>
                    </li>
                    <li>
                      Total resolutions:{" "}
                      <span className="font-semibold text-gray-900">
                        {abTestingTotals.variant_a_resolutions +
                          abTestingTotals.variant_b_resolutions}
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            ) : null}
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
                  setTicketsExpandedModal(true);
                  // Reset modal filters when opening
                  setTicketModalSearch("");
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
            {tickets.length > 0 && (
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

            {ticketsLoading ? (
              <div className="flex items-center justify-center py-4">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600 text-xs">
                    Loading tickets...
                  </p>
                </div>
              </div>
            ) : ticketsError ? (
              <div className="text-center py-4 text-gray-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-xs">{ticketsError}</p>
              </div>
            ) : tickets.length === 0 ? (
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
                        {ticket.subject}
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                Showing {filteredClustersModal.length} of {clusters.length}{" "}
                clusters
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
                        {getClusterStatusBadge(cluster.status)}
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
                Showing {filteredTicketsModal.length} of {tickets.length}{" "}
                tickets
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
                          {ticket.subject}
                        </h4>
                      </div>
                      <div className="text-xs text-gray-500 text-right">
                        <p className="line-clamp-1">{ticket.body}</p>
                        <p className="mt-1">{formatDate(ticket.created_at)}</p>
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
  );
}
