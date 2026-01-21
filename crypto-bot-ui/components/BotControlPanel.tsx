'use client';

import { useState } from 'react';
import { Settings, Play, Square, ChevronDown, ChevronUp, Save, AlertTriangle } from 'lucide-react';
import { useBot } from '@/contexts/BotContext';

const AVAILABLE_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT', 'DOGEUSDT'];
const STRATEGIES = [
  { value: 'eclipse', label: 'Eclipse Scalper', description: 'Otomatik scalping stratejisi' },
  { value: 'rsi', label: 'RSI', description: 'RSI tabanlı al/sat sinyalleri' },
  { value: 'sma', label: 'SMA Crossover', description: 'Hareketli ortalama kesişimi' },
  { value: 'macd', label: 'MACD', description: 'MACD histogram stratejisi' },
  { value: 'bollinger', label: 'Bollinger Bands', description: 'Bollinger bantları stratejisi' },
];

const INTERVALS = [
  { value: '1m', label: '1 Dakika' },
  { value: '5m', label: '5 Dakika' },
  { value: '15m', label: '15 Dakika' },
  { value: '1h', label: '1 Saat' },
  { value: '4h', label: '4 Saat' },
  { value: '1d', label: '1 Gün' },
];

export default function BotControlPanel() {
  const { config, updateConfig, isRunning, startBot, stopBot, isConnected } = useBot();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSymbolToggle = (symbol: string) => {
    const newSymbols = config.symbols.includes(symbol)
      ? config.symbols.filter(s => s !== symbol)
      : [...config.symbols, symbol];

    if (newSymbols.length > 0) {
      updateConfig({ symbols: newSymbols, symbol: newSymbols[0] });
    }
  };

  const handleSaveConfig = async () => {
    setSaving(true);
    // Config backend'e kaydedilebilir
    await new Promise(resolve => setTimeout(resolve, 500));
    setSaving(false);
  };

  const handleStartStop = async () => {
    if (isRunning) {
      await stopBot();
    } else {
      await startBot();
    }
  };

  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Bot Ayarlar</h3>
        </div>
        <button
          onClick={handleStartStop}
          disabled={!isConnected}
          className={`btn-modern flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all ${
            isRunning
              ? 'bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600 text-white shadow-lg shadow-red-500/25'
              : 'bg-gradient-to-r from-green-600 to-emerald-500 hover:from-green-700 hover:to-emerald-600 text-white shadow-lg shadow-green-500/25'
          } disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none`}
        >
          {isRunning ? (
            <>
              <Square className="w-4 h-4" />
              Durdur
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Baslat
            </>
          )}
        </button>
      </div>

      {!isConnected && (
        <div className="flex items-center gap-2 p-3 mb-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-yellow-400" />
          <span className="text-yellow-400 text-sm">Botu kontrol etmek icin once baglanti kurun</span>
        </div>
      )}

      {/* Trading Pairs */}
      <div className="mb-4">
        <label className="text-gray-400 text-sm block mb-2">Islem Ciftleri</label>
        <div className="flex flex-wrap gap-2">
          {AVAILABLE_SYMBOLS.map(symbol => (
            <button
              key={symbol}
              onClick={() => handleSymbolToggle(symbol)}
              disabled={isRunning}
              className={`px-3 py-1.5 rounded-xl text-sm font-medium transition-all ${
                config.symbols.includes(symbol)
                  ? 'bg-gradient-to-r from-purple-600 to-violet-500 text-white shadow-md shadow-purple-500/20'
                  : 'inner-card text-gray-400 hover:text-white hover:bg-white/5'
              } disabled:opacity-50`}
            >
              {symbol.replace('USDT', '')}
            </button>
          ))}
        </div>
      </div>

      {/* Strategy Selection */}
      <div className="mb-4">
        <label className="text-gray-400 text-sm block mb-2">Strateji</label>
        <div className="grid grid-cols-2 gap-2">
          {STRATEGIES.map(strategy => (
            <button
              key={strategy.value}
              onClick={() => updateConfig({ strategy: strategy.value as typeof config.strategy })}
              disabled={isRunning}
              className={`p-3 rounded-xl text-left transition-all ${
                config.strategy === strategy.value
                  ? 'bg-gradient-to-br from-purple-600/20 to-violet-600/10 border border-purple-500/50 shadow-lg shadow-purple-500/10'
                  : 'inner-card hover:bg-white/5 border border-transparent'
              } disabled:opacity-50`}
            >
              <div className="text-white font-medium text-sm">{strategy.label}</div>
              <div className="text-gray-400 text-xs mt-1">{strategy.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Basic Settings */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-gray-400 text-sm block mb-2">Islem Miktari</label>
          <input
            type="number"
            value={config.amount}
            onChange={(e) => updateConfig({ amount: parseFloat(e.target.value) || 0 })}
            disabled={isRunning}
            className="w-full inner-card rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-50 transition-all"
            step="0.001"
            min="0"
          />
        </div>
        <div>
          <label className="text-gray-400 text-sm block mb-2">Mod</label>
          <select
            value={config.mode}
            onChange={(e) => updateConfig({ mode: e.target.value as typeof config.mode })}
            disabled={isRunning}
            className="w-full inner-card rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-50 transition-all"
          >
            <option value="auto">Otomatik</option>
            <option value="micro">Micro</option>
            <option value="production">Production</option>
          </select>
        </div>
      </div>

      {/* Interval Selection */}
      <div className="mb-4">
        <label className="text-gray-400 text-sm block mb-2">Zaman Dilimi</label>
        <div className="flex flex-wrap gap-2">
          {INTERVALS.map(interval => (
            <button
              key={interval.value}
              onClick={() => updateConfig({ interval: interval.value as typeof config.interval })}
              disabled={isRunning}
              className={`px-3 py-1.5 rounded-xl text-sm font-medium transition-all ${
                config.interval === interval.value
                  ? 'bg-gradient-to-r from-purple-600 to-violet-500 text-white shadow-md shadow-purple-500/20'
                  : 'inner-card text-gray-400 hover:text-white hover:bg-white/5'
              } disabled:opacity-50`}
            >
              {interval.label}
            </button>
          ))}
        </div>
      </div>

      {/* Risk Management */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-gray-400 text-sm block mb-2">Günlük Max İşlem</label>
          <input
            type="number"
            value={config.maxTradesPerDay}
            onChange={(e) => updateConfig({ maxTradesPerDay: parseInt(e.target.value) || 10 })}
            disabled={isRunning}
            className="w-full inner-card rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-50 transition-all"
            min="1"
          />
        </div>
        <div>
          <label className="text-gray-400 text-sm block mb-2">Max Pozisyon %</label>
          <input
            type="number"
            value={config.maxPositionSize * 100}
            onChange={(e) => updateConfig({ maxPositionSize: (parseFloat(e.target.value) || 10) / 100 })}
            disabled={isRunning}
            className="w-full inner-card rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-50 transition-all"
            step="1"
            min="1"
            max="100"
          />
        </div>
      </div>

      {/* Stop Loss / Take Profit */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-gray-400 text-sm block mb-2">Stop Loss (%)</label>
          <input
            type="number"
            value={config.stopLoss || ''}
            onChange={(e) => updateConfig({ stopLoss: e.target.value ? parseFloat(e.target.value) : null })}
            disabled={isRunning}
            placeholder="Opsiyonel"
            className="w-full inner-card rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-50 transition-all placeholder:text-gray-600"
            step="0.1"
            min="0"
          />
        </div>
        <div>
          <label className="text-gray-400 text-sm block mb-2">Take Profit (%)</label>
          <input
            type="number"
            value={config.takeProfit || ''}
            onChange={(e) => updateConfig({ takeProfit: e.target.value ? parseFloat(e.target.value) : null })}
            disabled={isRunning}
            placeholder="Opsiyonel"
            className="w-full inner-card rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-50 transition-all placeholder:text-gray-600"
            step="0.1"
            min="0"
          />
        </div>
      </div>

      {/* Dry Run Toggle */}
      <div className="flex items-center justify-between p-4 inner-card rounded-xl mb-4">
        <div>
          <div className="text-white text-sm font-medium">Demo Mod (Dry Run)</div>
          <div className="text-gray-400 text-xs">Gercek islem yapmadan test et</div>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={config.dryRun}
            onChange={(e) => updateConfig({ dryRun: e.target.checked })}
            disabled={isRunning}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-[#3a3a5a] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
        </label>
      </div>

      {/* Advanced Settings Toggle */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm mb-4"
      >
        {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        Gelismis Ayarlar
      </button>

      {/* Advanced Settings */}
      {showAdvanced && (
        <div className="space-y-4 p-4 bg-[#2a2a4a] rounded-lg">
          {/* RSI Settings */}
          {config.strategy === 'rsi' && (
            <>
              <div className="text-white text-sm font-medium mb-2">RSI Parametreleri</div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-gray-400 text-xs block mb-1">Periyot</label>
                  <input
                    type="number"
                    value={config.rsiPeriod}
                    onChange={(e) => updateConfig({ rsiPeriod: parseInt(e.target.value) || 14 })}
                    disabled={isRunning}
                    className="w-full bg-[#1a1a2e] border border-[#3a3a5a] rounded px-2 py-1 text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-gray-400 text-xs block mb-1">Asiri Satim</label>
                  <input
                    type="number"
                    value={config.rsiOversold}
                    onChange={(e) => updateConfig({ rsiOversold: parseInt(e.target.value) || 30 })}
                    disabled={isRunning}
                    className="w-full bg-[#1a1a2e] border border-[#3a3a5a] rounded px-2 py-1 text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-gray-400 text-xs block mb-1">Asiri Alim</label>
                  <input
                    type="number"
                    value={config.rsiOverbought}
                    onChange={(e) => updateConfig({ rsiOverbought: parseInt(e.target.value) || 70 })}
                    disabled={isRunning}
                    className="w-full bg-[#1a1a2e] border border-[#3a3a5a] rounded px-2 py-1 text-white text-sm"
                  />
                </div>
              </div>
            </>
          )}

          {/* SMA Settings */}
          {config.strategy === 'sma' && (
            <>
              <div className="text-white text-sm font-medium mb-2">SMA Parametreleri</div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-gray-400 text-xs block mb-1">Kisa Periyot</label>
                  <input
                    type="number"
                    value={config.smaShort}
                    onChange={(e) => updateConfig({ smaShort: parseInt(e.target.value) || 10 })}
                    disabled={isRunning}
                    className="w-full bg-[#1a1a2e] border border-[#3a3a5a] rounded px-2 py-1 text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-gray-400 text-xs block mb-1">Uzun Periyot</label>
                  <input
                    type="number"
                    value={config.smaLong}
                    onChange={(e) => updateConfig({ smaLong: parseInt(e.target.value) || 50 })}
                    disabled={isRunning}
                    className="w-full bg-[#1a1a2e] border border-[#3a3a5a] rounded px-2 py-1 text-white text-sm"
                  />
                </div>
              </div>
            </>
          )}

          {/* MACD Settings */}
          {config.strategy === 'macd' && (
            <>
              <div className="text-white text-sm font-medium mb-2">MACD Parametreleri</div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-gray-400 text-xs block mb-1">Hızlı EMA</label>
                  <input
                    type="number"
                    value={config.macdFast}
                    onChange={(e) => updateConfig({ macdFast: parseInt(e.target.value) || 12 })}
                    disabled={isRunning}
                    className="w-full bg-[#1a1a2e] border border-[#3a3a5a] rounded px-2 py-1 text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-gray-400 text-xs block mb-1">Yavaş EMA</label>
                  <input
                    type="number"
                    value={config.macdSlow}
                    onChange={(e) => updateConfig({ macdSlow: parseInt(e.target.value) || 26 })}
                    disabled={isRunning}
                    className="w-full bg-[#1a1a2e] border border-[#3a3a5a] rounded px-2 py-1 text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-gray-400 text-xs block mb-1">Sinyal</label>
                  <input
                    type="number"
                    value={config.macdSignal}
                    onChange={(e) => updateConfig({ macdSignal: parseInt(e.target.value) || 9 })}
                    disabled={isRunning}
                    className="w-full bg-[#1a1a2e] border border-[#3a3a5a] rounded px-2 py-1 text-white text-sm"
                  />
                </div>
              </div>
            </>
          )}

          {/* Bollinger Bands Settings */}
          {config.strategy === 'bollinger' && (
            <>
              <div className="text-white text-sm font-medium mb-2">Bollinger Bands Parametreleri</div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-gray-400 text-xs block mb-1">Periyot</label>
                  <input
                    type="number"
                    value={config.bbPeriod}
                    onChange={(e) => updateConfig({ bbPeriod: parseInt(e.target.value) || 20 })}
                    disabled={isRunning}
                    className="w-full bg-[#1a1a2e] border border-[#3a3a5a] rounded px-2 py-1 text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-gray-400 text-xs block mb-1">Standart Sapma</label>
                  <input
                    type="number"
                    value={config.bbStd}
                    onChange={(e) => updateConfig({ bbStd: parseFloat(e.target.value) || 2.0 })}
                    disabled={isRunning}
                    className="w-full bg-[#1a1a2e] border border-[#3a3a5a] rounded px-2 py-1 text-white text-sm"
                    step="0.1"
                  />
                </div>
              </div>
            </>
          )}

          {/* Eclipse Settings */}
          {config.strategy === 'eclipse' && (
            <div className="text-gray-400 text-sm">
              Eclipse Scalper otomatik olarak en uygun parametreleri kullanir.
            </div>
          )}
        </div>
      )}

      {/* Save Button */}
      <button
        onClick={handleSaveConfig}
        disabled={saving || isRunning}
        className="btn-modern w-full mt-4 flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-violet-500 hover:from-purple-700 hover:to-violet-600 disabled:opacity-50 text-white py-3 rounded-xl font-medium transition-all shadow-lg shadow-purple-500/20 disabled:shadow-none"
      >
        <Save className="w-4 h-4" />
        {saving ? 'Kaydediliyor...' : 'Ayarlari Kaydet'}
      </button>
    </div>
  );
}
