import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bell, Send, AlertCircle, Info, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * Notification Center - Admin Interface
 * 
 * Allows admins to:
 * - Send notifications to all users
 * - View notification history
 * - Manage notification templates
 */
const NotificationCenter = () => {
  const [loading, setLoading] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [showSendForm, setShowSendForm] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    type: 'medicaid_update',
    category: 'info',
    title: '',
    message: '',
    source: 'admin',
    priority: 'normal',
    send_email: true
  });

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/notifications/list?limit=100`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotifications(response.data.notifications || []);
    } catch (error) {
      console.error('Error fetching notifications:', error);
      toast.error('Failed to load notifications');
    }
  };

  const handleSendNotification = async (e) => {
    e.preventDefault();
    
    if (!formData.title || !formData.message) {
      toast.error('Please fill in title and message');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/notifications/send`,
        {
          ...formData,
          recipients: ['all']  // Send to all users
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      toast.success(`Notification sent to ${response.data.notification.recipients_count} users!`);
      
      // Reset form
      setFormData({
        type: 'medicaid_update',
        category: 'info',
        title: '',
        message: '',
        source: 'admin',
        priority: 'normal',
        send_email: true
      });
      setShowSendForm(false);
      
      // Refresh list
      fetchNotifications();
    } catch (error) {
      console.error('Error sending notification:', error);
      toast.error(error.response?.data?.detail || 'Failed to send notification');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'success': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'error': return <AlertCircle className="w-5 h-5 text-red-600" />;
      case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      case 'delay': return <Clock className="w-5 h-5 text-orange-600" />;
      default: return <Info className="w-5 h-5 text-blue-600" />;
    }
  };

  const getPriorityBadge = (priority) => {
    const styles = {
      urgent: 'bg-red-100 text-red-800',
      high: 'bg-orange-100 text-orange-800',
      normal: 'bg-blue-100 text-blue-800',
      low: 'bg-gray-100 text-gray-800'
    };
    return styles[priority] || styles.normal;
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bell className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Notification Center</h1>
                <p className="text-gray-600">Send notifications about Medicaid, Sandata, Availity, and ODM updates</p>
              </div>
            </div>
            <button
              onClick={() => setShowSendForm(!showSendForm)}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Send className="w-5 h-5" />
              Send Notification
            </button>
          </div>
        </div>

        {/* Send Notification Form */}
        {showSendForm && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Send New Notification</h2>
            <form onSubmit={handleSendNotification} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notification Type
                  </label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="medicaid_update">Medicaid Update</option>
                    <option value="sandata_alert">Sandata Alert</option>
                    <option value="availity_alert">Availity Alert</option>
                    <option value="odm_notice">ODM Notice</option>
                    <option value="system_alert">System Alert</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="info">Information</option>
                    <option value="update">Update</option>
                    <option value="delay">Delay</option>
                    <option value="warning">Warning</option>
                    <option value="error">Error</option>
                    <option value="success">Success</option>
                  </select>
                </div>

                {/* Priority */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="low">Low</option>
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>

                {/* Send Email */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="send_email"
                    checked={formData.send_email}
                    onChange={(e) => setFormData({ ...formData, send_email: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="send_email" className="ml-2 text-sm font-medium text-gray-700">
                    Send Email Notification
                  </label>
                </div>
              </div>

              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g., Medicaid Processing Delay - Action Required"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              {/* Message */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Message *
                </label>
                <textarea
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  placeholder="Enter your notification message here..."
                  rows={6}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              {/* Buttons */}
              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Sending...' : 'Send to All Users'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowSendForm(false)}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-6 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Notification History */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Notification History</h2>
          
          {notifications.length === 0 ? (
            <div className="text-center py-12">
              <Bell className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No notifications sent yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1">
                      {getCategoryIcon(notification.category)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-900">{notification.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                        </div>
                        <span className={`text-xs font-semibold px-2 py-1 rounded ${getPriorityBadge(notification.priority)}`}>
                          {notification.priority.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                        <span>Type: {notification.type.replace('_', ' ')}</span>
                        <span>•</span>
                        <span>Source: {notification.source.toUpperCase()}</span>
                        <span>•</span>
                        <span>Recipients: {notification.recipient_emails?.length || 0}</span>
                        <span>•</span>
                        <span>{notification.email_sent ? '✅ Email Sent' : '⏸️ Email Pending'}</span>
                        <span>•</span>
                        <span>{new Date(notification.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationCenter;
