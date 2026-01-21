'use client';

import { useState } from 'react';
import { X, BookOpen, TrendingUp, Shield, Zap, DollarSign, AlertTriangle, ChevronRight, Target, BarChart3 } from 'lucide-react';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'intro' | 'strategies' | 'example' | 'risk';

export default function HelpModal({ isOpen, onClose }: HelpModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('intro');

  if (!isOpen) return null;

  const tabs = [
    { id: 'intro' as TabType, label: 'Başlangıç', icon: BookOpen },
    { id: 'strategies' as TabType, label: 'Stratejiler', icon: BarChart3 },
    { id: 'example' as TabType, label: '$100 Örneği', icon: DollarSign },
    { id: 'risk' as TabType, label: 'Risk Yönetimi', icon: Shield },
  ];

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1a2e] rounded-2xl w-full max-w-3xl max-h-[85vh] overflow-hidden border border-[#3a3a5a]">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[#3a3a5a]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">CryptoBot Kullanım Kılavuzu</h2>
              <p className="text-sm text-gray-400">Botunuzu nasıl kullanacağınızı öğrenin</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[#3a3a5a]">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-purple-400 border-b-2 border-purple-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto max-h-[calc(85vh-180px)]">
          {activeTab === 'intro' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-400" />
                  CryptoBot Nedir?
                </h3>
                <p className="text-gray-300 leading-relaxed">
                  CryptoBot, Binance Futures üzerinde otomatik alım-satım yapan bir trading botudur.
                  Teknik analiz stratejileri kullanarak piyasa koşullarını analiz eder ve sizin yerinize
                  işlem yapar.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-3">Başlamak İçin Adımlar</h3>
                <div className="space-y-3">
                  {[
                    { step: 1, title: 'Binance Hesabı Açın', desc: 'Binance Futures hesabınızı aktifleştirin' },
                    { step: 2, title: 'API Anahtarı Oluşturun', desc: 'Binance\'den API Key ve Secret alın' },
                    { step: 3, title: 'Demo Mod ile Test Edin', desc: 'Önce Testnet ile risk almadan deneyin' },
                    { step: 4, title: 'Strateji Seçin', desc: 'Size uygun stratejiyi belirleyin' },
                    { step: 5, title: 'Botu Başlatın', desc: 'Ayarları yapıp botu çalıştırın' },
                  ].map(item => (
                    <div key={item.step} className="flex items-start gap-3 p-3 bg-[#2a2a4a] rounded-lg">
                      <span className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0">
                        {item.step}
                      </span>
                      <div>
                        <p className="text-white font-medium">{item.title}</p>
                        <p className="text-gray-400 text-sm">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-yellow-400 font-medium">Önemli Uyarı</p>
                    <p className="text-yellow-200/80 text-sm mt-1">
                      Kripto para ticareti yüksek risk içerir. Kaybetmeyi göze alamayacağınız parayla
                      işlem yapmayın. Önce demo modda deneyim kazanın.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'strategies' && (
            <div className="space-y-4">
              <p className="text-gray-300 mb-4">
                Her strateji farklı piyasa koşullarında etkilidir. Doğru stratejiyi seçmek başarı için kritiktir.
              </p>

              {[
                {
                  name: 'Eclipse Scalper',
                  icon: '⚡',
                  desc: 'Otomatik scalping stratejisi. Kısa vadeli küçük kazançlar hedefler.',
                  best: 'Volatil piyasalar',
                  risk: 'Orta',
                  params: 'Otomatik optimize edilir'
                },
                {
                  name: 'RSI (Relative Strength Index)',
                  icon: '📊',
                  desc: 'Aşırı alım/satım bölgelerini tespit eder. RSI 30 altında AL, 70 üstünde SAT.',
                  best: 'Yatay piyasalar',
                  risk: 'Düşük-Orta',
                  params: 'Periyot: 14, Aşırı Satım: 30, Aşırı Alım: 70'
                },
                {
                  name: 'SMA Crossover',
                  icon: '📈',
                  desc: 'Kısa ve uzun vadeli hareketli ortalamaların kesişimini takip eder.',
                  best: 'Trend piyasaları',
                  risk: 'Düşük',
                  params: 'Kısa: 10, Uzun: 50'
                },
                {
                  name: 'MACD',
                  icon: '🎯',
                  desc: 'Momentum ve trend yönünü birlikte analiz eder.',
                  best: 'Trend başlangıçları',
                  risk: 'Orta',
                  params: 'Hızlı: 12, Yavaş: 26, Sinyal: 9'
                },
                {
                  name: 'Bollinger Bands',
                  icon: '📉',
                  desc: 'Fiyat bantlarını kullanarak aşırı hareketleri tespit eder.',
                  best: 'Volatilite patlamaları',
                  risk: 'Orta-Yüksek',
                  params: 'Periyot: 20, Std Sapma: 2.0'
                },
              ].map(strategy => (
                <div key={strategy.name} className="p-4 bg-[#2a2a4a] rounded-lg border border-[#3a3a5a]">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">{strategy.icon}</span>
                    <h4 className="text-white font-semibold">{strategy.name}</h4>
                  </div>
                  <p className="text-gray-300 text-sm mb-3">{strategy.desc}</p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="bg-[#1a1a2e] p-2 rounded">
                      <span className="text-gray-400">En İyi:</span>
                      <p className="text-white">{strategy.best}</p>
                    </div>
                    <div className="bg-[#1a1a2e] p-2 rounded">
                      <span className="text-gray-400">Risk:</span>
                      <p className="text-white">{strategy.risk}</p>
                    </div>
                    <div className="bg-[#1a1a2e] p-2 rounded">
                      <span className="text-gray-400">Parametreler:</span>
                      <p className="text-white">{strategy.params}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'example' && (
            <div className="space-y-6">
              <div className="text-center p-6 bg-gradient-to-br from-purple-600/20 to-blue-600/20 rounded-xl border border-purple-500/30">
                <DollarSign className="w-12 h-12 mx-auto mb-3 text-green-400" />
                <h3 className="text-2xl font-bold text-white mb-2">$100 ile Başlama Rehberi</h3>
                <p className="text-gray-300">Küçük sermaye ile büyük hayaller</p>
              </div>

              <div>
                <h4 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <Target className="w-5 h-5 text-purple-400" />
                  Önerilen Ayarlar ($100 Sermaye)
                </h4>
                <div className="bg-[#2a2a4a] rounded-lg p-4 space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-gray-400 text-sm">Strateji</span>
                      <p className="text-white font-medium">RSI veya SMA Crossover</p>
                    </div>
                    <div>
                      <span className="text-gray-400 text-sm">Zaman Dilimi</span>
                      <p className="text-white font-medium">1 Saat veya 4 Saat</p>
                    </div>
                    <div>
                      <span className="text-gray-400 text-sm">İşlem Miktarı</span>
                      <p className="text-white font-medium">0.001 - 0.002 BTC</p>
                    </div>
                    <div>
                      <span className="text-gray-400 text-sm">Kaldıraç</span>
                      <p className="text-white font-medium">3x - 5x (düşük tut!)</p>
                    </div>
                    <div>
                      <span className="text-gray-400 text-sm">Stop Loss</span>
                      <p className="text-white font-medium">%2 - %3</p>
                    </div>
                    <div>
                      <span className="text-gray-400 text-sm">Take Profit</span>
                      <p className="text-white font-medium">%3 - %5</p>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Gerçekçi Hedefler</h4>
                <div className="space-y-3">
                  <div className="p-4 bg-[#2a2a4a] rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400">1. Ay Hedefi</span>
                      <span className="text-green-400 font-bold">$100 → $105-110</span>
                    </div>
                    <div className="w-full bg-[#1a1a2e] rounded-full h-2">
                      <div className="bg-green-500 h-2 rounded-full" style={{ width: '10%' }}></div>
                    </div>
                    <p className="text-gray-400 text-xs mt-2">Aylık %5-10 hedefleyin. Sabırlı olun!</p>
                  </div>

                  <div className="p-4 bg-[#2a2a4a] rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400">6. Ay Hedefi</span>
                      <span className="text-green-400 font-bold">$100 → $130-180</span>
                    </div>
                    <div className="w-full bg-[#1a1a2e] rounded-full h-2">
                      <div className="bg-green-500 h-2 rounded-full" style={{ width: '40%' }}></div>
                    </div>
                    <p className="text-gray-400 text-xs mt-2">Bileşik getiri ile sermaye büyür</p>
                  </div>

                  <div className="p-4 bg-[#2a2a4a] rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400">1. Yıl Hedefi</span>
                      <span className="text-green-400 font-bold">$100 → $180-300</span>
                    </div>
                    <div className="w-full bg-[#1a1a2e] rounded-full h-2">
                      <div className="bg-green-500 h-2 rounded-full" style={{ width: '75%' }}></div>
                    </div>
                    <p className="text-gray-400 text-xs mt-2">Disiplin ve sabır ile mümkün</p>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Örnek Senaryo</h4>
                <div className="bg-[#0f0f1a] rounded-lg p-4 font-mono text-sm">
                  <div className="space-y-2">
                    <p className="text-gray-400"># Başlangıç: $100 USDT</p>
                    <p className="text-gray-400"># Strateji: RSI, 1 Saatlik grafik</p>
                    <p className="text-gray-400"># İşlem: 0.001 BTC (~$100 değerinde)</p>
                    <p className="text-gray-400"># Kaldıraç: 5x</p>
                    <br />
                    <p className="text-green-400">Senaryo 1 - Başarılı İşlem:</p>
                    <p className="text-white">RSI 28'e düştü → Bot 0.001 BTC LONG açtı</p>
                    <p className="text-white">BTC %2 yükseldi → Pozisyon kapandı</p>
                    <p className="text-green-400">Kar: $100 x 5x x %2 = +$10</p>
                    <p className="text-green-400">Yeni bakiye: $110</p>
                    <br />
                    <p className="text-red-400">Senaryo 2 - Zararlı İşlem:</p>
                    <p className="text-white">RSI 25'e düştü → Bot 0.001 BTC LONG açtı</p>
                    <p className="text-white">BTC %1 düştü → Stop Loss tetiklendi</p>
                    <p className="text-red-400">Zarar: $100 x 5x x %1 = -$5</p>
                    <p className="text-red-400">Yeni bakiye: $95</p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <p className="text-blue-400 font-medium mb-2">Pro İpucu</p>
                <p className="text-blue-200/80 text-sm">
                  Her gün %1-2 kar hedefleyin. Günde 1-2 başarılı işlem yeterli.
                  Aşırı işlem yapmayın, piyasayı takip edin ve sabırlı olun.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'risk' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <Shield className="w-5 h-5 text-green-400" />
                  Altın Kurallar
                </h3>
                <div className="grid gap-3">
                  {[
                    { rule: 'Asla %2\'den fazla riske girmeyin', desc: 'Tek işlemde sermayenizin max %2\'sini riske atın' },
                    { rule: 'Her zaman Stop Loss kullanın', desc: 'Stop Loss olmadan asla işlem açmayın' },
                    { rule: 'Düşük kaldıraç tercih edin', desc: 'Yeni başlayanlar için max 5x kaldıraç' },
                    { rule: 'Duygusal kararlar vermeyin', desc: 'Bot\'un stratejisine güvenin, müdahale etmeyin' },
                    { rule: 'Demo mod ile başlayın', desc: 'Gerçek paradan önce en az 1 hafta demo kullanın' },
                  ].map((item, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-[#2a2a4a] rounded-lg">
                      <ChevronRight className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-white font-medium">{item.rule}</p>
                        <p className="text-gray-400 text-sm">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Risk Hesaplama</h4>
                <div className="bg-[#2a2a4a] rounded-lg p-4">
                  <div className="space-y-4">
                    <div>
                      <p className="text-gray-400 text-sm mb-1">Örnek: $100 sermaye, %2 risk</p>
                      <p className="text-white">Maksimum kayıp = $100 x %2 = <span className="text-red-400 font-bold">$2</span></p>
                    </div>
                    <div className="border-t border-[#3a3a5a] pt-4">
                      <p className="text-gray-400 text-sm mb-2">Kaldıraç etkisi:</p>
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-[#1a1a2e] p-2 rounded">
                          <p className="text-white font-medium">3x</p>
                          <p className="text-green-400 text-xs">Güvenli</p>
                        </div>
                        <div className="bg-[#1a1a2e] p-2 rounded">
                          <p className="text-white font-medium">5x</p>
                          <p className="text-yellow-400 text-xs">Orta</p>
                        </div>
                        <div className="bg-[#1a1a2e] p-2 rounded">
                          <p className="text-white font-medium">10x+</p>
                          <p className="text-red-400 text-xs">Tehlikeli</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-lg font-semibold text-white mb-3">Önerilen Stop Loss/Take Profit</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-gray-400">
                        <th className="text-left p-2">Strateji</th>
                        <th className="text-center p-2">Stop Loss</th>
                        <th className="text-center p-2">Take Profit</th>
                        <th className="text-center p-2">Risk/Ödül</th>
                      </tr>
                    </thead>
                    <tbody className="text-white">
                      <tr className="border-t border-[#3a3a5a]">
                        <td className="p-2">RSI</td>
                        <td className="text-center p-2 text-red-400">%2</td>
                        <td className="text-center p-2 text-green-400">%4</td>
                        <td className="text-center p-2">1:2</td>
                      </tr>
                      <tr className="border-t border-[#3a3a5a]">
                        <td className="p-2">SMA</td>
                        <td className="text-center p-2 text-red-400">%1.5</td>
                        <td className="text-center p-2 text-green-400">%3</td>
                        <td className="text-center p-2">1:2</td>
                      </tr>
                      <tr className="border-t border-[#3a3a5a]">
                        <td className="p-2">MACD</td>
                        <td className="text-center p-2 text-red-400">%2</td>
                        <td className="text-center p-2 text-green-400">%5</td>
                        <td className="text-center p-2">1:2.5</td>
                      </tr>
                      <tr className="border-t border-[#3a3a5a]">
                        <td className="p-2">Scalping</td>
                        <td className="text-center p-2 text-red-400">%0.5</td>
                        <td className="text-center p-2 text-green-400">%1</td>
                        <td className="text-center p-2">1:2</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-red-400 font-medium">Kritik Uyarı</p>
                    <p className="text-red-200/80 text-sm mt-1">
                      Kripto piyasaları 7/24 açıktır ve çok volatildir. Tüm sermayenizi kaybedebilirsiniz.
                      Sadece kaybetmeyi göze alabileceğiniz parayı yatırın. Bu finansal tavsiye değildir.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
