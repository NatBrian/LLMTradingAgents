import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Wallet, TrendingUp, TrendingDown, DollarSign, Activity, Brain } from 'lucide-react';
import {
    AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, BarChart, Bar
} from 'recharts';
import type { DashboardData } from '../types';

interface PortfolioPageProps {
    data: DashboardData;
}

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899'];

export function PortfolioPage({ data }: PortfolioPageProps) {
    const { leaderboard, equityCurves, snapshots, runLogs } = data;

    const [selectedAgent, setSelectedAgent] = useState<string>(leaderboard[0]?.competitor_id || '');

    // Get selected agent's data
    const agent = leaderboard.find(a => a.competitor_id === selectedAgent);
    const snapshot = snapshots[selectedAgent];
    const agentCurve = equityCurves[selectedAgent] || [];
    const agentLogs = runLogs.filter(r => r.competitor_id === selectedAgent);

    // Prepare chart data
    const equityData = agentCurve.map(point => ({
        date: new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        equity: point.equity,
    }));

    // Allocation data
    const positions = useMemo(() => snapshot?.positions || [], [snapshot]);
    const allocationData = useMemo(() => {
        const data = [
            { name: 'Cash', value: snapshot?.cash || 0 }
        ];
        positions.forEach(p => {
            const value = p.market_value || p.qty * p.current_price;
            if (value > 0) {
                data.push({ name: p.ticker, value });
            }
        });
        return data;
    }, [snapshot, positions]);

    // P&L data
    const pnlData = positions.map(p => ({
        ticker: p.ticker,
        pnl: p.unrealized_pnl || (p.current_price - p.avg_cost) * p.qty
    }));

    // LLM stats
    const llmCalls = agentLogs.flatMap(r => r.llm_calls || []);
    const totalTokens = llmCalls.reduce((sum, c) => sum + (c.prompt_tokens || 0) + (c.completion_tokens || 0), 0);
    const avgLatency = llmCalls.length > 0
        ? llmCalls.reduce((sum, c) => sum + (c.latency_ms || 0), 0) / llmCalls.length
        : 0;
    const successRate = llmCalls.length > 0
        ? llmCalls.filter(c => c.success).length / llmCalls.length * 100
        : 0;

    // Recent proposals
    const recentProposals = agentLogs
        .filter(r => r.strategist_proposal)
        .slice(-5)
        .reverse();

    const formatCurrency = (value: number) =>
        `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    const formatReturn = (value: number) => {
        const pct = value * 100;
        return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`;
    };

    return (
        <div className="space-y-6">
            {/* Agent Selector */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-wrap gap-2"
            >
                {leaderboard.map((a, idx) => (
                    <button
                        key={a.competitor_id}
                        onClick={() => setSelectedAgent(a.competitor_id)}
                        className={`px-4 py-2 rounded-lg font-medium transition-all ${selectedAgent === a.competitor_id
                            ? 'bg-gradient-to-r from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] text-white'
                            : 'bg-[var(--color-bg-secondary)] border border-[var(--color-border-secondary)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                            }`}
                    >
                        <span className="text-xs opacity-60 mr-2">#{idx + 1}</span>
                        {a.name}
                    </button>
                ))}
            </motion.div>

            {agent && (
                <>
                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-4"
                        >
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-[var(--color-accent-primary)]/20 flex items-center justify-center">
                                    <Wallet className="w-5 h-5 text-[var(--color-accent-primary)]" />
                                </div>
                                <div>
                                    <p className="text-xs text-[var(--color-text-muted)]">Total Equity</p>
                                    <p className="text-lg font-bold text-[var(--color-text-primary)]">
                                        {formatCurrency(agent.current_equity)}
                                    </p>
                                </div>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-4"
                        >
                            <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${agent.total_return >= 0 ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
                                    {agent.total_return >= 0 ? (
                                        <TrendingUp className="w-5 h-5 text-emerald-400" />
                                    ) : (
                                        <TrendingDown className="w-5 h-5 text-red-400" />
                                    )}
                                </div>
                                <div>
                                    <p className="text-xs text-[var(--color-text-muted)]">Total Return</p>
                                    <p className={`text-lg font-bold ${agent.total_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                        {formatReturn(agent.total_return)}
                                    </p>
                                </div>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-4"
                        >
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                    <DollarSign className="w-5 h-5 text-blue-400" />
                                </div>
                                <div>
                                    <p className="text-xs text-[var(--color-text-muted)]">Cash</p>
                                    <p className="text-lg font-bold text-[var(--color-text-primary)]">
                                        {formatCurrency(snapshot?.cash || 0)}
                                    </p>
                                </div>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                            className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-4"
                        >
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                                    <Activity className="w-5 h-5 text-purple-400" />
                                </div>
                                <div>
                                    <p className="text-xs text-[var(--color-text-muted)]">Trades</p>
                                    <p className="text-lg font-bold text-[var(--color-text-primary)]">
                                        {agent.num_trades}
                                    </p>
                                </div>
                            </div>
                        </motion.div>
                    </div>

                    {/* Charts Row */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Equity Chart */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="lg:col-span-2 bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-6"
                        >
                            <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4">Equity History</h3>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={equityData}>
                                        <defs>
                                            <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                                                <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <XAxis dataKey="date" stroke="var(--color-text-muted)" fontSize={11} />
                                        <YAxis stroke="var(--color-text-muted)" fontSize={11} domain={['dataMin - 50', 'dataMax + 50']} />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: 'var(--color-bg-primary)',
                                                border: '1px solid var(--color-border-secondary)',
                                                borderRadius: '8px'
                                            }}
                                        />
                                        <Area type="monotone" dataKey="equity" stroke="#6366f1" fill="url(#equityGrad)" strokeWidth={2} />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </motion.div>

                        {/* Allocation Pie */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-6"
                        >
                            <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4">Allocation</h3>
                            <div className="h-48">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={allocationData}
                                            innerRadius={45}
                                            outerRadius={70}
                                            paddingAngle={3}
                                            dataKey="value"
                                        >
                                            {allocationData.map((_, idx) => (
                                                <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip formatter={(value: number | undefined) => value !== undefined ? formatCurrency(value) : ''} />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="flex flex-wrap gap-2 mt-2">
                                {allocationData.map((d, idx) => (
                                    <span key={d.name} className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
                                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                                        {d.name}
                                    </span>
                                ))}
                            </div>
                        </motion.div>
                    </div>

                    {/* P&L and Positions */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* P&L Bar Chart */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-6"
                        >
                            <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4">P&L by Position</h3>
                            {pnlData.length > 0 ? (
                                <div className="h-48">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={pnlData} layout="vertical">
                                            <XAxis type="number" stroke="var(--color-text-muted)" fontSize={11} />
                                            <YAxis dataKey="ticker" type="category" width={50} stroke="var(--color-text-muted)" fontSize={11} />
                                            <Tooltip formatter={(value: number | undefined) => value !== undefined ? formatCurrency(value) : ''} />
                                            <Bar dataKey="pnl" radius={[0, 4, 4, 0]}>
                                                {pnlData.map((item, idx) => (
                                                    <Cell key={idx} fill={item.pnl >= 0 ? '#10b981' : '#ef4444'} />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            ) : (
                                <div className="h-48 flex items-center justify-center text-[var(--color-text-muted)]">
                                    No positions
                                </div>
                            )}
                        </motion.div>

                        {/* Positions Table */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-6"
                        >
                            <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4">Current Positions</h3>
                            {positions.length > 0 ? (
                                <div className="overflow-x-auto">
                                    <table className="data-table w-full">
                                        <thead>
                                            <tr>
                                                <th>Ticker</th>
                                                <th>Qty</th>
                                                <th>Avg Cost</th>
                                                <th>Current</th>
                                                <th>P&L</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {positions.map((pos, idx) => {
                                                const pnl = pos.unrealized_pnl || (pos.current_price - pos.avg_cost) * pos.qty;
                                                const pnlPct = (pos.current_price - pos.avg_cost) / pos.avg_cost * 100;
                                                return (
                                                    <tr key={idx}>
                                                        <td className="font-mono font-medium">{pos.ticker}</td>
                                                        <td>{pos.qty}</td>
                                                        <td className="font-mono">${pos.avg_cost.toFixed(2)}</td>
                                                        <td className="font-mono">${pos.current_price.toFixed(2)}</td>
                                                        <td className={`font-mono font-medium ${pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                            {pnl >= 0 ? '+' : ''}{formatCurrency(pnl)} ({pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(1)}%)
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="h-32 flex items-center justify-center text-[var(--color-text-muted)]">
                                    No positions held
                                </div>
                            )}
                        </motion.div>
                    </div>

                    {/* AI Activity Section */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-6"
                    >
                        <div className="flex items-center gap-2 mb-4">
                            <Brain className="w-5 h-5 text-[var(--color-accent-primary)]" />
                            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">AI Activity</h3>
                        </div>

                        <div className="grid grid-cols-3 gap-4 mb-6">
                            <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-3">
                                <p className="text-xs text-[var(--color-text-muted)]">Total Tokens</p>
                                <p className="text-lg font-bold text-[var(--color-text-primary)]">{totalTokens.toLocaleString()}</p>
                            </div>
                            <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-3">
                                <p className="text-xs text-[var(--color-text-muted)]">Avg Latency</p>
                                <p className="text-lg font-bold text-[var(--color-text-primary)]">{avgLatency.toFixed(0)}ms</p>
                            </div>
                            <div className="bg-[var(--color-bg-tertiary)] rounded-lg p-3">
                                <p className="text-xs text-[var(--color-text-muted)]">Success Rate</p>
                                <p className="text-lg font-bold text-emerald-400">{successRate.toFixed(0)}%</p>
                            </div>
                        </div>

                        {/* Recent Proposals */}
                        <h4 className="text-xs font-medium text-[var(--color-text-muted)] mb-3">Recent Proposals</h4>
                        {recentProposals.length > 0 ? (
                            <div className="space-y-2">
                                {recentProposals.map((log, idx) => (
                                    <div key={idx} className="bg-[var(--color-bg-tertiary)] rounded-lg p-3">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm font-medium text-[var(--color-text-primary)]">
                                                {log.session_type} - {new Date(log.timestamp).toLocaleDateString()}
                                            </span>
                                        </div>
                                        <div className="flex flex-wrap gap-2">
                                            {log.strategist_proposal?.proposals?.map((p, pIdx) => (
                                                <span
                                                    key={pIdx}
                                                    className={`text-xs px-2 py-1 rounded font-medium ${p.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' :
                                                        p.action === 'SELL' ? 'bg-red-500/20 text-red-400' :
                                                            'bg-gray-500/20 text-gray-400'
                                                        }`}
                                                >
                                                    {p.action} {p.ticker} ({(p.confidence * 100).toFixed(0)}%)
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center text-[var(--color-text-muted)] py-4">
                                No proposals yet
                            </div>
                        )}
                    </motion.div>
                </>
            )}
        </div>
    );
}
