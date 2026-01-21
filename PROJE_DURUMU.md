# CryptoBot - Proje Durumu

**Son Güncelleme:** 2026-01-21 (21:00)

---

## Mevcut Durum: ECLIPSE SCALPER TAM ENTEGRE + SIMULATION MODE

### Bağlantı Bilgileri
- **API Bridge:** http://localhost:8000 (Eclipse Scalper entegre)
- **Frontend:** http://localhost:3000 (Next.js)
- **Binance Testnet:** Bağlı (~4973 USDT)

---

## Bu Oturumda Yapılanlar (21 Ocak 2026 - Son)

### 1. Unicode Encoding Hatası Düzeltildi
- `eclipse_scalper/utils/logging.py` dosyasındaki Unicode karakterler ASCII ile değiştirildi
- `Φ` → `*` (Yunan harfi)
- `—` → `-` (em dash)

### 2. Server.py Alan Eşleşmeleri Düzeltildi
| Alan | Önceki | Sonrası |
|------|--------|---------|
| Position PnL | `unrealized_pnl` (yoktu) | `(current_price - entry_price) * size * direction` hesaplanıyor |
| win_rate | 0-1 arası | 0-100 arası |
| max_drawdown | 0-1 arası | 0-100 arası |
| current_price | Eksikti | `bot.data.price` map'inden alınıyor |

### 3. IDE Uyarıları Çözüldü
- `api_bridge/pyrightconfig.json` oluşturuldu
- Pylance artık `eclipse_scalper` klasörünü tanıyor

### 4. Simulation Mode Eklendi
- Testnet modunda Eclipse loop'larının simülasyonu gösteriliyor
- Frontend'de Bot Logları panelinde tüm bileşenler görünür

### 5. Stop Bot Hatası Düzeltildi
- `asyncio.Task` kontrolü eklendi (simulation modda string olabilir)

---

## Çalıştırma Komutları

### 1. API Bridge'i Başlat
```bash
cd api_bridge
py server.py
```
URL: http://localhost:8000

### 2. Frontend'i Başlat
```bash
cd crypto-bot-ui
npm run dev
```
URL: http://localhost:3000

### 3. Giriş Yap
- API Key ve Secret ile giriş
- Testnet checkbox'ı işaretli → Simulation Mode
- Testnet kapalı → Eclipse Mode (Mainnet)

---

## Bot Modları

### Eclipse Mode (Testnet kapalı - Mainnet)
- Tam Eclipse Scalper entegrasyonu
- Gerçek loop'lar çalışır (guardian, data, entry)
- Gerçek strateji sinyalleri
- Otomatik trade execution

### Simulation Mode (Testnet açık)
- CCXT bağlantısı
- Eclipse loop'larının simülasyonu
- Tüm bileşenler loglarda görünür
- Gerçek işlem yapılmaz

---

## Frontend'de Görünen Loglar (Simulation Mode)

```
==================================================
[BRAIN] Eclipse Scalper BRAIN SIMULATION aktif
[MODE] TESTNET modu
==================================================
[BOOT] ECLIPSE SCALPER SIMULATION BASLATILIYOR...
[CONFIG] Mod: auto | Semboller: ['BTCUSDT', 'ETHUSDT']
==================================================
[SYMBOLS] 2 sembol aktif: BTCUSDT, ETHUSDT
[SAFE] TESTNET SIMULATION - Gercek islem yapilmayacak
--------------------------------------------------
[LOOPS] Bot loop'lari SIMULATION baslatiliyor...
[CORE] Eclipse CORE SIMULATION uyandirildi
[GUARDIAN] Guardian Loop SIMULATION AKTIF
[DATA] Data Loop SIMULATION AKTIF - Fiyat izleme
[ENTRY] Entry Loop SIMULATION AKTIF
[SIGNAL] Sinyal tarama SIMULATION BASLADI
[STATUS] Status Updater AKTIF - WebSocket broadcast
--------------------------------------------------
[OK] ECLIPSE SCALPER SIMULATION TAMAMEN AKTIF!
[TASKS] Simulated: guardian, data, entry, status
==================================================
```

---

## Dosya Yapısı (Güncel)

