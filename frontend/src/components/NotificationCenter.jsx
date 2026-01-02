import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Bell, Mail, MessageSquare, Check, X } from 'lucide-react';
import api from '../services/api';

export default function NotificationCenter({ projectId }) {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showPanel, setShowPanel] = useState(false);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [projectId]);

  const fetchNotifications = async () => {
    try {
      const response = await api.get(`/notifications/user_123?project_id=${projectId}&unread_only=false`);
      setNotifications(response.data.notifications);
      setUnreadCount(response.data.notifications.filter(n => !n.read).length);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await api.post('/notifications/mark-read', { notification_id: notificationId });
      fetchNotifications();
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'critical_issue': return <Bell className="text-red-500" />;
      case 'scan_complete': return <Check className="text-green-500" />;
      default: return <MessageSquare className="text-blue-500" />;
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowPanel(!showPanel)}
        className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
      >
        <Bell size={24} />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </button>

      {showPanel && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute right-0 mt-2 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 z-50"
        >
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold">Notifications</h3>
            <p className="text-sm text-gray-500">{unreadCount} unread</p>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No notifications
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750 ${
                    !notification.read ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {getIcon(notification.type)}
                    <div className="flex-1">
                      <h4 className="font-medium text-sm">
                        {notification.type.replace('_', ' ').toUpperCase()}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {notification.data.message}
                      </p>
                      <p className="text-xs text-gray-400 mt-2">
                        {new Date(notification.timestamp).toLocaleString()}
                      </p>
                    </div>
                    {!notification.read && (
                      <button
                        onClick={() => markAsRead(notification.id)}
                        className="text-blue-500 hover:text-blue-600"
                      >
                        <Check size={16} />
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setShowPanel(false)}
              className="w-full text-center text-sm text-blue-500 hover:text-blue-600"
            >
              Close
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}
