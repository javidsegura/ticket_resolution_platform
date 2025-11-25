import { useParams, useNavigate } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, ArrowLeft } from "lucide-react"

// Dummy data - will be replaced with API call
const dummyTicketData: Record<string, {
  id: string
  title: string
  customer: string
  status: string
  priority: string
  createdAt: string
  question: string
  resolution: string
}> = {
  "1": {
    id: "1",
    title: "How do I reset my password?",
    customer: "john.doe@example.com",
    status: "pending",
    priority: "high",
    createdAt: "2024-01-15T10:30:00Z",
    question: "I forgot my password and can't find the reset link on your website. Where should I look?",
    resolution: `**Website Improvement Recommendation:**

Add a prominent "Forgot Password?" link directly on the login page, positioned below the password input field. Currently, users are having difficulty locating this feature.

**FAQ Addition:**
Create a new FAQ entry titled "How to Reset Your Password" with the following content:
1. Click the "Forgot Password?" link on the login page
2. Enter your registered email address
3. Check your inbox (and spam folder) for the reset link
4. Click the link and follow the prompts to create a new password

**Layout Enhancement:**
Consider adding a visual indicator (icon or highlighted text) next to the "Forgot Password?" link to improve discoverability. Additionally, add a "Resend Reset Link" option if the email doesn't arrive within 5 minutes.`
  },
  "2": {
    id: "2",
    title: "Where can I find my order history?",
    customer: "jane.smith@example.com",
    status: "resolved",
    priority: "medium",
    createdAt: "2024-01-14T14:20:00Z",
    question: "I placed an order last week but can't find where to view my order history on your website. Can you help?",
    resolution: `**Website Layout Improvement:**

The order history section should be more prominently displayed in the user account dashboard. Currently, it's buried in a submenu.

**Recommendation:**
1. Add an "Order History" card/widget on the main dashboard page with a preview of recent orders
2. Include a direct link to the full order history page in the main navigation menu under "My Account"
3. Add breadcrumb navigation to help users understand their location on the site

**FAQ Update:**
Add to FAQ: "How do I view my past orders?" with step-by-step instructions including screenshots showing the exact location in the account dashboard.`
  },
  "3": {
    id: "3",
    title: "What is your return policy?",
    customer: "bob.johnson@example.com",
    status: "pending",
    priority: "low",
    createdAt: "2024-01-15T09:15:00Z",
    question: "I want to return a product I purchased. What is your return policy and how long do I have?",
    resolution: `**FAQ Enhancement:**

Create a comprehensive "Returns & Refunds" section in the FAQ with the following structure:
- Return window: 30 days from purchase date
- Condition requirements for returns
- Step-by-step return process
- Refund timeline information
- Contact information for return inquiries

**Website Layout Suggestion:**
Add a "Returns & Exchanges" link in the footer navigation, as this is a common customer inquiry. Consider adding a dedicated "Policies" page that consolidates return policy, shipping policy, and privacy policy for easy access.

**Support Area Improvement:**
Create a self-service return request form that allows customers to initiate returns directly from the website, reducing support ticket volume.`
  },
  "4": {
    id: "4",
    title: "How do I contact customer support?",
    customer: "alice.brown@example.com",
    status: "in_review",
    priority: "medium",
    createdAt: "2024-01-13T16:45:00Z",
    question: "I've been looking for a way to contact customer support but can't find a phone number or email address anywhere on your website.",
    resolution: `**Critical Website Layout Issue:**

The contact information is not easily discoverable, which is causing customer frustration and increased support requests.

**Immediate Recommendations:**
1. Add a "Contact Us" link in the main navigation menu (header)
2. Create a dedicated "Contact" page with multiple contact methods:
   - Support email address
   - Phone number (if available)
   - Live chat widget
   - Contact form
   - Business hours
3. Add contact information in the website footer on every page
4. Include a "Get Help" button in the account dashboard

**FAQ Addition:**
Add "How can I reach customer support?" as one of the top FAQ entries with all available contact methods and expected response times.

**Support Area Enhancement:**
Implement a help center with categorized articles and a search function to help customers find answers before needing to contact support directly.`
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  })
}

// Download handlers
const handleDownloadMarkdown = (ticket: typeof dummyTicketData[string]) => {
  const markdown = `# ${ticket.title}\n\n## Ticket Information\n- **ID:** ${ticket.id}\n- **Customer:** ${ticket.customer}\n- **Created:** ${formatDate(ticket.createdAt)}\n\n## Customer Question\n\n${ticket.question}`
  
  const blob = new Blob([markdown], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ticket-${ticket.id}.md`
  a.click()
  URL.revokeObjectURL(url)
}

const handleDownloadHTML = (ticket: typeof dummyTicketData[string]) => {
  const html = `<!DOCTYPE html>
<html>
<head>
  <title>${ticket.title}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }
    h1 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }
    h2 { color: #555; margin-top: 30px; }
    .info { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }
    .info p { margin: 5px 0; }
    .question { margin: 20px 0; padding: 15px; background: #fafafa; border-left: 4px solid #4a90e2; }
  </style>
</head>
<body>
  <h1>${ticket.title}</h1>
  <div class="info">
    <h2>Ticket Information</h2>
    <p><strong>ID:</strong> ${ticket.id}</p>
    <p><strong>Customer:</strong> ${ticket.customer}</p>
    <p><strong>Created:</strong> ${formatDate(ticket.createdAt)}</p>
  </div>
  <div class="question">
    <h2>Customer Question</h2>
    <p>${ticket.question}</p>
  </div>
</body>
</html>`
  
  const blob = new Blob([html], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ticket-${ticket.id}.html`
  a.click()
  URL.revokeObjectURL(url)
}

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  
  const ticket = id ? dummyTicketData[id] : null

  if (!ticket) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <p className="text-lg text-gray-600">Ticket not found</p>
        <Button onClick={() => navigate("/dashboard")} className="mt-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate("/dashboard")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{ticket.title}</h1>
          <p className="text-gray-600 mt-1">Ticket #{ticket.id}</p>
        </div>
      </div>

      {/* Ticket Info */}
      <Card>
        <CardHeader>
          <CardTitle>Ticket Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm text-muted-foreground">Customer</p>
              <p className="font-medium">{ticket.customer}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p className="font-medium">{formatDate(ticket.createdAt)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Customer Question */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Question</CardTitle>
          <CardDescription>The original question or issue raised by the customer</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="prose max-w-none">
            <p className="text-gray-700 leading-relaxed">
              {ticket.question}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Downloads */}
      <Card>
        <CardHeader>
          <CardTitle>Download Ticket</CardTitle>
          <CardDescription>Export the ticket information and resolution in different formats</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button 
              variant="outline"
              onClick={() => handleDownloadMarkdown(ticket)}
            >
              <Download className="mr-2 h-4 w-4" />
              Download as Markdown
            </Button>
            <Button 
              variant="outline"
              onClick={() => handleDownloadHTML(ticket)}
            >
              <Download className="mr-2 h-4 w-4" />
              Download as HTML
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

