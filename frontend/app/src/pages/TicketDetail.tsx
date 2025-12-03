import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, ArrowLeft, AlertCircle } from "lucide-react";
import { fetchTicketById, type Ticket as ApiTicket } from "@/services/tickets";

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// Download handlers
const handleDownloadMarkdown = (ticket: ApiTicket) => {
  const markdown = `# ${ticket.subject}\n\n## Ticket Information\n- **ID:** ${ticket.id}\n- **Created:** ${formatDate(ticket.created_at)}\n\n## Customer Message\n\n${ticket.body}`;

  const blob = new Blob([markdown], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `ticket-${ticket.id}.md`;
  a.click();
  URL.revokeObjectURL(url);
};

const handleDownloadHTML = (ticket: ApiTicket) => {
  const html = `<!DOCTYPE html>
<html>
<head>
  <title>${ticket.subject}</title>
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
  <h1>${ticket.subject}</h1>
  <div class="info">
    <h2>Ticket Information</h2>
    <p><strong>ID:</strong> ${ticket.id}</p>
    <p><strong>Created:</strong> ${formatDate(ticket.created_at)}</p>
  </div>
  <div class="question">
    <h2>Customer Message</h2>
    <p>${ticket.body}</p>
  </div>
</body>
</html>`;

  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `ticket-${ticket.id}.html`;
  a.click();
  URL.revokeObjectURL(url);
};

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<ApiTicket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTicket = async () => {
      if (!id) {
        setError("Ticket id is missing");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const data = await fetchTicketById(id);
        setTicket(data);
        setError(null);
      } catch (err) {
        console.error("Error loading ticket:", err);
        setError(err instanceof Error ? err.message : "Unable to load ticket");
        setTicket(null);
      } finally {
        setLoading(false);
      }
    };

    loadTicket();
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-sm text-gray-600">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mb-4" />
        Loading ticket...
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <AlertCircle className="h-10 w-10 text-gray-400 mb-3" />
        <p className="text-lg text-gray-600">{error || "Ticket not found"}</p>
        <Button onClick={() => navigate("/dashboard")} className="mt-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate("/dashboard")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{ticket.subject}</h1>
          <p className="text-gray-600 mt-1">Ticket #{ticket.id}</p>
        </div>
      </div>

      {/* Ticket Info */}
      <Card>
        <CardHeader>
          <CardTitle>Ticket Information</CardTitle>
          <CardDescription>
            Metadata pulled directly from the ticket record
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p className="font-medium">{formatDate(ticket.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Updated</p>
              <p className="font-medium">{formatDate(ticket.updated_at)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Customer Message */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Message</CardTitle>
          <CardDescription>
            The original question or issue raised by the customer
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="prose max-w-none">
            <p className="text-gray-700 leading-relaxed whitespace-pre-line">
              {ticket.body}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Downloads */}
      <Card>
        <CardHeader>
          <CardTitle>Download Ticket</CardTitle>
          <CardDescription>
            Export the ticket information in different formats
          </CardDescription>
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
  );
}
