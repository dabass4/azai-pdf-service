import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import NotificationPopup from '../components/NotificationPopup';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const NotificationContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
};

/**
 * NotificationProvider
 * 
 * Fetches unread notifications on login
 * Shows pop-ups one at a time
 * Tracks which have been shown
 */
export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [currentNotification, setCurrentNotification] = useState(null);
  const [notificationQueue, setNotificationQueue] = useState([]);
  const [hasChecked, setHasChecked] = useState(false);

  useEffect(() => {
    // Check for unread notifications when app loads
    // This happens after login
    const token = localStorage.getItem('token');
    if (token && !hasChecked) {
      checkForNotifications();
      setHasChecked(true);
    }
  }, [hasChecked]);

  useEffect(() => {
    // Show next notification in queue
    if (!currentNotification && notificationQueue.length > 0) {
      setCurrentNotification(notificationQueue[0]);
      setNotificationQueue(notificationQueue.slice(1));
    }
  }, [currentNotification, notificationQueue]);

  const checkForNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get(`${API}/notifications/unread`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const unread = response.data.notifications || [];
      
      if (unread.length > 0) {
        // Sort by priority (urgent first)
        const sorted = unread.sort((a, b) => {
          const priorityOrder = { urgent: 0, high: 1, normal: 2, low: 3 };
          return priorityOrder[a.priority] - priorityOrder[b.priority];
        });
        
        setNotifications(sorted);
        setNotificationQueue(sorted);
      }
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const handleCloseNotification = () => {
    setCurrentNotification(null);
  };

  const refreshNotifications = () => {
    setHasChecked(false);
  };

  return (
    <NotificationContext.Provider value={{ refreshNotifications }}>
      {children}
      {currentNotification && (
        <NotificationPopup
          notification={currentNotification}
          onClose={handleCloseNotification}
        />
      )}
    </NotificationContext.Provider>
  );
};