```
crypto-bot/
├── api_bridge/
│   ├── server.py              # API Bridge v2.1 (Eclipse + Simulation)
│   └── pyrightconfig.json     # IDE ayarları (YENİ)
│
├── eclipse_scalper/           # Eclipse Scalper Bot
│   ├── bot/
│   │   ├── core.py            # EclipseEternal ana sınıf
│   │   └── runner.py          # Standalone runner
│   ├── execution/
│   │   ├── guardian.py        # Brainstem loop
│   │   ├── entry.py           # Entry logic
│   │   ├── entry_loop.py      # Entry scheduling
│   │   ├── exit.py            # Exit handling
│   │   ├── data_loop.py       # Price/OHLCV polling
│   │   └── bootstrap.py       # Standalone bootstrap
│   ├── strategies/
│   │   └── eclipse_scalper.py # Sinyal stratejisi
│   ├── utils/
│   │   └── logging.py         # Logging (Unicode düzeltildi)
│   └── config/
│       └── settings.py        # Config, MicroConfig
│
├── crypto-bot-ui/             # Next.js Frontend
│   ├── app/
│   │   ├── globals.css        # Modern stiller
│   │   ├── page.tsx           # Ana sayfa
│   │   └── api/               # API routes
│   ├── components/
│   │   ├── BotSwitch.tsx      # Bot açma/kapama + tasks
│   │   ├── BotControlPanel.tsx# Tüm bot ayarları
│   │   ├── PositionsPanel.tsx # Açık pozisyonlar + uptime
│   │   ├── LogsPanel.tsx      # Bot logları
│   │   ├── HelpModal.tsx      # Kullanım kılavuzu
│   │   ├── TradeButtons.tsx   # AL/SAT
│   │   ├── BalanceCard.tsx    # Bakiye
│   │   ├── TradeHistory.tsx   # İşlem geçmişi
│   │   ├── PriceChart.tsx     # Grafik
│   │   └── LoginModal.tsx     # Giriş
│   ├── contexts/
│   │   ├── BotContext.tsx     # Bot state
│   │   └── AuthContext.tsx    # Auth state
│   └── hooks/
│       └── useBinanceData.ts
│
├── PROJE_DURUMU.md            # Bu dosya
└── CLAUDE.md                  # Proje talimatları
```

---

## API Credentials (Testnet)
```
API Key: CT5wmMvyeRzANwDgqB0Gymg0bu07xHhp91DfzgHkMMC8ibDcrddXjXLv4mPf44hg
API Secret: 7ACFUWNoAyTSWSHnuOST2sOWADGMSHbVay9YDz9W9pirSLoovA5GBsgv8tUxY55M
```

---

## WebSocket Mesaj Tipleri

| Tip | Açıklama |
|-----|----------|
| `status` | Bot durumu (equity, positions, tasks, uptime) |
| `log` | Tek log mesajı |
| `logs_init` | İlk bağlantıda tüm loglar |
| `new_signal` | Yeni trading sinyali |
| `new_trade` | Gerçekleşen trade |
| `bot_started` | Bot başladı (tasks listesi ile) |
| `bot_stopped` | Bot durdu |
| `positions_update` | Pozisyon güncellemesi |
| `error` | Hata mesajı |
| `pong` | Ping yanıtı |

---

## Sonraki Oturum İçin

1. Bu dosyayı oku (`PROJE_DURUMU.md`)
2. `cd api_bridge && py server.py` çalıştır
3. `cd crypto-bot-ui && npm run dev` çalıştır
4. Tarayıcıda http://localhost:3000 aç
5. Testnet credentials ile giriş yap
6. Bot'u başlat ve logları kontrol et

---

## Notlar

1. **Testnet = Simulation Mode** - Loop'lar simüle edilir, gerçek işlem yapılmaz
2. **Mainnet = Eclipse Mode** - Tam otomasyon, gerçek trading
3. **Dry Run** - Testnet'te otomatik aktif
4. **IDE Uyarıları** - pyrightconfig.json ile çözüldü (VS Code yeniden yükle)
5. **Unicode Hatası** - logging.py'de düzeltildi
