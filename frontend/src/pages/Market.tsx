import { motion } from 'framer-motion';
import { LineChart } from 'lucide-react';
import type { DashboardData } from '../types';

interface MarketPageProps {
    data: DashboardData;
}

export function MarketPage({ data }: MarketPageProps) {
    // Note: Full market data (OHLCV) would need to be added to the data export
    // For now, we show a placeholder with trade locations

    const { trades, leaderboard } = data;

    // Get unique tickers from trades
    const tickers = [...new Set(trades.map(t => t.ticker))].sort();

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-3xl font-bold gradient-text mb-2">Market View</h1>
                <p className="text-[var(--color-text-secondary)]">
                    View market charts and trade markers
                </p>
            </motion.div>

            {/* Coming Soon Notice */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-12 text-center"
            >
                <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] flex items-center justify-center">
                    <LineChart className="w-10 h-10 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-[var(--color-text-primary)] mb-3">
                    Market Charts Coming Soon
                </h2>
                <p className="text-[var(--color-text-secondary)] max-w-lg mx-auto mb-8">
                    Interactive candlestick charts with trade markers will be available once real-time market data is integrated into the dashboard export.
                </p>

                {/* Available Tickers */}
                <div className="max-w-2xl mx-auto">
                    <p className="text-sm text-[var(--color-text-muted)] mb-4">
                        Traded Tickers ({tickers.length})
                    </p>
                    <div className="flex flex-wrap justify-center gap-2">
                        {tickers.map(ticker => (
                            <span
                                key={ticker}
                                className="badge badge-primary font-mono"
                            >
                                {ticker}
                            </span>
                        ))}
                    </div>
                </div>
            </motion.div>

            {/* Trades by Ticker */}
            {tickers.map(ticker => {
                const tickerTrades = trades.filter(t => t.ticker === ticker);

                return (
                    <motion.div
                        key={ticker}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="glass-card p-6"
                    >
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                                {ticker}
                            </h3>
                            <span className="text-sm text-[var(--color-text-muted)]">
                                {tickerTrades.length} trades
                            </span>
                        </div>

                        <table className="data-table">
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
                                            <td className="text-[var(--color-text-secondary)]">
                                                {new Date(trade.timestamp).toLocaleDateString('en-US', {
                                                    month: 'short',
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit',
                                                })}
                                            </td>
                                            <td>{agent?.name || trade.competitor_id}</td>
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
                );
            })}
        </div>
    );
}
