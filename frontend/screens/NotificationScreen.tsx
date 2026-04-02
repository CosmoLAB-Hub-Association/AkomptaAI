
import React from 'react';
import { Screen } from '../types';
import { Header } from '../components/Shared';
import { useNotifications } from '../hooks';
import { Bell, CheckCircle, TrendingUp, Gift, AlertCircle } from 'lucide-react';

interface Props {
  onNavigate: (screen: Screen) => void;
  onToggleMenu: () => void;
}

const NotificationScreen: React.FC<Props> = ({ onNavigate, onToggleMenu }) => {
  const { data: notifications, loading, markRead } = useNotifications();

  const sortedNotifications = [...notifications].sort((a: any, b: any) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'reminder': return <AlertCircle size={20} />;
      case 'profit': return <TrendingUp size={20} />;
      case 'promo': return <Gift size={20} />;
      default: return <Bell size={20} />;
    }
  };

  const getNotificationColor = (type: string, isRead: boolean) => {
    const opacity = isRead ? 'opacity-60' : '';
    switch (type) {
      case 'reminder': return `bg-orange-500 dark:bg-orange-600 ${opacity}`;
      case 'profit': return `bg-green-600 dark:bg-green-700 ${opacity}`;
      case 'promo': return `bg-purple-500 dark:bg-purple-600 ${opacity}`;
      default: return `bg-[#7daea5] dark:bg-gray-800 ${opacity}`;
    }
  };

  const handleNotificationClick = async (notification: any) => {
    if (!notification.is_read) {
      await markRead(notification.id);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'maintenant';
    if (diffMins < 60) return `Il y a ${diffMins}min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    return `Il y a ${diffDays}j`;
  };

  return (
    <div className="flex flex-col h-full bg-[#8abcb3] dark:bg-gray-900 pb-24 overflow-y-auto no-scrollbar transition-colors">
      <Header
        title="Notifications"
        onBack={() => onNavigate(Screen.DASHBOARD)}
        onMenu={onToggleMenu}
      />

      <div className="px-4 space-y-4">
        {loading ? (
          <div className="text-center py-8 text-white dark:text-gray-400">
            Chargement...
          </div>
        ) : sortedNotifications.length === 0 ? (
          <div className="text-center py-8">
            <Bell size={48} className="mx-auto mb-4 text-white/50 dark:text-gray-500" />
            <p className="text-white dark:text-gray-400">Aucune notification</p>
          </div>
        ) : (
          sortedNotifications.map((notification: any) => (
            <div
              key={notification.id}
              onClick={() => handleNotificationClick(notification)}
              className={`${getNotificationColor(notification.type, notification.is_read)} rounded-3xl p-6 shadow-sm transition-all cursor-pointer hover:shadow-md active:scale-[0.98]`}
            >
              <div className="flex justify-between items-start text-white dark:text-gray-400 text-xs mb-2">
                <div className="flex items-center gap-2">
                  {getNotificationIcon(notification.type)}
                  <span className="uppercase font-bold text-white dark:text-green-400">
                    {notification.type === 'reminder' ? 'RAPPEL' :
                      notification.type === 'profit' ? 'BÉNÉFICE' :
                        notification.type === 'promo' ? 'PROMO' : 'INFO'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span>{formatDate(notification.created_at)}</span>
                  {notification.is_read && (
                    <CheckCircle size={14} className="text-white/70" />
                  )}
                </div>
              </div>
              <div className="text-white dark:text-white font-bold text-lg">
                {notification.title}
              </div>
              {notification.message && (
                <div className="text-white/80 dark:text-gray-300 text-sm mt-2">
                  {notification.message}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default NotificationScreen;