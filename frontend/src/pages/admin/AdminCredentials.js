import { useState, useEffect } from 'react';
import axios from 'axios';
import { Key, Eye, EyeOff, Save, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminCredentials = () => {
  const navigate = useNavigate();
  const [showPasswords, setShowPasswords] = useState({});
  const [loading, setLoading] = useState(false);
  const [organizations, setOrganizations] = useState([]);
  const [selectedOrg, setSelectedOrg] = useState('');
  
  const [omesCredentials, setOmesCredentials] = useState({
    soap_endpoint: 'https://ohioedi.mdhhs.ohio.gov/soap/eligibility',
    soap_username: '',
    soap_password: '',
    sftp_host: 'sftp.ohioedi.mdhhs.ohio.gov',
    sftp_port: '22',
    sftp_username: '',
    sftp_password: ''
  });

  const [availityCredentials, setAvailityCredentials] = useState({
    api_endpoint: 'https://api.availity.com',
    client_id: '',
    client_secret: '',
    organization_id: ''
  });

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrg) {
      fetchCredentials();
    }
  }, [selectedOrg]);

  const fetchOrganizations = async () => {
    try {
      const response = await axios.get(`${API}/admin/organizations`);
      // API returns { organizations: [...] }
      const orgs = response.data.organizations || [];
      setOrganizations(orgs);
      if (orgs.length > 0) {
        setSelectedOrg(orgs[0].id);
      }
    } catch (e) {
      console.error('Error fetching organizations:', e);
      toast.error('Failed to load organizations');
    }
  };

  const fetchCredentials = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/admin/credentials/${selectedOrg}`);
      if (response.data.omes) {
        setOmesCredentials({ ...omesCredentials, ...response.data.omes });
      }
      if (response.data.availity) {
        setAvailityCredentials({ ...availityCredentials, ...response.data.availity });
      }
    } catch (e) {
      console.error('Error fetching credentials:', e);
      // Don't show error if credentials don't exist yet
      if (e.response?.status !== 404) {
        toast.error('Failed to load credentials');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSaveOmes = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/admin/credentials/${selectedOrg}/omes`, omesCredentials);
      toast.success('OMES credentials saved successfully');
    } catch (e) {
      console.error('Error saving OMES credentials:', e);
      toast.error('Failed to save OMES credentials');
    }
  };

  const handleSaveAvality = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/admin/credentials/${selectedOrg}/availity`, availityCredentials);
      toast.success('Availity credentials saved successfully');
    } catch (e) {
      console.error('Error saving Availity credentials:', e);
      toast.error('Failed to save Availity credentials');
    }
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords(prev => ({ ...prev, [field]: !prev[field] }));
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <button
            onClick={() => navigate('/admin')}
            className="text-blue-600 hover:text-blue-800 mb-2"
          >
            ← Back to Admin Dashboard
          </button>
          <h1 className="text-3xl font-bold">Credentials Management</h1>
          <p className="text-gray-600 mt-1">Configure OMES and Availity integration credentials</p>
        </div>

        <Alert className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Credentials are encrypted and stored securely. Only authorized administrators can view and modify them.
          </AlertDescription>
        </Alert>

        {organizations.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center">
              <p className="text-gray-500">No organizations found. Please create an organization first.</p>
              <Button className="mt-4" onClick={() => navigate('/admin/organizations')}>
                Go to Organizations
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Select Organization</CardTitle>
              </CardHeader>
              <CardContent>
                <select
                  className="w-full border border-gray-300 rounded-md p-2"
                  value={selectedOrg}
                  onChange={(e) => setSelectedOrg(e.target.value)}
                >
                  {organizations.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </select>
              </CardContent>
            </Card>

            <Tabs defaultValue="omes" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="omes">OMES EDI</TabsTrigger>
                <TabsTrigger value="availity">Availity</TabsTrigger>
              </TabsList>

              <TabsContent value="omes">
                <Card>
                  <CardHeader>
                    <CardTitle>OMES EDI Credentials</CardTitle>
                    <CardDescription>Configure Ohio Medicaid SOAP and SFTP credentials</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleSaveOmes}>
                      <div className="space-y-4">
                        <div>
                          <Label>SOAP Endpoint</Label>
                          <Input
                            value={omesCredentials.soap_endpoint}
                            onChange={(e) => setOmesCredentials({ ...omesCredentials, soap_endpoint: e.target.value })}
                          />
                        </div>
                        <div>
                          <Label>SOAP Username</Label>
                          <Input
                            value={omesCredentials.soap_username}
                            onChange={(e) => setOmesCredentials({ ...omesCredentials, soap_username: e.target.value })}
                            required
                          />
                        </div>
                        <div>
                          <Label>SOAP Password</Label>
                          <div className="relative">
                            <Input
                              type={showPasswords.soap ? 'text' : 'password'}
                              value={omesCredentials.soap_password}
                              onChange={(e) => setOmesCredentials({ ...omesCredentials, soap_password: e.target.value })}
                              required
                            />
                            <button
                              type="button"
                              className="absolute right-2 top-2"
                              onClick={() => togglePasswordVisibility('soap')}
                            >
                              {showPasswords.soap ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                          </div>
                        </div>
                        <div className="border-t pt-4 mt-4">
                          <h3 className="font-semibold mb-4">SFTP Configuration</h3>
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <Label>SFTP Host</Label>
                                <Input
                                  value={omesCredentials.sftp_host}
                                  onChange={(e) => setOmesCredentials({ ...omesCredentials, sftp_host: e.target.value })}
                                />
                              </div>
                              <div>
                                <Label>SFTP Port</Label>
                                <Input
                                  value={omesCredentials.sftp_port}
                                  onChange={(e) => setOmesCredentials({ ...omesCredentials, sftp_port: e.target.value })}
                                />
                              </div>
                            </div>
                            <div>
                              <Label>SFTP Username</Label>
                              <Input
                                value={omesCredentials.sftp_username}
                                onChange={(e) => setOmesCredentials({ ...omesCredentials, sftp_username: e.target.value })}
                                required
                              />
                            </div>
                            <div>
                              <Label>SFTP Password</Label>
                              <div className="relative">
                                <Input
                                  type={showPasswords.sftp ? 'text' : 'password'}
                                  value={omesCredentials.sftp_password}
                                  onChange={(e) => setOmesCredentials({ ...omesCredentials, sftp_password: e.target.value })}
                                  required
                                />
                                <button
                                  type="button"
                                  className="absolute right-2 top-2"
                                  onClick={() => togglePasswordVisibility('sftp')}
                                >
                                  {showPasswords.sftp ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <Button type="submit" className="mt-6">
                        <Save className="w-4 h-4 mr-2" />
                        Save OMES Credentials
                      </Button>
                    </form>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="availity">
                <Card>
                  <CardHeader>
                    <CardTitle>Availity Credentials</CardTitle>
                    <CardDescription>Configure Availity clearinghouse API credentials</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleSaveAvality}>
                      <div className="space-y-4">
                        <div>
                          <Label>API Endpoint</Label>
                          <Input
                            value={availityCredentials.api_endpoint}
                            onChange={(e) => setAvailityCredentials({ ...availityCredentials, api_endpoint: e.target.value })}
                          />
                        </div>
                        <div>
                          <Label>Client ID</Label>
                          <Input
                            value={availityCredentials.client_id}
                            onChange={(e) => setAvailityCredentials({ ...availityCredentials, client_id: e.target.value })}
                            required
                          />
                        </div>
                        <div>
                          <Label>Client Secret</Label>
                          <div className="relative">
                            <Input
                              type={showPasswords.availity ? 'text' : 'password'}
                              value={availityCredentials.client_secret}
                              onChange={(e) => setAvailityCredentials({ ...availityCredentials, client_secret: e.target.value })}
                              required
                            />
                            <button
                              type="button"
                              className="absolute right-2 top-2"
                              onClick={() => togglePasswordVisibility('availity')}
                            >
                              {showPasswords.availity ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                          </div>
                        </div>
                        <div>
                          <Label>Organization ID</Label>
                          <Input
                            value={availityCredentials.organization_id}
                            onChange={(e) => setAvailityCredentials({ ...availityCredentials, organization_id: e.target.value })}
                            required
                          />
                        </div>
                      </div>
                      <Button type="submit" className="mt-6">
                        <Save className="w-4 h-4 mr-2" />
                        Save Availity Credentials
                      </Button>
                    </form>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </div>
  );
};

export default AdminCredentials;