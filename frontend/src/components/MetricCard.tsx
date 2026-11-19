import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  delta?: string;
  icon?: React.ReactNode;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'default';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  delta,
  icon,
  variant = 'default',
}) => {
  const borderStyles = {
    primary: 'border-l-4 border-l-primary',
    success: 'border-l-4 border-l-success',
    warning: 'border-l-4 border-l-warning',
    danger: 'border-l-4 border-l-danger',
    default: 'border-border',
  }[variant];

  return (
    <div className={`neuro-card p-4 flex flex-col justify-between ${borderStyles}`}>
      <div className="flex items-center justify-between text-muted text-xs font-semibold uppercase tracking-wider mb-2">
        <span>{label}</span>
        {icon && <span className="text-primary">{icon}</span>}
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-2xl font-extrabold text-heading">{value}</span>
        {delta && (
          <span className="text-xs font-bold text-success bg-success-light px-2 py-0.5 rounded-full">
            {delta}
          </span>
        )}
      </div>
    </div>
  );
};
