import { Link } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Ticket, TrendingUp, Clock, CheckCircle, Upload } from "lucide-react"

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

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Overview of tickets and statistics</p>
        </div>
        <Button onClick={handleTicketDropIn} variant="outline">
          <Upload className="mr-2 h-4 w-4" />
          Ticket Drop In (CSV)
        </Button>
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

      {/* Tickets Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Tickets</CardTitle>
          <CardDescription>List of all tickets requiring attention</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dummyTickets.map((ticket) => (
                <TableRow key={ticket.id}>
                  <TableCell className="font-medium">
                    <Link 
                      to={`/ticket/${ticket.id}`}
                      className="hover:text-primary-600 hover:underline"
                    >
                      {ticket.title}
                    </Link>
                  </TableCell>
                  <TableCell>{ticket.customer}</TableCell>
                  <TableCell>{getStatusBadge(ticket.status)}</TableCell>
                  <TableCell>{getPriorityBadge(ticket.priority)}</TableCell>
                  <TableCell>{formatDate(ticket.createdAt)}</TableCell>
                  <TableCell className="text-right">
                    <Link 
                      to={`/ticket/${ticket.id}`}
                      className="text-primary-600 hover:text-primary-800 hover:underline text-sm"
                    >
                      View →
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

