'use client';

import { useState, useEffect, useCallback } from 'react';

interface PriceData {
  symbol: string;
  price: number;
  priceChange: number;
  priceChangePercent: number;
  high: number;
  low: number;
  volume: number;
  quoteVolume: number;
}

interface Balance {
  asset: string;
  free: string;
  locked: string;
}

interface KlineData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export function useBinancePrice(symbol: string) {
  const [price, setPrice] = useState<PriceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPrice = useCallback(async () => {
    try {
      const response = await fetch(`/api/price?symbol=${symbol}`);
      if (!response.ok) throw new Error('Failed to fetch price');
      const data = await response.json();
      setPrice(data);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchPrice();
    const interval = setInterval(fetchPrice, 15000); // Update every 15 seconds (reduced frequency)
    return () => clearInterval(interval);
  }, [fetchPrice]);

  return { price, loading, error, refetch: fetchPrice };
}

export function useBinanceKlines(symbol: string, interval: string = '1h', limit: number = 100) {
  const [klines, setKlines] = useState<KlineData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchKlines = useCallback(async () => {
    try {
      const response = await fetch(
        `/api/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`
      );
      if (!response.ok) throw new Error('Failed to fetch klines');
      const data = await response.json();
      setKlines(data);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [symbol, interval, limit]);

  useEffect(() => {
    fetchKlines();
  }, [fetchKlines]);

  return { klines, loading, error, refetch: fetchKlines };
}

export function useBinanceBalance() {
  const [balances, setBalances] = useState<Balance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMock, setIsMock] = useState(false);

  const fetchBalances = useCallback(async () => {
    try {
      const response = await fetch('/api/balance');
      if (!response.ok) throw new Error('Failed to fetch balances');
      const data = await response.json();
      setBalances(data.balances);
      setIsMock(data.mock || false);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBalances();
    const interval = setInterval(fetchBalances, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, [fetchBalances]);

  return { balances, loading, error, isMock, refetch: fetchBalances };
}

export function useBinanceTrade() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeTrade = useCallback(async (params: {
    symbol: string;
    side: 'BUY' | 'SELL';
    type: 'MARKET' | 'LIMIT';
    quantity: number;
    price?: number;
  }) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/trade', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Trade failed');
      }

      return data;
    } catch (err) {
      setError((err as Error).message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { executeTrade, loading, error };
}
