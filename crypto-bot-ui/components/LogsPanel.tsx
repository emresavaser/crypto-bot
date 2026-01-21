'use client';

import { useState } from 'react';
import { Terminal, Trash2, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { useBot } from '@/contexts/BotContext';
import { useAuth } from '@/contexts/AuthContext';

type LogLevel = 'all' | 'info' | 'warn' | 'error' | 'trade';

export default function LogsPanel() {
  const { auth } = useAuth();
  const { logs, clearLogs, isConnected } = useBot();
  const [filter, setFilter] = useState<LogLevel>('all');
  const [expanded, setExpanded] = useState(true);

  const filteredLogs = filter === 'all'
    ? logs
    : logs.filter(log => log.level === filter);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'info': return 'text-blue-400';
      case 'warn': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      case 'trade': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const getLevelBg = (level: string) => {
    switch (level) {
      case 'info': return 'bg-blue-500/10';
      case 'warn': return 'bg-yellow-500/10';
      case 'error': return 'bg-red-500/10';
      case 'trade': return 'bg-green-500/10';
      default: return 'bg-gray-500/10';
    }
  };

  const formatTime = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString('tr-TR');
    } catch {
      return timestamp;
    }
  };

  if (!auth.isLoggedIn) {
    return (
      <div className="glass-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Terminal className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Bot Logları</h3>
        </div>
        <div className="text-center py-8">
          <Terminal className="w-10 h-10 mx-auto mb-3 text-gray-500" />
          <p className="text-gray-400 text-sm">Logları görmek için giriş yapın</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Bot Logları</h3>
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 text-gray-400 hover:text-white transition-colors"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          <button
            onClick={clearLogs}
            className="p-1.5 text-gray-400 hover:text-red-400 transition-colors"
            title="Logları Temizle"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {expanded && (
        <>
          {/* Filter Buttons */}
          <div className="flex flex-wrap gap-2 mb-4">
            {(['all', 'info', 'warn', 'error', 'trade'] as LogLevel[]).map(level => (
              <button
                key={level}
                onClick={() => setFilter(level)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  filter === level
                    ? 'bg-gradient-to-r from-purple-600 to-violet-500 text-white shadow-md shadow-purple-500/20'
                    : 'bg-slate-800/60 border border-white/10 text-gray-400 hover:text-white hover:border-purple-500/30'
                }`}
              >
                {level === 'all' ? 'Tümü' : level.toUpperCase()}
                {level !== 'all' && (
                  <span className="ml-1 opacity-70">
                    ({logs.filter(l => l.level === level).length})
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Logs List */}
          <div className="bg-gradient-to-br from-slate-900/80 to-black/60 border border-white/10 rounded-xl p-3 max-h-64 overflow-y-auto font-mono text-xs">
            {filteredLogs.length === 0 ? (
              <div className="text-center py-6 text-gray-500">
                <Terminal className="w-6 h-6 mx-auto mb-2" />
                <p>Henüz log kaydı yok</p>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredLogs.map((log, index) => (
                  <div
                    key={`${log.timestamp}-${index}`}
                    className={`flex items-start gap-2 p-1.5 rounded ${getLevelBg(log.level)}`}
                  >
                    <span className="text-gray-500 shrink-0">{formatTime(log.timestamp)}</span>
                    <span className={`shrink-0 font-medium ${getLevelColor(log.level)}`}>
                      [{log.level.toUpperCase()}]
                    </span>
                    <span className="text-gray-300 break-all">{log.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Log Count */}
          <div className="mt-2 text-right text-xs text-gray-500">
            {filteredLogs.length} / {logs.length} log gösteriliyor
          </div>
        </>
      )}
    </div>
  );
}
