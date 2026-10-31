import React, { useState, useEffect } from 'react';
import { CreditCard, RotateCcw, AlertTriangle, Search, CheckCircle2 } from 'lucide-react';
import { api } from '../api/client';
import { Payment } from '../types';
import { Navbar } from '../components/Navbar';
import { Modal } from '../components/Modal';
import { useAuth } from '../context/AuthContext';
import { formatDateSafe } from '../utils/date';

export const Payments: React.FC = () => {
  const { role } = useAuth();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Reversal modal
  const [selectedPay, setSelectedPay] = useState<Payment | null>(null);
  const [reversalReason, setReversalReason] = useState('');
  const [reversalError, setReversalError] = useState<string | null>(null);

  const fetchPayments = async () => {
    setIsLoading(true);
    try {
      const data = await api.get<Payment[]>('/payments?limit=100');
      setPayments(data);
    } catch (err) {
      console.error('Failed to load payments:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();
  }, []);

  const handleReversePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPay) return;
    setReversalError(null);

    try {
      await api.post(`/payments/${selectedPay.id}/reverse`, {
        reason: reversalReason,
      });
      setSelectedPay(null);
      setReversalReason('');
      fetchPayments();
      alert('Payment reversal completed and invoice balance updated.');
    } catch (err: any) {
      setReversalError(err.message || 'Reversal failed.');
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50 min-h-screen">
      <Navbar title="Payment Transactions & Reconciliation" />

      <main className="p-8 space-y-6 flex-1 overflow-y-auto">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="font-bold text-slate-900 text-sm">Settled & Recorded Payments</h3>
            <span className="text-xs text-slate-400">{payments.length} transactions</span>
          </div>

          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Payment #</th>
                <th className="py-3.5 px-4">Invoice #</th>
                <th className="py-3.5 px-4">Customer</th>
                <th className="py-3.5 px-4">Amount</th>
                <th className="py-3.5 px-4">Method</th>
                <th className="py-3.5 px-4">Reference</th>
                <th className="py-3.5 px-4">Date</th>
                <th className="py-3.5 px-4">Status</th>
                {role !== 'customer' && <th className="py-3.5 px-4 text-right">Action</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {payments.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    No payment transactions recorded.
                  </td>
                </tr>
              ) : (
                payments.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 px-4 font-bold text-slate-900">{p.payment_number}</td>
                    <td className="py-3.5 px-4 text-teal-600 font-semibold">Invoice #{p.invoice_id}</td>
                    <td className="py-3.5 px-4 font-medium text-slate-700">
                      {p.customer?.company_name || p.customer?.user?.full_name || `Cust #${p.customer_id}`}
                    </td>
                    <td className="py-3.5 px-4 font-bold text-emerald-600">₹{p.amount}</td>
                    <td className="py-3.5 px-4 uppercase text-[11px] font-semibold text-slate-600">
                      {p.payment_method.replace('_', ' ')}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 font-mono text-[11px]">
                      {p.transaction_reference || 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">{formatDateSafe(p.payment_date)}</td>
                    <td className="py-3.5 px-4">
                      {p.is_reversed ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                          Reversed
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Settled
                        </span>
                      )}
                    </td>
                    {role !== 'customer' && (
                      <td className="py-3.5 px-4 text-right">
                        {!p.is_reversed && (
                          <button
                            onClick={() => {
                              setSelectedPay(p);
                              setReversalError(null);
                            }}
                            className="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-xs font-semibold"
                          >
                            <RotateCcw className="w-3.5 h-3.5 inline mr-1" /> Reverse
                          </button>
                        )}
                        {p.is_reversed && (
                          <span className="text-[11px] text-slate-400 italic">
                            {p.reversed_reason || 'Reversed'}
                          </span>
                        )}
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Payment Reversal Modal */}
        {selectedPay && (
          <Modal
            isOpen={!!selectedPay}
            onClose={() => setSelectedPay(null)}
            title={`Reverse Payment ${selectedPay.payment_number}`}
          >
            <form onSubmit={handleReversePayment} className="space-y-4 text-xs">
              {reversalError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg">
                  {reversalError}
                </div>
              )}
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-800">
                <p className="font-semibold">Caution: Reversal Adjustment</p>
                <p className="mt-0.5">
                  Reversing this payment of ₹{selectedPay.amount} will restore the due balance on Invoice #{selectedPay.invoice_id} and create an auditable reversal log.
                </p>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Reversal Reason (Mandatory) *
                </label>
                <input
                  type="text"
                  required
                  value={reversalReason}
                  onChange={(e) => setReversalReason(e.target.value)}
                  placeholder="e.g. Chargeback, customer bank dispute, check bounced"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-rose-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedPay(null)}
                  className="px-3 py-1.5 border border-slate-300 text-slate-700 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-lg"
                >
                  Confirm Reversal
                </button>
              </div>
            </form>
          </Modal>
        )}
      </main>
    </div>
  );
};
