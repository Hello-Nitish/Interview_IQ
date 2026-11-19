import React from 'react';

interface BadgeProps {
  label: string;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'slate';
  icon?: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  variant = 'primary',
  icon,
  className = '',
}) => {
  const variantStyles = {
    primary: 'bg-primary-light text-primary-dark border-primary/20',
    success: 'bg-success-light text-success-dark border-success/20',
    warning: 'bg-warning-light text-warning-dark border-warning/20',
    danger: 'bg-danger-light text-danger-dark border-danger/20',
    slate: 'bg-inset text-muted border-border',
  }[variant];

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${variantStyles} ${className}`}
    >
      {icon && <span className="inline-block">{icon}</span>}
      {label}
    </span>
  );
};
