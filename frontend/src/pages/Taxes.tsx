import React, { useState, useEffect } from 'react';
import { Landmark, Plus, CheckCircle2, X } from 'lucide-react';
import { api } from '../api/client';
import { Tax } from '../types';
import { Navbar } from '../components/Navbar';
import { Modal } from '../components/Modal';
import { useAuth } from '../context/AuthContext';

export const Taxes: React.FC = () => {
  const { role } = useAuth();
  const [taxes, setTaxes] = useState<Tax[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const [newTax, setNewTax] = useState({
    name: '',
    rate: '',
    tax_type: 'percentage',
    description: '',
  });
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchTaxes = async () => {
    setIsLoading(true);
    try {
      const data = await api.get<Tax[]>('/taxes');
      setTaxes(data);
    } catch (err) {
      console.error('Failed to load taxes:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTaxes();
  }, []);

  const handleCreateTax = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      await api.post('/taxes', {
        name: newTax.name,
        rate: Number(newTax.rate),
        tax_type: newTax.tax_type,
        description: newTax.description,
      });
      setShowCreateModal(false);
      fetchTaxes();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create tax rule.');
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50 min-h-screen">
      <Navbar title="Tax Configuration & Rates" />

      <main className="p-8 space-y-6 flex-1 overflow-y-auto">
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500">
            Define applicable statutory taxes calculated automatically during recurring invoice generation.
          </p>

          {role === 'admin' && (
            <button
              onClick={() => { setShowCreateModal(true); setErrorMsg(null); }}
              className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Add Tax Rule
            </button>
          )}
        </div>

        {/* Taxes Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {taxes.map((t) => (
            <div
              key={t.id}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-3 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-200">
                    {t.tax_type}
                  </span>
                  <h3 className="font-bold text-slate-900 text-base mt-1.5">{t.name}</h3>
                </div>
                <span className="text-2xl font-black text-slate-900">{t.rate}%</span>
              </div>

              <p className="text-xs text-slate-600">{t.description || 'Statutory rate'}</p>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-400">Status:</span>
                <span className="font-semibold text-emerald-600 flex items-center">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Active
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Create Tax Modal */}
        {showCreateModal && (
          <Modal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            title="Configure Tax Rule"
          >
            <form onSubmit={handleCreateTax} className="space-y-4 text-xs">
              {errorMsg && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg">
                  {errorMsg}
                </div>
              )}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Tax Name *</label>
                <input
                  type="text"
                  required
                  value={newTax.name}
                  onChange={(e) => setNewTax({ ...newTax, name: e.target.value })}
                  placeholder="e.g. GST 18%"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Rate (%) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={newTax.rate}
                    onChange={(e) => setNewTax({ ...newTax, rate: e.target.value })}
                    placeholder="18.00"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Tax Type</label>
                  <select
                    value={newTax.tax_type}
                    onChange={(e) => setNewTax({ ...newTax, tax_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  >
                    <option value="percentage">Percentage (%)</option>
                    <option value="fixed">Fixed</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description</label>
                <input
                  type="text"
                  value={newTax.description}
                  onChange={(e) => setNewTax({ ...newTax, description: e.target.value })}
                  placeholder="e.g. Applicable on all Indian B2B software services"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
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
                  Save Tax Rule
                </button>
              </div>
            </form>
          </Modal>
        )}
      </main>
    </div>
  );
};
