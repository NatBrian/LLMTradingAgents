import { useState } from 'react';
import { motion } from 'framer-motion';
import { LineChart, TrendingUp, TrendingDown } from 'lucide-react';
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

    // Check if we have market data
    const hasMarketData = marketData && Object.keys(marketData).length > 0;
    const selectedData = hasMarketData && selectedTicker ? marketData[selectedTicker] : undefined;

    // Calculate price change for selected ticker
    const getPriceChange = (ticker: string) => {
        if (!marketData || !marketData[ticker] || marketData[ticker].length < 2) return null;
        const bars = marketData[ticker];
        const latest = bars[bars.length - 1];
        const previous = bars[bars.length - 2];
        const change = ((latest.close - previous.close) / previous.close) * 100;
        return { change, latest: latest.close };
    };

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-3xl font-bold gradient-text mb-2">Market View</h1>
                <p className="text-[var(--color-text-secondary)]">
                    Interactive charts with trade markers
                </p>
            </motion.div>

            {!hasMarketData ? (
                /* Coming Soon Notice - shown when no market data */
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
                        Run the data export script to fetch market data for traded tickers.
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
            ) : (
                <>
                    {/* Ticker Selection */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex flex-wrap gap-3"
                    >
                        {tickers.map(ticker => {
                            const priceInfo = getPriceChange(ticker);
                            const isSelected = ticker === selectedTicker;

                            return (
                                <button
                                    key={ticker}
                                    onClick={() => setSelectedTicker(ticker)}
                                    className={`
                                        px-4 py-3 rounded-xl font-medium transition-all duration-200
                                        ${isSelected
                                            ? 'bg-gradient-to-r from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] text-white shadow-lg shadow-purple-500/20'
                                            : 'glass-card hover:bg-white/10'
                                        }
                                    `}
                                >
                                    <div className="flex items-center gap-3">
                                        <span className="font-mono font-bold">{ticker}</span>
                                        {priceInfo && (
                                            <div className="flex items-center gap-1 text-sm">
                                                <span className="opacity-80">${priceInfo.latest.toFixed(2)}</span>
                                                <span className={priceInfo.change >= 0 ? 'text-green-400' : 'text-red-400'}>
                                                    {priceInfo.change >= 0 ? (
                                                        <TrendingUp className="w-3 h-3 inline" />
                                                    ) : (
                                                        <TrendingDown className="w-3 h-3 inline" />
                                                    )}
                                                    {priceInfo.change >= 0 ? '+' : ''}{priceInfo.change.toFixed(2)}%
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </button>
                            );
                        })}
                    </motion.div>

                    {/* Candlestick Chart */}
                    {selectedTicker && selectedData && (
                        <motion.div
                            key={selectedTicker}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="glass-card p-6"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xl font-bold text-[var(--color-text-primary)]">
                                    {selectedTicker} Price Chart
                                </h2>
                                <span className="text-sm text-[var(--color-text-muted)]">
                                    {selectedData.length} days
                                </span>
                            </div>
                            <CandlestickChart
                                ticker={selectedTicker}
                                data={selectedData}
                                trades={trades}
                                height={450}
                            />
                        </motion.div>
                    )}
                </>
            )}

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
