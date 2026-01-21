'use client';

import { useState } from 'react';
import { X, Key, Eye, EyeOff, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const { login } = useAuth();
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [isTestnet, setIsTestnet] = useState(true);
  const [showSecret, setShowSecret] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const result = await login(apiKey, apiSecret, isTestnet);

    if (result) {
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setApiKey('');
        setApiSecret('');
      }, 1000);
    } else {
      setError('API bağlantısı başarısız. Anahtarları kontrol edin.');
    }

    setIsLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-[#1a1a2e] border border-[#3a3a5a] rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
            <Key className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Binance Bağlantısı</h2>
            <p className="text-sm text-gray-400">API anahtarlarınızı girin</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-gray-400 text-sm block mb-2">API Key</label>
            <input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Binance API Key"
              className="w-full bg-[#2a2a4a] border border-[#3a3a5a] rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
              required
            />
          </div>

          <div>
            <label className="text-gray-400 text-sm block mb-2">API Secret</label>
            <div className="relative">
              <input
                type={showSecret ? 'text' : 'password'}
                value={apiSecret}
                onChange={(e) => setApiSecret(e.target.value)}
                placeholder="Binance API Secret"
                className="w-full bg-[#2a2a4a] border border-[#3a3a5a] rounded-lg px-4 py-3 pr-12 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                required
              />
              <button
                type="button"
                onClick={() => setShowSecret(!showSecret)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
              >
                {showSecret ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 bg-[#2a2a4a] rounded-lg">
            <input
              type="checkbox"
              id="testnet"
              checked={isTestnet}
              onChange={(e) => setIsTestnet(e.target.checked)}
              className="w-4 h-4 rounded border-gray-600 bg-[#1a1a2e] text-purple-500 focus:ring-purple-500"
            />
            <label htmlFor="testnet" className="text-sm text-gray-300">
              Testnet kullan (önerilir - gerçek para yok)
            </label>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <span className="text-red-400 text-sm">{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span className="text-green-400 text-sm">Bağlantı başarılı!</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !apiKey || !apiSecret}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3 rounded-lg font-semibold transition-all flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Bağlanıyor...
              </>
            ) : (
              'Giriş Yap'
            )}
          </button>
        </form>

        <div className="mt-4 p-3 bg-[#2a2a4a]/50 rounded-lg">
          <p className="text-xs text-gray-500">
            API anahtarlarını{' '}
            <a
              href="https://www.binance.com/en/my/settings/api-management"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:underline"
            >
              Binance API Yönetimi
            </a>
            {' '}sayfasından alabilirsiniz. Testnet için{' '}
            <a
              href="https://testnet.binance.vision/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-400 hover:underline"
            >
              testnet.binance.vision
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
