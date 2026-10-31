import React, { useState, useEffect } from 'react';
import {
  Users, RefreshCw, Package, IndianRupee, TrendingUp, AlertTriangle,
  Clock, ArrowUpRight, CheckCircle2, ShieldAlert
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, PieChart, Pie, Cell, Legend
} from 'recharts';
import { api } from '../api/client';
import { DashboardAnalytics, Subscription, Invoice, Payment } from '../types';
import { StatsCard } from '../components/StatsCard';
import { StatusBadge } from '../components/StatusBadge';
import { Navbar } from '../components/Navbar';

export const Dashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [recentSubs, setRecentSubs] = useState<Subscription[]>([]);
  const [recentInvs, setRecentInvs] = useState<Invoice[]>([]);
  const [recentPays, setRecentPays] = useState<Payment[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const [analyticsData, subsData, invsData, paysData] = await Promise.all([
        api.get<DashboardAnalytics>('/dashboard/analytics'),
        api.get<Subscription[]>('/subscriptions?limit=5'),
        api.get<Invoice[]>('/invoices?limit=5'),
        api.get<Payment[]>('/payments?limit=5'),
      ]);
      setAnalytics(analyticsData);
      setRecentSubs(subsData);
      setRecentInvs(invsData);
      setRecentPays(paysData);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const stats = analytics?.stats;
  const PIE_COLORS = ['#14b8a6', '#0ea5e9', '#f59e0b', '#ef4444', '#8b5cf6', '#64748b'];

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50 min-h-screen">
      <Navbar title="Executive Subscription Dashboard" />

      <main className="p-8 space-y-8 flex-1 overflow-y-auto">
        {/* KPI Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          <StatsCard
            title="Total Revenue"
            value={`₹${(Number(stats?.total_revenue_collected || 0)).toLocaleString('en-IN')}`}
            subtitle="Actual collected cash"
            icon={IndianRupee}
            color="brand"
            trend="+18.4% vs last mo"
            trendUp={true}
          />
          <StatsCard
            title="Monthly Rec. Rev (MRR)"
            value={`₹${(Number(stats?.mrr || 0)).toLocaleString('en-IN')}`}
            subtitle="Normalized monthly recurring"
            icon={TrendingUp}
            color="emerald"
            trend="Active run rate"
            trendUp={true}
          />
          <StatsCard
            title="Annual Rec. Rev (ARR)"
            value={`₹${(Number(stats?.arr || 0)).toLocaleString('en-IN')}`}
            subtitle="Projected annualized run rate"
            icon={ArrowUpRight}
            color="indigo"
          />
          <StatsCard
            title="Active Subscriptions"
            value={stats?.active_subscriptions || 0}
            subtitle={`${stats?.total_customers || 0} total customers`}
            icon={RefreshCw}
            color="brand"
          />
          <StatsCard
            title="Outstanding Receivables"
            value={`₹${(Number(stats?.pending_payments || 0)).toLocaleString('en-IN')}`}
            subtitle={`${stats?.overdue_invoices_count || 0} overdue invoices`}
            icon={AlertTriangle}
            color="rose"
            trend={stats?.overdue_invoices_count ? `₹${stats.overdue_invoices_amount} overdue` : 'On track'}
            trendUp={false}
          />
        </div>

        {/* Charts Row 1: Monthly Invoiced vs Collected & Subscription Growth */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Monthly Revenue Bar Chart */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Monthly Cash Collection vs Invoiced</h3>
                <p className="text-xs text-slate-500">Live recognized payments compared to total invoiced</p>
              </div>
            </div>
            <div className="h-72 w-full">
              {analytics?.monthly_revenue && (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.monthly_revenue} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} tickFormatter={(val) => `₹${val / 1000}k`} />
                    <Tooltip
                      formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')}`, '']}
                      contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
                    <Bar dataKey="revenue" name="Cash Collected" fill="#0d9488" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="invoiced" name="Invoiced Amount" fill="#cbd5e1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Subscription Growth Trend */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Subscription Trajectory & Net Additions</h3>
                <p className="text-xs text-slate-500">Active accounts and cancellation distribution</p>
              </div>
            </div>
            <div className="h-72 w-full">
              {analytics?.subscription_growth && (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={analytics.subscription_growth} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="activeGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
                    <Area type="monotone" dataKey="active" name="Active Portfolio" stroke="#0d9488" fillOpacity={1} fill="url(#activeGrad)" />
                    <Area type="monotone" dataKey="new_subs" name="New Subscriptions" stroke="#6366f1" fill="#e0e7ff" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        {/* Charts Row 2: Status Distributions & Product Revenue */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Subscription Status Breakdown */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-1">Subscription Status Mix</h3>
            <p className="text-xs text-slate-500 mb-4">Portfolio lifecycle segmentation</p>
            <div className="h-60 w-full flex items-center justify-center">
              {analytics?.subscription_status_distribution && (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={analytics.subscription_status_distribution}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={75}
                      innerRadius={45}
                      paddingAngle={4}
                    >
                      {analytics.subscription_status_distribution.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Payment Status Distribution */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-1">Invoice Settlement Status</h3>
            <p className="text-xs text-slate-500 mb-4">Paid, Partial, Overdue breakdown</p>
            <div className="h-60 w-full flex items-center justify-center">
              {analytics?.payment_status_distribution && (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={analytics.payment_status_distribution}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={75}
                      innerRadius={45}
                      paddingAngle={4}
                    >
                      {analytics.payment_status_distribution.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[(index + 2) % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Revenue by Product */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-1">Revenue by Product</h3>
            <p className="text-xs text-slate-500 mb-4">Top contributors to settled revenue</p>
            <div className="h-60 w-full">
              {analytics?.revenue_by_product && (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    layout="vertical"
                    data={analytics.revenue_by_product.slice(0, 5)}
                    margin={{ top: 0, right: 10, left: 20, bottom: 0 }}
                  >
                    <XAxis type="number" stroke="#94a3b8" fontSize={10} tickFormatter={(v) => `₹${v/1000}k`} />
                    <YAxis dataKey="product_name" type="category" stroke="#94a3b8" fontSize={10} width={80} />
                    <Tooltip
                      formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')}`, 'Revenue']}
                      contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                    />
                    <Bar dataKey="revenue" fill="#6366f1" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        {/* Live Operational Tables */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Subscriptions */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-900">Recent Subscriptions</h3>
              <span className="text-xs text-slate-500 font-medium">Auto-renewing</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider">
                    <th className="pb-3">Sub #</th>
                    <th className="pb-3">Customer</th>
                    <th className="pb-3">Plan</th>
                    <th className="pb-3">Total</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentSubs.map((sub) => (
                    <tr key={sub.id} className="hover:bg-slate-50/60">
                      <td className="py-3 font-semibold text-teal-600">{sub.subscription_number}</td>
                      <td className="py-3 text-slate-900 font-medium">
                        {sub.customer?.company_name || sub.customer?.user?.full_name || 'N/A'}
                      </td>
                      <td className="py-3 text-slate-600">{sub.plan?.name || 'Custom'}</td>
                      <td className="py-3 font-bold text-slate-900">₹{sub.total_amount}</td>
                      <td className="py-3">
                        <StatusBadge status={sub.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent Invoices */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-900">Recent Billing Invoices</h3>
              <span className="text-xs text-slate-500 font-medium">Real-time status</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider">
                    <th className="pb-3">Invoice #</th>
                    <th className="pb-3">Customer</th>
                    <th className="pb-3">Total</th>
                    <th className="pb-3">Due</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentInvs.map((inv) => (
                    <tr key={inv.id} className="hover:bg-slate-50/60">
                      <td className="py-3 font-semibold text-slate-900">{inv.invoice_number}</td>
                      <td className="py-3 text-slate-600">
                        {inv.customer?.company_name || inv.customer?.user?.full_name || 'N/A'}
                      </td>
                      <td className="py-3 font-bold text-slate-900">₹{inv.total}</td>
                      <td className="py-3 text-rose-600 font-semibold">₹{inv.amount_due}</td>
                      <td className="py-3">
                        <StatusBadge status={inv.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
