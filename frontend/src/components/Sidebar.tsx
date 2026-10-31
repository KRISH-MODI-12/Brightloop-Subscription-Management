import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Users, Package, CalendarRange,
  FileSpreadsheet, RefreshCw, Receipt, CreditCard,
  Percent, Landmark, ShieldCheck, LogOut, ExternalLink
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user, role, logout } = useAuth();

  const isCustomer = role === 'customer';
  const isAdmin = role === 'admin';

  const adminNavItems = [
    { name: 'Overview', path: '/', icon: LayoutDashboard },
    { name: 'Customers', path: '/customers', icon: Users },
    { name: 'Products', path: '/products', icon: Package },
    { name: 'Plans', path: '/plans', icon: CalendarRange },
    { name: 'Quotations', path: '/quotations', icon: FileSpreadsheet },
    { name: 'Subscriptions', path: '/subscriptions', icon: RefreshCw },
    { name: 'Invoices', path: '/invoices', icon: Receipt },
    { name: 'Payments', path: '/payments', icon: CreditCard },
    { name: 'Discounts', path: '/discounts', icon: Percent },
    { name: 'Taxes', path: '/taxes', icon: Landmark },
  ];

  const staffNavItems = [
    { name: 'Overview', path: '/', icon: LayoutDashboard },
    { name: 'Customers', path: '/customers', icon: Users },
    { name: 'Products', path: '/products', icon: Package },
    { name: 'Plans', path: '/plans', icon: CalendarRange },
    { name: 'Quotations', path: '/quotations', icon: FileSpreadsheet },
    { name: 'Subscriptions', path: '/subscriptions', icon: RefreshCw },
    { name: 'Invoices', path: '/invoices', icon: Receipt },
    { name: 'Payments', path: '/payments', icon: CreditCard },
  ];

  const customerNavItems = [
    { name: 'My Subscriptions', path: '/portal', icon: RefreshCw },
    { name: 'My Invoices', path: '/invoices', icon: Receipt },
    { name: 'My Payments', path: '/payments', icon: CreditCard },
    { name: 'Browse Catalog', path: '/plans', icon: Package },
  ];

  const navItems = isCustomer ? customerNavItems : (isAdmin ? adminNavItems : staffNavItems);

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 border-r border-slate-800">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-teal-500/20">
            <RefreshCw className="w-5 h-5 text-white animate-spin-slow" />
          </div>
          <div>
            <span className="font-bold text-white tracking-tight text-base block leading-none">BRIGHTLOOP</span>
            <span className="text-[10px] text-teal-400 font-semibold uppercase tracking-wider block mt-1">Subscription OS</span>
          </div>
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          {isCustomer ? 'Self-Service Portal' : 'Operations & Billing'}
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-teal-500/10 text-teal-400 border-l-2 border-teal-500'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}

        {/* Quick portal switch for admin/staff to test customer view */}
        {!isCustomer && (
          <div className="pt-4 mt-4 border-t border-slate-800/80">
            <NavLink
              to="/portal"
              className="flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-teal-300 hover:bg-slate-800/40"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Customer Portal View</span>
            </NavLink>
          </div>
        )}
      </nav>

      {/* User Footer Profile */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40">
        <div className="flex items-center justify-between">
          <div className="min-w-0 flex-1 mr-2">
            <p className="text-sm font-semibold text-white truncate">{user?.full_name || 'User'}</p>
            <div className="flex items-center space-x-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-xs uppercase tracking-wider text-slate-400 font-medium">
                {role || 'Guest'}
              </span>
            </div>
          </div>
          <button
            onClick={logout}
            title="Sign Out"
            className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
