'use client';

import { createContext, useContext, useState, useCallback, useEffect, useRef, ReactNode } from 'react';
import { useAuth } from './AuthContext';

// Eclipse Scalper API Bridge URL
const BOT_API_URL = process.env.NEXT_PUBLIC_BOT_API_URL || 'http://localhost:8000';

// Eclipse Scalper Position
interface Position {
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entry_price: number;
  leverage: number;
  pnl: number;
}

interface BotStats {
  totalTrades: number;
  profit: number;
  winRate: number;
  isRunning: boolean;
  lastTradeTime: Date | null;
  lastSignal: string | null;
  lastPrice: number | null;
  // Eclipse Scalper ek alanları
  equity: number;
  peakEquity: number;
  dailyPnl: number;
  maxDrawdown: number;
  positionCount: number;
  uptime: number;
  activeSymbols: string[];
  tasksRunning: string[];
  mode: string | null;
}

interface BotConfig {
  // Eclipse Scalper config
  symbols: string[];
  mode: 'auto' | 'micro' | 'production';
  dryRun: boolean;
  // Temel ayarlar
  strategy: 'rsi' | 'sma' | 'macd' | 'bollinger' | 'eclipse';
  symbol: string;
  amount: number;
  interval: '1m' | '5m' | '15m' | '1h' | '4h' | '1d';
  // Risk yonetimi
  stopLoss: number | null;
  takeProfit: number | null;
  maxTradesPerDay: number;
  maxPositionSize: number;
  // RSI parametreleri
  rsiPeriod: number;
  rsiOversold: number;
  rsiOverbought: number;
  // SMA parametreleri
  smaShort: number;
  smaLong: number;
  // MACD parametreleri
  macdFast: number;
  macdSlow: number;
  macdSignal: number;
  // Bollinger parametreleri
  bbPeriod: number;
  bbStd: number;
}

interface Signal {
  type: string;
  price: number;
  timestamp: string;
  reason: string;
  confidence: number;
}

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'trade';
  message: string;
}

interface BotContextType {
  stats: BotStats;
  config: BotConfig;
  positions: Position[];
  isRunning: boolean;
  isConnected: boolean;
  signals: Signal[];
  logs: LogEntry[];
  startBot: () => Promise<boolean>;
  stopBot: () => Promise<void>;
  updateConfig: (config: Partial<BotConfig>) => void;
  connectToBackend: () => Promise<boolean>;
  getBalance: () => Promise<{ total: number; free: number; used: number } | null>;
  clearLogs: () => void;
}

const defaultStats: BotStats = {
  totalTrades: 0,
  profit: 0,
  winRate: 0,
  isRunning: false,
  lastTradeTime: null,
  lastSignal: null,
  lastPrice: null,
  // Eclipse Scalper defaults
  equity: 0,
  peakEquity: 0,
  dailyPnl: 0,
  maxDrawdown: 0,
  positionCount: 0,
  uptime: 0,
  activeSymbols: [],
  tasksRunning: [],
  mode: null,
};

const defaultConfig: BotConfig = {
  // Eclipse Scalper config
  symbols: ['BTCUSDT', 'ETHUSDT'],
  mode: 'auto',
  dryRun: true,
  // Temel ayarlar
  strategy: 'eclipse',
  symbol: 'BTCUSDT',
  amount: 0.002,
  interval: '1h',
  // Risk yonetimi
  stopLoss: null,
  takeProfit: null,
  maxTradesPerDay: 10,
  maxPositionSize: 0.1,
  // RSI parametreleri
  rsiPeriod: 14,
  rsiOversold: 30,
  rsiOverbought: 70,
  // SMA parametreleri
  smaShort: 10,
  smaLong: 50,
  // MACD parametreleri
  macdFast: 12,
  macdSlow: 26,
  macdSignal: 9,
  // Bollinger parametreleri
  bbPeriod: 20,
  bbStd: 2.0,
};

const BotContext = createContext<BotContextType | null>(null);

