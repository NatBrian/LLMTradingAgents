import { useState } from 'react';
import { motion } from 'framer-motion';
import { DollarSign, Wallet, PieChart, TrendingUp } from 'lucide-react';
import {
    PieChart as RechartsPie,
    Pie,
    Cell,
    ResponsiveContainer,
    Tooltip,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    BarChart,
    Bar
} from 'recharts';
import { StatCard } from '../components/StatCard';
import type { DashboardData } from '../types';

interface PortfolioPageProps {
    data: DashboardData;
}

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export function PortfolioPage({ data }: PortfolioPageProps) {
    const { snapshots, leaderboard, equityCurves } = data;
    const [selectedAgent, setSelectedAgent] = useState<string>(leaderboard[0]?.competitor_id || '');

    const snapshot = snapshots[selectedAgent];
    const agentCurve = equityCurves[selectedAgent] || [];

    if (!snapshot) {
        return (
            <div className="flex items-center justify-center h-64">
                <p className="text-[var(--color-text-muted)]">No portfolio data available</p>
            </div>
        );
    }

    // Calculate derived values
    const positionsValue = snapshot.positions?.reduce((sum, p) =>
        sum + (p.market_value || p.qty * p.current_price), 0
    ) || 0;
    const equity = snapshot.equity || (snapshot.cash + positionsValue);
    const unrealizedPnL = snapshot.unrealized_pnl ||
        snapshot.positions?.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0) || 0;

    // Prepare allocation data for pie chart
    const allocationData = [
        { name: 'Cash', value: snapshot.cash },
        ...(snapshot.positions?.map(p => ({
            name: p.ticker,
            value: p.market_value || p.qty * p.current_price,
        })) || []),
    ].filter(d => d.value > 0);

    // Prepare P&L data for bar chart
    const pnlData = snapshot.positions?.map(p => ({
        ticker: p.ticker,
        pnl: p.unrealized_pnl || (p.current_price - p.avg_cost) * p.qty,
    })) || [];

    // Prepare equity history
    const equityHistory = agentCurve.map(point => ({
        date: new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        equity: point.equity,
    }));

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start justify-between"
            >
                <div>
                    <h1 className="text-3xl font-bold gradient-text mb-2">Portfolio</h1>
                    <p className="text-[var(--color-text-secondary)]">
                        View holdings and performance by agent
                    </p>
                </div>

                {/* Agent Selector */}
                <select
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    className="bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] border border-[var(--color-border-primary)] rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-primary)]"
                >
                    {leaderboard.map(agent => (
                        <option key={agent.competitor_id} value={agent.competitor_id}>
                            {agent.name}
                        </option>
                    ))}
                </select>
            </motion.div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total Equity"
                    value={`$${equity.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`}
                    icon={<DollarSign className="w-6 h-6" />}
                />
                <StatCard
                    title="Cash"
                    value={`$${snapshot.cash.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`}
                    icon={<Wallet className="w-6 h-6" />}
                />
                <StatCard
                    title="Positions Value"
                    value={`$${positionsValue.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`}
                    icon={<PieChart className="w-6 h-6" />}
                />
                <StatCard
                    title="Unrealized P&L"
                    value={`${unrealizedPnL >= 0 ? '+' : ''}$${unrealizedPnL.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`}
                    icon={<TrendingUp className="w-6 h-6" />}
                    variant={unrealizedPnL >= 0 ? 'success' : 'danger'}
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Allocation Pie Chart */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="glass-card p-6"
                >
                    <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                        Portfolio Allocation
                    </h2>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <RechartsPie>
                                <Pie
                                    data={allocationData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    paddingAngle={2}
                                    dataKey="value"
                                    label={({ name, percent }) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                                    labelLine={{ stroke: 'var(--color-text-muted)', strokeWidth: 1 }}
                                >
                                    {allocationData.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'var(--color-bg-secondary)',
                                        border: '1px solid var(--color-border-primary)',
                                        borderRadius: '8px',
                                        color: 'var(--color-text-primary)',
                                    }}
                                    formatter={(value) => value != null ? [`$${Number(value).toLocaleString()}`, ''] : ['', '']}
                                />
                            </RechartsPie>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* P&L by Position */}
                {pnlData.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="glass-card p-6"
                    >
                        <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                            P&L by Position
                        </h2>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={pnlData} layout="vertical">
                                    <XAxis
                                        type="number"
                                        stroke="var(--color-text-muted)"
                                        fontSize={12}
                                        tickFormatter={(v) => `$${v.toLocaleString()}`}
                                    />
                                    <YAxis
                                        type="category"
                                        dataKey="ticker"
                                        stroke="var(--color-text-muted)"
                                        fontSize={12}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'var(--color-bg-secondary)',
                                            border: '1px solid var(--color-border-primary)',
                                            borderRadius: '8px',
                                        }}
                                        formatter={(value) => value != null ? [`$${Number(value).toLocaleString()}`, 'P&L'] : ['', 'P&L']}
                                    />
                                    <Bar
                                        dataKey="pnl"
                                        fill="var(--color-accent-primary)"
                                        radius={[0, 4, 4, 0]}
                                    >
                                        {pnlData.map((entry, index) => (
                                            <Cell
                                                key={`cell-${index}`}
                                                fill={entry.pnl >= 0 ? 'var(--color-accent-success)' : 'var(--color-accent-danger)'}
                                            />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </motion.div>
                )}
            </div>

            {/* Positions Table */}
            {snapshot.positions && snapshot.positions.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="glass-card p-6"
                >
                    <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                        Current Positions
                    </h2>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Ticker</th>
                                <th>Quantity</th>
                                <th>Avg Cost</th>
                                <th>Current Price</th>
                                <th>Market Value</th>
                                <th>P&L</th>
                                <th>P&L %</th>
                            </tr>
                        </thead>
                        <tbody>
                            {snapshot.positions.map((pos, index) => {
                                const marketValue = pos.market_value || pos.qty * pos.current_price;
                                const pnl = pos.unrealized_pnl || (pos.current_price - pos.avg_cost) * pos.qty;
                                const pnlPct = pos.unrealized_pnl_pct || ((pos.current_price / pos.avg_cost - 1) * 100);
                                const isPositive = pnl >= 0;

                                return (
                                    <tr key={index}>
                                        <td className="font-mono font-medium">{pos.ticker}</td>
                                        <td>{pos.qty}</td>
                                        <td className="font-mono">${pos.avg_cost.toFixed(2)}</td>
                                        <td className="font-mono">${pos.current_price.toFixed(2)}</td>
                                        <td className="font-mono">${marketValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                                        <td className={`font-mono ${isPositive ? 'value-positive' : 'value-negative'}`}>
                                            {isPositive ? '+' : ''}${pnl.toFixed(2)}
                                        </td>
                                        <td className={`font-mono ${isPositive ? 'value-positive' : 'value-negative'}`}>
                                            {isPositive ? '+' : ''}{pnlPct.toFixed(2)}%
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </motion.div>
            )}

            {/* Equity History */}
            {equityHistory.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="glass-card p-6"
                >
                    <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                        Equity History
                    </h2>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={equityHistory}>
                                <defs>
                                    <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--color-accent-primary)" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="var(--color-accent-primary)" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis
                                    dataKey="date"
                                    stroke="var(--color-text-muted)"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    stroke="var(--color-text-muted)"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                                    domain={['dataMin - 500', 'dataMax + 500']}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'var(--color-bg-secondary)',
                                        border: '1px solid var(--color-border-primary)',
                                        borderRadius: '8px',
                                    }}
                                    formatter={(value) => value != null ? [`$${Number(value).toLocaleString()}`, 'Equity'] : ['', 'Equity']}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="equity"
                                    stroke="var(--color-accent-primary)"
                                    strokeWidth={2}
                                    fill="url(#equityGradient)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>
            )}
        </div>
    );
}
