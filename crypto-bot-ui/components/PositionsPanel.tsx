'use client';

import { TrendingUp, TrendingDown, Wallet, RefreshCw } from 'lucide-react';
import { useBot } from '@/contexts/BotContext';
import { useAuth } from '@/contexts/AuthContext';

export default function PositionsPanel() {
  const { auth } = useAuth();
  const { positions, stats, isConnected } = useBot();

  if (!auth.isLoggedIn) {
    return (
      <div className="glass-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Wallet className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Açık Pozisyonlar</h3>
        </div>
        <div className="text-center py-8">
          <Wallet className="w-10 h-10 mx-auto mb-3 text-gray-500" />
          <p className="text-gray-400 text-sm">Pozisyonları görmek için giriş yapın</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Wallet className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Açık Pozisyonlar</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
          <span className="text-gray-400 text-xs">{positions.length} pozisyon</span>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border border-emerald-500/30 rounded-xl p-2.5 text-center">
          <p className="text-xs text-emerald-300/80">Equity</p>
          <p className="text-base font-bold text-white">${stats.equity.toFixed(2)}</p>
        </div>
        <div className={`bg-gradient-to-br ${stats.dailyPnl >= 0 ? 'from-green-500/20 to-green-600/10 border-green-500/30' : 'from-red-500/20 to-red-600/10 border-red-500/30'} border rounded-xl p-2.5 text-center`}>
          <p className={`text-xs ${stats.dailyPnl >= 0 ? 'text-green-300/80' : 'text-red-300/80'}`}>Günlük P/L</p>
          <p className={`text-base font-bold ${stats.dailyPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {stats.dailyPnl >= 0 ? '+' : ''}${stats.dailyPnl.toFixed(2)}
          </p>
        </div>
        <div className="bg-gradient-to-br from-red-500/20 to-red-600/10 border border-red-500/30 rounded-xl p-2.5 text-center">
          <p className="text-xs text-red-300/80">Max DD</p>
          <p className="text-base font-bold text-red-400">{stats.maxDrawdown.toFixed(2)}%</p>
        </div>
      </div>

      {/* Positions List */}
      {positions.length === 0 ? (
        <div className="text-center py-6 bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10 rounded-xl">
          <RefreshCw className="w-8 h-8 mx-auto mb-2 text-gray-500" />
          <p className="text-gray-400 text-sm">Açık pozisyon yok</p>
          <p className="text-gray-500 text-xs mt-1">Bot çalıştığında pozisyonlar burada görünecek</p>
        </div>
      ) : (
        <div className="space-y-2">
          {positions.map((position, index) => (
            <div
              key={`${position.symbol}-${index}`}
              className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-white/10 rounded-xl p-3 hover:border-purple-500/30 transition-all"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {position.side === 'long' ? (
                    <TrendingUp className="w-4 h-4 text-green-400" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-400" />
                  )}
                  <span className="text-white font-medium">{position.symbol}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    position.side === 'long'
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-red-500/20 text-red-400'
                  }`}>
                    {position.side.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-400">{position.leverage}x</span>
                </div>
                <span className={`font-bold ${position.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-400">Miktar: </span>
                  <span className="text-white">{position.size}</span>
                </div>
                <div>
                  <span className="text-gray-400">Giriş: </span>
                  <span className="text-white">${position.entry_price.toLocaleString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Active Symbols */}
      {stats.activeSymbols.length > 0 && (
        <div className="mt-4 pt-4 border-t border-[#3a3a5a]">
          <p className="text-xs text-gray-400 mb-2">Aktif Semboller</p>
          <div className="flex flex-wrap gap-1">
            {stats.activeSymbols.map(symbol => (
              <span
                key={symbol}
                className="text-xs px-2 py-1 bg-purple-500/20 text-purple-400 rounded"
              >
                {symbol}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Bot Uptime */}
      {stats.uptime > 0 && (
        <div className="mt-3 pt-3 border-t border-[#3a3a5a] flex justify-between items-center text-xs">
          <span className="text-gray-400">Çalışma Süresi</span>
          <span className="text-purple-400 font-mono">
            {Math.floor(stats.uptime / 3600)}s {Math.floor((stats.uptime % 3600) / 60)}d {stats.uptime % 60}sn
          </span>
        </div>
      )}

      {/* Peak Equity */}
      {stats.peakEquity > 0 && (
        <div className="mt-2 flex justify-between items-center text-xs">
          <span className="text-gray-400">Peak Equity</span>
          <span className="text-emerald-400">${stats.peakEquity.toFixed(2)}</span>
        </div>
      )}
    </div>
  );
}
