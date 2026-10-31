import React, { useState, useEffect } from 'react';
import {
  RefreshCw, Plus, Search, Filter, Play, Pause, XCircle, RotateCcw,
  Receipt, FileText, CheckCircle2, ChevronRight, History
} from 'lucide-react';
import { api } from '../api/client';
import { Subscription, SubscriptionPlan, Customer, Product } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Navbar } from '../components/Navbar';
import { Modal } from '../components/Modal';
import { useAuth } from '../context/AuthContext';

import { getLocalDateString } from '../utils/date';

export const Subscriptions: React.FC = () => {
  const { role } = useAuth();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedSub, setSelectedSub] = useState<Subscription | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showActionModal, setShowActionModal] = useState(false);
  const [actionType, setActionType] = useState<'pause' | 'resume' | 'close' | 'renew' | 'confirm' | 'activate' | null>(null);
  const [actionReason, setActionReason] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  // Form for new subscription
  const [newSub, setNewSub] = useState({
    customer_id: '',
    plan_id: '',
    start_date: getLocalDateString(),
    payment_terms: 'net_30',
    notes: '',
  });

  const fetchSubscriptions = async () => {
    setIsLoading(true);
    try {
      let path = '/subscriptions?limit=100';
      if (statusFilter) path += `&status=${statusFilter}`;
      if (search) path += `&search=${encodeURIComponent(search)}`;
      const data = await api.get<Subscription[]>(path);
      setSubscriptions(data);

      if (role !== 'customer') {
        const [plansData, custsData] = await Promise.all([
          api.get<SubscriptionPlan[]>('/plans'),
          api.get<Customer[]>('/customers'),
        ]);
        setPlans(plansData);
        setCustomers(custsData);
      }
    } catch (err) {
      console.error('Failed to load subscriptions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscriptions();
  }, [statusFilter, search]);

  const handleAction = async () => {
    if (!selectedSub || !actionType) return;
    setActionError(null);
    try {
      await api.post(`/subscriptions/${selectedSub.id}/${actionType}`, { reason: actionReason });
      setShowActionModal(false);
      setActionReason('');
      fetchSubscriptions();
      // refresh selected subscription details
      const updated = await api.get<Subscription>(`/subscriptions/${selectedSub.id}`);
      setSelectedSub(updated);
    } catch (err: any) {
      setActionError(err.message || `Failed to ${actionType} subscription.`);
    }
  };

  const handleCreateSub = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);
    try {
      await api.post('/subscriptions', {
        customer_id: Number(newSub.customer_id),
        plan_id: Number(newSub.plan_id),
        start_date: newSub.start_date,
        payment_terms: newSub.payment_terms,
        notes: newSub.notes,
      });
      setShowCreateModal(false);
      fetchSubscriptions();
    } catch (err: any) {
      setActionError(err.message || 'Failed to create subscription.');
    }
  };

  const handleGenerateInvoice = async (subId: number) => {
    try {
      await api.post(`/invoices/from-subscription/${subId}`);
      alert('Invoice successfully generated from active subscription!');
      fetchSubscriptions();
    } catch (err: any) {
      alert(`Invoice generation notice: ${err.message}`);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50 min-h-screen">
      <Navbar title="Subscriptions Lifecycle Management" />

      <main className="p-8 space-y-6 flex-1 overflow-y-auto">
        {/* Actions bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3 flex-1 max-w-md">
            <div className="relative w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search subscriptions by number or notes..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-teal-500 focus:outline-none"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-teal-500 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="confirmed">Confirmed</option>
              <option value="paused">Paused</option>
              <option value="closed">Closed</option>
              <option value="cancelled">Cancelled</option>
              <option value="draft">Draft</option>
            </select>
          </div>

          {role !== 'customer' && (
            <button
              onClick={() => { setShowCreateModal(true); setActionError(null); }}
              className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              New Subscription
            </button>
          )}
        </div>

        {/* Subscriptions Table */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Sub Number</th>
                <th className="py-3.5 px-4">Customer</th>
                <th className="py-3.5 px-4">Plan & Product</th>
                <th className="py-3.5 px-4">Billing Frequency</th>
                <th className="py-3.5 px-4">Start / Expiry</th>
                <th className="py-3.5 px-4">Total Amount</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {subscriptions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    No subscriptions found.
                  </td>
                </tr>
              ) : (
                subscriptions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 px-4 font-bold text-teal-600">
                      {sub.subscription_number}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-900">
                      {sub.customer?.company_name || sub.customer?.user?.full_name || `Cust #${sub.customer_id}`}
                    </td>
                    <td className="py-3.5 px-4 text-slate-700">
                      <div className="font-medium text-slate-900">{sub.plan?.name}</div>
                      <div className="text-[11px] text-slate-400">{sub.plan?.product?.name}</div>
                    </td>
                    <td className="py-3.5 px-4 uppercase text-[11px] font-semibold text-slate-600">
                      {sub.plan?.billing_frequency}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      <div>{sub.start_date}</div>
                      <div className="text-[11px] text-slate-400">Exp: {sub.expiry_date}</div>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-slate-900">
                      ₹{sub.total_amount}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={sub.status} />
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-1">
                      <button
                        onClick={() => setSelectedSub(sub)}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium"
                      >
                        Inspect
                      </button>
                      {role !== 'customer' && sub.status === 'active' && (
                        <button
                          onClick={() => handleGenerateInvoice(sub.id)}
                          title="Generate Invoice Now"
                          className="px-2.5 py-1 bg-teal-50 hover:bg-teal-100 text-teal-700 rounded-lg text-xs font-semibold"
                        >
                          <Receipt className="w-3.5 h-3.5 inline mr-1" />
                          Bill
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Selected Subscription Detail Drawer / Modal */}
        {selectedSub && (
          <Modal
            isOpen={!!selectedSub}
            onClose={() => setSelectedSub(null)}
            title={`Subscription ${selectedSub.subscription_number}`}
            maxWidth="2xl"
          >
            <div className="space-y-6 text-xs">
              {/* Header Overview */}
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100">
                <div>
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Customer</span>
                  <span className="text-sm font-bold text-slate-900">
                    {selectedSub.customer?.company_name || selectedSub.customer?.user?.full_name}
                  </span>
                  <p className="text-slate-500">{selectedSub.customer?.user?.email}</p>
                </div>
                <div className="text-right">
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Status</span>
                  <StatusBadge status={selectedSub.status} />
                  <span className="text-xs font-bold text-slate-900 block mt-1">₹{selectedSub.total_amount}</span>
                </div>
              </div>

              {/* Lifecycle Actions */}
              <div className="p-4 bg-slate-50/60 rounded-xl border border-slate-200">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-600 block mb-2">
                  Subscription Lifecycle Actions:
                </span>
                <div className="flex flex-wrap gap-2">
                  {selectedSub.status === 'confirmed' && role !== 'customer' && (
                    <button
                      onClick={() => { setActionType('activate'); setShowActionModal(true); }}
                      className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg font-semibold flex items-center"
                    >
                      <Play className="w-3.5 h-3.5 mr-1" /> Activate
                    </button>
                  )}
                  {selectedSub.status === 'active' && (
                    <button
                      onClick={() => { setActionType('pause'); setShowActionModal(true); }}
                      className="px-3 py-1.5 bg-amber-600 text-white rounded-lg font-semibold flex items-center"
                    >
                      <Pause className="w-3.5 h-3.5 mr-1" /> Pause
                    </button>
                  )}
                  {selectedSub.status === 'paused' && (
                    <button
                      onClick={() => { setActionType('resume'); setShowActionModal(true); }}
                      className="px-3 py-1.5 bg-teal-600 text-white rounded-lg font-semibold flex items-center"
                    >
                      <Play className="w-3.5 h-3.5 mr-1" /> Resume
                    </button>
                  )}
                  {['active', 'paused'].includes(selectedSub.status) && (
                    <button
                      onClick={() => { setActionType('close'); setShowActionModal(true); }}
                      className="px-3 py-1.5 bg-slate-700 text-white rounded-lg font-semibold flex items-center"
                    >
                      <XCircle className="w-3.5 h-3.5 mr-1" /> Close Early
                    </button>
                  )}
                  {['active', 'closed'].includes(selectedSub.status) && (
                    <button
                      onClick={() => { setActionType('renew'); setShowActionModal(true); }}
                      className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg font-semibold flex items-center"
                    >
                      <RotateCcw className="w-3.5 h-3.5 mr-1" /> Renew Subscription
                    </button>
                  )}
                </div>
              </div>

              {/* Line items */}
              <div>
                <h4 className="font-bold text-slate-900 mb-2">Subscription Product Lines</h4>
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left">
                    <thead className="bg-slate-50 text-slate-500">
                      <tr>
                        <th className="py-2 px-3">Product</th>
                        <th className="py-2 px-3">Qty</th>
                        <th className="py-2 px-3">Unit Price</th>
                        <th className="py-2 px-3">Tax</th>
                        <th className="py-2 px-3">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedSub.lines.map((l) => (
                        <tr key={l.id}>
                          <td className="py-2 px-3 font-medium text-slate-900">
                            {l.product?.name} {l.variant ? `(${l.variant.variant_name})` : ''}
                          </td>
                          <td className="py-2 px-3">{l.quantity}</td>
                          <td className="py-2 px-3">₹{l.unit_price}</td>
                          <td className="py-2 px-3">₹{l.tax_amount}</td>
                          <td className="py-2 px-3 font-bold text-slate-900">₹{l.line_total}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Status History Trail */}
              <div>
                <h4 className="font-bold text-slate-900 mb-2 flex items-center">
                  <History className="w-4 h-4 mr-1 text-slate-400" />
                  Audit Trail & State History
                </h4>
                <div className="space-y-2 border-l-2 border-teal-500 pl-3">
                  {selectedSub.status_history?.map((h) => (
                    <div key={h.id} className="text-[11px]">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold uppercase text-teal-700">{h.to_status}</span>
                        <span className="text-slate-400">by User #{h.changed_by}</span>
                        <span className="text-slate-400">({new Date(h.changed_at).toLocaleString()})</span>
                      </div>
                      {h.reason && <p className="text-slate-600 italic">"{h.reason}"</p>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Modal>
        )}

        {/* Modal for Lifecycle Action (Confirm reason) */}
        {showActionModal && (
          <Modal
            isOpen={showActionModal}
            onClose={() => setShowActionModal(false)}
            title={`Confirm: ${actionType?.toUpperCase()} Subscription`}
          >
            <div className="space-y-4 text-xs">
              {actionError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg">
                  {actionError}
                </div>
              )}
              <p className="text-slate-600">
                Are you sure you want to transition {selectedSub?.subscription_number} to {actionType}?
              </p>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Reason / Notes</label>
                <input
                  type="text"
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  placeholder="e.g. Customer request or payment cycle"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-teal-500"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  onClick={() => setShowActionModal(false)}
                  className="px-3 py-1.5 border border-slate-300 text-slate-700 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAction}
                  className="px-3 py-1.5 bg-teal-600 text-white font-semibold rounded-lg hover:bg-teal-700"
                >
                  Confirm Action
                </button>
              </div>
            </div>
          </Modal>
        )}

        {/* Create Subscription Modal */}
        {showCreateModal && (
          <Modal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            title="Create New Subscription"
          >
            <form onSubmit={handleCreateSub} className="space-y-4 text-xs">
              {actionError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg">
                  {actionError}
                </div>
              )}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Select Customer *</label>
                <select
                  required
                  value={newSub.customer_id}
                  onChange={(e) => setNewSub({ ...newSub, customer_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                >
                  <option value="">Choose a customer...</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.company_name ? `${c.company_name} (${c.user?.full_name})` : c.user?.full_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Subscription Plan *</label>
                <select
                  required
                  value={newSub.plan_id}
                  onChange={(e) => setNewSub({ ...newSub, plan_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                >
                  <option value="">Choose a plan...</option>
                  {plans.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} — ₹{p.price}/{p.billing_frequency}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Start Date</label>
                  <input
                    type="date"
                    required
                    value={newSub.start_date}
                    onChange={(e) => setNewSub({ ...newSub, start_date: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Payment Terms</label>
                  <select
                    value={newSub.payment_terms}
                    onChange={(e) => setNewSub({ ...newSub, payment_terms: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  >
                    <option value="immediate">Immediate</option>
                    <option value="net_15">Net 15 Days</option>
                    <option value="net_30">Net 30 Days</option>
                    <option value="net_45">Net 45 Days</option>
                    <option value="net_60">Net 60 Days</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Notes</label>
                <textarea
                  value={newSub.notes}
                  onChange={(e) => setNewSub({ ...newSub, notes: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  placeholder="Terms, PO number, or custom notes"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 border border-slate-300 text-slate-700 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg"
                >
                  Create Subscription
                </button>
              </div>
            </form>
          </Modal>
        )}
      </main>
    </div>
  );
};
