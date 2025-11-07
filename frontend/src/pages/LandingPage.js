import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Check, ArrowRight, Building2, Users, FileText, Shield, Zap, TrendingUp } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  const plans = [
    {
      id: 'basic',
      name: 'Basic',
      price: 49,
      description: 'Perfect for small healthcare providers',
      features: [
        '100 timesheets per month',
        'Up to 5 employees',
        'Up to 10 patients',
        'Sandata submission',
        'Email support'
      ],
      limits: '100 timesheets/month',
      cta: 'Start Free Trial'
    },
    {
      id: 'professional',
      name: 'Professional',
      price: 149,
      description: 'For growing healthcare organizations',
      features: [
        'Unlimited timesheets',
        'Unlimited employees',
        'Unlimited patients',
        'Sandata + Ohio EVV submission',
        'Bulk operations',
        'Advanced reporting',
        'Priority support'
      ],
      limits: 'Unlimited',
      cta: 'Start Free Trial',
      popular: true
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: 'Custom',
      description: 'Custom solutions for large organizations',
      features: [
        'Everything in Professional',
        'API access',
        'Custom integrations',
        'White-label option',
        'Dedicated support',
        'SLA guarantee'
      ],
      limits: 'Custom',
      cta: 'Contact Sales'
    }
  ];

  const features = [
    {
      icon: FileText,
      title: 'AI-Powered Scanning',
      description: 'Upload PDF or JPG timesheets and let AI extract all data automatically'
    },
    {
      icon: Shield,
      title: 'Ohio Medicaid EVV Compliant',
      description: 'Built-in compliance for Ohio Department of Medicaid EVV requirements'
    },
    {
      icon: Users,
      title: 'Multi-Tenant Isolation',
      description: 'Your data is completely isolated and secure in your own organization'
    },
    {
      icon: Zap,
      title: 'Bulk Operations',
      description: 'Submit multiple timesheets to Sandata and Medicaid with one click'
    },
    {
      icon: TrendingUp,
      title: 'Advanced Reporting',
      description: 'Track submissions, monitor compliance, and generate reports'
    },
    {
      icon: Building2,
      title: 'Organization Management',
      description: 'Manage employees, patients, and service codes all in one place'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <FileText className="text-blue-600" size={32} />
            <h1 className="text-2xl font-bold text-gray-900">Timesheet Scanner</h1>
          </div>
          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => navigate('/login')}>
              Sign In
            </Button>
            <Button onClick={() => navigate('/signup')} className="bg-blue-600 hover:bg-blue-700">
              Start Free Trial
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Healthcare Timesheet Management
          <br />
          <span className="text-blue-600">Made Simple</span>
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          AI-powered timesheet scanning and submission for Ohio Medicaid providers. 
          Sandata integration, EVV compliance, and automated workflows.
        </p>
        <div className="flex gap-4 justify-center">
          <Button size="lg" onClick={() => navigate('/signup')} className="bg-blue-600 hover:bg-blue-700 text-lg px-8 py-6">
            Start 14-Day Free Trial
            <ArrowRight className="ml-2" size={20} />
          </Button>
          <Button size="lg" variant="outline" onClick={() => navigate('/login')} className="text-lg px-8 py-6">
            Sign In
          </Button>
        </div>
        <p className="text-sm text-gray-500 mt-4">No credit card required • Cancel anytime</p>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 bg-white rounded-3xl shadow-xl my-12">
        <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">
          Everything you need to manage timesheets
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div key={index} className="text-center">
                <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Icon className="text-blue-600" size={32} />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Pricing Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-xl text-gray-600">
            Choose the plan that's right for your organization
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <Card 
              key={plan.id} 
              className={`relative ${plan.popular ? 'border-4 border-blue-500 shadow-2xl scale-105' : 'border-2 border-gray-200'}`}
            >
              {plan.popular && (
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                    Most Popular
                  </span>
                </div>
              )}
              
              <CardHeader className="text-center pt-8">
                <CardTitle className="text-2xl font-bold text-gray-900">{plan.name}</CardTitle>
                <CardDescription className="text-gray-600 mt-2">{plan.description}</CardDescription>
                <div className="mt-4">
                  {typeof plan.price === 'number' ? (
                    <>
                      <span className="text-5xl font-bold text-gray-900">${plan.price}</span>
                      <span className="text-gray-600">/month</span>
                    </>
                  ) : (
                    <span className="text-5xl font-bold text-gray-900">{plan.price}</span>
                  )}
                </div>
              </CardHeader>

              <CardContent className="pt-6">
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <Check className="text-green-500 flex-shrink-0 mt-1" size={20} />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button 
                  className={`w-full ${plan.popular ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-900 hover:bg-gray-800'}`}
                  size="lg"
                  onClick={() => navigate('/signup')}
                >
                  {plan.cta}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-12 text-center text-white">
          <h2 className="text-4xl font-bold mb-4">
            Ready to streamline your timesheet management?
          </h2>
          <p className="text-xl mb-8 text-blue-100">
            Join healthcare providers who trust us for Ohio Medicaid compliance
          </p>
          <Button 
            size="lg" 
            onClick={() => navigate('/signup')}
            className="bg-white text-blue-600 hover:bg-gray-100 text-lg px-8 py-6"
          >
            Start Your Free Trial
            <ArrowRight className="ml-2" size={20} />
          </Button>
          <p className="text-sm text-blue-100 mt-4">14-day free trial • No credit card required</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-400">
            © 2025 Timesheet Scanner. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
