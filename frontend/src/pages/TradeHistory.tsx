import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
    TrendingUp, TrendingDown, DollarSign, Activity, ArrowUpDown, Clock,
    BarChart3, ChevronDown, ChevronUp
} from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import type { DashboardData } from '../types';

interface TradeHistoryPageProps {
    data: DashboardData;
}

type SortField = 'timestamp' | 'ticker' | 'qty' | 'notional';
type SortDirection = 'asc' | 'desc';

export function TradeHistoryPage({ data }: TradeHistoryPageProps) {
    const { trades, leaderboard } = data;

    const [agentFilter, setAgentFilter] = useState<string>('all');
    const [tickerFilter, setTickerFilter] = useState<string>('all');
    const [sideFilter, setSideFilter] = useState<string>('all');
    const [sortField, setSortField] = useState<SortField>('timestamp');
    const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

    const uniqueTickers = useMemo(() => [...new Set(trades.map(t => t.ticker))].sort(), [trades]);

    const filteredTrades = useMemo(() => {
        let result = [...trades];
        if (agentFilter !== 'all') result = result.filter(t => t.competitor_id === agentFilter);
        if (tickerFilter !== 'all') result = result.filter(t => t.ticker === tickerFilter);
        if (sideFilter !== 'all') result = result.filter(t => t.side === sideFilter);

        result.sort((a, b) => {
            let cmp = 0;
            switch (sortField) {
                case 'timestamp': cmp = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(); break;
                case 'ticker': cmp = a.ticker.localeCompare(b.ticker); break;
                case 'qty': cmp = a.qty - b.qty; break;
                case 'notional': cmp = a.notional - b.notional; break;
            }
            return sortDirection === 'desc' ? -cmp : cmp;
        });
        return result;
    }, [trades, agentFilter, tickerFilter, sideFilter, sortField, sortDirection]);

    // Stats
    const totalVolume = filteredTrades.reduce((sum, t) => sum + t.notional, 0);
    const buyCount = filteredTrades.filter(t => t.side === 'BUY').length;
    const sellCount = filteredTrades.filter(t => t.side === 'SELL').length;
    const avgTradeSize = filteredTrades.length > 0 ? totalVolume / filteredTrades.length : 0;

    // Volume by day
    const volumeByDay = useMemo(() => {
        const groups: Record<string, number> = {};
        filteredTrades.forEach(t => {
            const day = new Date(t.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            groups[day] = (groups[day] || 0) + t.notional;
        });
        return Object.entries(groups).map(([date, volume]) => ({ date, volume }));
    }, [filteredTrades]);

    // Ticker distribution
    const tickerDistribution = useMemo(() => {
        const counts: Record<string, number> = {};
        filteredTrades.forEach(t => { counts[t.ticker] = (counts[t.ticker] || 0) + 1; });
        return Object.entries(counts).map(([ticker, count]) => ({ ticker, count })).sort((a, b) => b.count - a.count).slice(0, 6);
    }, [filteredTrades]);

    const sideDistribution = [
        { name: 'BUY', value: buyCount, color: '#10b981' },
        { name: 'SELL', value: sellCount, color: '#ef4444' },
    ];

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortDirection(d => d === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('desc');
        }
    };

    const getAgentName = (id: string) => {
        const agent = leaderboard.find(a => a.competitor_id === id);
        return agent?.name || id;
    };

    return (
        <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard icon={<Activity className="w-5 h-5 text-blue-400" />} label="Total Trades" value={filteredTrades.length.toString()} color="blue" />
                <StatCard icon={<DollarSign className="w-5 h-5 text-purple-400" />} label="Total Volume" value={`$${(totalVolume / 1000).toFixed(1)}K`} color="purple" />
                <StatCard icon={<TrendingUp className="w-5 h-5 text-emerald-400" />} label="Buy Orders" value={buyCount.toString()} color="emerald" />
                <StatCard icon={<TrendingDown className="w-5 h-5 text-red-400" />} label="Sell Orders" value={sellCount.toString()} color="red" />
            </div>

            {/* Filters + Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Filters */}
                <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-5">
                    <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4">Filters</h3>
                    <div className="space-y-4">
                        <FilterSelect label="Agent" value={agentFilter} onChange={setAgentFilter} options={[{ value: 'all', label: 'All Agents' }, ...leaderboard.map(a => ({ value: a.competitor_id, label: getAgentName(a.competitor_id) }))]} />
                        <FilterSelect label="Ticker" value={tickerFilter} onChange={setTickerFilter} options={[{ value: 'all', label: 'All Tickers' }, ...uniqueTickers.map(t => ({ value: t, label: t }))]} />
                        <FilterSelect label="Side" value={sideFilter} onChange={setSideFilter} options={[{ value: 'all', label: 'All' }, { value: 'BUY', label: 'Buy' }, { value: 'SELL', label: 'Sell' }]} />
                    </div>
                    <div className="mt-4 pt-4 border-t border-[var(--color-border-secondary)]">
                        <p className="text-xs text-[var(--color-text-muted)]">Avg Trade Size</p>
                        <p className="text-lg font-bold text-[var(--color-text-primary)]">${avgTradeSize.toFixed(0)}</p>
                    </div>
                </div>

                {/* Volume Over Time */}
                <div className="lg:col-span-2 bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-5">
                    <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4 flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-[var(--color-accent-primary)]" />
                        Trading Volume Over Time
                    </h3>
                    <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={volumeByDay}>
                                <defs>
                                    <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="var(--color-accent-primary)" stopOpacity={0.3} />
                                        <stop offset="100%" stopColor="var(--color-accent-primary)" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="date" stroke="var(--color-text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                                <YAxis stroke="var(--color-text-muted)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                                <Tooltip
                                    formatter={(value: number | undefined) => [value != null ? `$${value.toLocaleString()}` : '$0', 'Volume']}
                                    contentStyle={{ backgroundColor: 'var(--color-bg-primary)', border: '1px solid var(--color-border-secondary)', borderRadius: '8px' }}
                                />
                                <Area type="monotone" dataKey="volume" stroke="var(--color-accent-primary)" strokeWidth={2} fill="url(#volumeGradient)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Ticker Distribution */}
                <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-5">
                    <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4">Most Traded Tickers</h3>
                    <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={tickerDistribution} layout="vertical">
                                <XAxis type="number" stroke="var(--color-text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                                <YAxis type="category" dataKey="ticker" stroke="var(--color-text-muted)" fontSize={11} width={50} tickLine={false} axisLine={false} />
                                <Tooltip contentStyle={{ backgroundColor: 'var(--color-bg-primary)', border: '1px solid var(--color-border-secondary)', borderRadius: '8px' }} />
                                <Bar dataKey="count" fill="var(--color-accent-primary)" radius={[0, 4, 4, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Buy/Sell Ratio */}
                <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-5">
                    <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-4">Buy/Sell Breakdown</h3>
                    <div className="h-48 flex items-center">
                        <div className="w-1/2">
                            <ResponsiveContainer width="100%" height={150}>
                                <PieChart>
                                    <Pie data={sideDistribution} cx="50%" cy="50%" innerRadius={40} outerRadius={60} dataKey="value" paddingAngle={4}>
                                        {sideDistribution.map((entry, idx) => <Cell key={idx} fill={entry.color} />)}
                                    </Pie>
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="w-1/2 space-y-3">
                            <div className="flex items-center gap-3">
                                <div className="w-3 h-3 rounded-full bg-emerald-500" />
                                <div>
                                    <p className="text-xs text-[var(--color-text-muted)]">Buy Orders</p>
                                    <p className="text-lg font-bold text-emerald-400">{buyCount} <span className="text-xs text-[var(--color-text-muted)]">({((buyCount / (buyCount + sellCount)) * 100).toFixed(0)}%)</span></p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="w-3 h-3 rounded-full bg-red-500" />
                                <div>
                                    <p className="text-xs text-[var(--color-text-muted)]">Sell Orders</p>
                                    <p className="text-lg font-bold text-red-400">{sellCount} <span className="text-xs text-[var(--color-text-muted)]">({((sellCount / (buyCount + sellCount)) * 100).toFixed(0)}%)</span></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Trades Table */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] overflow-hidden"
            >
                <div className="p-5 border-b border-[var(--color-border-secondary)]">
                    <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Trade History</h3>
                    <p className="text-xs text-[var(--color-text-muted)]">{filteredTrades.length} trades found</p>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-[var(--color-bg-tertiary)]">
                            <tr>
                                <SortableHeader field="timestamp" current={sortField} direction={sortDirection} onClick={handleSort}>Time</SortableHeader>
                                <th className="text-left py-3 px-4 text-[var(--color-text-muted)] font-medium">Agent</th>
                                <SortableHeader field="ticker" current={sortField} direction={sortDirection} onClick={handleSort}>Ticker</SortableHeader>
                                <th className="text-left py-3 px-4 text-[var(--color-text-muted)] font-medium">Side</th>
                                <SortableHeader field="qty" current={sortField} direction={sortDirection} onClick={handleSort}>Qty</SortableHeader>
                                <th className="text-right py-3 px-4 text-[var(--color-text-muted)] font-medium">Price</th>
                                <SortableHeader field="notional" current={sortField} direction={sortDirection} onClick={handleSort}>Notional</SortableHeader>
                                <th className="text-right py-3 px-4 text-[var(--color-text-muted)] font-medium">Fees</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[var(--color-border-secondary)]">
                            {filteredTrades.slice(0, 50).map((trade, i) => (
                                <tr key={i} className="hover:bg-[var(--color-bg-tertiary)] transition-colors">
                                    <td className="py-3 px-4 text-[var(--color-text-muted)]">
                                        <div className="flex items-center gap-2">
                                            <Clock className="w-3 h-3" />
                                            {new Date(trade.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                    </td>
                                    <td className="py-3 px-4 text-[var(--color-text-primary)]">{getAgentName(trade.competitor_id)}</td>
                                    <td className="py-3 px-4 font-mono font-medium text-[var(--color-text-primary)]">{trade.ticker}</td>
                                    <td className="py-3 px-4">
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${trade.side === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                                            {trade.side}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-[var(--color-text-primary)]">{trade.qty}</td>
                                    <td className="py-3 px-4 text-right font-mono text-[var(--color-text-primary)]">${trade.price.toFixed(2)}</td>
                                    <td className="py-3 px-4 text-right font-mono text-[var(--color-text-primary)]">${trade.notional.toLocaleString()}</td>
                                    <td className="py-3 px-4 text-right font-mono text-[var(--color-text-muted)]">${trade.fees.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {filteredTrades.length > 50 && (
                    <div className="p-4 text-center border-t border-[var(--color-border-secondary)]">
                        <p className="text-sm text-[var(--color-text-muted)]">Showing 50 of {filteredTrades.length} trades</p>
                    </div>
                )}
            </motion.div>
        </div>
    );
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
    const colorClasses: Record<string, string> = { blue: 'bg-blue-500/20', purple: 'bg-purple-500/20', emerald: 'bg-emerald-500/20', red: 'bg-red-500/20' };
    return (
        <div className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-4">
            <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg ${colorClasses[color]} flex items-center justify-center`}>{icon}</div>
                <div>
                    <p className="text-xs text-[var(--color-text-muted)]">{label}</p>
                    <p className="text-lg font-bold text-[var(--color-text-primary)]">{value}</p>
                </div>
            </div>
        </div>
    );
}

function FilterSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: { value: string; label: string }[] }) {
    return (
        <div>
            <label className="text-xs text-[var(--color-text-muted)] mb-1.5 block">{label}</label>
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full bg-[var(--color-bg-tertiary)] text-[var(--color-text-primary)] border border-[var(--color-border-primary)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-primary)]"
            >
                {options.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
        </div>
    );
}

function SortableHeader({ field, current, direction, onClick, children }: { field: SortField; current: SortField; direction: SortDirection; onClick: (f: SortField) => void; children: React.ReactNode }) {
    const isActive = current === field;
    return (
        <th
            className="text-left py-3 px-4 text-[var(--color-text-muted)] font-medium cursor-pointer hover:text-[var(--color-text-primary)] transition-colors"
            onClick={() => onClick(field)}
        >
            <div className="flex items-center gap-1">
                {children}
                {isActive ? (direction === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />) : <ArrowUpDown className="w-3 h-3 opacity-30" />}
            </div>
        </th>
    );
}
