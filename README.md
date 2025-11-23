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

- **Analiza wydajności:**
  - Backtest strategii na danych historycznych z Binance
  - Szczegółowe raporty P/L w USDT
  - Statystyki sygnałów i transakcji
  - Analiza win rate i risk/reward ratio

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

**UWAGA:** Strategia została zoptymalizowana (23.11.2025) - szczegóły w `OPTIMIZATION_CHANGES.md`

### Sygnał BUY (kupno/otwarcie LONG)
Bot generuje sygnał kupna gdy:
- Trend jest zwyżkowy (MA10 > MA30 > MA60)
- OBV pokazuje trend wzrostowy
- Wolumen jest wysoki
- Wolumen jest rosnący
- Cena powyżej kluczowych średnich kroczących
- Cena powyżej długoterminowej MA60
- **Minimum 4 warunki muszą być spełnione** (zwiększone z 3)
- **Minimum 60% pewności sygnału** (zwiększone z 40%)

**Akcje:**
- Otwiera pozycję LONG jeśli nie ma żadnej pozycji
- Zamyka pozycję SHORT jeśli była otwarta

### Sygnał SELL (sprzedaż/otwarcie SHORT)
Bot generuje sygnał sprzedaży gdy:
- **Główny trend NIE jest wzrostowy** (filtr ochronny!)
- Trend jest spadkowy (MA10 < MA30 < MA60)
- OBV pokazuje trend spadkowy
- Cena poniżej kluczowych średnich kroczących
- Cena poniżej długoterminowej MA60
- Wykryta dywergencja OBV
- Wysoki wolumen (wymagane dla potwierdzenia)
- **Minimum 4 warunki muszą być spełnione** (zwiększone z 3)
- **Minimum 60% pewności sygnału** (zwiększone z 40%)

**Akcje:**
- Zamyka pozycję LONG jeśli była otwarta
- Otwiera pozycję SHORT jeśli nie ma żadnej pozycji (wymaga margin/futures)

**WAŻNE:** Bot blokuje wszystkie sygnały SHORT gdy główny trend (MA30 vs MA60) jest wzrostowy!

### Stop Loss / Take Profit
- **Stop Loss:** Automatyczne zamknięcie pozycji przy stracie 3% (zwiększone z 2%)
- **Take Profit:** Automatyczne zamknięcie pozycji przy zysku 6% (zwiększone z 4%)
- **Risk/Reward Ratio:** 1:2
- Działa dla obu kierunków: LONG i SHORT

## Struktura projektu

```
.
├── trading_bot.py            # Główny plik bota
├── indicators.py             # Moduł obliczania wskaźników
├── price_action.py           # Moduł analizy price action
├── config.py                 # Konfiguracja
├── performance_analysis.py   # Analiza wydajności (rzeczywiste dane)
├── demo_analysis.py          # Demo analizy (dane symulowane)
├── requirements.txt          # Zależności
├── .env.example              # Przykładowa konfiguracja
├── README.md                 # Dokumentacja
├── PERFORMANCE_ANALYSIS.md   # Dokumentacja analizy wydajności
├── logs/                     # Logi z pracy bota
└── reports/                  # Raporty wydajności
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

## Analiza wydajności

Bot zawiera narzędzia do analizy wydajności i backtestingu strategii:

### Analiza rzeczywistych danych z Binance
```bash
python performance_analysis.py
```

Pobiera dane historyczne z Binance i testuje strategię bota. Generuje szczegółowy raport:
- Statystyki sygnałów (BUY/SELL/HOLD)
- Liczba i wyniki transakcji
- Win rate i risk/reward ratio
- Szczegółowe P/L dla każdej transakcji w USDT

### Demo z danymi symulowanymi
```bash
python demo_analysis.py
```

Demonstracja analizy wydajności używająca symulowanych danych (nie wymaga internetu).

### Więcej informacji
Szczegółowa dokumentacja narzędzi analizy dostępna w pliku `PERFORMANCE_ANALYSIS.md`.

## Wsparcie

W razie problemów:
1. Sprawdź logi bota w katalogu `logs/`
2. Upewnij się, że klucze API są poprawne
3. Sprawdź połączenie z internetem
4. Sprawdź limity API na giełdzie
5. Przejrzyj raporty wydajności w katalogu `reports/`

## Licencja

MIT License

## Disclaimer

Ten bot jest narzędziem edukacyjnym. Handel kryptowalutami niesie ze sobą wysokie ryzyko. Autor nie ponosi odpowiedzialności za straty finansowe wynikające z użycia tego oprogramowania.
