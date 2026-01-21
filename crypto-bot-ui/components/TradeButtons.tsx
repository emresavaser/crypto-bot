'use client';

import { useState } from 'react';
import { ArrowUpCircle, ArrowDownCircle, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { useBinanceTrade } from '@/hooks/useBinanceData';

interface TradeButtonsProps {
  symbol?: string;
  currentPrice: number;
  onTradeComplete?: () => void;
}

export default function TradeButtons({
  symbol = 'BTCUSDT',
  currentPrice = 0,
  onTradeComplete
}: TradeButtonsProps) {
  const [amount, setAmount] = useState<string>('0.002');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [limitPrice, setLimitPrice] = useState<string>('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { executeTrade, loading, error } = useBinanceTrade();

  const handleTrade = async (side: 'BUY' | 'SELL') => {
    setMessage(null);

    try {
      const params: {
        symbol: string;
        side: 'BUY' | 'SELL';
        type: 'MARKET' | 'LIMIT';
        quantity: number;
        price?: number;
      } = {
        symbol,
        side,
        type: orderType,
        quantity: parseFloat(amount),
      };

      if (orderType === 'LIMIT' && limitPrice) {
        params.price = parseFloat(limitPrice);
      }

      const result = await executeTrade(params);

      setMessage({
        type: 'success',
        text: `${side === 'BUY' ? 'Alım' : 'Satım'} emri başarılı! Order ID: ${result.order.orderId}`,
      });

      onTradeComplete?.();
    } catch (err) {
      setMessage({
        type: 'error',
        text: (err as Error).message || 'İşlem başarısız',
      });
    }
  };

  const total = parseFloat(amount || '0') * (orderType === 'LIMIT' && limitPrice ? parseFloat(limitPrice) : currentPrice);
  const baseAsset = symbol.replace('USDT', '');

  return (
    <div className="glass-card rounded-2xl p-5">
      <h3 className="text-lg font-semibold text-white mb-4">Hızlı İşlem</h3>

      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setOrderType('MARKET')}
          className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-all
            ${orderType === 'MARKET'
              ? 'bg-gradient-to-r from-purple-600 to-violet-500 text-white shadow-md shadow-purple-500/20'
              : 'inner-card text-gray-400 hover:text-white hover:bg-white/5'}`}
        >
          Market
        </button>
        <button
          onClick={() => setOrderType('LIMIT')}
          className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-all
            ${orderType === 'LIMIT'
              ? 'bg-gradient-to-r from-purple-600 to-violet-500 text-white shadow-md shadow-purple-500/20'
              : 'inner-card text-gray-400 hover:text-white hover:bg-white/5'}`}
        >
          Limit
        </button>
      </div>

      <div className="space-y-4">
        <div>
          <label className="text-gray-400 text-sm block mb-2">Miktar ({baseAsset})</label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="w-full inner-card rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
            step="0.001"
            min="0"
          />
        </div>

        {orderType === 'LIMIT' && (
          <div>
            <label className="text-gray-400 text-sm block mb-2">Limit Fiyat (USDT)</label>
            <input
              type="number"
              value={limitPrice}
              onChange={(e) => setLimitPrice(e.target.value)}
              placeholder={currentPrice.toString()}
              className="w-full inner-card rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all placeholder:text-gray-600"
              step="0.01"
              min="0"
            />
          </div>
        )}

        <div className="flex gap-2">
          {['25%', '50%', '75%', '100%'].map((pct) => (
            <button
              key={pct}
              onClick={() => {
                const maxAmount = 0.01; // Example max amount
                setAmount((parseFloat(pct) / 100 * maxAmount).toFixed(6));
              }}
              className="flex-1 py-2 text-xs rounded-lg inner-card text-gray-400 hover:text-white hover:bg-white/5 transition-all"
            >
              {pct}
            </button>
          ))}
        </div>

        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-white/10 rounded-xl p-3 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Fiyat</span>
            <span className="text-white font-medium">
              ${(orderType === 'LIMIT' && limitPrice ? parseFloat(limitPrice) : currentPrice).toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Toplam</span>
            <span className="text-white font-medium">
              ${total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT
            </span>
          </div>
        </div>

        {message && (
          <div className={`flex items-center gap-2 p-3 rounded-lg ${
            message.type === 'success'
              ? 'bg-green-500/10 border border-green-500/30'
              : 'bg-red-500/10 border border-red-500/30'
          }`}>
            {message.type === 'success' ? (
              <CheckCircle className="w-4 h-4 text-green-400" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-400" />
            )}
            <span className={message.type === 'success' ? 'text-green-400' : 'text-red-400'} style={{ fontSize: '0.875rem' }}>
              {message.text}
            </span>
          </div>
        )}

        {error && !message && (
          <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span className="text-red-400 text-sm">{error}</span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => handleTrade('BUY')}
            disabled={loading || parseFloat(amount) <= 0}
            className="btn-modern flex items-center justify-center gap-2 bg-gradient-to-r from-green-600 to-emerald-500 hover:from-green-700 hover:to-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3.5 rounded-xl font-semibold transition-all shadow-lg shadow-green-500/20 disabled:shadow-none"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <ArrowUpCircle className="w-5 h-5" />
            )}
            AL
          </button>
          <button
            onClick={() => handleTrade('SELL')}
            disabled={loading || parseFloat(amount) <= 0}
            className="btn-modern flex items-center justify-center gap-2 bg-gradient-to-r from-red-600 to-rose-500 hover:from-red-700 hover:to-rose-600 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3.5 rounded-xl font-semibold transition-all shadow-lg shadow-red-500/20 disabled:shadow-none"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <ArrowDownCircle className="w-5 h-5" />
            )}
            SAT
          </button>
        </div>

        <p className="text-xs text-gray-500 text-center">
          API anahtarı olmadan işlem yapamazsınız. .env.local dosyasını yapılandırın.
        </p>
      </div>
    </div>
  );
}
