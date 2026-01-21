# Teknik Geliştirme Günlüğü

## Oturum: 21 Ocak 2026

---

## Değiştirilen Dosyalar (Detaylı)

### 1. crypto-bot-ui/contexts/BotContext.tsx

**Eklenen Interface'ler:**
```typescript
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
  // Risk yönetimi
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

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'trade';
  message: string;
}
```

**Eklenen State'ler:**
- `logs: LogEntry[]`
- `addLog()` ve `clearLogs()` fonksiyonları

**WebSocket Mesaj Handler Güncellemeleri:**
- `new_signal` → log ekleme
- `new_trade` → log ekleme
- `bot_started` → log ekleme
- `bot_stopped` → log ekleme
- `log` → backend'den gelen logları işleme

---

### 2. crypto-bot-ui/components/BotControlPanel.tsx

**Eklenen Sabitler:**
```typescript
const INTERVALS = [
  { value: '1m', label: '1 Dakika' },
  { value: '5m', label: '5 Dakika' },
  { value: '15m', label: '15 Dakika' },
  { value: '1h', label: '1 Saat' },
  { value: '4h', label: '4 Saat' },
  { value: '1d', label: '1 Gün' },
];

const STRATEGIES = [
  // ... mevcut stratejiler
  { value: 'bollinger', label: 'Bollinger Bands', description: 'Bollinger bantları stratejisi' },
];
```

**Eklenen UI Bölümleri:**
- Zaman Dilimi seçim butonları
- Günlük Max İşlem input
- Max Pozisyon % input
- MACD parametreleri (Gelişmiş Ayarlar)
- Bollinger parametreleri (Gelişmiş Ayarlar)

---

### 3. crypto-bot-ui/components/PositionsPanel.tsx (YENİ)

**Özellikler:**
- Açık pozisyon listesi
- Equity, Günlük P/L, Max DD istatistikleri
- Long/Short pozisyon gösterimi
- Leverage ve PnL bilgileri
- Aktif semboller listesi

---

### 4. crypto-bot-ui/components/LogsPanel.tsx (YENİ)

**Özellikler:**
- Log seviyesi filtreleme (all, info, warn, error, trade)
- Renk kodlu log mesajları
- Timestamp gösterimi
- Temizleme ve genişletme butonları
- Max 100 log tutma

---

### 5. crypto-bot-ui/components/HelpModal.tsx (YENİ)

**Sekmeler:**
1. Başlangıç - Genel bilgi ve 5 adımlık rehber
2. Stratejiler - Tüm stratejilerin detaylı açıklaması
3. $100 Örneği - Pratik senaryo ve hedefler
4. Risk Yönetimi - Altın kurallar ve öneriler

---

### 6. crypto-bot-ui/app/globals.css

**Eklenen CSS Sınıfları:**
```css
.glass-card {
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
}

.inner-card {
  background: rgba(20, 20, 35, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.btn-modern {
  /* Parlama animasyonu */
}

.gradient-text {
  background: linear-gradient(135deg, #a855f7, #3b82f6);
  -webkit-background-clip: text;
}

.glow-purple { box-shadow: 0 0 20px rgba(139, 92, 246, 0.3); }
.glow-green { box-shadow: 0 0 20px rgba(34, 197, 94, 0.3); }
```

**Arka Plan:**
```css
body {
  background-image:
    radial-gradient(ellipse at 20% 20%, rgba(124, 58, 237, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(59, 130, 246, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(139, 92, 246, 0.03) 0%, transparent 70%);
}
```

---

### 7. crypto-bot-ui/app/page.tsx

**Değişiklikler:**
- HelpModal import ve state eklendi
- PositionsPanel ve LogsPanel import edildi
- Header'a "Nasıl Kullanılır?" butonu eklendi
- Layout güncellendi (TradeHistory + PositionsPanel yan yana, LogsPanel altta)
- Modern stiller uygulandı

---

## API Endpoint'leri (api_bridge/server.py)

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/api/auth/connect` | POST | Binance bağlantısı |
| `/api/bot/start` | POST | Bot başlat |
| `/api/bot/stop` | POST | Bot durdur |
| `/api/status` | GET | Bot durumu |
| `/api/trade` | POST | Manuel işlem |
| `/api/trades` | GET | İşlem geçmişi |
| `/api/positions` | GET | Açık pozisyonlar |
| `/api/balance` | GET | Bakiye |
| `/api/price/{symbol}` | GET | Fiyat |
| `/ws` | WebSocket | Real-time güncellemeler |

---

## WebSocket Mesaj Tipleri

**Gelen (Frontend'e):**
- `status` - Bot durumu güncellemesi
- `price` - Fiyat güncellemesi
- `new_signal` - Yeni sinyal
- `new_trade` - Yeni işlem
- `bot_started` - Bot başladı
- `bot_stopped` - Bot durdu
- `log` - Log mesajı
- `pong` - Ping yanıtı

**Giden (Backend'e):**
- `ping` - Bağlantı kontrolü
- `get_status` - Durum isteği
- `get_price` - Fiyat isteği

---

## Renk Kodları (UI)

| Element | Renk | Kullanım |
|---------|------|----------|
| Primary | `purple-600` / `violet-500` | Butonlar, seçimler |
| Success | `green-500` / `emerald-500` | AL butonu, kar |
| Danger | `red-500` / `rose-500` | SAT butonu, zarar |
| Warning | `yellow-500` / `orange-500` | Uyarılar |
| Info | `blue-500` | Bilgi kartları |
| Background | `#0a0a14` | Ana arka plan |
| Card | `rgba(26, 26, 46, 0.85)` | Glassmorphism kartlar |

---

## Sorun Giderme

### "Bot bağlı değil" hatası
1. API Bridge'in çalıştığından emin ol: `http://localhost:8000`
2. Frontend'i yenile
3. Tekrar giriş yap

### Trade başarısız
1. Minimum order değerini kontrol et (100 USDT)
2. Bakiye yeterliliğini kontrol et
3. API Bridge loglarını kontrol et

### WebSocket bağlantı kopması
- Otomatik yeniden bağlanma var (5 saniye)
- Sayfa yenileme sorunu çözer

---

## Performans Notları

- Fiyat polling: 15 saniye interval
- Max log sayısı: 100
- WebSocket timeout: 2 saniye
- Balance refresh: 30 saniye

---

## Test Edilenler

- [x] Giriş/çıkış
- [x] Bot başlat/durdur
- [x] Manuel AL/SAT işlemi
- [x] İşlem geçmişi görüntüleme
- [x] Strateji değiştirme
- [x] Zaman dilimi değiştirme
- [x] Log filtreleme
- [x] Responsive tasarım
- [x] Glassmorphism efektleri
