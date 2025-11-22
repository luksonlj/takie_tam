# BTC/USDT Trading Bot

Prosty bot handlowy dla pary BTC/USDT wykorzystujący analizę techniczną i price action.

## Funkcje

- **Wskaźniki techniczne:**
  - OBV (On-Balance Volume) - analiza przepływu wolumenu
  - Średnie kroczące: MA10, MA30, MA60
  - Analiza wolumenu z wykrywaniem nietypowych wartości

- **Analiza Price Action:**
  - Wykrywanie trendów (bullish/bearish/neutral)
  - Analiza dywergencji OBV
  - Potwierdzenie sygnałów poprzez wolumen

- **Zarządzanie ryzykiem:**
  - Stop Loss automatyczny
  - Take Profit automatyczny
  - Maksymalny rozmiar pozycji

- **Tryb testowy:**
  - Możliwość pracy na testnet bez prawdziwych transakcji

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone <repository-url>
cd takie_tam
```

2. Zainstaluj wymagane biblioteki:
```bash
pip install -r requirements.txt
```

3. Skonfiguruj plik .env:
```bash
cp .env.example .env
# Edytuj .env i dodaj swoje klucze API
```

## Konfiguracja

Edytuj plik `.env` i ustaw następujące parametry:

```bash
# Konfiguracja giełdy
EXCHANGE=binance
API_KEY=twoj_klucz_api
API_SECRET=twoj_sekret_api

# Konfiguracja handlu
SYMBOL=BTC/USDT
TIMEFRAME=1h
TRADE_AMOUNT=0.001
TESTNET=true  # Ustaw false dla prawdziwego handlu

# Zarządzanie ryzykiem
MAX_POSITION_SIZE=0.01
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=4.0
```

## Użycie

Uruchom bota:
```bash
python trading_bot.py
```

Bot będzie:
1. Pobierał dane OHLCV z giełdy co 30 sekund
2. Obliczał wskaźniki techniczne
3. Analizował price action
4. Generował sygnały handlowe BUY i SELL
5. Wykonywał transakcje w obie strony (LONG i SHORT)

## Strategia handlowa

### Sygnał BUY (kupno/otwarcie LONG)
Bot generuje sygnał kupna gdy:
- Trend jest zwyżkowy (MA10 > MA30 > MA60)
- OBV pokazuje trend wzrostowy
- Wolumen jest wysoki i rosnący
- Cena powyżej kluczowych średnich kroczących
- Minimum 3 warunki muszą być spełnione
- Minimum 40% pewności sygnału

**Akcje:**
- Otwiera pozycję LONG jeśli nie ma żadnej pozycji
- Zamyka pozycję SHORT jeśli była otwarta

### Sygnał SELL (sprzedaż/otwarcie SHORT)
Bot generuje sygnał sprzedaży gdy:
- Trend jest spadkowy (MA10 < MA30 < MA60)
- OBV pokazuje trend spadkowy
- Cena poniżej kluczowych średnich kroczących
- Wykryta dywergencja OBV
- Minimum 3 warunki muszą być spełnione
- Minimum 40% pewności sygnału

**Akcje:**
- Zamyka pozycję LONG jeśli była otwarta
- Otwiera pozycję SHORT jeśli nie ma żadnej pozycji (wymaga margin/futures)

### Stop Loss / Take Profit
- **Stop Loss:** Automatyczne zamknięcie pozycji przy stracie 2% (domyślnie)
- **Take Profit:** Automatyczne zamknięcie pozycji przy zysku 4% (domyślnie)
- Działa dla obu kierunków: LONG i SHORT

## Struktura projektu

```
.
├── trading_bot.py      # Główny plik bota
├── indicators.py       # Moduł obliczania wskaźników
├── price_action.py     # Moduł analizy price action
├── config.py           # Konfiguracja
├── requirements.txt    # Zależności
├── .env.example        # Przykładowa konfiguracja
└── README.md           # Dokumentacja
```

## Uwagi bezpieczeństwa

⚠️ **WAŻNE:**
- Zawsze testuj bota na testnet przed uruchomieniem na prawdziwych środkach
- Nie udostępniaj swoich kluczy API nikomu
- Używaj kluczy API z ograniczonymi uprawnieniami (tylko handel, bez wypłat)
- Regularnie monitoruj działanie bota
- Inwestuj tylko to, na czego stratę możesz sobie pozwolić

## Wymagania systemowe

- Python 3.8+
- Połączenie z internetem
- Konto na giełdzie (Binance lub inna wspierana przez CCXT)
- Klucze API z uprawnieniami do handlu

## Wsparcie

W razie problemów:
1. Sprawdź logi bota
2. Upewnij się, że klucze API są poprawne
3. Sprawdź połączenie z internetem
4. Sprawdź limity API na giełdzie

## Licencja

MIT License

## Disclaimer

Ten bot jest narzędziem edukacyjnym. Handel kryptowalutami niesie ze sobą wysokie ryzyko. Autor nie ponosi odpowiedzialności za straty finansowe wynikające z użycia tego oprogramowania.
