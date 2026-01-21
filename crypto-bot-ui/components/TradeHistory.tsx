'use client';

import { useState, useEffect } from 'react';
import { History, ArrowUp, ArrowDown, CheckCircle, Clock, XCircle, RefreshCw, LogIn } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface Trade {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  price: string;
  qty: string;
  quoteQty: string;
  time: number;
  isMaker: boolean;
}

interface TradeHistoryProps {
  symbol: string;
  onLoginClick?: () => void;
}

export default function TradeHistory({ symbol, onLoginClick }: TradeHistoryProps) {
  const { auth } = useAuth();
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'BUY' | 'SELL'>('all');

  const fetchTrades = async () => {
    if (!auth.isLoggedIn) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/trades?symbol=${symbol}`, {
        headers: {
          'x-api-key': auth.apiKey,
          'x-api-secret': auth.apiSecret,
          'x-testnet': auth.isTestnet.toString(),
        },
      });

      if (!response.ok) throw new Error('İşlem geçmişi alınamadı');

      const data = await response.json();
      setTrades(data.trades || []);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (auth.isLoggedIn) {
      fetchTrades();
    } else {
      setTrades([]);
    }
  }, [auth.isLoggedIn, symbol]);

  const filteredTrades = trades.filter((trade) => {
    if (filter === 'all') return true;
    return trade.side === filter;
  });

  const formatTime = (timestamp: number) => {
    return new Intl.DateTimeFormat('tr-TR', {
      hour: '2-digit',
      minute: '2-digit',
      day: '2-digit',
      month: '2-digit',
    }).format(new Date(timestamp));
  };

  // Not logged in state
  if (!auth.isLoggedIn) {
    return (
      <div className="glass-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <History className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">İşlem Geçmişi</h3>
        </div>

        <div className="text-center py-8">
          <History className="w-12 h-12 mx-auto mb-3 text-gray-500" />
          <p className="text-gray-400 mb-4">İşlem geçmişini görmek için giriş yapın</p>
          {onLoginClick && (
            <button
              onClick={onLoginClick}
              className="inline-flex items-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-all"
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
          <History className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">İşlem Geçmişi</h3>
          {auth.isTestnet && (
            <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">
              Testnet
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            {(['all', 'BUY', 'SELL'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 text-sm rounded-lg transition-colors
                  ${filter === f
                    ? 'bg-purple-600 text-white'
                    : 'bg-[#2a2a4a] text-gray-400 hover:bg-[#3a3a5a]'}`}
              >
                {f === 'all' ? 'Tümü' : f === 'BUY' ? 'Alım' : 'Satım'}
              </button>
            ))}
          </div>
          <button
            onClick={fetchTrades}
            disabled={loading}
            className="p-1.5 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 mb-4 bg-red-500/10 border border-red-500/30 rounded-lg">
          <XCircle className="w-4 h-4 text-red-400" />
          <span className="text-red-400 text-sm">{error}</span>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-gray-400 text-sm border-b border-[#3a3a5a]">
              <th className="text-left py-3 font-medium">Tip</th>
              <th className="text-left py-3 font-medium">Coin</th>
              <th className="text-right py-3 font-medium">Miktar</th>
              <th className="text-right py-3 font-medium">Fiyat</th>
              <th className="text-right py-3 font-medium">Toplam</th>
              <th className="text-right py-3 font-medium">Tarih</th>
              <th className="text-center py-3 font-medium">Durum</th>
            </tr>
          </thead>
          <tbody>
            {filteredTrades.slice(0, 10).map((trade) => (
              <tr
                key={trade.id}
                className="border-b border-[#2a2a4a] hover:bg-[#2a2a4a]/50 transition-colors"
              >
                <td className="py-3">
                  <div className={`flex items-center gap-1 ${trade.side === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                    {trade.side === 'BUY' ? (
                      <ArrowUp className="w-4 h-4" />
                    ) : (
                      <ArrowDown className="w-4 h-4" />
                    )}
                    <span className="font-medium">
                      {trade.side === 'BUY' ? 'AL' : 'SAT'}
                    </span>
                  </div>
                </td>
                <td className="py-3">
                  <span className="text-white font-medium">{trade.symbol.replace('USDT', '')}</span>
                </td>
                <td className="py-3 text-right text-white">
                  {parseFloat(trade.qty).toFixed(6)}
                </td>
                <td className="py-3 text-right text-gray-300">
                  ${parseFloat(trade.price).toLocaleString()}
                </td>
                <td className="py-3 text-right text-white font-medium">
                  ${parseFloat(trade.quoteQty).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
                <td className="py-3 text-right text-gray-400 text-sm">
                  {formatTime(trade.time)}
                </td>
                <td className="py-3">
                  <div className="flex justify-center">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredTrades.length === 0 && !loading && (
        <div className="text-center py-8 text-gray-400">
          <History className="w-8 h-8 mx-auto mb-2 text-gray-500" />
          <p>Henüz işlem bulunmuyor</p>
          <p className="text-sm text-gray-500 mt-1">Bot çalıştığında işlemler burada görünecek</p>
        </div>
      )}

      {loading && (
        <div className="text-center py-8 text-gray-400">
          <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin text-purple-400" />
          <p>Yükleniyor...</p>
        </div>
      )}
    </div>
  );
}
