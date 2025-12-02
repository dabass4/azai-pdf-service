import { useState } from 'react';
import axios from 'axios';
import { Search, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EligibilityCheck = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState({
    patient_id: '',
    medicaid_id: '',
    date_of_birth: '',
    service_date: new Date().toISOString().split('T')[0]
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setResult(null);
      const response = await axios.post(`${API}/claims/eligibility`, formData);
      setResult(response.data);
      toast.success('Eligibility check completed');
    } catch (e) {
      console.error('Error checking eligibility:', e);
      const errorMsg = e.response?.data?.detail || 'Failed to check eligibility';
      toast.error(errorMsg);
      setResult({ error: errorMsg, eligible: false });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      patient_id: '',
      medicaid_id: '',
      date_of_birth: '',
      service_date: new Date().toISOString().split('T')[0]
    });
    setResult(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Patient Eligibility Verification</h1>
          <p className="text-gray-600 mt-1">Verify Medicaid eligibility in real-time</p>
        </div>

        <Alert className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            This feature connects to Ohio Medicaid (OMES) SOAP service for real-time eligibility verification.
            Ensure OMES credentials are configured in the Admin Panel.
          </AlertDescription>
        </Alert>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Eligibility Query</CardTitle>
              <CardDescription>Enter patient information to verify coverage</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="patient_id">Patient ID</Label>
                    <Input
                      id="patient_id"
                      placeholder="Enter patient ID"
                      value={formData.patient_id}
                      onChange={(e) => setFormData({ ...formData, patient_id: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="medicaid_id">Medicaid ID *</Label>
                    <Input
                      id="medicaid_id"
                      placeholder="Enter Medicaid ID"
                      value={formData.medicaid_id}
                      onChange={(e) => setFormData({ ...formData, medicaid_id: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="date_of_birth">Date of Birth *</Label>
                    <Input
                      id="date_of_birth"
                      type="date"
                      value={formData.date_of_birth}
                      onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="service_date">Service Date</Label>
                    <Input
                      id="service_date"
                      type="date"
                      value={formData.service_date}
                      onChange={(e) => setFormData({ ...formData, service_date: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="flex gap-2 mt-6">
                  <Button type="submit" disabled={loading}>
                    {loading ? (
                      <>
                        <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                        Checking...
                      </>
                    ) : (
                      <>
                        <Search className="w-4 h-4 mr-2" />
                        Check Eligibility
                      </>
                    )}
                  </Button>
                  <Button type="button" variant="outline" onClick={handleReset}>
                    Reset
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card className={result ? 'block' : 'hidden lg:block'}>
            <CardHeader>
              <CardTitle>Verification Result</CardTitle>
              <CardDescription>Eligibility status and coverage details</CardDescription>
            </CardHeader>
            <CardContent>
              {!result ? (
                <div className="text-center py-12 text-gray-500">
                  <Search className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Submit a query to view results</p>
                </div>
              ) : result.error ? (
                <div className="text-center py-8">
                  <XCircle className="w-16 h-16 mx-auto text-red-500 mb-4" />
                  <h3 className="text-lg font-semibold text-red-700 mb-2">Verification Failed</h3>
                  <p className="text-gray-600">{result.error}</p>
                </div>
              ) : result.eligible ? (
                <div>
                  <div className="text-center py-4 mb-6 bg-green-50 rounded-lg">
                    <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-2" />
                    <h3 className="text-lg font-semibold text-green-700">Patient is Eligible</h3>
                    <p className="text-sm text-green-600 mt-1">Coverage confirmed for service date</p>
                  </div>
                  <div className="space-y-3">
                    <div className="border-b pb-2">
                      <p className="text-sm text-gray-600">Patient Name</p>
                      <p className="font-medium">{result.patient_name || 'N/A'}</p>
                    </div>
                    <div className="border-b pb-2">
                      <p className="text-sm text-gray-600">Medicaid ID</p>
                      <p className="font-medium">{result.medicaid_id}</p>
                    </div>
                    <div className="border-b pb-2">
                      <p className="text-sm text-gray-600">Coverage Period</p>
                      <p className="font-medium">
                        {result.coverage_start ? new Date(result.coverage_start).toLocaleDateString() : 'N/A'} - 
                        {result.coverage_end ? new Date(result.coverage_end).toLocaleDateString() : 'Active'}
                      </p>
                    </div>
                    <div className="border-b pb-2">
                      <p className="text-sm text-gray-600">Plan Type</p>
                      <p className="font-medium">{result.plan_type || 'Standard'}</p>
                    </div>
                    {result.copay_amount && (
                      <div className="border-b pb-2">
                        <p className="text-sm text-gray-600">Copay Amount</p>
                        <p className="font-medium">${result.copay_amount}</p>
                      </div>
                    )}
                    {result.notes && (
                      <div className="pt-2">
                        <p className="text-sm text-gray-600">Additional Notes</p>
                        <p className="text-sm">{result.notes}</p>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <XCircle className="w-16 h-16 mx-auto text-orange-500 mb-4" />
                  <h3 className="text-lg font-semibold text-orange-700 mb-2">Not Eligible</h3>
                  <p className="text-gray-600">{result.reason || 'Patient does not have active coverage for the specified service date.'}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default EligibilityCheck;