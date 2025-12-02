import { useState, useEffect } from 'react';
import axios from 'axios';
import { FileText, RefreshCw, Filter, Eye, CheckCircle, Clock, XCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ClaimTracking = () => {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetchClaims();
  }, [filter]);

  const fetchClaims = async () => {
    try {
      setLoading(true);
      const params = filter !== 'all' ? `?status=${filter}` : '';
      const response = await axios.get(`${API}/claims/list${params}`);
      setClaims(response.data);
    } catch (e) {
      console.error('Error fetching claims:', e);
      toast.error('Failed to load claims');
    } finally {
      setLoading(false);
    }
  };

  const fetchClaimDetails = async (claimId) => {
    try {
      const response = await axios.get(`${API}/claims/${claimId}/status`);
      setSelectedClaim(response.data);
      setShowDetails(true);
    } catch (e) {
      console.error('Error fetching claim details:', e);
      toast.error('Failed to load claim details');
    }
  };

  const getStatusIcon = (status) => {
    const icons = {
      submitted: <Clock className="w-4 h-4" />,
      pending: <AlertCircle className="w-4 h-4" />,
      accepted: <CheckCircle className="w-4 h-4" />,
      rejected: <XCircle className="w-4 h-4" />,
      paid: <CheckCircle className="w-4 h-4" />
    };
    return icons[status?.toLowerCase()] || <FileText className="w-4 h-4" />;
  };

  const getStatusColor = (status) => {
    const colors = {
      submitted: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800',
      accepted: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      paid: 'bg-green-100 text-green-800'
    };
    return colors[status?.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold">Claim Tracking Dashboard</h1>
              <p className="text-gray-600 mt-1">Monitor status and history of submitted claims</p>
            </div>
            <Button onClick={fetchClaims}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex gap-2 flex-wrap">
              <Button
                variant={filter === 'all' ? 'default' : 'outline'}
                onClick={() => setFilter('all')}
              >
                All Claims
              </Button>
              <Button
                variant={filter === 'submitted' ? 'default' : 'outline'}
                onClick={() => setFilter('submitted')}
              >
                Submitted
              </Button>
              <Button
                variant={filter === 'pending' ? 'default' : 'outline'}
                onClick={() => setFilter('pending')}
              >
                Pending
              </Button>
              <Button
                variant={filter === 'accepted' ? 'default' : 'outline'}
                onClick={() => setFilter('accepted')}
              >
                Accepted
              </Button>
              <Button
                variant={filter === 'rejected' ? 'default' : 'outline'}
                onClick={() => setFilter('rejected')}
              >
                Rejected
              </Button>
              <Button
                variant={filter === 'paid' ? 'default' : 'outline'}
                onClick={() => setFilter('paid')}
              >
                Paid
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Claims List ({claims.length})</CardTitle>
            <CardDescription>View and manage submitted Medicaid claims</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-center py-8">Loading claims...</p>
            ) : claims.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">No claims found. Submit your first claim to get started.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Claim ID</TableHead>
                      <TableHead>Patient</TableHead>
                      <TableHead>Service Date</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {claims.map((claim) => (
                      <TableRow key={claim.id}>
                        <TableCell className="font-mono text-sm">{claim.claim_number || claim.id}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{claim.patient_name || 'N/A'}</p>
                            <p className="text-xs text-gray-500">Medicaid: {claim.patient_medicaid_id || 'N/A'}</p>
                          </div>
                        </TableCell>
                        <TableCell>{claim.service_date ? new Date(claim.service_date).toLocaleDateString() : 'N/A'}</TableCell>
                        <TableCell className="font-medium">${claim.total_amount?.toFixed(2) || '0.00'}</TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(claim.status)}>
                            <span className="mr-1">{getStatusIcon(claim.status)}</span>
                            {claim.status || 'Unknown'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => fetchClaimDetails(claim.id)}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {showDetails && selectedClaim && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>Claim Details</CardTitle>
                    <CardDescription>Claim #{selectedClaim.claim_number || selectedClaim.id}</CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => setShowDetails(false)}>
                    Close
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Status</p>
                      <Badge className={getStatusColor(selectedClaim.status)}>
                        {selectedClaim.status || 'Unknown'}
                      </Badge>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Submission Date</p>
                      <p className="font-medium">
                        {selectedClaim.submission_date ? new Date(selectedClaim.submission_date).toLocaleDateString() : 'N/A'}
                      </p>
                    </div>
                  </div>
                  <div className="border-t pt-4">
                    <h3 className="font-semibold mb-2">Patient Information</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-gray-600">Name</p>
                        <p>{selectedClaim.patient_name || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Medicaid ID</p>
                        <p>{selectedClaim.patient_medicaid_id || 'N/A'}</p>
                      </div>
                    </div>
                  </div>
                  <div className="border-t pt-4">
                    <h3 className="font-semibold mb-2">Service Details</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-gray-600">Service Date</p>
                        <p>{selectedClaim.service_date ? new Date(selectedClaim.service_date).toLocaleDateString() : 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Total Amount</p>
                        <p className="font-medium">${selectedClaim.total_amount?.toFixed(2) || '0.00'}</p>
                      </div>
                    </div>
                  </div>
                  {selectedClaim.rejection_reason && (
                    <div className="border-t pt-4">
                      <h3 className="font-semibold mb-2 text-red-700">Rejection Reason</h3>
                      <p className="text-sm bg-red-50 p-3 rounded">{selectedClaim.rejection_reason}</p>
                    </div>
                  )}
                  {selectedClaim.notes && (
                    <div className="border-t pt-4">
                      <h3 className="font-semibold mb-2">Notes</h3>
                      <p className="text-sm">{selectedClaim.notes}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClaimTracking;