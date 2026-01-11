import { useState, useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { TrendingUp, TrendingDown, Activity, Users, DollarSign, Trophy, LineChart, Menu, X } from 'lucide-react';
import type { DashboardData } from '../types';

interface CommandCenterProps {
    data: DashboardData;
}

type TimeRange = '1W' | '1M' | '3M' | 'ALL';
const TIME_RANGES: TimeRange[] = ['1W', '1M', '3M', 'ALL'];

const NAV_ITEMS = [
    { path: '/', label: 'Dashboard' },
    { path: '/trades', label: 'Trades' },
    { path: '/thinking', label: 'AI Thinking' },
    { path: '/market', label: 'Markets' },
    { path: '/portfolio', label: 'Portfolio' },
    { path: '/architecture', label: 'About' },
];

const AGENT_COLORS = [
    '#10b981', '#6366f1', '#f59e0b', '#ec4899', '#8b5cf6',
    '#14b8a6', '#f97316', '#84cc16', '#06b6d4', '#ef4444'
];

export function CommandCenter({ data }: CommandCenterProps) {
    const location = useLocation();
    const [timeRange, setTimeRange] = useState<TimeRange>('ALL');
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const { leaderboard, equityCurves, trades } = data;

    // Summary stats
    const stats = useMemo(() => {
        const totalEquity = leaderboard.reduce((sum, a) => sum + a.current_equity, 0);
        const bestReturn = Math.max(...leaderboard.map(a => a.total_return));
        const totalTrades = trades.length;
        const activeAgents = leaderboard.length;
        return { totalEquity, bestReturn, totalTrades, activeAgents };
    }, [leaderboard, trades]);

    // Prepare chart data
    const chartData = useMemo(() => {
        const allTimestamps = new Set<string>();
        Object.values(equityCurves).forEach(curve => {
            curve.forEach(point => allTimestamps.add(point.timestamp));
        });

        const sortedTimestamps = Array.from(allTimestamps).sort();

        // Filter based on time range
        const now = new Date();
        const cutoff = new Date();
        if (timeRange === '1W') cutoff.setDate(now.getDate() - 7);
        else if (timeRange === '1M') cutoff.setMonth(now.getMonth() - 1);
        else if (timeRange === '3M') cutoff.setMonth(now.getMonth() - 3);

        const filteredTimestamps = timeRange === 'ALL'
            ? sortedTimestamps
            : sortedTimestamps.filter(t => new Date(t) >= cutoff);

        return filteredTimestamps.map(timestamp => {
            const dataPoint: Record<string, number | string> = {
                date: new Date(timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            };
            leaderboard.forEach(agent => {
                const curve = equityCurves[agent.competitor_id] || [];
                const point = curve.find(p => p.timestamp === timestamp) ||
                    curve.filter(p => p.timestamp <= timestamp).pop();
                if (point) dataPoint[agent.competitor_id] = point.equity;
            });
            return dataPoint;
        });
    }, [equityCurves, leaderboard, timeRange]);

    const getAgentColor = (idx: number) => AGENT_COLORS[idx % AGENT_COLORS.length];

    const formatCurrency = (value: number) =>
        `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    const formatReturn = (value: number) => {
        const pct = value * 100;
        return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`;
    };

    return (
        <div className="min-h-screen bg-[var(--color-bg-primary)]">
            {/* Header */}
            <header className="border-b border-[var(--color-border-secondary)] bg-[var(--color-bg-primary)]/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-4">
                    <div className="flex items-center justify-between">
                        <Link to="/" className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] flex items-center justify-center">
                                <LineChart className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-lg font-bold text-[var(--color-text-primary)]">Trading Arena</h1>
                                <p className="text-xs text-[var(--color-text-muted)] hidden sm:block">LLM Trading Competition</p>
                            </div>
                        </Link>
                        <nav className="hidden md:flex items-center gap-1">
                            {NAV_ITEMS.map(item => (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${location.pathname === item.path
                                        ? 'bg-[var(--color-accent-primary)] text-white'
                                        : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)]'
                                        }`}
                                >
                                    {item.label}
                                </Link>
                            ))}
                        </nav>
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="md:hidden p-2 rounded-lg text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)]"
                        >
                            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                        </button>
                    </div>

                    {/* Mobile Navigation */}
                    {mobileMenuOpen && (
                        <nav className="md:hidden mt-4 pb-2 border-t border-[var(--color-border-secondary)] pt-4">
                            <div className="flex flex-col gap-1">
                                {NAV_ITEMS.map(item => (
                                    <Link
                                        key={item.path}
                                        to={item.path}
                                        onClick={() => setMobileMenuOpen(false)}
                                        className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${location.pathname === item.path
                                            ? 'bg-[var(--color-accent-primary)] text-white'
                                            : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)]'
                                            }`}
                                    >
                                        {item.label}
                                    </Link>
                                ))}
                            </div>
                        </nav>
                    )}
                </div>
            </header>


            <main className="max-w-[1600px] mx-auto px-4 sm:px-6 py-6 space-y-6">
                {/* Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-[var(--color-accent-primary)]/20 flex items-center justify-center">
                                <DollarSign className="w-5 h-5 text-[var(--color-accent-primary)]" />
                            </div>
                            <div>
                                <p className="text-xs text-[var(--color-text-muted)]">Total AUM</p>
                                <p className="text-lg font-bold text-[var(--color-text-primary)]">
                                    {formatCurrency(stats.totalEquity)}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-4">
                        <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${stats.bestReturn >= 0 ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
                                {stats.bestReturn >= 0 ? (
                                    <TrendingUp className="w-5 h-5 text-emerald-400" />
                                ) : (
                                    <TrendingDown className="w-5 h-5 text-red-400" />
                                )}
                            </div>
                            <div>
                                <p className="text-xs text-[var(--color-text-muted)]">Best Return</p>
                                <p className={`text-lg font-bold ${stats.bestReturn >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                    {formatReturn(stats.bestReturn)}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                <Activity className="w-5 h-5 text-blue-400" />
                            </div>
                            <div>
                                <p className="text-xs text-[var(--color-text-muted)]">Total Trades</p>
                                <p className="text-lg font-bold text-[var(--color-text-primary)]">{stats.totalTrades}</p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                                <Users className="w-5 h-5 text-purple-400" />
                            </div>
                            <div>
                                <p className="text-xs text-[var(--color-text-muted)]">Active Agents</p>
                                <p className="text-lg font-bold text-[var(--color-text-primary)]">{stats.activeAgents}</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Chart - 2 columns */}
                    <div className="lg:col-span-2 bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <LineChart className="w-5 h-5 text-[var(--color-accent-primary)]" />
                                <h2 className="text-base font-semibold text-[var(--color-text-primary)]">Portfolio Value</h2>
                            </div>
                            <div className="flex gap-1">
                                {TIME_RANGES.map(range => (
                                    <button
                                        key={range}
                                        onClick={() => setTimeRange(range)}
                                        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${timeRange === range
                                            ? 'bg-[var(--color-accent-primary)] text-white'
                                            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)]'
                                            }`}
                                    >
                                        {range}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                    <defs>
                                        {leaderboard.map((agent, idx) => (
                                            <linearGradient key={agent.competitor_id} id={`grad-${agent.competitor_id}`} x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="0%" stopColor={getAgentColor(idx)} stopOpacity={0.3} />
                                                <stop offset="100%" stopColor={getAgentColor(idx)} stopOpacity={0} />
                                            </linearGradient>
                                        ))}
                                    </defs>
                                    <XAxis
                                        dataKey="date"
                                        stroke="var(--color-text-muted)"
                                        fontSize={11}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis
                                        stroke="var(--color-text-muted)"
                                        fontSize={11}
                                        tickLine={false}
                                        axisLine={false}
                                        domain={['dataMin - 20', 'dataMax + 20']}
                                        tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'var(--color-bg-primary)',
                                            border: '1px solid var(--color-border-secondary)',
                                            borderRadius: '8px',
                                            fontSize: '12px'
                                        }}
                                        formatter={(value: number | undefined) => [value !== undefined ? formatCurrency(value) : '', '']}
                                        labelFormatter={(label) => label}
                                    />
                                    <Legend
                                        wrapperStyle={{ paddingTop: '16px', fontSize: '11px' }}
                                        formatter={(value) => {
                                            const agent = leaderboard.find(a => a.competitor_id === value);
                                            return agent?.name || value;
                                        }}
                                    />
                                    {leaderboard.map((agent, idx) => (
                                        <Area
                                            key={agent.competitor_id}
                                            type="monotone"
                                            dataKey={agent.competitor_id}
                                            stroke={getAgentColor(idx)}
                                            fill={`url(#grad-${agent.competitor_id})`}
                                            strokeWidth={2}
                                            dot={false}
                                        />
                                    ))}
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Leaderboard - 1 column */}
                    <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-6">
                        <div className="flex items-center gap-2 mb-4">
                            <Trophy className="w-5 h-5 text-amber-400" />
                            <h2 className="text-base font-semibold text-[var(--color-text-primary)]">Leaderboard</h2>
                        </div>

                        <div className="space-y-3">
                            {leaderboard.map((agent, idx) => (
                                <Link
                                    key={agent.competitor_id}
                                    to="/portfolio"
                                    className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-elevated)] transition-colors group"
                                >
                                    <div className="flex items-center gap-3">
                                        <div
                                            className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm"
                                            style={{
                                                backgroundColor: `${getAgentColor(idx)}20`,
                                                color: getAgentColor(idx)
                                            }}
                                        >
                                            {idx + 1}
                                        </div>
                                        <div>
                                            <div className="font-medium text-[var(--color-text-primary)] text-sm group-hover:text-[var(--color-accent-primary)] transition-colors">
                                                {agent.name}
                                            </div>
                                            <div className="text-xs text-[var(--color-text-muted)]">
                                                {agent.num_trades} trades
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-semibold text-[var(--color-text-primary)] text-sm">
                                            {formatCurrency(agent.current_equity)}
                                        </div>
                                        <div className={`text-xs font-medium ${agent.total_return >= 0
                                            ? 'text-emerald-400'
                                            : 'text-red-400'
                                            }`}>
                                            {formatReturn(agent.total_return)}
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>

                        <Link
                            to="/portfolio"
                            className="block mt-4 text-center text-sm text-[var(--color-accent-primary)] hover:underline"
                        >
                            View Portfolio Details →
                        </Link>
                    </div>
                </div>
            </main>
        </div>
    );
}
