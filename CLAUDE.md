# CryptoBot - Eclipse Scalper Entegrasyonu

## Proje Yapısı

```
crypto-bot/
│
├── eclipse_scalper/              # ████ ANA BOT - DOKUNMA ████
│   ├── bot/
│   │   ├── core.py              # Ana bot motoru (EclipseEternal)
│   │   └── runner.py            # Bot çalıştırıcı
│   ├── brain/                   # Durum yönetimi
│   │   ├── state.py             # PsycheState - pozisyon/trade durumu
│   │   └── persistence.py       # Disk'e kaydetme/yükleme
│   ├── data/
│   │   └── cache.py             # Fiyat verileri cache (GodEmperorDataOracle)
│   ├── config/
│   │   ├── settings.py          # Config/MicroConfig sınıfları
│   │   └── symbols.py           # İşlem sembolleri
│   ├── exchanges/
│   │   └── binance.py           # Binance Futures bağlantısı (ccxt)
│   ├── execution/               # İşlem yürütme modülleri
│   │   ├── entry.py             # Pozisyon girişi
│   │   ├── exit.py              # Pozisyon çıkışı
│   │   ├── guardian.py          # Pozisyon koruma
│   │   └── ...
│   ├── strategies/
│   │   └── eclipse_scalper.py   # Ana scalping stratejisi
│   ├── risk/
│   │   └── kill_switch.py       # Acil durdurma mekanizması
│   ├── notifications/
│   │   └── telegram.py          # Telegram bildirimleri
│   ├── utils/
│   │   └── logging.py           # Loglama sistemi
│   ├── main.py                  # Standalone çalıştırma
│   └── requirements.txt
│
├── api_bridge/                   # ████ FRONTEND KÖPRÜSÜ ████
│   ├── server.py                # FastAPI server
│   └── requirements.txt
│
├── crypto-bot-ui/               # ████ WEB ARAYÜZÜ ████
│   ├── app/                     # Next.js sayfaları
│   ├── components/              # React bileşenleri
│   └── contexts/
│       ├── AuthContext.tsx      # Kimlik doğrulama
│       └── BotContext.tsx       # Bot durumu (Eclipse'e bağlı)
│
├── .env.example                 # Ortam değişkenleri örneği
├── install_dependencies.bat     # Bağımlılık kurulumu
├── start_backend.bat            # API Bridge başlat
├── start_frontend.bat           # Frontend başlat
└── start_eclipse_standalone.bat # Eclipse'i doğrudan başlat
```

---

## Mimari

```
┌─────────────────────────────────────────────────────────────────┐
│                      NEXT.JS FRONTEND                           │
│                    http://localhost:3000                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API / WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API BRIDGE (FastAPI)                       │
│                    http://localhost:8000                        │
│   - Eclipse'e komut gönderir                                    │
│   - Durum bilgisini frontend'e aktarır                          │
│   - WebSocket ile real-time güncelleme                          │
└────────────────────────────┬────────────────────────────────────┘
                             │ Python import
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ECLIPSE SCALPER                             │
│              (Profesyonel Scalping Botu)                        │
│   - ccxt ile Binance Futures bağlantısı                         │
│   - Gelişmiş multi-indicator strateji                           │
│   - Otomatik pozisyon yönetimi                                  │
│   - Risk kontrolü (kill switch)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Çalıştırma

### 1. Bağımlılıkları Kur
```bash
install_dependencies.bat
```

### 2. .env Dosyasını Oluştur
```bash
copy .env.example .env
# .env dosyasını düzenle, API key'lerini ekle
```

### 3. Backend'i Başlat (Terminal 1)
```bash
start_backend.bat
```
Server: http://localhost:8000

### 4. Frontend'i Başlat (Terminal 2)
```bash
start_frontend.bat
```
Arayüz: http://localhost:3000

---

## API Endpoints

| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/api/status` | GET | Bot durumu |
| `/api/auth/connect` | POST | Binance bağlantısı |
| `/api/bot/start` | POST | Bot başlat |
| `/api/bot/stop` | POST | Bot durdur |
| `/api/positions` | GET | Açık pozisyonlar |
| `/api/balance` | GET | Bakiye bilgisi |
| `/api/trades` | GET | İşlem geçmişi |
| `/api/price/{symbol}` | GET | Anlık fiyat |
| `/ws` | WebSocket | Real-time güncellemeler |

---

## Bot Modları

| Mod | Equity | Açıklama |
|-----|--------|----------|
| `auto` | Otomatik | Equity'ye göre mod seçer |
| `micro` | < $100 | Küçük hesaplar için |
| `production` | >= $100 | Tam özellikli mod |

---

## Önemli Kurallar

1. **Eclipse Scalper'a DOKUNMA** - Tüm kodlar test edilmiş ve çalışır durumda
2. **API Bridge üzerinden erişim** - Frontend hiçbir zaman doğrudan Eclipse'e erişmez
3. **DRY_RUN ile test et** - Gerçek para kullanmadan önce simülasyon yap
4. **Stop loss kullan** - Risk yönetimi kritik

---

## Teknolojiler

- **Eclipse Scalper:** Python, ccxt, pandas, pandas-ta
- **API Bridge:** FastAPI, uvicorn, websockets
- **Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS
- **Grafikler:** lightweight-charts (TradingView)
