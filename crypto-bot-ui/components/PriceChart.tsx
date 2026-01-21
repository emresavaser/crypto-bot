'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { createChart, ColorType, CandlestickSeries, Time } from 'lightweight-charts';
import { useBinanceKlines } from '@/hooks/useBinanceData';
import useBinanceWebSocket from '@/hooks/useBinanceWebSocket';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';

interface PriceChartProps {
  symbol?: string;
  onPriceUpdate?: (price: number) => void;
}

type IntervalType = '1m' | '5m' | '15m' | '1h' | '4h' | '1d';

const INTERVALS: { label: string; value: IntervalType }[] = [
  { label: '1m', value: '1m' },
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
  { label: '1H', value: '1h' },
  { label: '4H', value: '4h' },
  { label: '1D', value: '1d' },
];

export default function PriceChart({ symbol = 'BTCUSDT', onPriceUpdate }: PriceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const seriesRef = useRef<ReturnType<ReturnType<typeof createChart>['addSeries']> | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [priceChange, setPriceChange] = useState<number>(0);
  const [interval, setInterval] = useState<IntervalType>('1h');

  const { klines, loading, refetch } = useBinanceKlines(symbol, interval, 100);

  const handleKlineUpdate = useCallback((kline: {
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
  }) => {
    if (seriesRef.current) {
      seriesRef.current.update({
        time: kline.time as Time,
        open: kline.open,
        high: kline.high,
        low: kline.low,
        close: kline.close,
      });
    }
    setCurrentPrice(kline.close);
    onPriceUpdate?.(kline.close);
  }, [onPriceUpdate]);

  const handleTickerUpdate = useCallback((ticker: {
    price: number;
    priceChangePercent: number;
  }) => {
    setCurrentPrice(ticker.price);
    setPriceChange(ticker.priceChangePercent);
    onPriceUpdate?.(ticker.price);
  }, [onPriceUpdate]);

  const { isConnected } = useBinanceWebSocket({
    symbol,
    interval: interval === '1d' ? '1d' : interval,
    onKline: handleKlineUpdate,
    onTicker: handleTickerUpdate,
  });

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a2e' },
        textColor: '#e0e0e0',
      },
      grid: {
        vertLines: { color: '#2a2a4a' },
        horzLines: { color: '#2a2a4a' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      timeScale: {
        borderColor: '#3a3a5a',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#3a3a5a',
      },
      crosshair: {
        mode: 1,
      },
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderDownColor: '#ef4444',
      borderUpColor: '#22c55e',
      wickDownColor: '#ef4444',
      wickUpColor: '#22c55e',
    });

    chartRef.current = chart;
    seriesRef.current = candlestickSeries;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // Update chart data when klines change
  useEffect(() => {
    if (seriesRef.current && klines.length > 0) {
      const formattedData = klines.map(k => ({
        time: k.time as Time,
        open: k.open,
        high: k.high,
        low: k.low,
        close: k.close,
      }));

      seriesRef.current.setData(formattedData);

      const lastKline = klines[klines.length - 1];
      const firstKline = klines[0];
      setCurrentPrice(lastKline.close);
      setPriceChange(((lastKline.close - firstKline.open) / firstKline.open) * 100);
    }
  }, [klines]);

  const handleIntervalChange = (newInterval: IntervalType) => {
    setInterval(newInterval);
  };

  const displaySymbol = `${symbol.replace('USDT', '')}/USDT`;

  return (
    <div className="glass-card rounded-2xl p-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white">{displaySymbol}</h2>
            {isConnected ? (
              <Wifi className="w-4 h-4 text-green-400" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-400" />
            )}
            {loading && <RefreshCw className="w-4 h-4 text-gray-400 animate-spin" />}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-2xl font-semibold text-white">
              {currentPrice > 0
                ? `$${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : loading ? 'Yükleniyor...' : '$0,00'}
            </span>
            <span className={`text-sm font-medium ${priceChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          {INTERVALS.map((int) => (
            <button
              key={int.value}
              onClick={() => handleIntervalChange(int.value)}
              className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                interval === int.value
                  ? 'bg-purple-600 text-white'
                  : 'bg-[#2a2a4a] text-gray-300 hover:bg-[#3a3a5a]'
              }`}
            >
              {int.label}
            </button>
          ))}
          <button
            onClick={() => refetch()}
            className="px-3 py-1 text-sm rounded-lg bg-[#2a2a4a] text-gray-300 hover:bg-[#3a3a5a] transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
}
