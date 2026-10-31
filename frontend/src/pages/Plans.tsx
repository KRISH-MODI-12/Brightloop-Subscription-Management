import React, { useState, useEffect } from 'react';
import { CalendarRange, Plus, Check, X, Shield, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import { SubscriptionPlan, Product } from '../types';
import { Navbar } from '../components/Navbar';
import { Modal } from '../components/Modal';
import { useAuth } from '../context/AuthContext';

export const Plans: React.FC = () => {
  const { role } = useAuth();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const [newPlan, setNewPlan] = useState({
    name: '',
    product_id: '',
    price: '',
    billing_frequency: 'monthly',
    min_quantity: '1',
    auto_close: false,
    allow_early_closure: true,
    allow_pause: true,
    allow_renewal: true,
    description: '',
  });

  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchPlans = async () => {
    setIsLoading(true);
    try {
      const [plansData, productsData] = await Promise.all([
        api.get<SubscriptionPlan[]>('/plans?limit=100'),
        api.get<Product[]>('/products'),
      ]);
      setPlans(plansData);
      setProducts(productsData);
    } catch (err) {
      console.error('Failed to load plans:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, []);

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      await api.post('/plans', {
        name: newPlan.name,
        product_id: Number(newPlan.product_id),
        price: Number(newPlan.price),
        billing_frequency: newPlan.billing_frequency,
        min_quantity: Number(newPlan.min_quantity),
        auto_close: newPlan.auto_close,
        allow_early_closure: newPlan.allow_early_closure,
        allow_pause: newPlan.allow_pause,
        allow_renewal: newPlan.allow_renewal,
        description: newPlan.description,
      });
      setShowCreateModal(false);
      fetchPlans();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create plan.');
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50 min-h-screen">
      <Navbar title="Subscription Plans & Frequencies" />

      <main className="p-8 space-y-6 flex-1 overflow-y-auto">
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500">
            Configure flexible recurring plans across daily, weekly, monthly, and yearly cycles.
          </p>

          {role === 'admin' && (
            <button
              onClick={() => { setShowCreateModal(true); setErrorMsg(null); }}
              className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Configure Plan
            </button>
          )}
        </div>

        {/* Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {plans.map((p) => (
            <div
              key={p.id}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between hover:shadow-md transition-shadow relative overflow-hidden"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2.5 py-0.5 rounded-full border border-teal-200">
                    {p.billing_frequency}
                  </span>
                  <span className="text-xs text-slate-400">Min: {p.min_quantity} qty</span>
                </div>

                <div>
                  <h3 className="font-bold text-slate-900 text-base">{p.name}</h3>
                  <p className="text-xs text-slate-500 font-medium">{p.product?.name}</p>
                </div>

                <div className="pt-2">
                  <span className="text-2xl font-extrabold text-slate-900">₹{p.price}</span>
                  <span className="text-xs text-slate-400"> / {p.billing_frequency}</span>
                </div>

                {/* Permissions matrix */}
                <div className="pt-3 border-t border-slate-100 space-y-1.5 text-[11px] text-slate-600">
                  <div className="flex items-center justify-between">
                    <span>Allow Early Closure:</span>
                    {p.allow_early_closure ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <X className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Allow Pause:</span>
                    {p.allow_pause ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <X className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Allow Renewal:</span>
                    {p.allow_renewal ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <X className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </div>
                </div>
              </div>

              <div className="pt-4 mt-3 border-t border-slate-100 text-center">
                <span className="text-[11px] font-semibold text-teal-600 uppercase tracking-wider">
                  Status: {p.status}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Create Plan Modal */}
        {showCreateModal && (
          <Modal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            title="Create Subscription Plan"
          >
            <form onSubmit={handleCreatePlan} className="space-y-4 text-xs">
              {errorMsg && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg">
                  {errorMsg}
                </div>
              )}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Plan Name *</label>
                <input
                  type="text"
                  required
                  value={newPlan.name}
                  onChange={(e) => setNewPlan({ ...newPlan, name: e.target.value })}
                  placeholder="e.g. Enterprise Cloud ERP Annual"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Related Product *</label>
                <select
                  required
                  value={newPlan.product_id}
                  onChange={(e) => setNewPlan({ ...newPlan, product_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                >
                  <option value="">Select a product...</option>
                  {products.map((prod) => (
                    <option key={prod.id} value={prod.id}>
                      {prod.name} (Base: ₹{prod.sales_price})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={newPlan.price}
                    onChange={(e) => setNewPlan({ ...newPlan, price: e.target.value })}
                    placeholder="5000.00"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Billing Frequency</label>
                  <select
                    value={newPlan.billing_frequency}
                    onChange={(e) => setNewPlan({ ...newPlan, billing_frequency: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Min Quantity</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={newPlan.min_quantity}
                    onChange={(e) => setNewPlan({ ...newPlan, min_quantity: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
              </div>

              {/* Policy Toggles */}
              <div className="space-y-2 pt-2 border-t border-slate-100">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={newPlan.allow_early_closure}
                    onChange={(e) => setNewPlan({ ...newPlan, allow_early_closure: e.target.checked })}
                    className="rounded text-teal-600"
                  />
                  <span>Allow Early Closure before expiry</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={newPlan.allow_pause}
                    onChange={(e) => setNewPlan({ ...newPlan, allow_pause: e.target.checked })}
                    className="rounded text-teal-600"
                  />
                  <span>Allow Pausing subscription</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={newPlan.allow_renewal}
                    onChange={(e) => setNewPlan({ ...newPlan, allow_renewal: e.target.checked })}
                    className="rounded text-teal-600"
                  />
                  <span>Allow Recurring Renewal</span>
                </label>
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
                  Save Plan
                </button>
              </div>
            </form>
          </Modal>
        )}
      </main>
    </div>
  );
};
