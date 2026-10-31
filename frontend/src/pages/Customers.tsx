import React, { useState, useEffect } from 'react';
import { Users, Plus, Search, Building2, Mail, Phone, MapPin } from 'lucide-react';
import { api } from '../api/client';
import { Customer } from '../types';
import { Navbar } from '../components/Navbar';
import { Modal } from '../components/Modal';
import { useAuth } from '../context/AuthContext';

export const Customers: React.FC = () => {
  const { role } = useAuth();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);

  const [newCust, setNewCust] = useState({
    full_name: '',
    email: '',
    phone: '',
    password: '',
    company_name: '',
    address: '',
    city: '',
    state: '',
    gst_number: '',
  });
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchCustomers = async () => {
    setIsLoading(true);
    try {
      let path = '/customers?limit=100';
      if (search) path += `&search=${encodeURIComponent(search)}`;
      const data = await api.get<Customer[]>(path);
      setCustomers(data);
    } catch (err) {
      console.error('Failed to load customers:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [search]);

  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      await api.post('/customers', newCust);
      setShowCreateModal(false);
      setNewCust({
        full_name: '',
        email: '',
        phone: '',
        password: '',
        company_name: '',
        address: '',
        city: '',
        state: '',
        gst_number: '',
      });
      fetchCustomers();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create customer.');
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50 min-h-screen">
      <Navbar title="Customer Relationship Management" />

      <main className="p-8 space-y-6 flex-1 overflow-y-auto">
        <div className="flex items-center justify-between">
          <div className="relative w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search customers by name, company, email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-teal-500 focus:outline-none"
            />
          </div>

          {role !== 'customer' && (
            <button
              onClick={() => { setShowCreateModal(true); setErrorMsg(null); }}
              className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Add Customer
            </button>
          )}
        </div>

        {/* Customer Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {customers.map((c) => (
            <div
              key={c.id}
              onClick={() => setSelectedCustomer(c)}
              className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer space-y-3"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">
                    {c.company_name || c.user?.full_name || 'Individual Customer'}
                  </h4>
                  <p className="text-xs text-slate-500 font-medium">{c.user?.full_name}</p>
                </div>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              </div>

              <div className="space-y-1.5 text-xs text-slate-600 pt-2 border-t border-slate-100">
                <div className="flex items-center space-x-2">
                  <Mail className="w-3.5 h-3.5 text-slate-400" />
                  <span className="truncate">{c.user?.email}</span>
                </div>
                {c.user?.phone && (
                  <div className="flex items-center space-x-2">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span>{c.user.phone}</span>
                  </div>
                )}
                {c.city && (
                  <div className="flex items-center space-x-2">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>{c.city}, {c.country}</span>
                  </div>
                )}
              </div>

              <div className="pt-2 flex justify-between items-center text-[11px] text-slate-400">
                <span>GST: {c.gst_number || 'Unregistered'}</span>
                <span className="text-teal-600 font-semibold hover:underline">View details →</span>
              </div>
            </div>
          ))}
        </div>

        {/* Create Customer Modal */}
        {showCreateModal && (
          <Modal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            title="Register New Customer"
          >
            <form onSubmit={handleCreateCustomer} className="space-y-4 text-xs">
              {errorMsg && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg">
                  {errorMsg}
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Contact Name *</label>
                  <input
                    type="text"
                    required
                    value={newCust.full_name}
                    onChange={(e) => setNewCust({ ...newCust, full_name: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                    placeholder="Sameer Joshi"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Company Name</label>
                  <input
                    type="text"
                    value={newCust.company_name}
                    onChange={(e) => setNewCust({ ...newCust, company_name: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                    placeholder="Pulse Healthcare"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Email *</label>
                  <input
                    type="email"
                    required
                    value={newCust.email}
                    onChange={(e) => setNewCust({ ...newCust, email: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                    placeholder="contact@pulse.com"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Phone</label>
                  <input
                    type="text"
                    value={newCust.phone}
                    onChange={(e) => setNewCust({ ...newCust, phone: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                    placeholder="+91 98765 43210"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Temporary Password *</label>
                <input
                  type="password"
                  required
                  value={newCust.password}
                  onChange={(e) => setNewCust({ ...newCust, password: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  placeholder="Min 8 chars, uppercase, lowercase, special"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">City</label>
                  <input
                    type="text"
                    value={newCust.city}
                    onChange={(e) => setNewCust({ ...newCust, city: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">State</label>
                  <input
                    type="text"
                    value={newCust.state}
                    onChange={(e) => setNewCust({ ...newCust, state: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">GST Number</label>
                  <input
                    type="text"
                    value={newCust.gst_number}
                    onChange={(e) => setNewCust({ ...newCust, gst_number: e.target.value })}
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
                  Create Customer
                </button>
              </div>
            </form>
          </Modal>
        )}

        {/* Customer Detail Modal */}
        {selectedCustomer && (
          <Modal
            isOpen={!!selectedCustomer}
            onClose={() => setSelectedCustomer(null)}
            title="Customer Profile"
          >
            <div className="space-y-4 text-xs">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <h4 className="text-base font-bold text-slate-900">
                  {selectedCustomer.company_name || selectedCustomer.user?.full_name}
                </h4>
                <p className="text-slate-500">{selectedCustomer.user?.full_name} ({selectedCustomer.user?.email})</p>
                <p className="text-slate-500 mt-1">Phone: {selectedCustomer.user?.phone || 'N/A'}</p>
                <p className="text-slate-500">Address: {selectedCustomer.address || 'N/A'}, {selectedCustomer.city}, {selectedCustomer.state}</p>
                <p className="text-slate-500">GST: {selectedCustomer.gst_number || 'N/A'}</p>
              </div>
            </div>
          </Modal>
        )}
      </main>
    </div>
  );
};
