import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, Plus, CheckCircle2, Search, ArrowRight, Eye } from 'lucide-react';
import { api } from '../api/client';
import { Quotation, Customer, SubscriptionPlan, Product, Tax } from '../types';
import { Navbar } from '../components/Navbar';
import { Modal } from '../components/Modal';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { getLocalDateString } from '../utils/date';

export const Quotations: React.FC = () => {
  const { role } = useAuth();
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [taxes, setTaxes] = useState<Tax[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedQuo, setSelectedQuo] = useState<Quotation | null>(null);

  // Quotation form
  const [newQuo, setNewQuo] = useState({
    customer_id: '',
    plan_id: '',
    valid_until: getLocalDateString(new Date(Date.now() + 15 * 86400000)),
    notes: '',
    lines: [
      { product_id: '', quantity: 1, unit_price: '', tax_id: '', description: '' },
    ],
  });

  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchQuotations = async () => {
    setIsLoading(true);
    try {
      const data = await api.get<Quotation[]>('/quotations?limit=100');
      setQuotations(data);

      if (role !== 'customer') {
        const [custData, planData, prodData, taxData] = await Promise.all([
          api.get<Customer[]>('/customers'),
          api.get<SubscriptionPlan[]>('/plans'),
          api.get<Product[]>('/products'),
          api.get<Tax[]>('/taxes'),
        ]);
        setCustomers(custData);
        setPlans(planData);
        setProducts(prodData);
        setTaxes(taxData);
      }
    } catch (err) {
      console.error('Failed to load quotations:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQuotations();
  }, []);

  const handleConfirmToSub = async (quoId: number) => {
    try {
      await api.post(`/quotations/${quoId}/confirm`);
      alert('Quotation successfully converted to active subscription!');
      fetchQuotations();
      setSelectedQuo(null);
    } catch (err: any) {
      alert(`Could not confirm quotation: ${err.message}`);
    }
  };

  const handleAddLine = () => {
    setNewQuo({
      ...newQuo,
      lines: [...newQuo.lines, { product_id: '', quantity: 1, unit_price: '', tax_id: '', description: '' }],
    });
  };

  const handleLineChange = (index: number, field: string, val: any) => {
    const updated = [...newQuo.lines];
    (updated[index] as any)[field] = val;

    // auto populate price if product selected
    if (field === 'product_id') {
      const prod = products.find((p) => p.id === Number(val));
      if (prod) {
        updated[index].unit_price = String(prod.sales_price);
      }
    }

    setNewQuo({ ...newQuo, lines: updated });
  };

  const handleCreateQuo = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      const formattedLines = newQuo.lines.map((l) => {
        const sub = Number(l.unit_price) * Number(l.quantity);
        let taxAmt = 0;
        if (l.tax_id) {
          const t = taxes.find((tax) => tax.id === Number(l.tax_id));
          if (t) taxAmt = sub * (t.rate / 100);
        }
        return {
          product_id: Number(l.product_id),
          quantity: Number(l.quantity),
          unit_price: Number(l.unit_price),
          tax_id: l.tax_id ? Number(l.tax_id) : null,
          tax_amount: taxAmt,
          discount_amount: 0,
          line_total: sub + taxAmt,
          description: l.description,
        };
      });

      await api.post('/quotations', {
        customer_id: Number(newQuo.customer_id),
        plan_id: newQuo.plan_id ? Number(newQuo.plan_id) : null,
        valid_until: newQuo.valid_until,
        notes: newQuo.notes,
        lines: formattedLines,
      });

      setShowCreateModal(false);
      fetchQuotations();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create quotation.');
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50 min-h-screen">
      <Navbar title="Sales Quotations & Proposals" />

      <main className="p-8 space-y-6 flex-1 overflow-y-auto">
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500">
            Generate customized software proposals with taxes and validity constraints.
          </p>

          {role !== 'customer' && (
            <button
              onClick={() => { setShowCreateModal(true); setErrorMsg(null); }}
              className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              New Quotation
            </button>
          )}
        </div>

        {/* Quotations Table */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Quotation #</th>
                <th className="py-3.5 px-4">Customer</th>
                <th className="py-3.5 px-4">Valid Until</th>
                <th className="py-3.5 px-4">Subtotal</th>
                <th className="py-3.5 px-4">Tax</th>
                <th className="py-3.5 px-4">Total</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {quotations.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    No quotations generated yet.
                  </td>
                </tr>
              ) : (
                quotations.map((q) => (
                  <tr key={q.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 px-4 font-bold text-slate-900">{q.quotation_number}</td>
                    <td className="py-3.5 px-4 font-medium text-slate-700">
                      {q.customer?.company_name || q.customer?.user?.full_name || `Cust #${q.customer_id}`}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">{q.valid_until}</td>
                    <td className="py-3.5 px-4 text-slate-600">₹{q.subtotal}</td>
                    <td className="py-3.5 px-4 text-slate-600">₹{q.tax_amount}</td>
                    <td className="py-3.5 px-4 font-bold text-slate-900">₹{q.total}</td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={q.status} />
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-1">
                      <button
                        onClick={() => setSelectedQuo(q)}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium"
                      >
                        <Eye className="w-3.5 h-3.5 inline mr-1" /> View
                      </button>
                      {role !== 'customer' && q.status === 'draft' && (
                        <button
                          onClick={() => handleConfirmToSub(q.id)}
                          className="px-2.5 py-1 bg-teal-50 hover:bg-teal-100 text-teal-700 rounded-lg text-xs font-semibold"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 inline mr-1" /> Convert to Sub
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Create Quotation Modal */}
        {showCreateModal && (
          <Modal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            title="Generate New Quotation"
            maxWidth="2xl"
          >
            <form onSubmit={handleCreateQuo} className="space-y-4 text-xs">
              {errorMsg && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg">
                  {errorMsg}
                </div>
              )}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Customer *</label>
                  <select
                    required
                    value={newQuo.customer_id}
                    onChange={(e) => setNewQuo({ ...newQuo, customer_id: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  >
                    <option value="">Select customer...</option>
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.company_name || c.user?.full_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Target Plan (for conversion)</label>
                  <select
                    value={newQuo.plan_id}
                    onChange={(e) => setNewQuo({ ...newQuo, plan_id: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  >
                    <option value="">Select target plan...</option>
                    {plans.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Valid Until Date *</label>
                  <input
                    type="date"
                    required
                    value={newQuo.valid_until}
                    onChange={(e) => setNewQuo({ ...newQuo, valid_until: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>

              {/* Line Items */}
              <div className="pt-2">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-slate-900">Line Items</span>
                  <button
                    type="button"
                    onClick={handleAddLine}
                    className="text-teal-600 font-semibold hover:underline"
                  >
                    + Add Product Line
                  </button>
                </div>

                <div className="space-y-2">
                  {newQuo.lines.map((line, idx) => (
                    <div key={idx} className="grid grid-cols-4 gap-2 p-2 bg-slate-50 rounded-lg border border-slate-200">
                      <div>
                        <select
                          required
                          value={line.product_id}
                          onChange={(e) => handleLineChange(idx, 'product_id', e.target.value)}
                          className="w-full px-2 py-1.5 border border-slate-300 rounded text-xs"
                        >
                          <option value="">Choose Product...</option>
                          {products.map((prod) => (
                            <option key={prod.id} value={prod.id}>
                              {prod.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <input
                          type="number"
                          min="1"
                          required
                          placeholder="Qty"
                          value={line.quantity}
                          onChange={(e) => handleLineChange(idx, 'quantity', e.target.value)}
                          className="w-full px-2 py-1.5 border border-slate-300 rounded text-xs"
                        />
                      </div>
                      <div>
                        <input
                          type="number"
                          step="0.01"
                          required
                          placeholder="Unit Price"
                          value={line.unit_price}
                          onChange={(e) => handleLineChange(idx, 'unit_price', e.target.value)}
                          className="w-full px-2 py-1.5 border border-slate-300 rounded text-xs"
                        />
                      </div>
                      <div>
                        <select
                          value={line.tax_id}
                          onChange={(e) => handleLineChange(idx, 'tax_id', e.target.value)}
                          className="w-full px-2 py-1.5 border border-slate-300 rounded text-xs"
                        >
                          <option value="">Tax (Optional)</option>
                          {taxes.map((t) => (
                            <option key={t.id} value={t.id}>
                              {t.name} ({t.rate}%)
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Notes / Terms</label>
                <textarea
                  rows={2}
                  value={newQuo.notes}
                  onChange={(e) => setNewQuo({ ...newQuo, notes: e.target.value })}
                  placeholder="Validity terms, delivery timelines, payment milestones"
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
                  Generate Quotation
                </button>
              </div>
            </form>
          </Modal>
        )}
      </main>
    </div>
  );
};