export function BotProvider({ children }: { children: ReactNode }) {
  const { auth } = useAuth();
  const [stats, setStats] = useState<BotStats>(defaultStats);
  const [config, setConfig] = useState<BotConfig>(defaultConfig);
  const [positions, setPositions] = useState<Position[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const addLog = useCallback((level: LogEntry['level'], message: string) => {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
    };
    setLogs(prev => [entry, ...prev].slice(0, 100)); // Max 100 log
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket bağlantısı kur
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(`${BOT_API_URL.replace('http', 'ws')}/ws`);

      ws.onopen = () => {
        console.log('Bot WebSocket bağlantısı kuruldu');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          switch (message.type) {
            case 'status':
              // Eclipse Scalper status update
              const data = message.data;
              setStats(prev => ({
                ...prev,
                totalTrades: data.total_trades || 0,
                profit: data.daily_pnl || 0,
                winRate: data.win_rate || 0,
                isRunning: data.is_running || false,
                equity: data.equity || 0,
                peakEquity: data.peak_equity || 0,
                dailyPnl: data.daily_pnl || 0,
                maxDrawdown: data.max_drawdown || 0,
                positionCount: data.position_count || 0,
                uptime: data.uptime || 0,
                activeSymbols: data.active_symbols || [],
                tasksRunning: data.tasks_running || [],
                mode: data.mode || null,
              }));
              setPositions(data.positions || []);
              setIsRunning(data.is_running || false);
              break;

            case 'price':
              // Fiyat güncellemesi
              setStats(prev => ({
                ...prev,
                lastPrice: message.data.price,
              }));
              break;

            case 'new_signal':
              setSignals(prev => [message.data, ...prev.slice(0, 19)]);
              setStats(prev => ({
                ...prev,
                lastSignal: message.data.side || message.data.type,
                lastPrice: message.data.price,
              }));
              addLog('info', `Yeni sinyal: ${message.data.symbol} ${message.data.side} (güven: ${(message.data.confidence * 100).toFixed(0)}%)`);
              break;

            case 'new_trade':
              setStats(prev => ({
                ...prev,
                totalTrades: prev.totalTrades + 1,
                lastTradeTime: new Date(),
              }));
              const trade = message.data;
              addLog('trade', `${trade.side} ${trade.amount} ${trade.symbol} @ $${trade.price}${trade.pnl ? ` PnL: $${trade.pnl.toFixed(2)}` : ''}`);
              break;

            case 'bot_started':
              setIsRunning(true);
              setStats(prev => ({
                ...prev,
                isRunning: true,
                tasksRunning: message.tasks || [],
                mode: message.mode || prev.mode,
              }));
              addLog('info', `Bot başlatıldı - Mod: ${message.mode || 'eclipse'}, Semboller: ${(message.symbols || []).join(', ')}`);
              break;

            case 'bot_stopped':
              setIsRunning(false);
              setStats(prev => ({ ...prev, isRunning: false, tasksRunning: [] }));
              setPositions([]);
              addLog('info', 'Bot durduruldu');
              break;

            case 'log':
              // Backend'den gelen log mesajı
              const logData = message.data;
              setLogs(prev => {
                const newLog: LogEntry = {
                  timestamp: logData.timestamp || new Date().toISOString(),
                  level: logData.level || 'info',
                  message: logData.message || '',
                };
                return [newLog, ...prev].slice(0, 200);
              });
              break;

            case 'logs_init':
              // İlk bağlantıda tüm logları al
              const initLogs = (message.data || []).map((log: any) => ({
                timestamp: log.timestamp || new Date().toISOString(),
                level: log.level || 'info',
                message: log.message || '',
              }));
              setLogs(initLogs.reverse());
              break;

            case 'positions_update':
              // Pozisyon güncellemesi
              setPositions(message.data || []);
              break;

            case 'error':
              // Hata mesajı
              addLog('error', message.data?.message || 'Bilinmeyen hata');
              break;

            case 'pong':
              // Ping response - ignore
              break;
          }
        } catch (error) {
          console.error('WebSocket mesaj parse hatası:', error);
        }
      };

      ws.onclose = () => {
        console.log('Bot WebSocket bağlantısı kapandı');
        setIsConnected(false);
        wsRef.current = null;

        // Yeniden bağlan
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 5000);
      };

      ws.onerror = () => {
        setIsConnected(false);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('WebSocket bağlantı hatası:', error);
      setIsConnected(false);
    }
  }, []);

  // Eclipse Scalper API Bridge'e bağlan
  const connectToBackend = useCallback(async (): Promise<boolean> => {
    if (!auth.isLoggedIn) return false;

    try {
      const response = await fetch(`${BOT_API_URL}/api/auth/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: auth.apiKey,
          api_secret: auth.apiSecret,
          testnet: auth.isTestnet,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Eclipse Scalper bağlantısı başarılı:', data);
        connectWebSocket();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Eclipse API Bridge bağlantı hatası:', error);
      return false;
    }
  }, [auth, connectWebSocket]);

  // Eclipse Scalper botu başlat
  const startBot = useCallback(async (): Promise<boolean> => {
    if (!isConnected) {
      const connected = await connectToBackend();
      if (!connected) return false;
    }

    try {
      const response = await fetch(`${BOT_API_URL}/api/bot/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbols: config.symbols,
          mode: config.mode,
          dry_run: config.dryRun,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Eclipse Scalper başlatıldı:', data);
        setIsRunning(true);
        setStats(prev => ({ ...prev, isRunning: true }));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Eclipse bot başlatma hatası:', error);
      return false;
    }
  }, [config, isConnected, connectToBackend]);

  // Bakiye al
  const getBalance = useCallback(async (): Promise<{ total: number; free: number; used: number } | null> => {
    try {
      const response = await fetch(`${BOT_API_URL}/api/balance`);
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('Bakiye alma hatası:', error);
      return null;
    }
  }, []);

  // Botu durdur
  const stopBot = useCallback(async () => {
    try {
      const response = await fetch(`${BOT_API_URL}/api/bot/stop`, {
        method: 'POST',
      });

      if (response.ok) {
        setIsRunning(false);
        setStats(prev => ({ ...prev, isRunning: false }));
      }
    } catch (error) {
      console.error('Bot durdurma hatası:', error);
    }
  }, []);

  // Config güncelle
  const updateConfig = useCallback((newConfig: Partial<BotConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  }, []);

  // Auth değiştiğinde backend'e bağlan
  useEffect(() => {
    if (auth.isLoggedIn) {
      connectToBackend();
    } else {
      // Bağlantıyı kapat
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      setIsConnected(false);
      setIsRunning(false);
      setStats(defaultStats);
    }
  }, [auth.isLoggedIn, connectToBackend]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  const value: BotContextType = {
    stats,
    config,
    positions,
    isRunning,
    isConnected,
    signals,
    logs,
    startBot,
    stopBot,
    updateConfig,
    connectToBackend,
    getBalance,
    clearLogs,
  };

  return (
    <BotContext.Provider value={value}>
      {children}
    </BotContext.Provider>
  );
}

export function useBot() {
  const context = useContext(BotContext);
  if (!context) {
    throw new Error('useBot must be used within BotProvider');
  }
  return context;
}

export function useBotStats() {
  const { stats } = useBot();
  return stats;
}
