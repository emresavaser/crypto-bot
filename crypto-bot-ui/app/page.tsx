'use client';

import { useState, useCallback, useEffect } from 'react';
import { Activity, Bell, Settings, ChevronDown, LogIn, LogOut, HelpCircle } from 'lucide-react';
import PriceChart from '@/components/PriceChart';
import BalanceCard from '@/components/BalanceCard';
import TradeButtons from '@/components/TradeButtons';
import BotSwitch from '@/components/BotSwitch';
import BotControlPanel from '@/components/BotControlPanel';
import TradeHistory from '@/components/TradeHistory';
import PositionsPanel from '@/components/PositionsPanel';
import LogsPanel from '@/components/LogsPanel';
import LoginModal from '@/components/LoginModal';
import HelpModal from '@/components/HelpModal';
import { useAuth } from '@/contexts/AuthContext';

const TRADING_PAIRS = [
  'BTCUSDT',
  'ETHUSDT',
  'BNBUSDT',
  'SOLUSDT',
  'XRPUSDT',
  'DOGEUSDT',
  'ADAUSDT',
  'AVAXUSDT',
];

export default function Home() {
  const { auth, logout } = useAuth();
  const [selectedPair, setSelectedPair] = useState('BTCUSDT');
  const [showPairMenu, setShowPairMenu] = useState(false);
  const [currentPrice, setCurrentPrice] = useState(0);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    setCurrentTime(new Date().toLocaleTimeString('tr-TR'));
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString('tr-TR'));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handlePriceUpdate = useCallback((price: number) => {
    setCurrentPrice(price);
  }, []);

  const displayPair = `${selectedPair.replace('USDT', '')}/USDT`;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-white/5 bg-[#0a0a14]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-gradient-to-br from-purple-500 via-violet-500 to-blue-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/20 glow-purple">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">CryptoBot</h1>
              <p className="text-xs text-gray-400">
                {auth.isLoggedIn
                  ? `Binance ${auth.isTestnet ? 'Testnet' : ''} Bağlı`
                  : 'Bağlantı yok'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Pair Selector */}
            <div className="relative">
              <button
                onClick={() => setShowPairMenu(!showPairMenu)}
                className="flex items-center gap-2 bg-[#2a2a4a] px-4 py-2 rounded-lg hover:bg-[#3a3a5a] transition-colors"
              >
                <span className="text-white font-medium">{displayPair}</span>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showPairMenu ? 'rotate-180' : ''}`} />
              </button>

              {showPairMenu && (
                <div className="absolute top-full mt-2 right-0 bg-[#1a1a2e] border border-[#3a3a5a] rounded-lg shadow-xl py-2 min-w-[150px] z-50">
                  {TRADING_PAIRS.map((pair) => (
                    <button
                      key={pair}
                      onClick={() => {
                        setSelectedPair(pair);
                        setShowPairMenu(false);
                      }}
                      className={`w-full px-4 py-2 text-left hover:bg-[#2a2a4a] transition-colors ${
                        selectedPair === pair ? 'text-purple-400' : 'text-white'
                      }`}
                    >
                      {pair.replace('USDT', '/USDT')}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={() => setShowHelpModal(true)}
              className="flex items-center gap-2 px-3 py-2 bg-[#2a2a4a] rounded-lg hover:bg-[#3a3a5a] transition-colors text-gray-300 hover:text-white"
            >
              <HelpCircle className="w-4 h-4" />
              <span className="text-sm hidden sm:inline">Nasıl Kullanılır?</span>
            </button>

            <button className="relative p-2 text-gray-400 hover:text-white transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>

            <button className="p-2 text-gray-400 hover:text-white transition-colors">
              <Settings className="w-5 h-5" />
            </button>

            {/* Login/Logout Button */}
            {auth.isLoggedIn ? (
              <button
                onClick={logout}
                className="flex items-center gap-2 bg-[#2a2a4a] px-3 py-2 rounded-lg hover:bg-[#3a3a5a] transition-colors text-gray-300 hover:text-white"
              >
                <LogOut className="w-4 h-4" />
                <span className="text-sm">Çıkış</span>
              </button>
            ) : (
              <button
                onClick={() => setShowLoginModal(true)}
                className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-4 py-2 rounded-lg transition-all text-white font-medium"
              >
                <LogIn className="w-4 h-4" />
                <span className="text-sm">Giriş Yap</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Chart & Trade History */}
          <div className="lg:col-span-2 space-y-6">
            <PriceChart symbol={selectedPair} onPriceUpdate={handlePriceUpdate} />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <TradeHistory symbol={selectedPair} onLoginClick={() => setShowLoginModal(true)} />
              <PositionsPanel />
            </div>
            <LogsPanel />
          </div>

          {/* Right Column - Controls */}
          <div className="space-y-6">
            <BotSwitch />
            <BotControlPanel />
            <BalanceCard onLoginClick={() => setShowLoginModal(true)} />
            <TradeButtons symbol={selectedPair} currentPrice={currentPrice} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 mt-8 bg-[#0a0a14]/50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <p className="flex items-center gap-2">
              <span className="gradient-text font-semibold">CryptoBot</span>
              <span className="text-gray-600">v1.2</span>
            </p>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5">
                <span className={`w-2 h-2 rounded-full ${auth.isLoggedIn ? 'bg-green-500 animate-pulse shadow-lg shadow-green-500/50' : 'bg-yellow-500'}`} />
                {auth.isLoggedIn ? 'Bağlı' : 'Bağlantı Yok'}
              </span>
              <span className="text-gray-600">{currentTime || 'Yükleniyor...'}</span>
            </div>
          </div>
        </div>
      </footer>

      {/* Login Modal */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
      />

      {/* Help Modal */}
      <HelpModal
        isOpen={showHelpModal}
        onClose={() => setShowHelpModal(false)}
      />
    </div>
  );
}
