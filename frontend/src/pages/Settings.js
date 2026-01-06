import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';
import { CreditCard, Users, FileText, Shield, ArrowRight, Check, Settings as SettingsIcon, Building2, Sparkles } from 'lucide-react';

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
      trial: { text: 'Free Trial', class: 'status-badge status-processing' },
      active: { text: 'Active', class: 'status-badge status-completed' },
      suspended: { text: 'Suspended', class: 'status-badge status-pending' },
      cancelled: { text: 'Cancelled', class: 'status-badge status-error' }
    };
    return badges[status] || badges.trial;
  };

  const statusBadge = getStatusBadge(subscriptionStatus);

  return (
    <div className="min-h-screen healthcare-pattern" data-testid="settings-page">
      <div className="animated-bg"></div>
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center gap-4">
            <div className="icon-container">
              <SettingsIcon className="w-6 h-6 text-teal-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Account Settings
              </h1>
              <p className="text-gray-400">Manage your subscription and billing</p>
            </div>
          </div>
        </div>

        {/* Current Plan Card */}
        <div className="glass-card rounded-2xl overflow-hidden mb-8 animate-slide-up">
          <div className="p-6 border-b border-white/10 bg-gradient-to-r from-teal-500/20 to-purple-500/20">
            <div className="flex items-center gap-3">
              <div className="icon-container">
                <Sparkles className="w-6 h-6 text-teal-400" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">Current Plan</h2>
                <p className="text-gray-400">Your active subscription details</p>
              </div>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-500 mb-1">Organization</p>
                <p className="text-xl font-semibold text-white">{organization?.name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Plan</p>
                <div className="flex items-center gap-3">
                  <p className="text-xl font-semibold text-white capitalize">{currentPlan}</p>
                  <span className={statusBadge.class}>
                    {statusBadge.text}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Timesheets Limit</p>
                <p className="text-xl font-semibold text-white">
                  {organization?.max_timesheets === -1 ? 'Unlimited' : `${organization?.max_timesheets} per month`}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Employees Limit</p>
                <p className="text-xl font-semibold text-white">
                  {organization?.max_employees === -1 ? 'Unlimited' : organization?.max_employees}
                </p>
              </div>
            </div>

            {/* Features */}
            <div className="mt-6">
              <p className="text-sm text-gray-500 mb-3">Active Features:</p>
              <div className="flex flex-wrap gap-2">
                {organization?.features?.map((feature, index) => (
                  <span key={index} className="status-badge status-completed flex items-center gap-1">
                    <Check size={14} />
                    {feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                ))}
              </div>
            </div>

            {/* Billing Management */}
            {organization?.stripe_customer_id && (
              <div className="mt-6 pt-6 border-t border-white/10">
                <button
                  onClick={handleManageBilling}
                  disabled={loading}
                  className="btn-secondary flex items-center gap-2"
                >
                  <CreditCard size={18} />
                  Manage Billing & Payment Methods
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Available Plans */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">Available Plans</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 stagger-children">
            {plans.map((plan) => {
              const isCurrentPlan = plan.id === currentPlan;
              const isUpgrade = (plan.id === 'professional' && currentPlan === 'basic') || 
                               (plan.id === 'enterprise' && (currentPlan === 'basic' || currentPlan === 'professional'));
              
              return (
                <div 
                  key={plan.id}
                  className={`glass-card rounded-2xl overflow-hidden relative card-lift ${isCurrentPlan ? 'border-2 border-teal-500 glow-teal' : ''}`}
                >
                  {isCurrentPlan && (
                    <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10">
                      <span className="gradient-teal text-white px-4 py-1 rounded-full text-sm font-semibold">
                        Current Plan
                      </span>
                    </div>
                  )}
                  
                  <div className="p-6 text-center pt-8">
                    <h3 className="text-2xl font-bold text-white">{plan.name}</h3>
                    <div className="mt-4">
                      {typeof plan.price === 'number' ? (
                        <>
                          <span className="text-4xl font-bold gradient-text">${plan.price}</span>
                          <span className="text-gray-400">/month</span>
                        </>
                      ) : (
                        <span className="text-4xl font-bold gradient-text">{plan.price}</span>
                      )}
                    </div>
                  </div>

                  <div className="p-6 pt-0">
                    <div className="space-y-3 mb-6">
                      <div className="text-sm text-gray-400">
                        <p className="font-semibold text-gray-300 mb-2">Features:</p>
                        <ul className="space-y-1">
                          {plan.features.map((feature, index) => (
                            <li key={index} className="flex items-center gap-2">
                              <Check className="text-teal-400" size={16} />
                              <span>{feature.replace(/_/g, ' ')}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="text-sm text-gray-400">
                        <p className="font-semibold text-gray-300 mb-1">Limits:</p>
                        <p>Timesheets: {plan.limits.max_timesheets === -1 ? 'Unlimited' : plan.limits.max_timesheets}</p>
                        <p>Employees: {plan.limits.max_employees === -1 ? 'Unlimited' : plan.limits.max_employees}</p>
                        <p>Patients: {plan.limits.max_patients === -1 ? 'Unlimited' : plan.limits.max_patients}</p>
                      </div>
                    </div>

                    {!isCurrentPlan && isUpgrade && (
                      <button
                        onClick={() => handleUpgrade(plan.id)}
                        disabled={loading}
                        className="w-full btn-primary flex items-center justify-center gap-2"
                      >
                        {loading ? 'Loading...' : `Upgrade to ${plan.name}`}
                        <ArrowRight size={16} />
                      </button>
                    )}

                    {isCurrentPlan && (
                      <button
                        disabled
                        className="w-full btn-secondary opacity-50 cursor-not-allowed"
                      >
                        Current Plan
                      </button>
                    )}

                    {plan.id === 'enterprise' && !isCurrentPlan && (
                      <button
                        onClick={() => handleUpgrade(plan.id)}
                        className="w-full btn-secondary"
                      >
                        Contact Sales
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Test Mode Notice */}
        <div className="glass-card rounded-2xl p-6 border border-amber-500/30 bg-amber-500/5">
          <div className="flex items-start gap-3">
            <div className="icon-container-sm" style={{ background: 'rgba(251, 191, 36, 0.2)' }}>
              <Shield className="text-amber-400" size={20} />
            </div>
            <div>
              <p className="font-semibold text-amber-400">Test Mode Active</p>
              <p className="text-sm text-amber-300/80 mt-1">
                Payments are in test mode. Use test card: <code className="bg-amber-500/20 px-2 py-1 rounded text-amber-300">4242 4242 4242 4242</code>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
