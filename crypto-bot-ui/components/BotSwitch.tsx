'use client';

import { Bot, Activity, Zap, Shield, Settings } from 'lucide-react';
import { useBot } from '@/contexts/BotContext';
import { useAuth } from '@/contexts/AuthContext';

interface BotSwitchProps {
  onSettingsClick?: () => void;
}

export default function BotSwitch({ onSettingsClick }: BotSwitchProps) {
  const { auth } = useAuth();
  const { stats, isRunning, startBot, stopBot, config } = useBot();

  const handleToggle = async () => {
    if (isRunning) {
      await stopBot();
    } else {
      await startBot();
    }
  };

  const hasData = stats.totalTrades > 0;

  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bot className={`w-6 h-6 ${isRunning ? 'text-green-400' : 'text-gray-400'}`} />
          <h3 className="text-lg font-semibold text-white">Trading Bot</h3>
        </div>

        <div className="flex items-center gap-2">
          {onSettingsClick && (
            <button
              onClick={onSettingsClick}
              className="p-1.5 text-gray-400 hover:text-white transition-colors"
            >
              <Settings className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={handleToggle}
            disabled={!auth.isLoggedIn}
            className={`relative w-12 h-6 rounded-full transition-colors duration-300 disabled:opacity-50 disabled:cursor-not-allowed
              ${isRunning ? 'bg-green-600' : 'bg-gray-600'}`}
          >
            <span
              className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition-all duration-300 shadow-md
                ${isRunning ? 'left-[26px]' : 'left-0.5'}`}
            />
          </button>
        </div>
      </div>

      <div className={`flex items-center gap-2 mb-4 ${isRunning ? 'text-green-400' : 'text-gray-500'}`}>
        <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
        <span className="text-sm font-medium">
          {!auth.isLoggedIn
            ? 'Giriş yapınız'
            : isRunning
            ? `Bot Aktif - ${config.strategy.toUpperCase()}`
            : 'Bot Pasif'}
        </span>
      </div>

      {auth.isLoggedIn ? (
        <>
          {hasData ? (
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 rounded-xl p-3 text-center hover:border-blue-400/50 transition-all">
                <Activity className="w-5 h-5 mx-auto mb-1 text-blue-400" />
                <p className="text-2xl font-bold text-white">{stats.totalTrades}</p>
                <p className="text-xs text-blue-300/80">İşlem</p>
              </div>
              <div className="bg-gradient-to-br from-yellow-500/20 to-orange-600/10 border border-yellow-500/30 rounded-xl p-3 text-center hover:border-yellow-400/50 transition-all">
                <Zap className="w-5 h-5 mx-auto mb-1 text-yellow-400" />
                <p className={`text-2xl font-bold ${stats.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${stats.profit.toFixed(0)}
                </p>
                <p className="text-xs text-yellow-300/80">Kar</p>
              </div>
              <div className="bg-gradient-to-br from-purple-500/20 to-violet-600/10 border border-purple-500/30 rounded-xl p-3 text-center hover:border-purple-400/50 transition-all">
                <Shield className="w-5 h-5 mx-auto mb-1 text-purple-400" />
                <p className="text-2xl font-bold text-white">{stats.winRate.toFixed(0)}%</p>
                <p className="text-xs text-purple-300/80">Başarı</p>
              </div>
            </div>
          ) : (
            <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10 rounded-xl p-4 text-center">
              <Bot className="w-8 h-8 mx-auto mb-2 text-gray-500" />
              <p className="text-gray-400 text-sm">Henüz işlem verisi yok</p>
              <p className="text-gray-500 text-xs mt-1">Bot çalıştığında istatistikler burada görünecek</p>
            </div>
          )}

          {isRunning && (
            <div className="mt-4 p-3 bg-gradient-to-r from-green-500/20 to-emerald-500/10 border border-green-500/30 rounded-xl">
              <p className="text-green-400 text-sm font-medium">
                Bot {config.symbol} çiftinde {config.strategy} stratejisi ile çalışıyor.
              </p>
              {stats.tasksRunning && stats.tasksRunning.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {stats.tasksRunning.map((task, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-green-500/20 text-green-300 text-xs rounded-full">
                      {task}
                    </span>
                  ))}
                </div>
              )}
              {stats.mode && (
                <p className="text-green-300/70 text-xs mt-1">Mod: {stats.mode}</p>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10 rounded-xl p-4 text-center">
          <Bot className="w-8 h-8 mx-auto mb-2 text-gray-500" />
          <p className="text-gray-400 text-sm">Botu kullanmak için giriş yapın</p>
        </div>
      )}
    </div>
  );
}
