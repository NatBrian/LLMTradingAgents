import type { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    change?: number;
    changeLabel?: string;
    icon?: ReactNode;
    variant?: 'default' | 'success' | 'danger';
}

export function StatCard({
    title,
    value,
    subtitle,
    change,
    changeLabel,
    icon,
    variant = 'default',
}: StatCardProps) {
    const isPositive = change !== undefined && change > 0;
    const isNegative = change !== undefined && change < 0;

    const borderColor = variant === 'success'
        ? 'border-[var(--color-accent-success)]/30'
        : variant === 'danger'
            ? 'border-[var(--color-accent-danger)]/30'
            : 'border-[var(--color-glass-border)]';

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className={`glass-card glass-card-hover p-6 ${borderColor}`}
        >
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-sm text-[var(--color-text-secondary)] mb-1">{title}</p>
                    <motion.p
                        className="text-3xl font-bold text-[var(--color-text-primary)] tracking-tight"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.2 }}
                    >
                        {value}
                    </motion.p>

                    {(change !== undefined || subtitle) && (
                        <div className="flex items-center gap-2 mt-2">
                            {change !== undefined && (
                                <span className={`flex items-center gap-1 text-sm font-medium ${isPositive ? 'value-positive' : isNegative ? 'value-negative' : 'value-neutral'
                                    }`}>
                                    {isPositive ? <TrendingUp className="w-4 h-4" /> :
                                        isNegative ? <TrendingDown className="w-4 h-4" /> :
                                            <Minus className="w-4 h-4" />}
                                    {isPositive ? '+' : ''}{typeof change === 'number' ? change.toFixed(2) : change}%
                                </span>
                            )}
                            {changeLabel && (
                                <span className="text-xs text-[var(--color-text-muted)]">{changeLabel}</span>
                            )}
                            {subtitle && !change && (
                                <span className="text-sm text-[var(--color-text-secondary)]">{subtitle}</span>
                            )}
                        </div>
                    )}
                </div>

                {icon && (
                    <div className="w-12 h-12 rounded-xl bg-[var(--color-bg-tertiary)] flex items-center justify-center text-[var(--color-accent-primary)]">
                        {icon}
                    </div>
                )}
            </div>
        </motion.div>
    );
}
