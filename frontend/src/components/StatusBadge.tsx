import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const norm = (status || '').toLowerCase().replace(/_/g, ' ');

  const getStyle = () => {
    switch (norm) {
      case 'active':
      case 'paid':
      case 'confirmed':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-600/20';
      case 'partially paid':
      case 'quotation':
      case 'sent':
        return 'bg-blue-50 text-blue-700 border-blue-200 ring-blue-600/20';
      case 'draft':
      case 'paused':
        return 'bg-amber-50 text-amber-700 border-amber-200 ring-amber-600/20';
      case 'overdue':
      case 'expired':
      case 'cancelled':
      case 'closed':
        return 'bg-rose-50 text-rose-700 border-rose-200 ring-rose-600/20';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200 ring-slate-600/20';
    }
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border ring-1 ring-inset ${getStyle()}`}
    >
      <span className="w-1.5 h-1.5 mr-1.5 rounded-full bg-current opacity-70" />
      {norm}
    </span>
  );
};
