import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Filter, ArrowUpDown } from 'lucide-react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell
} from 'recharts';
import type { DashboardData } from '../types';

interface TradeHistoryPageProps {
    data: DashboardData;
}

type SortField = 'timestamp' | 'ticker' | 'qty' | 'notional';
type SortDirection = 'asc' | 'desc';

export function TradeHistoryPage({ data }: TradeHistoryPageProps) {
    const { trades, leaderboard } = data;

    // Filters
    const [agentFilter, setAgentFilter] = useState<string>('all');
    const [tickerFilter, setTickerFilter] = useState<string>('all');
    const [sideFilter, setSideFilter] = useState<string>('all');

    // Sort
    const [sortField, setSortField] = useState<SortField>('timestamp');
    const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

    // Get unique tickers
    const uniqueTickers = useMemo(() =>
        [...new Set(trades.map(t => t.ticker))].sort(),
        [trades]
    );

    // Filter and sort trades
    const filteredTrades = useMemo(() => {
        let result = [...trades];

        if (agentFilter !== 'all') {
            result = result.filter(t => t.competitor_id === agentFilter);
        }
        if (tickerFilter !== 'all') {
            result = result.filter(t => t.ticker === tickerFilter);
        }
        if (sideFilter !== 'all') {
            result = result.filter(t => t.side === sideFilter);
        }

        result.sort((a, b) => {
            let cmp = 0;
            switch (sortField) {
                case 'timestamp':
                    cmp = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
                    break;
                case 'ticker':
                    cmp = a.ticker.localeCompare(b.ticker);
                    break;
                case 'qty':
                    cmp = a.qty - b.qty;
                    break;
                case 'notional':
                    cmp = a.notional - b.notional;
                    break;
            }
            return sortDirection === 'desc' ? -cmp : cmp;
        });

        return result;
    }, [trades, agentFilter, tickerFilter, sideFilter, sortField, sortDirection]);

    // Summary stats
    const totalVolume = filteredTrades.reduce((sum, t) => sum + t.notional, 0);
    const buyCount = filteredTrades.filter(t => t.side === 'BUY').length;
    const sellCount = filteredTrades.filter(t => t.side === 'SELL').length;

    // Ticker distribution
    const tickerDistribution = useMemo(() => {
        const counts: Record<string, number> = {};
        filteredTrades.forEach(t => {
            counts[t.ticker] = (counts[t.ticker] || 0) + 1;
        });
        return Object.entries(counts)
            .map(([ticker, count]) => ({ ticker, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 10);
    }, [filteredTrades]);

    // Buy/Sell distribution for pie chart
    const sideDistribution = [
        { name: 'BUY', value: buyCount },
        { name: 'SELL', value: sellCount },
    ];

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortDirection(d => d === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('desc');
        }
    };

    const getAgentName = (id: string) =>
        leaderboard.find(a => a.competitor_id === id)?.name || id;

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-3xl font-bold gradient-text mb-2">Trade History</h1>
                <p className="text-[var(--color-text-secondary)]">
                    Browse and analyze all executed trades
                </p>
            </motion.div>

            {/* Filters */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-6"
            >
                <div className="flex items-center gap-2 mb-4">
                    <Filter className="w-5 h-5 text-[var(--color-text-muted)]" />
                    <span className="font-medium text-[var(--color-text-primary)]">Filters</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm text-[var(--color-text-muted)] mb-1">Agent</label>
                        <select
                            value={agentFilter}
                            onChange={(e) => setAgentFilter(e.target.value)}
                            className="w-full bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] border border-[var(--color-border-primary)] rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-primary)]"
                        >
                            <option value="all">All Agents</option>
                            {leaderboard.map(agent => (
                                <option key={agent.competitor_id} value={agent.competitor_id}>
                                    {agent.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm text-[var(--color-text-muted)] mb-1">Ticker</label>
                        <select
                            value={tickerFilter}
                            onChange={(e) => setTickerFilter(e.target.value)}
                            className="w-full bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] border border-[var(--color-border-primary)] rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-primary)]"
                        >
                            <option value="all">All Tickers</option>
                            {uniqueTickers.map(ticker => (
                                <option key={ticker} value={ticker}>{ticker}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm text-[var(--color-text-muted)] mb-1">Side</label>
                        <select
                            value={sideFilter}
                            onChange={(e) => setSideFilter(e.target.value)}
                            className="w-full bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] border border-[var(--color-border-primary)] rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-primary)]"
                        >
                            <option value="all">All</option>
                            <option value="BUY">BUY</option>
                            <option value="SELL">SELL</option>
                        </select>
                    </div>
                </div>
            </motion.div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="glass-card p-4">
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Total Trades</p>
                    <p className="text-2xl font-bold text-[var(--color-text-primary)]">{filteredTrades.length}</p>
                </div>
                <div className="glass-card p-4">
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Total Volume</p>
                    <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                        ${totalVolume.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                    </p>
                </div>
                <div className="glass-card p-4">
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Buys</p>
                    <p className="text-2xl font-bold value-positive">{buyCount}</p>
                </div>
                <div className="glass-card p-4">
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Sells</p>
                    <p className="text-2xl font-bold value-negative">{sellCount}</p>
                </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Ticker Distribution */}
                {tickerDistribution.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="glass-card p-6"
                    >
                        <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                            Most Traded Tickers
                        </h2>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={tickerDistribution} layout="vertical">
                                    <XAxis type="number" stroke="var(--color-text-muted)" fontSize={12} />
                                    <YAxis
                                        type="category"
                                        dataKey="ticker"
                                        stroke="var(--color-text-muted)"
                                        fontSize={12}
                                        width={50}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'var(--color-bg-secondary)',
                                            border: '1px solid var(--color-border-primary)',
                                            borderRadius: '8px',
                                        }}
                                    />
                                    <Bar
                                        dataKey="count"
                                        fill="var(--color-accent-primary)"
                                        radius={[0, 4, 4, 0]}
                                    />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </motion.div>
                )}

                {/* Buy/Sell Distribution */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="glass-card p-6"
                >
                    <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                        Buy/Sell Ratio
                    </h2>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={sideDistribution}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    paddingAngle={5}
                                    dataKey="value"
                                    label={({ name, percent }) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                                >
                                    <Cell fill="var(--color-accent-success)" />
                                    <Cell fill="var(--color-accent-danger)" />
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'var(--color-bg-secondary)',
                                        border: '1px solid var(--color-border-primary)',
                                        borderRadius: '8px',
                                    }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>
            </div>

            {/* Trades Table */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="glass-card p-6"
            >
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                    All Trades
                </h2>
                <div className="overflow-x-auto">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th
                                    className="cursor-pointer hover:text-[var(--color-text-primary)]"
                                    onClick={() => handleSort('timestamp')}
                                >
                                    <div className="flex items-center gap-1">
                                        Time
                                        {sortField === 'timestamp' && (
                                            <ArrowUpDown className="w-3 h-3" />
                                        )}
                                    </div>
                                </th>
                                <th>Agent</th>
                                <th
                                    className="cursor-pointer hover:text-[var(--color-text-primary)]"
                                    onClick={() => handleSort('ticker')}
                                >
                                    <div className="flex items-center gap-1">
                                        Ticker
                                        {sortField === 'ticker' && (
                                            <ArrowUpDown className="w-3 h-3" />
                                        )}
                                    </div>
                                </th>
                                <th>Side</th>
                                <th
                                    className="cursor-pointer hover:text-[var(--color-text-primary)]"
                                    onClick={() => handleSort('qty')}
                                >
                                    <div className="flex items-center gap-1">
                                        Qty
                                        {sortField === 'qty' && (
                                            <ArrowUpDown className="w-3 h-3" />
                                        )}
                                    </div>
                                </th>
                                <th>Price</th>
                                <th
                                    className="cursor-pointer hover:text-[var(--color-text-primary)]"
                                    onClick={() => handleSort('notional')}
                                >
                                    <div className="flex items-center gap-1">
                                        Notional
                                        {sortField === 'notional' && (
                                            <ArrowUpDown className="w-3 h-3" />
                                        )}
                                    </div>
                                </th>
                                <th>Fees</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredTrades.slice(0, 50).map((trade, index) => (
                                <tr key={index}>
                                    <td className="text-[var(--color-text-secondary)]">
                                        {new Date(trade.timestamp).toLocaleDateString('en-US', {
                                            month: 'short',
                                            day: 'numeric',
                                            hour: '2-digit',
                                            minute: '2-digit',
                                        })}
                                    </td>
                                    <td>{getAgentName(trade.competitor_id)}</td>
                                    <td className="font-mono">{trade.ticker}</td>
                                    <td>
                                        <span className={`badge ${trade.side === 'BUY' ? 'badge-success' : 'badge-danger'}`}>
                                            {trade.side}
                                        </span>
                                    </td>
                                    <td>{trade.qty}</td>
                                    <td className="font-mono">${trade.price.toFixed(2)}</td>
                                    <td className="font-mono">${trade.notional.toLocaleString()}</td>
                                    <td className="font-mono text-[var(--color-text-muted)]">${trade.fees.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {filteredTrades.length > 50 && (
                        <p className="text-center text-sm text-[var(--color-text-muted)] mt-4">
                            Showing 50 of {filteredTrades.length} trades
                        </p>
                    )}
                </div>
            </motion.div>
        </div>
    );
}
