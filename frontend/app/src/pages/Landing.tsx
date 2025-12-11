import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Ticket,
  Brain,
  Zap,
  Shield,
  BarChart3,
  Users,
  ArrowRight,
  CheckCircle,
  Mail,
  Phone,
  MessageSquare,
} from "lucide-react";

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b bg-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Ticket className="h-6 w-6 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">
                Ticket Resolution Platform AAAAA
              </span>
            </div>
            <div className="flex items-center gap-4">
              <Link to="/login">
                <Button variant="ghost">Sign In</Button>
              </Link>
              <Link to="/signup">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            AI-Powered Ticket Resolution
            <span className="text-primary-600"> Made Simple</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Transform customer support tickets into actionable website
            improvements. Our AI analyzes customer inquiries and generates
            recommendations for your FAQ and support pages, helping you reduce
            support volume and improve customer satisfaction.
          </p>
          <div className="flex gap-4 justify-center">
            <Link to="/signup">
              <Button size="lg" className="text-lg px-8">
                Get Started Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="text-lg px-8">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why Choose Our Platform?
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Everything you need to streamline your customer support and
              improve your website
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card>
              <CardHeader>
                <Brain className="h-10 w-10 text-primary-600 mb-4" />
                <CardTitle>AI-Powered Analysis</CardTitle>
                <CardDescription>
                  Advanced AI analyzes customer tickets and generates
                  intelligent recommendations
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <Zap className="h-10 w-10 text-primary-600 mb-4" />
                <CardTitle>Lightning Fast</CardTitle>
                <CardDescription>
                  Get resolutions and recommendations in seconds, not hours
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <Shield className="h-10 w-10 text-primary-600 mb-4" />
                <CardTitle>Secure & Private</CardTitle>
                <CardDescription>
                  Your customer data is encrypted and handled with the highest
                  security standards
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <BarChart3 className="h-10 w-10 text-primary-600 mb-4" />
                <CardTitle>Actionable Insights</CardTitle>
                <CardDescription>
                  Detailed statistics and analytics to track your support
                  improvements
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <Users className="h-10 w-10 text-primary-600 mb-4" />
                <CardTitle>Team Collaboration</CardTitle>
                <CardDescription>
                  Review and approve recommendations with your HR and support
                  teams
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <Ticket className="h-10 w-10 text-primary-600 mb-4" />
                <CardTitle>Easy Integration</CardTitle>
                <CardDescription>
                  Import tickets via CSV or connect directly with your support
                  system
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Simple steps to transform your customer support
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-primary-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-600">1</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Import Tickets</h3>
              <p className="text-gray-600">
                Upload your customer support tickets via CSV or connect your
                support system
              </p>
            </div>
            <div className="text-center">
              <div className="bg-primary-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-600">2</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">AI Analysis</h3>
              <p className="text-gray-600">
                Our AI analyzes each ticket and generates recommendations for
                FAQ and website improvements
              </p>
            </div>
            <div className="text-center">
              <div className="bg-primary-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-600">3</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Review & Implement</h3>
              <p className="text-gray-600">
                Review recommendations, approve changes, and update your website
                to reduce support volume
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-lg text-gray-600">
              Everything you need to know about our platform
            </p>
          </div>
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>What is the Ticket Resolution Platform?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Our platform uses AI to analyze customer support tickets and
                  generate actionable recommendations for improving your
                  website's FAQ section and support pages. This helps reduce
                  support ticket volume by addressing common customer questions
                  proactively.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>How do I import tickets?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  You can import tickets in two ways: upload a CSV file directly
                  through the dashboard, or connect your existing support system
                  via API integration. The CSV format is simple and includes
                  ticket ID, customer email, question, and timestamp.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>
                  What kind of recommendations does the AI generate?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  The AI analyzes customer questions and provides specific
                  recommendations such as: new FAQ entries to add, website
                  layout improvements, navigation enhancements, missing
                  information on support pages, and suggestions for self-service
                  options.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Can I edit the AI-generated resolutions?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Yes! All AI-generated resolutions can be reviewed, edited,
                  approved, or declined. You have full control over which
                  recommendations get implemented on your website.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Is my customer data secure?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Absolutely. We use industry-standard encryption for all data
                  in transit and at rest. Your customer information is never
                  shared with third parties, and you can delete tickets and data
                  at any time.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>
                  What formats can I download resolutions in?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  You can download ticket resolutions in both Markdown and HTML
                  formats, making it easy to integrate recommendations into your
                  existing website or documentation system.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Get in Touch
            </h2>
            <p className="text-lg text-gray-600">
              Have questions? We're here to help
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <Card className="text-center">
              <CardHeader>
                <Mail className="h-10 w-10 text-primary-600 mx-auto mb-4" />
                <CardTitle>Email Us</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">Send us an email anytime</p>
                <a
                  href="mailto:support@ticketresolution.com"
                  className="text-primary-600 hover:underline"
                >
                  support@ticketresolution.com
                </a>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardHeader>
                <Phone className="h-10 w-10 text-primary-600 mx-auto mb-4" />
                <CardTitle>Call Us</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">Mon-Fri 9am-5pm EST</p>
                <a
                  href="tel:+1234567890"
                  className="text-primary-600 hover:underline"
                >
                  +1 (234) 567-890
                </a>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardHeader>
                <MessageSquare className="h-10 w-10 text-primary-600 mx-auto mb-4" />
                <CardTitle>Live Chat</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">Chat with our team</p>
                <Button variant="outline">Start Chat</Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-600 py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your Customer Support?
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Join hundreds of businesses using AI to improve their support
            experience
          </p>
          <Link to="/signup">
            <Button size="lg" variant="secondary" className="text-lg px-8">
              Get Started Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Ticket className="h-6 w-6" />
                <span className="text-lg font-bold">
                  Ticket Resolution Platform
                </span>
              </div>
              <p className="text-gray-400 text-sm">
                AI-powered ticket resolution for modern businesses
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>
                  <a href="#" className="hover:text-white">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white">
                    Pricing
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white">
                    Integrations
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>
                  <a href="#" className="hover:text-white">
                    About
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white">
                    Blog
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white">
                    Careers
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>
                  <a href="#" className="hover:text-white">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white">
                    Contact
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white">
                    Privacy
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
            <p>© 2024 Ticket Resolution Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
