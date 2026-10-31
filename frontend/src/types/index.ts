export type UserRole = 'admin' | 'staff' | 'customer';

export interface User {
  id: number;
  email: string;
  full_name: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  customer_id?: number;
  last_login?: string;
  created_at: string;
}

export interface Customer {
  id: number;
  user_id: number;
  company_name?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  gst_number?: string;
  notes?: string;
  is_active: boolean;
  created_at: string;
  user?: User;
}

export interface ProductVariant {
  id: number;
  product_id: number;
  variant_name: string;
  additional_price: number;
  description?: string;
  is_active: boolean;
}

export interface Product {
  id: number;
  name: string;
  product_type: 'software' | 'service' | 'addon' | 'support';
  sales_price: number;
  cost_price: number;
  description?: string;
  status: 'active' | 'inactive' | 'archived';
  is_deleted: boolean;
  variants: ProductVariant[];
  created_at: string;
}

export interface SubscriptionPlan {
  id: number;
  name: string;
  product_id: number;
  price: number;
  billing_frequency: 'daily' | 'weekly' | 'monthly' | 'yearly';
  min_quantity: number;
  start_date?: string;
  end_date?: string;
  auto_close: boolean;
  allow_early_closure: boolean;
  allow_pause: boolean;
  allow_renewal: boolean;
  description?: string;
  status: 'active' | 'inactive' | 'archived';
  product?: Product;
}

export type SubscriptionStatus = 'draft' | 'quotation' | 'confirmed' | 'active' | 'paused' | 'closed' | 'cancelled';
export type PaymentTerms = 'immediate' | 'net_15' | 'net_30' | 'net_45' | 'net_60';

export interface SubscriptionLine {
  id: number;
  product_id: number;
  variant_id?: number;
  description?: string;
  quantity: number;
  unit_price: number;
  tax_amount: number;
  discount_amount: number;
  line_total: number;
  product?: Product;
  variant?: ProductVariant;
}

export interface StatusHistory {
  id: number;
  from_status?: SubscriptionStatus;
  to_status: SubscriptionStatus;
  changed_by: number;
  reason?: string;
  changed_at: string;
}

export interface Subscription {
  id: number;
  subscription_number: string;
  customer_id: number;
  plan_id: number;
  quotation_id?: number;
  start_date: string;
  expiry_date: string;
  payment_terms: PaymentTerms;
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
  status: SubscriptionStatus;
  last_invoice_date?: string;
  next_invoice_date?: string;
  renewal_count: number;
  notes?: string;
  customer?: Customer;
  plan?: SubscriptionPlan;
  lines: SubscriptionLine[];
  status_history: StatusHistory[];
}

export type InvoiceStatus = 'draft' | 'confirmed' | 'paid' | 'partially_paid' | 'overdue' | 'cancelled';

export interface InvoiceLine {
  id: number;
  product_id: number;
  variant_id?: number;
  description?: string;
  quantity: number;
  unit_price: number;
  tax_amount: number;
  discount_amount: number;
  line_total: number;
  product?: Product;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  customer_id: number;
  subscription_id?: number;
  invoice_date: string;
  due_date: string;
  billing_period_start?: string;
  billing_period_end?: string;
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total: number;
  amount_paid: number;
  amount_due: number;
  status: InvoiceStatus;
  notes?: string;
  customer?: Customer;
  lines: InvoiceLine[];
}

export type PaymentMethod = 'cash' | 'bank_transfer' | 'upi' | 'card' | 'other';

export interface Payment {
  id: number;
  payment_number: string;
  invoice_id: number;
  customer_id: number;
  amount: number;
  payment_method: PaymentMethod;
  payment_date: string;
  transaction_reference?: string;
  notes?: string;
  is_reversed: boolean;
  reversed_reason?: string;
  customer?: Customer;
}

export interface Tax {
  id: number;
  name: string;
  rate: number;
  tax_type: 'percentage' | 'fixed';
  description?: string;
  is_active: boolean;
}

export interface Discount {
  id: number;
  name: string;
  discount_type: 'fixed' | 'percentage';
  value: number;
  min_purchase_amount?: number;
  min_quantity?: number;
  start_date?: string;
  end_date?: string;
  max_usage_limit?: number;
  usage_count: number;
  description?: string;
  is_active: boolean;
}

export interface Quotation {
  id: number;
  quotation_number: string;
  customer_id: number;
  plan_id?: number;
  valid_until: string;
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total: number;
  status: 'draft' | 'sent' | 'confirmed' | 'expired' | 'cancelled';
  notes?: string;
  customer?: Customer;
  lines: any[];
}

export interface DashboardStats {
  total_customers: number;
  active_subscriptions: number;
  total_products: number;
  total_revenue_collected: number;
  mrr: number;
  arr: number;
  pending_payments: number;
  overdue_invoices_count: number;
  overdue_invoices_amount: number;
  upcoming_renewals_count: number;
}

export interface DashboardAnalytics {
  stats: DashboardStats;
  monthly_revenue: { month: string; revenue: number; invoiced: number }[];
  subscription_growth: { month: string; active: number; new_subs: number; cancelled: number }[];
  subscription_status_distribution: { name: string; value: number }[];
  payment_status_distribution: { name: string; value: number }[];
  revenue_by_product: { product_name: string; revenue: number; subscription_count: number }[];
}

export interface AppNotification {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  link?: string;
  created_at: string;
}
