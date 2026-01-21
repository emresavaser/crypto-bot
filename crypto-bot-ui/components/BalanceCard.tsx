'use client';

import { useEffect, useState } from 'react';
import { Wallet, TrendingUp, RefreshCw, AlertCircle, LogIn } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useBinancePrice } from '@/hooks/useBinanceData';

interface Balance {
  asset: string;
  free: string;
  locked: string;
}

interface BalanceWithValue extends Balance {
  valueUSD: number;
}

interface BalanceCardProps {
  onLoginClick?: () => void;
}

export default function BalanceCard({ onLoginClick }: BalanceCardProps) {
  const { auth } = useAuth();
  const { price: btcPrice } = useBinancePrice('BTCUSDT');
  const { price: ethPrice } = useBinancePrice('ETHUSDT');

  const [balances, setBalances] = useState<Balance[]>([]);
  const [balancesWithValue, setBalancesWithValue] = useState<BalanceWithValue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBalances = async () => {
    if (!auth.isLoggedIn) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/balance', {
        headers: {
          'x-api-key': auth.apiKey,
          'x-api-secret': auth.apiSecret,
          'x-testnet': auth.isTestnet.toString(),
        },
      });

      if (!response.ok) throw new Error('Failed to fetch balances');

      const data = await response.json();
      setBalances(data.balances || []);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (auth.isLoggedIn) {
      fetchBalances();
      const interval = setInterval(fetchBalances, 30000);
      return () => clearInterval(interval);
    } else {
      setBalances([]);
      setBalancesWithValue([]);
    }
  }, [auth.isLoggedIn]);

  useEffect(() => {
    if (balances.length > 0) {
      const updated = balances.map((balance) => {
        let valueUSD = 0;
        const amount = parseFloat(balance.free) + parseFloat(balance.locked);

        if (['USDT', 'BUSD', 'USDC'].includes(balance.asset)) {
          valueUSD = amount;
        } else if (balance.asset === 'BTC' && btcPrice) {
          valueUSD = amount * btcPrice.price;
        } else if (balance.asset === 'ETH' && ethPrice) {
          valueUSD = amount * ethPrice.price;
        }

        return { ...balance, valueUSD };
      });

      updated.sort((a, b) => b.valueUSD - a.valueUSD);
      setBalancesWithValue(updated);
    }
  }, [balances, btcPrice, ethPrice]);

  const totalValue = balancesWithValue.reduce((sum, b) => sum + b.valueUSD, 0);

  const getAssetColor = (asset: string) => {
    const colors: Record<string, string> = {
      BTC: 'bg-orange-500/20 text-orange-400',
      ETH: 'bg-blue-500/20 text-blue-400',
      USDT: 'bg-green-500/20 text-green-400',
      BUSD: 'bg-green-500/20 text-green-400',
      USDC: 'bg-green-500/20 text-green-400',
      BNB: 'bg-yellow-500/20 text-yellow-400',
    };
    return colors[asset] || 'bg-purple-500/20 text-purple-400';
  };

  // Not logged in state
  if (!auth.isLoggedIn) {
    return (
      <div className="glass-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Wallet className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Bakiye</h3>
        </div>

        <div className="text-center py-6">
          <Wallet className="w-12 h-12 mx-auto mb-3 text-gray-500" />
          <p className="text-gray-400 mb-4">Bakiyenizi görmek için giriş yapın</p>
          {onLoginClick && (
            <button
              onClick={onLoginClick}
              className="btn-modern inline-flex items-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-4 py-2.5 rounded-xl font-medium transition-all shadow-lg shadow-purple-500/20"
            >
              <LogIn className="w-4 h-4" />
              Giriş Yap
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Wallet className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Bakiye</h3>
          {auth.isTestnet && (
            <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">
              Testnet
            </span>
          )}
        </div>
        <button
          onClick={fetchBalances}
          disabled={loading}
          className="p-1.5 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 mb-4 bg-red-500/10 border border-red-500/30 rounded-lg">
          <AlertCircle className="w-4 h-4 text-red-400" />
          <span className="text-red-400 text-sm">{error}</span>
        </div>
      )}

      <div className="mb-4">
        <p className="text-gray-400 text-sm">Toplam Değer</p>
        <p className="text-3xl font-bold text-white">
          ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </p>
        <div className="flex items-center gap-1 mt-1">
          <TrendingUp className="w-4 h-4 text-green-500" />
          <span className="text-green-500 text-sm">
            Binance {auth.isTestnet ? 'Testnet' : 'Hesabı'}
          </span>
        </div>
      </div>

      <div className="space-y-3 max-h-64 overflow-y-auto">
        {balancesWithValue.slice(0, 10).map((balance) => (
          <div
            key={balance.asset}
            className="flex justify-between items-center p-3 inner-card rounded-xl hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${getAssetColor(balance.asset)}`}>
                {balance.asset.charAt(0)}
              </div>
              <div>
                <p className="text-white font-medium">{balance.asset}</p>
                <p className="text-gray-400 text-sm">
                  {parseFloat(balance.free).toFixed(6)}
                  {parseFloat(balance.locked) > 0 && (
                    <span className="text-yellow-400 ml-1">
                      (+{parseFloat(balance.locked).toFixed(6)} kilitli)
                    </span>
                  )}
                </p>
              </div>
            </div>
            {balance.valueUSD > 0 && (
              <p className="text-white font-semibold">
                ${balance.valueUSD.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            )}
          </div>
        ))}

        {balancesWithValue.length === 0 && !loading && (
          <div className="text-center py-4 text-gray-400">
            Bakiye bulunamadı
          </div>
        )}

        {loading && balancesWithValue.length === 0 && (
          <div className="text-center py-4 text-gray-400">
            Yükleniyor...
          </div>
        )}
      </div>
    </div>
  );
}
