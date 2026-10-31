import React, { useState, useEffect } from 'react';
import { Percent, Plus, Tag, Calendar, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import { Discount } from '../types';
import { Navbar } from '../components/Navbar';
import { Modal } from '../components/Modal';
import { useAuth } from '../context/AuthContext';

export const Discounts: React.FC = () => {
  const { role } = useAuth();
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const [newDisc, setNewDisc] = useState({
    name: '',
    discount_type: 'percentage',
    value: '',
    min_purchase_amount: '',
    min_quantity: '',
    start_date: '',
    end_date: '',
    max_usage_limit: '',
    description: '',
  });

  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchDiscounts = async () => {
    setIsLoading(true);
    try {
      const data = await api.get<Discount[]>('/discounts');
      setDiscounts(data);
    } catch (err) {
      console.error('Failed to load discounts:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDiscounts();
  }, []);

  const handleCreateDiscount = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      await api.post('/discounts', {
        name: newDisc.name,
        discount_type: newDisc.discount_type,
        value: Number(newDisc.value),
        min_purchase_amount: newDisc.min_purchase_amount ? Number(newDisc.min_purchase_amount) : null,
        min_quantity: newDisc.min_quantity ? Number(newDisc.min_quantity) : null,
        start_date: newDisc.start_date || null,
        end_date: newDisc.end_date || null,
        max_usage_limit: newDisc.max_usage_limit ? Number(newDisc.max_usage_limit) : null,
        description: newDisc.description,
      });
      setShowCreateModal(false);
      fetchDiscounts();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create discount.');
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50 min-h-screen">
      <Navbar title="Discount & Promotion Rules" />

      <main className="p-8 space-y-6 flex-1 overflow-y-auto">
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500">
            Define promotional discount rules with spend thresholds, quantity constraints, and redemption caps.
          </p>

          {role === 'admin' && (
            <button
              onClick={() => { setShowCreateModal(true); setErrorMsg(null); }}
              className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Create Discount Rule
            </button>
          )}
        </div>

        {/* Discounts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {discounts.map((d) => (
            <div
              key={d.id}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-3 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-200">
                    {d.discount_type}
                  </span>
                  <h3 className="font-bold text-slate-900 text-base mt-1">{d.name}</h3>
                </div>
                <div className="text-right">
                  <span className="text-xl font-black text-slate-900">
                    {d.discount_type === 'percentage' ? `${d.value}%` : `₹${d.value}`}
                  </span>
                  <span className="text-[10px] text-slate-400 block">DEDUCTION</span>
                </div>
              </div>

              <p className="text-xs text-slate-600">{d.description || 'Promotional rule'}</p>

              <div className="pt-3 border-t border-slate-100 space-y-1.5 text-xs text-slate-600">
                <div className="flex justify-between">
                  <span>Usage Count:</span>
                  <span className="font-semibold text-slate-900">
                    {d.usage_count} {d.max_usage_limit ? `/ ${d.max_usage_limit} limit` : '(unlimited)'}
                  </span>
                </div>
                {d.min_purchase_amount && (
                  <div className="flex justify-between">
                    <span>Min Spend Required:</span>
                    <span className="font-semibold text-slate-900">₹{d.min_purchase_amount}</span>
                  </div>
                )}
                {d.end_date && (
                  <div className="flex justify-between text-slate-400">
                    <span>Valid Until:</span>
                    <span>{d.end_date}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Create Discount Modal */}
        {showCreateModal && (
          <Modal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            title="Create Discount Rule"
          >
            <form onSubmit={handleCreateDiscount} className="space-y-4 text-xs">
              {errorMsg && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg">
                  {errorMsg}
                </div>
              )}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Discount Name *</label>
                <input
                  type="text"
                  required
                  value={newDisc.name}
                  onChange={(e) => setNewDisc({ ...newDisc, name: e.target.value })}
                  placeholder="e.g. Festival Booster 15%"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Type</label>
                  <select
                    value={newDisc.discount_type}
                    onChange={(e) => setNewDisc({ ...newDisc, discount_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  >
                    <option value="percentage">Percentage (%)</option>
                    <option value="fixed">Fixed Amount (₹)</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Value *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={newDisc.value}
                    onChange={(e) => setNewDisc({ ...newDisc, value: e.target.value })}
                    placeholder={newDisc.discount_type === 'percentage' ? '15.00' : '1000.00'}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Min Spend (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newDisc.min_purchase_amount}
                    onChange={(e) => setNewDisc({ ...newDisc, min_purchase_amount: e.target.value })}
                    placeholder="e.g. 5000"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Max Usages</label>
                  <input
                    type="number"
                    value={newDisc.max_usage_limit}
                    onChange={(e) => setNewDisc({ ...newDisc, max_usage_limit: e.target.value })}
                    placeholder="e.g. 100"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Start Date</label>
                  <input
                    type="date"
                    value={newDisc.start_date}
                    onChange={(e) => setNewDisc({ ...newDisc, start_date: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">End Date</label>
                  <input
                    type="date"
                    value={newDisc.end_date}
                    onChange={(e) => setNewDisc({ ...newDisc, end_date: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
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
                  Save Discount Rule
                </button>
              </div>
            </form>
          </Modal>
        )}
      </main>
    </div>
  );
};
