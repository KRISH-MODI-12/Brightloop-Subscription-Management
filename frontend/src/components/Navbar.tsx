import React, { useState, useEffect } from 'react';
import { Bell, RefreshCw, CheckCircle2, AlertCircle, PlayCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { AppNotification } from '../types';

interface NavbarProps {
  title: string;
}

export const Navbar: React.FC<NavbarProps> = ({ title }) => {
  const { user, role } = useAuth();
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [isBillingRunning, setIsBillingRunning] = useState(false);
  const [billingResultMsg, setBillingResultMsg] = useState<string | null>(null);

  const fetchNotifications = async () => {
    try {
      const data = await api.get<AppNotification[]>('/notifications?limit=8');
      setNotifications(data);
      const unread = await api.get<{ unread_count: number }>('/notifications/unread-count');
      setUnreadCount(unread.unread_count);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000); // 30s poll
    return () => clearInterval(interval);
  }, []);

  const handleRunBilling = async () => {
    setIsBillingRunning(true);
    setBillingResultMsg(null);
    try {
      const res = await api.post<{ generated_invoices: number; overdue_marked: number }>(
        '/invoices/run-billing-job'
      );
      setBillingResultMsg(`Billing Run: ${res.generated_invoices} invoices generated, ${res.overdue_marked} overdue marked.`);
      fetchNotifications();
      setTimeout(() => setBillingResultMsg(null), 6000);
    } catch (err: any) {
      setBillingResultMsg(`Billing error: ${err.message}`);
      setTimeout(() => setBillingResultMsg(null), 6000);
    } finally {
      setIsBillingRunning(false);
    }
  };

  const markAllRead = async () => {
    try {
      await api.put('/notifications/mark-all-read');
      setUnreadCount(0);
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
    } catch {
      // ignore
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h1>
      </div>

      <div className="flex items-center space-x-4">
        {/* Trigger automated recurring billing run (Admin & Staff) */}
        {role !== 'customer' && (
          <button
            onClick={handleRunBilling}
            disabled={isBillingRunning}
            title="Execute background billing job now"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 border border-teal-200 transition-colors disabled:opacity-50"
          >
            <PlayCircle className={`w-3.5 h-3.5 ${isBillingRunning ? 'animate-spin' : ''}`} />
            <span>{isBillingRunning ? 'Running Billing...' : 'Run Billing Job'}</span>
          </button>
        )}

        {billingResultMsg && (
          <span className="text-xs font-medium text-teal-600 bg-teal-50 px-2 py-1 rounded border border-teal-200 animate-in fade-in">
            {billingResultMsg}
          </span>
        )}

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-teal-600 text-white rounded-full text-[10px] font-bold flex items-center justify-center ring-2 ring-white">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="flex items-center justify-between px-4 py-2 border-b border-slate-100">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Notifications</span>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllRead}
                    className="text-[11px] text-teal-600 hover:underline font-semibold"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-72 overflow-y-auto divide-y divide-slate-100">
                {notifications.length === 0 ? (
                  <p className="p-4 text-xs text-slate-400 text-center">No notifications yet</p>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`p-3 text-xs ${n.is_read ? 'bg-white' : 'bg-teal-50/50'}`}
                    >
                      <p className="font-semibold text-slate-900">{n.title}</p>
                      <p className="text-slate-600 mt-0.5">{n.message}</p>
                      <span className="text-[10px] text-slate-400 mt-1 block">
                        {new Date(n.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Role badge */}
        <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-bold uppercase">
            {user?.full_name ? user.full_name[0] : 'U'}
          </div>
          <div className="hidden md:block text-left">
            <span className="text-xs font-semibold text-slate-900 block leading-tight">{user?.full_name}</span>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">{role}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
