import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Sidebar } from './components/Sidebar';
import { RoleGuard } from './components/RoleGuard';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { Customers } from './pages/Customers';
import { Products } from './pages/Products';
import { Plans } from './pages/Plans';
import { Quotations } from './pages/Quotations';
import { Subscriptions } from './pages/Subscriptions';
import { Invoices } from './pages/Invoices';
import { Payments } from './pages/Payments';
import { Discounts } from './pages/Discounts';
import { Taxes } from './pages/Taxes';
import { CustomerPortal } from './pages/CustomerPortal';

const ProtectedLayout: React.FC = () => {
  const { isAuthenticated, isLoading, role } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center text-teal-400 font-semibold">
        Loading Brightloop Subscription Management...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Routes>
          {/* Dashboard / Overview: Admin & Staff only */}
          <Route
            path="/"
            element={
              role === 'customer' ? (
                <Navigate to="/portal" replace />
              ) : (
                <RoleGuard allowedRoles={['admin', 'staff']}>
                  <Dashboard />
                </RoleGuard>
              )
            }
          />

          {/* Operational routes: Admin & Staff only */}
          <Route
            path="/customers"
            element={
              <RoleGuard allowedRoles={['admin', 'staff']}>
                <Customers />
              </RoleGuard>
            }
          />
          <Route
            path="/products"
            element={
              <RoleGuard allowedRoles={['admin', 'staff']}>
                <Products />
              </RoleGuard>
            }
          />
          <Route
            path="/quotations"
            element={
              <RoleGuard allowedRoles={['admin', 'staff']}>
                <Quotations />
              </RoleGuard>
            }
          />
          <Route
            path="/subscriptions"
            element={
              <RoleGuard allowedRoles={['admin', 'staff']}>
                <Subscriptions />
              </RoleGuard>
            }
          />

          {/* Admin-only routes */}
          <Route
            path="/discounts"
            element={
              <RoleGuard allowedRoles={['admin']}>
                <Discounts />
              </RoleGuard>
            }
          />
          <Route
            path="/taxes"
            element={
              <RoleGuard allowedRoles={['admin']}>
                <Taxes />
              </RoleGuard>
            }
          />

          {/* Accessible by all authenticated roles */}
          <Route
            path="/plans"
            element={
              <RoleGuard allowedRoles={['admin', 'staff', 'customer']}>
                <Plans />
              </RoleGuard>
            }
          />
          <Route
            path="/invoices"
            element={
              <RoleGuard allowedRoles={['admin', 'staff', 'customer']}>
                <Invoices />
              </RoleGuard>
            }
          />
          <Route
            path="/payments"
            element={
              <RoleGuard allowedRoles={['admin', 'staff', 'customer']}>
                <Payments />
              </RoleGuard>
            }
          />
          <Route
            path="/portal"
            element={
              <RoleGuard allowedRoles={['admin', 'staff', 'customer']}>
                <CustomerPortal />
              </RoleGuard>
            }
          />

          {/* Catch-all fallback */}
          <Route
            path="*"
            element={<Navigate to={role === 'customer' ? '/portal' : '/'} replace />}
          />
        </Routes>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/*" element={<ProtectedLayout />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
