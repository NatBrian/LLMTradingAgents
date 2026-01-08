import { motion } from 'framer-motion';
import { DollarSign, TrendingUp, Users, Activity } from 'lucide-react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';
import { StatCard } from '../components/StatCard';
import { AgentCard } from '../components/AgentCard';
import type { DashboardData } from '../types';

interface OverviewPageProps {
    data: DashboardData;
}

export function OverviewPage({ data }: OverviewPageProps) {
    const { leaderboard, equityCurves, metadata, trades } = data;

    // Calculate total portfolio value and P&L
    const totalEquity = leaderboard.reduce((sum, agent) => sum + agent.current_equity, 0);
    const initialTotal = leaderboard.length * 100000; // Assuming $100k initial per agent
    const totalPnL = totalEquity - initialTotal;
    const totalPnLPct = (totalPnL / initialTotal) * 100;

    // Best performer
    const bestAgent = leaderboard[0];
    const bestReturn = bestAgent ? bestAgent.total_return * 100 : 0;

    // Prepare equity curve data for chart
    const equityCurveData = prepareEquityCurveData(equityCurves);

    // Recent trades (last 5)
    const recentTrades = trades?.slice(0, 5) || [];

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8"
            >
                <h1 className="text-3xl font-bold gradient-text mb-2">Trading Overview</h1>
                <p className="text-[var(--color-text-secondary)]">
                    Monitor AI agent performance across all trading sessions
                </p>
            </motion.div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total AUM"
                    value={`$${(totalEquity).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`}
                    change={totalPnLPct}
                    changeLabel="all-time"
                    icon={<DollarSign className="w-6 h-6" />}
                    variant={totalPnL >= 0 ? 'success' : 'danger'}
                />
                <StatCard
                    title="Best Performer"
                    value={bestAgent?.name || 'N/A'}
                    change={bestReturn}
                    changeLabel="return"
                    icon={<TrendingUp className="w-6 h-6" />}
                    variant="success"
                />
                <StatCard
                    title="Active Agents"
                    value={metadata.totalCompetitors}
                    subtitle="competing"
                    icon={<Users className="w-6 h-6" />}
                />
                <StatCard
                    title="Total Trades"
                    value={metadata.totalTrades}
                    subtitle={`across ${metadata.totalRuns} sessions`}
                    icon={<Activity className="w-6 h-6" />}
                />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                {/* Equity Curves Chart */}
                <div className="xl:col-span-2">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="glass-card p-6"
                    >
                        <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                            Equity Curves
                        </h2>
                        <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={equityCurveData}>
                                    <defs>
                                        {Object.keys(equityCurves).map((id, index) => {
                                            const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444'];
                                            const color = colors[index % colors.length];
                                            return (
                                                <linearGradient key={id} id={`gradient-${id}`} x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                                                    <stop offset="95%" stopColor={color} stopOpacity={0} />
                                                </linearGradient>
                                            );
                                        })}
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
                                        domain={['dataMin - 1000', 'dataMax + 1000']}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'var(--color-bg-secondary)',
                                            border: '1px solid var(--color-border-primary)',
                                            borderRadius: '8px',
                                            color: 'var(--color-text-primary)',
                                        }}
                                        formatter={(value) => value != null ? [`$${Number(value).toLocaleString()}`, ''] : ['', '']}
                                    />
                                    <Legend
                                        wrapperStyle={{ paddingTop: '20px' }}
                                        formatter={(value) => {
                                            const agent = leaderboard.find(a => a.competitor_id === value);
                                            return agent?.name || value;
                                        }}
                                    />
                                    {Object.entries(equityCurves).map(([id], index) => {
                                        const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444'];
                                        const color = colors[index % colors.length];
                                        return (
                                            <Area
                                                key={id}
                                                type="monotone"
                                                dataKey={id}
                                                stroke={color}
                                                strokeWidth={2}
                                                fill={`url(#gradient-${id})`}
                                                dot={false}
                                            />
                                        );
                                    })}
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </motion.div>
                </div>

                {/* Leaderboard */}
                <div className="xl:col-span-1">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="glass-card p-6"
                    >
                        <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                            Agent Leaderboard
                        </h2>
                        <div className="space-y-3">
                            {leaderboard.map((agent, index) => (
                                <AgentCard key={agent.competitor_id} agent={agent} rank={index + 1} />
                            ))}
                        </div>
                    </motion.div>
                </div>
            </div>

            {/* Recent Trades */}
            {recentTrades.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="glass-card p-6"
                >
                    <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                        Recent Trades
                    </h2>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Agent</th>
                                <th>Ticker</th>
                                <th>Side</th>
                                <th>Qty</th>
                                <th>Price</th>
                                <th>Notional</th>
                            </tr>
                        </thead>
                        <tbody>
                            {recentTrades.map((trade, index) => {
                                const agent = leaderboard.find(a => a.competitor_id === trade.competitor_id);
                                return (
                                    <tr key={index}>
                                        <td className="text-[var(--color-text-secondary)]">
                                            {new Date(trade.timestamp).toLocaleDateString('en-US', {
                                                month: 'short',
                                                day: 'numeric',
                                                hour: '2-digit',
                                                minute: '2-digit',
                                            })}
                                        </td>
                                        <td className="font-medium">{agent?.name || trade.competitor_id}</td>
                                        <td className="font-mono">{trade.ticker}</td>
                                        <td>
                                            <span className={`badge ${trade.side === 'BUY' ? 'badge-success' : 'badge-danger'}`}>
                                                {trade.side}
                                            </span>
                                        </td>
                                        <td>{trade.qty}</td>
                                        <td className="font-mono">${trade.price.toFixed(2)}</td>
                                        <td className="font-mono">${trade.notional.toLocaleString()}</td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </motion.div>
            )}
        </div>
    );
}

// Helper function to prepare equity curve data for Recharts
function prepareEquityCurveData(equityCurves: Record<string, { timestamp: string; equity: number }[]>) {
    const allDates = new Set<string>();
    const dataByDate: Record<string, Record<string, number>> = {};

    // Collect all dates and organize data
    Object.entries(equityCurves).forEach(([id, points]) => {
        points.forEach(point => {
            const date = new Date(point.timestamp).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
            });
            allDates.add(date);
            if (!dataByDate[date]) {
                dataByDate[date] = {};
            }
            dataByDate[date][id] = point.equity;
        });
    });

    // Convert to array format for Recharts
    return Array.from(allDates)
        .sort((a, b) => new Date(a).getTime() - new Date(b).getTime())
        .map(date => ({
            date,
            ...dataByDate[date],
        }));
}
