'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

interface KlineData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TickerData {
  symbol: string;
  price: number;
  priceChange: number;
  priceChangePercent: number;
  high: number;
  low: number;
  volume: number;
}

interface UseBinanceWebSocketOptions {
  symbol: string;
  interval?: string;
  onKline?: (kline: KlineData) => void;
  onTicker?: (ticker: TickerData) => void;
}

export function useBinanceWebSocket({
  symbol,
  interval = '1m',
  onKline,
  onTicker,
}: UseBinanceWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastPrice, setLastPrice] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  // Store callbacks in refs to avoid reconnection on callback changes
  const onKlineRef = useRef(onKline);
  const onTickerRef = useRef(onTicker);

  useEffect(() => {
    onKlineRef.current = onKline;
    onTickerRef.current = onTicker;
  }, [onKline, onTicker]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null; // Prevent reconnect on intentional close
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return;

    const symbolLower = symbol.toLowerCase();
    const streams = [
      `${symbolLower}@kline_${interval}`,
      `${symbolLower}@ticker`,
    ];

    const wsUrl = `wss://stream.binance.com:9443/stream?streams=${streams.join('/')}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (!mountedRef.current) {
          ws.close();
          return;
        }
        console.log('Binance WebSocket connected');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const message = JSON.parse(event.data);
          const { stream, data } = message;

          if (stream?.includes('@kline_')) {
            const kline = data.k;
            const klineData: KlineData = {
              time: Math.floor(kline.t / 1000),
              open: parseFloat(kline.o),
              high: parseFloat(kline.h),
              low: parseFloat(kline.l),
              close: parseFloat(kline.c),
              volume: parseFloat(kline.v),
            };
            setLastPrice(klineData.close);
            onKlineRef.current?.(klineData);
          }

          if (stream?.includes('@ticker')) {
            const tickerData: TickerData = {
              symbol: data.s,
              price: parseFloat(data.c),
              priceChange: parseFloat(data.p),
              priceChangePercent: parseFloat(data.P),
              high: parseFloat(data.h),
              low: parseFloat(data.l),
              volume: parseFloat(data.v),
            };
            setLastPrice(tickerData.price);
            onTickerRef.current?.(tickerData);
          }
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      ws.onerror = () => {
        // Error is logged via onclose, no need to log here
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;

        console.log('Binance WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          if (mountedRef.current) {
            connect();
          }
        }, 5000);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('WebSocket connection error:', error);
    }
  }, [symbol, interval]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastPrice,
    reconnect: connect,
    disconnect,
  };
}

export default useBinanceWebSocket;
