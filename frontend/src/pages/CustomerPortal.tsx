import React, { useState, useEffect } from 'react';
import {
  RefreshCw, Receipt, CreditCard, Download, AlertCircle, CheckCircle2,
  Calendar, RotateCcw, Pause, Play, IndianRupee
} from 'lucide-react';
import { api } from '../api/client';
import { Subscription, Invoice, Payment } from '../types';
import { Navbar } from '../components/Navbar';
import { StatusBadge } from '../components/StatusBadge';
import { StatsCard } from '../components/StatsCard';
import { useAuth } from '../context/AuthContext';
import { formatDateSafe } from '../utils/date';

export const CustomerPortal: React.FC = () => {
  const { user } = useAuth();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCustomerData = async () => {
    setIsLoading(true);
    try {
      const [subsData, invsData, paysData] = await Promise.all([
        api.get<Subscription[]>('/subscriptions'),
        api.get<Invoice[]>('/invoices'),
        api.get<Payment[]>('/payments'),
      ]);
      setSubscriptions(subsData);
      setInvoices(invsData);
      setPayments(paysData);
    } catch (err) {
      console.error('Failed to load customer portal data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomerData();
  }, []);

  const totalOutstanding = invoices
    .filter((inv) => ['confirmed', 'partially_paid', 'overdue'].includes(inv.status))
    .reduce((sum, inv) => sum + Number(inv.amount_due), 0);

  const activeSubscriptionsCount = subscriptions.filter((s) => s.status === 'active').length;

  const handleRenewSub = async (subId: number) => {
    if (!confirm('Would you like to renew this subscription for another billing cycle?')) return;
    try {
      await api.post(`/subscriptions/${subId}/renew`, { reason: 'Customer self-renewal' });
      alert('Subscription renewed successfully!');
      fetchCustomerData();
    } catch (err: any) {
      alert(`Could not renew: ${err.message}`);
    }
  };

  const handleDownloadPdf = async (inv: Invoice) => {
    try {
      await api.download(`/invoices/${inv.id}/pdf`, `Invoice-${inv.invoice_number}.pdf`);
    } catch (err: any) {
      alert(`Download failed: ${err.message}`);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50 min-h-screen">
      <Navbar title="Customer Self-Service Hub" />

      <main className="p-8 space-y-8 flex-1 overflow-y-auto">
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-3xl p-6 sm:p-8 text-white shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-6 border border-slate-700/60">
          <div>
            <span className="text-teal-400 text-xs font-bold uppercase tracking-wider block mb-1">
              Customer Portal
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Hello, {user?.full_name || 'Subscriber'}!
            </h2>
            <p className="text-slate-300 text-xs sm:text-sm mt-1 max-w-xl">
              Manage your active software licenses, download tax invoices, track renewal timelines, and inspect payment receipts.
            </p>
          </div>
          <div className="flex items-center space-x-4 bg-slate-800/80 p-4 rounded-2xl border border-slate-700">
            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Outstanding Due</span>
              <span className="text-xl font-bold text-rose-400">₹{totalOutstanding.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Customer Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <StatsCard
            title="Active Subscriptions"
            value={activeSubscriptionsCount}
            subtitle="Current live services"
            icon={RefreshCw}
            color="brand"
          />
          <StatsCard
            title="Unpaid Balance"
            value={`₹${totalOutstanding.toFixed(2)}`}
            subtitle="Pending payments"
            icon={IndianRupee}
            color="rose"
          />
          <StatsCard
            title="Completed Invoices"
            value={invoices.filter((i) => i.status === 'paid').length}
            subtitle={`${invoices.length} total billed`}
            icon={Receipt}
            color="emerald"
          />
        </div>

        {/* Active Subscriptions Section */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900">My Subscriptions</h3>
            <span className="text-xs text-slate-400">{subscriptions.length} registered</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {subscriptions.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 col-span-2 text-center">
                No subscriptions registered under your account.
              </p>
            ) : (
              subscriptions.map((sub) => (
                <div
                  key={sub.id}
                  className="p-5 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3 hover:border-teal-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-teal-600 font-bold text-sm block">
                        {sub.subscription_number}
                      </span>
                      <h4 className="font-bold text-slate-900 text-sm mt-0.5">
                        {sub.plan?.name || 'Software Subscription'}
                      </h4>
                      <p className="text-xs text-slate-500">{sub.plan?.product?.name}</p>
                    </div>
                    <StatusBadge status={sub.status} />
                  </div>

                  <div className="pt-2 border-t border-slate-200/80 flex items-center justify-between text-xs">
                    <div>
                      <span className="text-slate-400 block text-[10px]">RECURRING CHARGE</span>
                      <span className="font-extrabold text-slate-900 text-base">
                        ₹{sub.total_amount} <span className="text-xs font-normal text-slate-400">/{sub.plan?.billing_frequency}</span>
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-slate-400 block text-[10px]">EXPIRY / RENEWAL</span>
                      <span className="font-semibold text-slate-700">{sub.expiry_date}</span>
                    </div>
                  </div>

                  {/* Customer Self-Actions */}
                  {sub.status === 'active' && sub.plan?.allow_renewal && (
                    <div className="pt-2 flex justify-end">
                      <button
                        onClick={() => handleRenewSub(sub.id)}
                        className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold flex items-center"
                      >
                        <RotateCcw className="w-3.5 h-3.5 mr-1" />
                        Renew Cycle
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Customer Invoices & Download */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900">Invoices & Receipts</h3>
            <span className="text-xs text-slate-400">Instant PDF download available</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Invoice #</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Due Date</th>
                  <th className="py-3 px-4">Total</th>
                  <th className="py-3 px-4">Due Balance</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Download</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {invoices.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-6 text-center text-slate-400">
                      No invoices available.
                    </td>
                  </tr>
                ) : (
                  invoices.map((inv) => (
                    <tr key={inv.id} className="hover:bg-slate-50/70">
                      <td className="py-3 px-4 font-bold text-slate-900">
                        {inv.invoice_number}
                        {inv.billing_period_start && inv.billing_period_end && (
                          <div className="text-[10px] text-slate-400 font-normal">
                            Period: {formatDateSafe(inv.billing_period_start)} to {formatDateSafe(inv.billing_period_end)}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-600 font-medium">{formatDateSafe(inv.invoice_date)}</td>
                      <td className="py-3 px-4 text-slate-600">{formatDateSafe(inv.due_date)}</td>
                      <td className="py-3 px-4 font-bold text-slate-900">₹{inv.total}</td>
                      <td className="py-3 px-4 font-semibold text-rose-600">₹{inv.amount_due}</td>
                      <td className="py-3 px-4">
                        <StatusBadge status={inv.status} />
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleDownloadPdf(inv)}
                          className="px-2.5 py-1 bg-teal-50 hover:bg-teal-100 text-teal-700 rounded-lg font-semibold inline-flex items-center"
                        >
                          <Download className="w-3.5 h-3.5 mr-1" /> PDF
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Customer Payment History */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900">Recorded Payment History</h3>
            <span className="text-xs text-slate-400">Settled receipts</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Receipt #</th>
                  <th className="py-3 px-4">Invoice #</th>
                  <th className="py-3 px-4">Amount Paid</th>
                  <th className="py-3 px-4">Method</th>
                  <th className="py-3 px-4">Transaction Ref</th>
                  <th className="py-3 px-4">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {payments.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-slate-400">
                      No payments recorded yet.
                    </td>
                  </tr>
                ) : (
                  payments.map((p) => (
                    <tr key={p.id}>
                      <td className="py-3 px-4 font-bold text-slate-900">{p.payment_number}</td>
                      <td className="py-3 px-4 text-teal-600 font-semibold">Invoice #{p.invoice_id}</td>
                      <td className="py-3 px-4 font-bold text-emerald-600">₹{p.amount}</td>
                      <td className="py-3 px-4 uppercase text-[11px] font-semibold text-slate-600">
                        {p.payment_method.replace('_', ' ')}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-500">{p.transaction_reference || 'N/A'}</td>
                      <td className="py-3 px-4 text-slate-600">{p.payment_date}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
};
