import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Settings, Bell, Mail, BellOff } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * Notification Preferences Page
 * 
 * Allows users to manage their notification settings
 */
const NotificationPreferences = () => {
  const [loading, setLoading] = useState(false);
  const [preferences, setPreferences] = useState(null);
  const [formData, setFormData] = useState({
    email_enabled: true,
    medicaid_updates: true,
    sandata_alerts: true,
    availity_alerts: true,
    odm_notices: true,
    system_alerts: true,
    digest_mode: false,
    digest_time: '09:00'
  });

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/notifications/preferences/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const prefs = response.data.preferences;
      setPreferences(prefs);
      setFormData({
        email_enabled: prefs.email_enabled ?? true,
        medicaid_updates: prefs.medicaid_updates ?? true,
        sandata_alerts: prefs.sandata_alerts ?? true,
        availity_alerts: prefs.availity_alerts ?? true,
        odm_notices: prefs.odm_notices ?? true,
        system_alerts: prefs.system_alerts ?? true,
        digest_mode: prefs.digest_mode ?? false,
        digest_time: prefs.digest_time ?? '09:00'
      });
    } catch (error) {
      console.error('Error fetching preferences:', error);
      toast.error('Failed to load preferences');
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API}/notifications/preferences/me`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      toast.success('Preferences saved successfully!');
      fetchPreferences();
    } catch (error) {
      console.error('Error saving preferences:', error);
      toast.error('Failed to save preferences');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center gap-3 mb-2">
            <Settings className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">Notification Preferences</h1>
          </div>
          <p className="text-gray-600">
            Manage how you receive notifications about Medicaid updates, Sandata alerts, and more
          </p>
        </div>

        {/* Preferences Form */}
        <form onSubmit={handleSave}>
          <div className="bg-white rounded-lg shadow-sm p-6 space-y-6">
            {/* Email Notifications */}
            <div className="border-b border-gray-200 pb-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Mail className="w-6 h-6 text-gray-600" />
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Email Notifications</h2>
                    <p className="text-sm text-gray-600">Receive notifications via email</p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.email_enabled}
                    onChange={(e) => setFormData({ ...formData, email_enabled: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>

            {/* Notification Types */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Notification Types</h2>
              <div className="space-y-4">
                {/* Medicaid Updates */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">Medicaid Updates</p>
                    <p className="text-sm text-gray-600">Updates about Medicaid processing and delays</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.medicaid_updates}
                    onChange={(e) => setFormData({ ...formData, medicaid_updates: e.target.checked })}
                    disabled={!formData.email_enabled}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 disabled:opacity-50"
                  />
                </div>

                {/* Sandata Alerts */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">Sandata Alerts</p>
                    <p className="text-sm text-gray-600">Status updates and alerts from Sandata</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.sandata_alerts}
                    onChange={(e) => setFormData({ ...formData, sandata_alerts: e.target.checked })}
                    disabled={!formData.email_enabled}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 disabled:opacity-50"
                  />
                </div>

                {/* Availity Alerts */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">Availity Alerts</p>
                    <p className="text-sm text-gray-600">Status updates from Availity clearinghouse</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.availity_alerts}
                    onChange={(e) => setFormData({ ...formData, availity_alerts: e.target.checked })}
                    disabled={!formData.email_enabled}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 disabled:opacity-50"
                  />
                </div>

                {/* ODM Notices */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">ODM Notices</p>
                    <p className="text-sm text-gray-600">Official notices from Ohio Department of Medicaid</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.odm_notices}
                    onChange={(e) => setFormData({ ...formData, odm_notices: e.target.checked })}
                    disabled={!formData.email_enabled}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 disabled:opacity-50"
                  />
                </div>

                {/* System Alerts */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">System Alerts</p>
                    <p className="text-sm text-gray-600">Important system notifications and updates</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={formData.system_alerts}
                    onChange={(e) => setFormData({ ...formData, system_alerts: e.target.checked })}
                    disabled={!formData.email_enabled}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 disabled:opacity-50"
                  />
                </div>
              </div>
            </div>

            {/* Digest Mode (Future Feature) */}
            <div className="border-t border-gray-200 pt-6">
              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">Daily Digest Mode</p>
                  <p className="text-sm text-gray-600">
                    Receive a single daily email with all notifications (Coming Soon)
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={formData.digest_mode}
                  onChange={(e) => setFormData({ ...formData, digest_mode: e.target.checked })}
                  disabled={true}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 disabled:opacity-50"
                />
              </div>
            </div>

            {/* Save Button */}
            <div className="flex items-center justify-end gap-3 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Saving...' : 'Save Preferences'}
              </button>
            </div>
          </div>
        </form>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> You will receive important system notifications regardless of your preferences.
            Critical alerts about security, account issues, or service outages will always be sent.
          </p>
        </div>
      </div>
    </div>
  );
};

export default NotificationPreferences;
