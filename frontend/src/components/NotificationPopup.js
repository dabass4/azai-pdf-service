import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Bell, AlertCircle, Info, CheckCircle, Clock, AlertTriangle } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * NotificationPopup Component
 * 
 * Shows pop-up notifications when user logs in
 * Displays unread notifications one at a time
 * Sends email copy so users can refer back
 */
const NotificationPopup = ({ onClose, notification }) => {
  const getCategoryIcon = (category) => {
    switch (category) {
      case 'success': return <CheckCircle className="w-6 h-6 text-green-600" />;
      case 'error': return <AlertCircle className="w-6 h-6 text-red-600" />;
      case 'warning': return <AlertTriangle className="w-6 h-6 text-yellow-600" />;
      case 'delay': return <Clock className="w-6 h-6 text-orange-600" />;
      default: return <Info className="w-6 h-6 text-blue-600" />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'bg-red-600';
      case 'high': return 'bg-orange-500';
      case 'normal': return 'bg-blue-600';
      case 'low': return 'bg-gray-500';
      default: return 'bg-blue-600';
    }
  };

  const handleDismiss = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/notifications/dismiss/${notification.id}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (error) {
      console.error('Error dismissing notification:', error);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        {/* Header with priority color */}
        <div className={`${getPriorityColor(notification.priority)} p-4 flex items-center justify-between`}>
          <div className="flex items-center gap-3 text-white">
            <Bell className="w-6 h-6" />
            <h2 className="text-xl font-bold">AZAI Notification</h2>
          </div>
          <button
            onClick={handleDismiss}
            className="text-white hover:bg-white hover:bg-opacity-20 rounded p-1 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* Icon and Title */}
          <div className="flex items-start gap-4 mb-4">
            {getCategoryIcon(notification.category)}
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {notification.title}
              </h3>
              <div className="flex items-center gap-3 text-sm text-gray-600 mb-4">
                <span className="font-medium">Source: {notification.source.toUpperCase()}</span>
                <span>•</span>
                <span>Type: {notification.type.replace('_', ' ').toUpperCase()}</span>
                <span>•</span>
                <span className={`font-semibold ${
                  notification.priority === 'urgent' ? 'text-red-600' :
                  notification.priority === 'high' ? 'text-orange-600' :
                  'text-blue-600'
                }`}>
                  Priority: {notification.priority.toUpperCase()}
                </span>
              </div>
            </div>
          </div>

          {/* Message */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
            <p className="text-gray-800 text-lg leading-relaxed whitespace-pre-wrap">
              {notification.message}
            </p>
          </div>

          {/* Timestamp */}
          <p className="text-sm text-gray-500 text-center">
            {new Date(notification.created_at).toLocaleString('en-US', {
              dateStyle: 'full',
              timeStyle: 'short'
            })}
          </p>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 p-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              📧 <strong>Also sent to your email</strong> for your records
            </p>
            <button
              onClick={handleDismiss}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors"
            >
              Got it!
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationPopup;
