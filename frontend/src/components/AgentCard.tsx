import { motion } from 'framer-motion';
import type { LeaderboardEntry } from '../types';

interface AgentCardProps {
    agent: LeaderboardEntry;
    rank: number;
}

export function AgentCard({ agent, rank }: AgentCardProps) {
    const isPositive = agent.total_return > 0;
    const isNegative = agent.total_return < 0;

    const getRankStyle = (rank: number) => {
        switch (rank) {
            case 1:
                return 'bg-gradient-to-br from-yellow-500 to-amber-600 text-white';
            case 2:
                return 'bg-gradient-to-br from-slate-300 to-slate-400 text-slate-900';
            case 3:
                return 'bg-gradient-to-br from-amber-600 to-amber-700 text-white';
            default:
                return 'bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)]';
        }
    };

    const getProviderBadge = (provider: string) => {
        switch (provider) {
            case 'gemini':
                return { bg: 'bg-blue-500/15', text: 'text-blue-400', label: 'Gemini' };
            case 'openrouter':
                return { bg: 'bg-purple-500/15', text: 'text-purple-400', label: 'OpenRouter' };
            default:
                return { bg: 'bg-gray-500/15', text: 'text-gray-400', label: provider };
        }
    };

    const badge = getProviderBadge(agent.provider);

    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: rank * 0.1 }}
            className="glass-card glass-card-hover p-5 flex items-center gap-4"
        >
            {/* Rank Badge */}
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${getRankStyle(rank)}`}>
                {rank}
            </div>

            {/* Agent Info */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-[var(--color-text-primary)] truncate">
                        {agent.name}
                    </h3>
                    <span className={`badge ${badge.bg} ${badge.text}`}>
                        {badge.label}
                    </span>
                </div>
                <p className="text-xs text-[var(--color-text-muted)] truncate">
                    {agent.model}
                </p>
            </div>

            {/* Stats */}
            <div className="text-right">
                <p className="text-lg font-bold text-[var(--color-text-primary)]">
                    ${agent.current_equity.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                </p>
                <p className={`text-sm font-medium ${isPositive ? 'value-positive' : isNegative ? 'value-negative' : 'value-neutral'
                    }`}>
                    {isPositive ? '+' : ''}{(agent.total_return * 100).toFixed(2)}%
                </p>
            </div>

            {/* Additional Stats */}
            <div className="hidden sm:flex flex-col items-end gap-1 text-xs text-[var(--color-text-muted)] border-l border-[var(--color-border-secondary)] pl-4 ml-2">
                <span>DD: {(agent.max_drawdown * 100).toFixed(1)}%</span>
                <span>Trades: {agent.num_trades}</span>
            </div>
        </motion.div>
    );
}
