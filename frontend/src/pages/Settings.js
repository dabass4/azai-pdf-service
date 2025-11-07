import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { CreditCard, Zap, Users, FileText, Shield, ArrowRight, Check } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Settings = () => {
  const { user, organization } = useAuth();
  const [loading, setLoading] = useState(false);
  const [plans, setPlans] = useState([]);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/payments/plans`);
      setPlans(response.data.plans);
    } catch (error) {
      console.error('Error fetching plans:', error);
    }
  };

  const handleUpgrade = async (planId) => {
    if (planId === 'enterprise') {
      toast.info('Please contact sales for Enterprise plan');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/payments/create-checkout`, {
        plan: planId
      });

      // Redirect to Stripe checkout
      window.location.href = response.data.url;
    } catch (error) {
      console.error('Checkout error:', error);
      toast.error(error.response?.data?.detail || 'Failed to start checkout');
    } finally {
      setLoading(false);
    }
  };

  const handleManageBilling = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/payments/create-portal`);
      window.location.href = response.data.url;
    } catch (error) {
      console.error('Billing portal error:', error);
      toast.error(error.response?.data?.detail || 'Failed to open billing portal');
    } finally {
      setLoading(false);
    }
  };

  const currentPlan = organization?.plan || 'basic';
  const subscriptionStatus = organization?.subscription_status || 'trial';

  const getStatusBadge = (status) => {
    const badges = {
      trial: { text: 'Free Trial', color: 'bg-blue-100 text-blue-800' },
      active: { text: 'Active', color: 'bg-green-100 text-green-800' },
      suspended: { text: 'Suspended', color: 'bg-yellow-100 text-yellow-800' },
      cancelled: { text: 'Cancelled', color: 'bg-red-100 text-red-800' }
    };
    return badges[status] || badges.trial;
  };

  const statusBadge = getStatusBadge(subscriptionStatus);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Account Settings
          </h1>
          <p className="text-gray-600 mt-2">Manage your subscription and billing</p>
        </div>

        {/* Current Plan Card */}
        <Card className="mb-8 border-2 border-blue-200 shadow-xl">
          <CardHeader className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
            <CardTitle className="text-2xl">Current Plan</CardTitle>
            <CardDescription className="text-blue-100">Your active subscription details</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-600 mb-1">Organization</p>
                <p className="text-xl font-semibold text-gray-900">{organization?.name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Plan</p>
                <div className="flex items-center gap-3">
                  <p className="text-xl font-semibold text-gray-900 capitalize">{currentPlan}</p>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${statusBadge.color}`}>
                    {statusBadge.text}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Timesheets Limit</p>
                <p className="text-xl font-semibold text-gray-900">
                  {organization?.max_timesheets === -1 ? 'Unlimited' : `${organization?.max_timesheets} per month`}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Employees Limit</p>
                <p className="text-xl font-semibold text-gray-900">
                  {organization?.max_employees === -1 ? 'Unlimited' : organization?.max_employees}
                </p>
              </div>
            </div>

            {/* Features */}
            <div className="mt-6">
              <p className="text-sm text-gray-600 mb-3">Active Features:</p>
              <div className="flex flex-wrap gap-2">
                {organization?.features?.map((feature, index) => (
                  <span key={index} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1">
                    <Check size={16} />
                    {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                ))}
              </div>
            </div>

            {/* Billing Management */}
            {organization?.stripe_customer_id && (
              <div className="mt-6 pt-6 border-t">
                <Button
                  onClick={handleManageBilling}
                  disabled={loading}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <CreditCard size={18} />
                  Manage Billing & Payment Methods
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Available Plans */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Available Plans</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => {
              const isCurrentPlan = plan.id === currentPlan;
              const isUpgrade = (plan.id === 'professional' && currentPlan === 'basic') || 
                               (plan.id === 'enterprise' && (currentPlan === 'basic' || currentPlan === 'professional'));
              
              return (
                <Card 
                  key={plan.id}
                  className={`relative ${isCurrentPlan ? 'border-4 border-blue-500' : 'border-2 border-gray-200'}`}
                >
                  {isCurrentPlan && (
                    <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                      <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                        Current Plan
                      </span>
                    </div>
                  )}
                  
                  <CardHeader className="text-center pt-8">
                    <CardTitle className="text-2xl font-bold">{plan.name}</CardTitle>
                    <div className="mt-4">
                      {typeof plan.price === 'number' ? (
                        <>
                          <span className="text-4xl font-bold">${plan.price}</span>
                          <span className="text-gray-600">/month</span>
                        </>
                      ) : (
                        <span className="text-4xl font-bold">{plan.price}</span>
                      )}
                    </div>
                  </CardHeader>

                  <CardContent>
                    <div className="space-y-3 mb-6">
                      <div className="text-sm text-gray-600">
                        <p className="font-semibold mb-2">Features:</p>
                        <ul className="space-y-1">
                          {plan.features.map((feature, index) => (
                            <li key={index} className="flex items-center gap-2">
                              <Check className="text-green-500" size={16} />
                              <span>{feature.replace(/_/g, ' ')}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="text-sm text-gray-600">
                        <p className="font-semibold mb-1">Limits:</p>
                        <p>Timesheets: {plan.limits.max_timesheets === -1 ? 'Unlimited' : plan.limits.max_timesheets}</p>
                        <p>Employees: {plan.limits.max_employees === -1 ? 'Unlimited' : plan.limits.max_employees}</p>
                        <p>Patients: {plan.limits.max_patients === -1 ? 'Unlimited' : plan.limits.max_patients}</p>
                      </div>
                    </div>

                    {!isCurrentPlan && isUpgrade && (
                      <Button
                        onClick={() => handleUpgrade(plan.id)}
                        disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-700"
                      >
                        {loading ? 'Loading...' : `Upgrade to ${plan.name}`}
                        <ArrowRight size={16} className="ml-2" />
                      </Button>
                    )}

                    {isCurrentPlan && (
                      <Button
                        disabled
                        variant="outline"
                        className="w-full"
                      >
                        Current Plan
                      </Button>
                    )}

                    {plan.id === 'enterprise' && !isCurrentPlan && (
                      <Button
                        onClick={() => handleUpgrade(plan.id)}
                        variant="outline"
                        className="w-full"
                      >
                        Contact Sales
                      </Button>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Test Mode Notice */}
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Shield className="text-yellow-600 flex-shrink-0 mt-1" size={24} />
              <div>
                <p className="font-semibold text-yellow-900">Test Mode Active</p>
                <p className="text-sm text-yellow-800 mt-1">
                  Payments are in test mode. Use test card: <code className="bg-yellow-100 px-2 py-1 rounded">4242 4242 4242 4242</code>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Settings;
