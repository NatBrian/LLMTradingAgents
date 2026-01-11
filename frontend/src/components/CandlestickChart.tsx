import { useEffect, useRef } from 'react';
import { createChart, ColorType, CandlestickSeries, createSeriesMarkers } from 'lightweight-charts';
import type { IChartApi, CandlestickData, Time, ISeriesApi, SeriesMarker, CandlestickSeriesOptions, ISeriesMarkersPluginApi } from 'lightweight-charts';
import type { OHLCVBar, TradeRecord } from '../types';

interface CandlestickChartProps {
    ticker: string;
    data: OHLCVBar[];
    trades?: TradeRecord[];
    height?: number;
}

export function CandlestickChart({ ticker, data, trades = [], height = 400 }: CandlestickChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
    const markersRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current || data.length === 0) {
            return;
        }

        // Create chart with dark theme
        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: 'rgba(255, 255, 255, 0.7)',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
            },
            crosshair: {
                vertLine: {
                    color: 'rgba(139, 92, 246, 0.5)',
                    labelBackgroundColor: 'rgba(139, 92, 246, 0.9)',
                },
                horzLine: {
                    color: 'rgba(139, 92, 246, 0.5)',
                    labelBackgroundColor: 'rgba(139, 92, 246, 0.9)',
                },
            },
            width: chartContainerRef.current.clientWidth,
            height: height,
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                timeVisible: true,
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
            },
        });

        chartRef.current = chart;

        // Add candlestick series with v5 API
        const seriesOptions: Partial<CandlestickSeriesOptions> = {
            upColor: '#22c55e',
            downColor: '#ef4444',
            borderUpColor: '#22c55e',
            borderDownColor: '#ef4444',
            wickUpColor: '#22c55e',
            wickDownColor: '#ef4444',
        };

        const candlestickSeries = chart.addSeries(CandlestickSeries, seriesOptions);

        candlestickSeriesRef.current = candlestickSeries;

        // Convert data to lightweight-charts format
        const chartData: CandlestickData<Time>[] = data.map(bar => ({
            time: bar.date as Time,
            open: bar.open,
            high: bar.high,
            low: bar.low,
            close: bar.close,
        }));

        candlestickSeries.setData(chartData);

        // Add trade markers using v5 plugin API
        if (trades.length > 0) {
            const tickerTrades = trades.filter(t => t.ticker === ticker);
            if (tickerTrades.length > 0) {
                const markers: SeriesMarker<Time>[] = tickerTrades.map(trade => {
                    const tradeDate = trade.timestamp.split('T')[0];
                    return {
                        time: tradeDate as Time,
                        position: trade.side === 'BUY' ? 'belowBar' as const : 'aboveBar' as const,
                        color: trade.side === 'BUY' ? '#22c55e' : '#ef4444',
                        shape: trade.side === 'BUY' ? 'arrowUp' as const : 'arrowDown' as const,
                        text: `${trade.side} ${trade.qty}`,
                    };
                });

                // Create markers plugin attached to series
                const markersPlugin = createSeriesMarkers(candlestickSeries, markers);
                markersRef.current = markersPlugin;
            }
        }

        // Fit content
        chart.timeScale().fitContent();

        // Handle resize
        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
            chartRef.current = null;
            candlestickSeriesRef.current = null;
            markersRef.current = null;
        };
    }, [data, trades, ticker, height]);

    if (data.length === 0) {
        return (
            <div
                className="flex items-center justify-center text-[var(--color-text-muted)]"
                style={{ height }}
            >
                No market data available for {ticker}
            </div>
        );
    }

    return (
        <div className="relative">
            <div ref={chartContainerRef} style={{ height }} />
        </div>
    );
}
