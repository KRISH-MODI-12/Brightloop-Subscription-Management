import React, { useState, useEffect } from 'react';
import { Package, Plus, Tag, Search, Edit3, Archive, Layers } from 'lucide-react';
import { api } from '../api/client';
import { Product, ProductVariant } from '../types';
import { Navbar } from '../components/Navbar';
import { Modal } from '../components/Modal';
import { useAuth } from '../context/AuthContext';

export const Products: React.FC = () => {
  const { role } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showVariantModal, setShowVariantModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // New product form
  const [newProd, setNewProd] = useState({
    name: '',
    product_type: 'software',
    sales_price: '',
    cost_price: '',
    description: '',
  });

  // New variant form
  const [newVar, setNewVar] = useState({
    variant_name: '',
    additional_price: '',
    description: '',
  });

  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchProducts = async () => {
    setIsLoading(true);
    try {
      let path = '/products?limit=100';
      if (search) path += `&search=${encodeURIComponent(search)}`;
      if (typeFilter) path += `&product_type=${typeFilter}`;
      const data = await api.get<Product[]>(path);
      setProducts(data);
    } catch (err) {
      console.error('Failed to load products:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [search, typeFilter]);

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      await api.post('/products', {
        name: newProd.name,
        product_type: newProd.product_type,
        sales_price: Number(newProd.sales_price),
        cost_price: Number(newProd.cost_price || 0),
        description: newProd.description,
      });
      setShowCreateModal(false);
      fetchProducts();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create product.');
    }
  };

  const handleAddVariant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProduct) return;
    setErrorMsg(null);
    try {
      await api.post(`/products/${selectedProduct.id}/variants`, {
        variant_name: newVar.variant_name,
        additional_price: Number(newVar.additional_price),
        description: newVar.description,
      });
      setShowVariantModal(false);
      setNewVar({ variant_name: '', additional_price: '', description: '' });
      fetchProducts();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to add variant.');
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-slate-50 min-h-screen">
      <Navbar title="Product Catalog & Variants" />

      <main className="p-8 space-y-6 flex-1 overflow-y-auto">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 w-96">
            <div className="relative w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search products..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-teal-500 focus:outline-none"
              />
            </div>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs text-slate-700"
            >
              <option value="">All Types</option>
              <option value="software">Software</option>
              <option value="service">Service</option>
              <option value="addon">Addon</option>
              <option value="support">Support</option>
            </select>
          </div>

          {role === 'admin' && (
            <button
              onClick={() => { setShowCreateModal(true); setErrorMsg(null); }}
              className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Create Product
            </button>
          )}
        </div>

        {/* Product Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map((p) => (
            <div
              key={p.id}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between space-y-4 hover:shadow-md transition-shadow"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-teal-600 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-100">
                      {p.product_type}
                    </span>
                    <h3 className="font-bold text-slate-900 text-base mt-1.5">{p.name}</h3>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400 block">Base Price</span>
                    <span className="text-lg font-bold text-slate-900">₹{p.sales_price}</span>
                  </div>
                </div>

                <p className="text-xs text-slate-600 line-clamp-2">{p.description || 'No description provided.'}</p>

                {/* Variants Section */}
                <div className="pt-3 border-t border-slate-100">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between mb-2">
                    <span>Configured Variants ({p.variants?.length || 0})</span>
                    {role === 'admin' && (
                      <button
                        onClick={() => { setSelectedProduct(p); setShowVariantModal(true); setErrorMsg(null); }}
                        className="text-teal-600 hover:underline lowercase font-semibold"
                      >
                        + add variant
                      </button>
                    )}
                  </span>

                  <div className="space-y-1.5">
                    {p.variants && p.variants.length > 0 ? (
                      p.variants.map((v) => (
                        <div
                          key={v.id}
                          className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 text-xs"
                        >
                          <span className="font-medium text-slate-700">{v.variant_name}</span>
                          <span className="font-bold text-teal-700">
                            +₹{v.additional_price} (₹{Number(p.sales_price) + Number(v.additional_price)})
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-[11px] text-slate-400 italic">No custom brand variants configured.</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                <span>Cost: ₹{p.cost_price}</span>
                <span className="font-semibold text-emerald-600 capitalize">{p.status}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Create Product Modal */}
        {showCreateModal && (
          <Modal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            title="Create Software Product"
          >
            <form onSubmit={handleCreateProduct} className="space-y-4 text-xs">
              {errorMsg && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg">
                  {errorMsg}
                </div>
              )}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Product Name *</label>
                <input
                  type="text"
                  required
                  value={newProd.name}
                  onChange={(e) => setNewProd({ ...newProd, name: e.target.value })}
                  placeholder="Brightloop Cloud ERP"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Product Type</label>
                  <select
                    value={newProd.product_type}
                    onChange={(e) => setNewProd({ ...newProd, product_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  >
                    <option value="software">Software</option>
                    <option value="service">Service</option>
                    <option value="addon">Addon</option>
                    <option value="support">Support</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Sales Price (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={newProd.sales_price}
                    onChange={(e) => setNewProd({ ...newProd, sales_price: e.target.value })}
                    placeholder="1000.00"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Cost Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newProd.cost_price}
                    onChange={(e) => setNewProd({ ...newProd, cost_price: e.target.value })}
                    placeholder="300.00"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description / Notes</label>
                <textarea
                  rows={3}
                  value={newProd.description}
                  onChange={(e) => setNewProd({ ...newProd, description: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  placeholder="Enterprise capabilities, integrations, etc."
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
                  Save Product
                </button>
              </div>
            </form>
          </Modal>
        )}

        {/* Add Variant Modal */}
        {showVariantModal && selectedProduct && (
          <Modal
            isOpen={showVariantModal}
            onClose={() => setShowVariantModal(false)}
            title={`Add Brand Variant to ${selectedProduct.name}`}
          >
            <form onSubmit={handleAddVariant} className="space-y-4 text-xs">
              {errorMsg && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg">
                  {errorMsg}
                </div>
              )}
              <div className="p-3 bg-teal-50 border border-teal-200 rounded-lg text-teal-800">
                <p className="font-semibold">Base Price: ₹{selectedProduct.sales_price}</p>
                <p className="mt-0.5 text-[11px]">
                  Example from hackathon: Odoo Brand Additional Price = ₹560 → Final Price = ₹{Number(selectedProduct.sales_price) + 560}
                </p>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Variant Name *</label>
                <input
                  type="text"
                  required
                  value={newVar.variant_name}
                  onChange={(e) => setNewVar({ ...newVar, variant_name: e.target.value })}
                  placeholder="e.g. Odoo Brand Enterprise"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Additional Price (₹) *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={newVar.additional_price}
                  onChange={(e) => setNewVar({ ...newVar, additional_price: e.target.value })}
                  placeholder="560.00"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description</label>
                <input
                  type="text"
                  value={newVar.description}
                  onChange={(e) => setNewVar({ ...newVar, description: e.target.value })}
                  placeholder="Includes brand connectors and customized UI"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowVariantModal(false)}
                  className="px-3 py-1.5 border border-slate-300 text-slate-700 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg"
                >
                  Save Variant
                </button>
              </div>
            </form>
          </Modal>
        )}
      </main>
    </div>
  );
};
