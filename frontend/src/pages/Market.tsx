import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, TrendingUp, TrendingDown, Activity, Users, ChevronDown, ChevronRight } from 'lucide-react';
import { CandlestickChart } from '../components/CandlestickChart';
import type { DashboardData } from '../types';

interface MarketPageProps {
    data: DashboardData;
}

export function MarketPage({ data }: MarketPageProps) {
    const { trades, leaderboard, marketData } = data;

    // Get unique tickers from trades
    const tickers = [...new Set(trades.map(t => t.ticker))].sort();

    // Selected ticker state
    const [selectedTicker, setSelectedTicker] = useState<string>(tickers[0] || '');
    const [expandedTickers, setExpandedTickers] = useState<Set<string>>(new Set([tickers[0]]));

    // Check if we have market data
    const hasMarketData = marketData && Object.keys(marketData).length > 0;
    const selectedData = hasMarketData && selectedTicker ? marketData[selectedTicker] : undefined;

    // Market summary stats
    const marketStats = useMemo(() => {
        const totalVolume = trades.reduce((sum, t) => sum + t.notional, 0);
        const uniqueAgents = new Set(trades.map(t => t.competitor_id)).size;
        const buyCount = trades.filter(t => t.side === 'BUY').length;
        const sellCount = trades.filter(t => t.side === 'SELL').length;

        return { totalVolume, uniqueAgents, buyCount, sellCount, totalTrades: trades.length };
    }, [trades]);

    // Get ticker stats
    const getTickerStats = (ticker: string) => {
        const tickerTrades = trades.filter(t => t.ticker === ticker);
        const volume = tickerTrades.reduce((sum, t) => sum + t.notional, 0);
        const buyCount = tickerTrades.filter(t => t.side === 'BUY').length;
        const sellCount = tickerTrades.filter(t => t.side === 'SELL').length;
        const agents = new Set(tickerTrades.map(t => t.competitor_id)).size;

        // Price change from market data
        let priceChange: { change: number; latest: number } | null = null;
        if (marketData && marketData[ticker] && marketData[ticker].length >= 2) {
            const bars = marketData[ticker];
            const latest = bars[bars.length - 1];
            const previous = bars[bars.length - 2];
            priceChange = {
                change: ((latest.close - previous.close) / previous.close) * 100,
                latest: latest.close
            };
        }

        return { volume, buyCount, sellCount, agents, tradeCount: tickerTrades.length, priceChange };
    };

    const toggleExpanded = (ticker: string) => {
        const newExpanded = new Set(expandedTickers);
        if (newExpanded.has(ticker)) {
            newExpanded.delete(ticker);
        } else {
            newExpanded.add(ticker);
        }
        setExpandedTickers(newExpanded);
    };

    const formatCurrency = (value: number) => {
        if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
        if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
        return `$${value.toFixed(0)}`;
    };

    return (
        <div className="space-y-6">
            {/* Market Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-4"
                >
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-[var(--color-accent-primary)]/20 flex items-center justify-center">
                            <Activity className="w-5 h-5 text-[var(--color-accent-primary)]" />
                        </div>
                        <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Total Volume</p>
                            <p className="text-lg font-bold text-[var(--color-text-primary)]">
                                {formatCurrency(marketStats.totalVolume)}
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
                        <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                            <TrendingUp className="w-5 h-5 text-emerald-400" />
                        </div>
                        <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Buy Orders</p>
                            <p className="text-lg font-bold text-emerald-400">{marketStats.buyCount}</p>
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
                        <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                            <TrendingDown className="w-5 h-5 text-red-400" />
                        </div>
                        <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Sell Orders</p>
                            <p className="text-lg font-bold text-red-400">{marketStats.sellCount}</p>
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
                        <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                            <Users className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Active Agents</p>
                            <p className="text-lg font-bold text-[var(--color-text-primary)]">{marketStats.uniqueAgents}</p>
                        </div>
                    </div>
                </motion.div>
            </div>

            {!hasMarketData ? (
                /* Coming Soon Notice */
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] p-12 text-center"
                >
                    <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] flex items-center justify-center">
                        <LineChart className="w-10 h-10 text-white" />
                    </div>
                    <h2 className="text-2xl font-bold text-[var(--color-text-primary)] mb-3">
                        Candlestick Charts
                    </h2>
                    <p className="text-[var(--color-text-muted)] max-w-lg mx-auto mb-6">
                        Run <code className="text-[var(--color-accent-primary)] bg-[var(--color-bg-tertiary)] px-2 py-0.5 rounded">export_data.py</code> with yfinance to fetch OHLCV data.
                    </p>
                </motion.div>
            ) : (
                /* Chart Section */
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] overflow-hidden"
                >
                    {/* Ticker Tabs */}
                    <div className="flex overflow-x-auto border-b border-[var(--color-border-secondary)]">
                        {tickers.map(ticker => {
                            const stats = getTickerStats(ticker);
                            const isSelected = ticker === selectedTicker;

                            return (
                                <button
                                    key={ticker}
                                    onClick={() => setSelectedTicker(ticker)}
                                    className={`flex-shrink-0 px-6 py-4 border-b-2 transition-colors ${isSelected
                                        ? 'border-[var(--color-accent-primary)] bg-[var(--color-bg-tertiary)]'
                                        : 'border-transparent hover:bg-[var(--color-bg-tertiary)]'
                                        }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <span className={`font-mono font-bold ${isSelected ? 'text-[var(--color-accent-primary)]' : 'text-[var(--color-text-primary)]'}`}>
                                            {ticker}
                                        </span>
                                        {stats.priceChange && (
                                            <span className={`text-sm ${stats.priceChange.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {stats.priceChange.change >= 0 ? '+' : ''}{stats.priceChange.change.toFixed(2)}%
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-xs text-[var(--color-text-muted)] mt-1">
                                        {stats.tradeCount} trades
                                    </div>
                                </button>
                            );
                        })}
                    </div>

                    {/* Chart */}
                    {selectedTicker && selectedData && (
                        <div className="p-6">
                            <CandlestickChart
                                ticker={selectedTicker}
                                data={selectedData}
                                trades={trades}
                                height={450}
                            />
                        </div>
                    )}
                </motion.div>
            )}

            {/* Trades by Ticker - Collapsible */}
            <div className="space-y-3">
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Trades by Ticker</h2>

                {tickers.map(ticker => {
                    const tickerTrades = trades.filter(t => t.ticker === ticker);
                    const stats = getTickerStats(ticker);
                    const isExpanded = expandedTickers.has(ticker);

                    return (
                        <motion.div
                            key={ticker}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-[var(--color-bg-secondary)] rounded-xl border border-[var(--color-border-secondary)] overflow-hidden"
                        >
                            {/* Header - Clickable */}
                            <button
                                onClick={() => toggleExpanded(ticker)}
                                className="w-full flex items-center justify-between p-4 hover:bg-[var(--color-bg-tertiary)] transition-colors"
                            >
                                <div className="flex items-center gap-4">
                                    {isExpanded ? (
                                        <ChevronDown className="w-5 h-5 text-[var(--color-text-muted)]" />
                                    ) : (
                                        <ChevronRight className="w-5 h-5 text-[var(--color-text-muted)]" />
                                    )}
                                    <span className="font-mono font-bold text-[var(--color-text-primary)]">{ticker}</span>
                                    {stats.priceChange && (
                                        <span className={`text-sm ${stats.priceChange.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                            ${stats.priceChange.latest.toFixed(2)} ({stats.priceChange.change >= 0 ? '+' : ''}{stats.priceChange.change.toFixed(2)}%)
                                        </span>
                                    )}
                                </div>
                                <div className="flex items-center gap-6 text-sm">
                                    <span className="text-[var(--color-text-muted)]">
                                        {stats.tradeCount} trades
                                    </span>
                                    <span className="text-[var(--color-text-muted)]">
                                        Vol: {formatCurrency(stats.volume)}
                                    </span>
                                    <div className="flex items-center gap-2">
                                        <span className="text-emerald-400">{stats.buyCount} buy</span>
                                        <span className="text-[var(--color-text-muted)]">/</span>
                                        <span className="text-red-400">{stats.sellCount} sell</span>
                                    </div>
                                </div>
                            </button>

                            {/* Collapsible Content */}
                            <AnimatePresence>
                                {isExpanded && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="overflow-hidden border-t border-[var(--color-border-secondary)]"
                                    >
                                        <div className="p-4 overflow-x-auto">
                                            <table className="data-table w-full">
                                                <thead>
                                                    <tr>
                                                        <th>Time</th>
                                                        <th>Agent</th>
                                                        <th>Side</th>
                                                        <th>Qty</th>
                                                        <th>Price</th>
                                                        <th>Notional</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {tickerTrades.map((trade, index) => {
                                                        const agent = leaderboard.find(a => a.competitor_id === trade.competitor_id);
                                                        return (
                                                            <tr key={index}>
                                                                <td className="text-[var(--color-text-muted)]">
                                                                    {new Date(trade.timestamp).toLocaleDateString('en-US', {
                                                                        month: 'short',
                                                                        day: 'numeric',
                                                                        hour: '2-digit',
                                                                        minute: '2-digit',
                                                                    })}
                                                                </td>
                                                                <td>{agent?.name || trade.competitor_id}</td>
                                                                <td>
                                                                    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${trade.side === 'BUY'
                                                                        ? 'bg-emerald-500/20 text-emerald-400'
                                                                        : 'bg-red-500/20 text-red-400'
                                                                        }`}>
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
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
}
