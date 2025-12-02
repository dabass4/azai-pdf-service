import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Key, MessageSquare, FileText, Activity, Users } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const AdminDashboard = () => {
  const navigate = useNavigate();

  const adminCards = [
    {
      title: 'Organizations',
      description: 'Manage client organizations and their details',
      icon: Building2,
      color: 'bg-blue-600 hover:bg-blue-700',
      path: '/admin/organizations'
    },
    {
      title: 'Credentials',
      description: 'Configure OMES and Availity credentials per organization',
      icon: Key,
      color: 'bg-green-600 hover:bg-green-700',
      path: '/admin/credentials'
    },
    {
      title: 'Support Tickets',
      description: 'Track and resolve client support issues',
      icon: MessageSquare,
      color: 'bg-purple-600 hover:bg-purple-700',
      path: '/admin/support'
    },
    {
      title: 'System Logs',
      description: 'Monitor application activity and errors',
      icon: FileText,
      color: 'bg-gray-600 hover:bg-gray-700',
      path: '/admin/logs'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">Manage your multi-tenant healthcare platform</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {adminCards.map((card) => (
            <Card 
              key={card.path}
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => navigate(card.path)}
            >
              <CardContent className="pt-6">
                <div className={`w-12 h-12 rounded-lg ${card.color} flex items-center justify-center mb-4`}>
                  <card.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{card.title}</h3>
                <p className="text-sm text-gray-600">{card.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Quick Start Guide
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="space-y-3 text-sm">
                <li className="flex gap-2">
                  <span className="font-semibold text-blue-600">1.</span>
                  <span>Create client organizations in <strong>Organizations</strong></span>
                </li>
                <li className="flex gap-2">
                  <span className="font-semibold text-blue-600">2.</span>
                  <span>Configure OMES/Availity credentials in <strong>Credentials</strong></span>
                </li>
                <li className="flex gap-2">
                  <span className="font-semibold text-blue-600">3.</span>
                  <span>Monitor client issues in <strong>Support Tickets</strong></span>
                </li>
                <li className="flex gap-2">
                  <span className="font-semibold text-blue-600">4.</span>
                  <span>Track system health in <strong>System Logs</strong></span>
                </li>
              </ol>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Admin Panel Features
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">✓</span>
                  <span>Manage all client organizations in one place</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">✓</span>
                  <span>Configure credentials per organization (encrypted storage)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">✓</span>
                  <span>Track and resolve support tickets</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">✓</span>
                  <span>Monitor system logs and errors in real-time</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">✓</span>
                  <span>No restart needed - update client configs on the fly</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">✓</span>
                  <span>Multi-tenant architecture with data isolation</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6 bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <div className="bg-blue-600 rounded-full p-2 mt-1">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-blue-900 mb-1">Need Help?</h3>
                <p className="text-sm text-blue-800">
                  See <strong>ADMIN_LOGIN_GUIDE.md</strong> for complete instructions on creating super admin accounts,
                  onboarding new clients, and managing the multi-tenant system.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboard;
