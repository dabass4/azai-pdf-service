import { useState, useEffect } from 'react';
import axios from 'axios';
import { MessageSquare, Plus, X, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminSupport = () => {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    organization_id: '',
    subject: '',
    description: '',
    priority: 'medium'
  });
  const [organizations, setOrganizations] = useState([]);

  useEffect(() => {
    fetchTickets();
    fetchOrganizations();
  }, []);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/admin/support/tickets`);
      setTickets(response.data);
    } catch (e) {
      console.error('Error fetching tickets:', e);
      toast.error('Failed to load support tickets');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrganizations = async () => {
    try {
      const response = await axios.get(`${API}/admin/organizations`);
      setOrganizations(response.data);
    } catch (e) {
      console.error('Error fetching organizations:', e);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/admin/support/tickets`, formData);
      toast.success('Support ticket created successfully');
      resetForm();
      fetchTickets();
    } catch (e) {
      console.error('Error creating ticket:', e);
      toast.error('Failed to create support ticket');
    }
  };

  const handleUpdateStatus = async (ticketId, newStatus) => {
    try {
      await axios.patch(`${API}/admin/support/tickets/${ticketId}`, { status: newStatus });
      toast.success('Ticket status updated');
      fetchTickets();
    } catch (e) {
      console.error('Error updating ticket:', e);
      toast.error('Failed to update ticket status');
    }
  };

  const resetForm = () => {
    setFormData({
      organization_id: '',
      subject: '',
      description: '',
      priority: 'medium'
    });
    setShowForm(false);
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-red-100 text-red-800'
    };
    return colors[priority] || colors.medium;
  };

  const getStatusIcon = (status) => {
    const icons = {
      open: <Clock className="w-4 h-4" />,
      in_progress: <AlertCircle className="w-4 h-4" />,
      resolved: <CheckCircle className="w-4 h-4" />,
      closed: <CheckCircle className="w-4 h-4" />
    };
    return icons[status] || icons.open;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6 flex justify-between items-center">
          <div>
            <button
              onClick={() => navigate('/admin')}
              className="text-blue-600 hover:text-blue-800 mb-2"
            >
              ← Back to Admin Dashboard
            </button>
            <h1 className="text-3xl font-bold">Support Ticket Management</h1>
            <p className="text-gray-600 mt-1">Track and resolve client support issues</p>
          </div>
          <Button onClick={() => setShowForm(true)}>
            <Plus className="w-4 h-4 mr-2" />
            New Ticket
          </Button>
        </div>

        {showForm && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Create Support Ticket</CardTitle>
              <CardDescription>Enter ticket details below</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="organization_id">Organization *</Label>
                    <select
                      id="organization_id"
                      className="w-full border border-gray-300 rounded-md p-2"
                      value={formData.organization_id}
                      onChange={(e) => setFormData({ ...formData, organization_id: e.target.value })}
                      required
                    >
                      <option value="">Select Organization</option>
                      {organizations.map((org) => (
                        <option key={org.id} value={org.id}>
                          {org.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label htmlFor="subject">Subject *</Label>
                    <Input
                      id="subject"
                      value={formData.subject}
                      onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="description">Description *</Label>
                    <Textarea
                      id="description"
                      rows={4}
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="priority">Priority</Label>
                    <select
                      id="priority"
                      className="w-full border border-gray-300 rounded-md p-2"
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                </div>
                <div className="flex gap-2 mt-6">
                  <Button type="submit">
                    Create Ticket
                  </Button>
                  <Button type="button" variant="outline" onClick={resetForm}>
                    <X className="w-4 h-4 mr-2" />
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 gap-4">
          {loading ? (
            <Card>
              <CardContent className="py-8 text-center">
                <p>Loading support tickets...</p>
              </CardContent>
            </Card>
          ) : tickets.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <MessageSquare className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">No support tickets found. Create your first ticket above.</p>
              </CardContent>
            </Card>
          ) : (
            tickets.map((ticket) => (
              <Card key={ticket.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{ticket.subject}</CardTitle>
                      <CardDescription className="mt-1">
                        {ticket.organization_name} • Created {new Date(ticket.created_at).toLocaleDateString()}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Badge className={getPriorityColor(ticket.priority)}>
                        {ticket.priority}
                      </Badge>
                      <Badge variant="outline">
                        <span className="mr-1">{getStatusIcon(ticket.status)}</span>
                        {ticket.status}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 mb-4">{ticket.description}</p>
                  <div className="flex gap-2">
                    {ticket.status !== 'resolved' && ticket.status !== 'closed' && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleUpdateStatus(ticket.id, 'in_progress')}
                        >
                          Mark In Progress
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleUpdateStatus(ticket.id, 'resolved')}
                        >
                          Resolve
                        </Button>
                      </>
                    )}
                    {ticket.status === 'resolved' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleUpdateStatus(ticket.id, 'closed')}
                      >
                        Close Ticket
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminSupport;