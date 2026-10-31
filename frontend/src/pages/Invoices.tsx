import React, { useState, useEffect } from 'react';
import {
  Receipt, Download, Search, Filter, CreditCard, Ban, CheckCircle2,
  AlertCircle, Eye
} from 'lucide-react';
import { api } from '../api/client';
import { Invoice, PaymentMethod } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Navbar } from '../components/Navbar';
import { Modal } from '../components/Modal';
import { useAuth } from '../context/AuthContext';
import { formatDateSafe } from '../utils/date';

export const Invoices: React.FC = () => {
  const { role } = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Payment Recording State
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('upi');
  const [paymentRef, setPaymentRef] = useState('');
  const [paymentNotes, setPaymentNotes] = useState('');
  const [paymentError, setPaymentError] = useState<string | null>(null);

  const fetchInvoices = async () => {
    setIsLoading(true);
    try {
      let path = '/invoices?limit=100';
      if (statusFilter) path += `&status=${statusFilter}`;
      if (search) path += `&search=${encodeURIComponent(search)}`;
      const data = await api.get<Invoice[]>(path);
      setInvoices(data);
    } catch (err) {
      console.error('Failed to load invoices:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [statusFilter, search]);

  const handleDownloadPdf = async (inv: Invoice) => {
    try {
      await api.download(`/invoices/${inv.id}/pdf`, `Invoice-${inv.invoice_number}.pdf`);
    } catch (err: any) {
      alert(`Could not download PDF: ${err.message}`);
    }
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    setPaymentError(null);

    try {
      await api.post('/payments', {
        invoice_id: selectedInvoice.id,
        amount: Number(paymentAmount),
        payment_method: paymentMethod,
        transaction_reference: paymentRef,
        notes: paymentNotes,
      });
      setShowPaymentModal(false);
      fetchInvoices();
      // refresh selected invoice
      const updated = await api.get<Invoice>(`/invoices/${selectedInvoice.id}`);
      setSelectedInvoice(updated);
      alert('Payment successfully recorded and allocated to invoice!');
    } catch (err: any) {
      setPaymentError(err.message || 'Payment recording failed.');
    }
  };

  const handleCancelInvoice = async (invId: number) => {
    if (!confirm('Are you sure you want to cancel this invoice?')) return;
    try {
      await api.put(`/invoices/${invId}/cancel`);
      fetchInvoices();
      setSelectedInvoice(null);
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50 min-h-screen">
      <Navbar title="Billing & Invoicing" />

      <main className="p-8 space-y-6 flex-1 overflow-y-auto">
        {/* Filters */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3 flex-1 max-w-md">
            <div className="relative w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search invoices by invoice number or notes..."
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
              <option value="confirmed">Confirmed</option>
              <option value="paid">Paid</option>
              <option value="partially_paid">Partially Paid</option>
              <option value="overdue">Overdue</option>
              <option value="draft">Draft</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Invoice Table */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Invoice #</th>
                <th className="py-3.5 px-4">Customer</th>
                <th className="py-3.5 px-4">Invoice Date</th>
                <th className="py-3.5 px-4">Due Date</th>
                <th className="py-3.5 px-4">Total</th>
                <th className="py-3.5 px-4">Paid</th>
                <th className="py-3.5 px-4">Due Balance</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {invoices.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    No invoices found.
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 px-4 font-bold text-slate-900">
                      {inv.invoice_number}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-700">
                      {inv.customer?.company_name || inv.customer?.user?.full_name || 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">{formatDateSafe(inv.invoice_date)}</td>
                    <td className="py-3.5 px-4 text-slate-500">{formatDateSafe(inv.due_date)}</td>
                    <td className="py-3.5 px-4 font-bold text-slate-900">₹{inv.total}</td>
                    <td className="py-3.5 px-4 text-emerald-600 font-semibold">₹{inv.amount_paid}</td>
                    <td className="py-3.5 px-4 text-rose-600 font-bold">₹{inv.amount_due}</td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={inv.status} />
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-1">
                      <button
                        onClick={() => setSelectedInvoice(inv)}
                        title="View details"
                        className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium"
                      >
                        <Eye className="w-3.5 h-3.5 inline mr-1" /> View
                      </button>
                      <button
                        onClick={() => handleDownloadPdf(inv)}
                        title="Download PDF"
                        className="px-2.5 py-1 bg-teal-50 hover:bg-teal-100 text-teal-700 rounded-lg text-xs font-semibold"
                      >
                        <Download className="w-3.5 h-3.5 inline mr-1" /> PDF
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Invoice Detail Modal */}
        {selectedInvoice && (
          <Modal
            isOpen={!!selectedInvoice}
            onClose={() => setSelectedInvoice(null)}
            title={`Invoice ${selectedInvoice.invoice_number}`}
            maxWidth="2xl"
          >
            <div className="space-y-6 text-xs">
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div>
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Customer</span>
                  <span className="text-sm font-bold text-slate-900">
                    {selectedInvoice.customer?.company_name || selectedInvoice.customer?.user?.full_name}
                  </span>
                  <p className="text-slate-500">
                    {selectedInvoice.customer?.city}, {selectedInvoice.customer?.country} | GST: {selectedInvoice.customer?.gst_number || 'N/A'}
                  </p>
                </div>
                <div className="text-right">
                  <StatusBadge status={selectedInvoice.status} />
                  <span className="text-lg font-bold text-slate-900 block mt-1">₹{selectedInvoice.total}</span>
                  <span className="text-rose-600 font-semibold block">Due: ₹{selectedInvoice.amount_due}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between">
                <button
                  onClick={() => handleDownloadPdf(selectedInvoice)}
                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold flex items-center"
                >
                  <Download className="w-4 h-4 mr-1.5" /> Download PDF
                </button>

                <div className="space-x-2">
                  {role !== 'customer' && selectedInvoice.amount_due > 0 && selectedInvoice.status !== 'cancelled' && (
                    <button
                      onClick={() => {
                        setPaymentAmount(String(selectedInvoice.amount_due));
                        setShowPaymentModal(true);
                        setPaymentError(null);
                      }}
                      className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold"
                    >
                      <CreditCard className="w-4 h-4 mr-1.5 inline" /> Record Payment
                    </button>
                  )}
                  {role !== 'customer' && selectedInvoice.amount_paid === 0 && selectedInvoice.status !== 'cancelled' && (
                    <button
                      onClick={() => handleCancelInvoice(selectedInvoice.id)}
                      className="px-3 py-1.5 bg-rose-50 text-rose-600 hover:bg-rose-100 rounded-lg font-semibold"
                    >
                      <Ban className="w-4 h-4 mr-1.5 inline" /> Cancel
                    </button>
                  )}
                </div>
              </div>

              {/* Line items */}
              <div>
                <h4 className="font-bold text-slate-900 mb-2">Invoice Line Items</h4>
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left">
                    <thead className="bg-slate-50 text-slate-500">
                      <tr>
                        <th className="py-2 px-3">Item</th>
                        <th className="py-2 px-3">Qty</th>
                        <th className="py-2 px-3">Unit Price</th>
                        <th className="py-2 px-3">Tax</th>
                        <th className="py-2 px-3">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedInvoice.lines?.map((l) => (
                        <tr key={l.id}>
                          <td className="py-2 px-3 font-medium text-slate-900">{l.product?.name || 'Service'}</td>
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

              {/* Financial summary breakdown */}
              <div className="flex justify-end">
                <div className="w-64 space-y-1.5 text-right">
                  <div className="flex justify-between text-slate-500">
                    <span>Subtotal:</span>
                    <span>₹{selectedInvoice.subtotal}</span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Tax:</span>
                    <span>₹{selectedInvoice.tax_amount}</span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Discount:</span>
                    <span>-₹{selectedInvoice.discount_amount}</span>
                  </div>
                  <div className="flex justify-between font-bold text-slate-900 border-t border-slate-200 pt-1 text-sm">
                    <span>Grand Total:</span>
                    <span>₹{selectedInvoice.total}</span>
                  </div>
                  <div className="flex justify-between font-semibold text-emerald-600">
                    <span>Amount Paid:</span>
                    <span>₹{selectedInvoice.amount_paid}</span>
                  </div>
                  <div className="flex justify-between font-bold text-rose-600">
                    <span>Balance Due:</span>
                    <span>₹{selectedInvoice.amount_due}</span>
                  </div>
                </div>
              </div>
            </div>
          </Modal>
        )}

        {/* Record Payment Modal */}
        {showPaymentModal && selectedInvoice && (
          <Modal
            isOpen={showPaymentModal}
            onClose={() => setShowPaymentModal(false)}
            title={`Record Payment for ${selectedInvoice.invoice_number}`}
          >
            <form onSubmit={handleRecordPayment} className="space-y-4 text-xs">
              {paymentError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg">
                  {paymentError}
                </div>
              )}

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex justify-between">
                <span>Remaining Balance Due:</span>
                <span className="font-bold text-rose-600">₹{selectedInvoice.amount_due}</span>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Payment Amount (₹) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  max={selectedInvoice.amount_due}
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-teal-500"
                />
                <span className="text-[11px] text-slate-400 mt-1 block">
                  Supports partial payment up to remaining balance
                </span>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Payment Method *</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-teal-500"
                >
                  <option value="upi">UPI (GPay / PhonePe / Paytm)</option>
                  <option value="bank_transfer">Bank Transfer (NEFT / RTGS)</option>
                  <option value="card">Credit / Debit Card</option>
                  <option value="cash">Cash</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Transaction Reference / UTR
                </label>
                <input
                  type="text"
                  value={paymentRef}
                  onChange={(e) => setPaymentRef(e.target.value)}
                  placeholder="e.g. UTR1234567890"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Notes</label>
                <input
                  type="text"
                  value={paymentNotes}
                  onChange={(e) => setPaymentNotes(e.target.value)}
                  placeholder="Optional payment notes"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPaymentModal(false)}
                  className="px-3 py-1.5 border border-slate-300 text-slate-700 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg"
                >
                  Confirm Payment
                </button>
              </div>
            </form>
          </Modal>
        )}
      </main>
    </div>
  );
};
