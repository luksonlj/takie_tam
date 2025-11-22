# Performance Analysis Tools

Narzędzia do analizy wydajności bota handlowego BTC/USDT i porównania jego decyzji z rzeczywistymi danymi rynkowymi z Binance.

## Dostępne narzędzia

### 1. performance_analysis.py
**Główny skrypt analizy** - pobiera rzeczywiste dane historyczne z Binance i testuje strategię bota.

**Wymagania:**
- Połączenie z internetem
- Zainstalowane zależności (`pip install -r requirements.txt`)
- Plik `.env` z konfiguracją (bez kluczy API - dane historyczne są publiczne)

**Użycie:**
```bash
python performance_analysis.py
```

**Co robi:**
1. Pobiera 168 godzin (7 dni) danych historycznych BTC/USDT z Binance Futures
2. Stosuje strategię bota do tych danych (backtest)
3. Symuluje transakcje zgodnie z regułami bota
4. Generuje szczegółowy raport wydajności
5. Zapisuje raport do katalogu `reports/`

**Konfiguracja okresu analizy:**
Edytuj linię w `main()`:
```python
# Zmień hours=168 na żądaną liczbę godzin
data = analyzer.download_historical_data(hours=168)
```

### 2. demo_analysis.py
**Skrypt demonstracyjny** - używa symulowanych danych do pokazania jak działa analiza.

**Użycie:**
```bash
python demo_analysis.py
```

**Kiedy używać:**
- Gdy nie masz dostępu do internetu
- Chcesz przetestować działanie narzędzia
- Chcesz zobaczyć przykładowy raport

## Struktura raportu

Raport zawiera następujące sekcje:

### 📈 Statystyki sygnałów
- Liczba wszystkich przeanalizowanych sygnałów
- Podział na BUY / SELL / HOLD
- Procent każdego typu sygnału

### 💼 Statystyki transakcji
- Całkowita liczba wykonanych transakcji
- Liczba otwartych pozycji
- Liczba zamkniętych pozycji

### 💰 Zysk i Strata (P/L)
- **Całkowity P/L** w USDT
- Liczba wygranych transakcji (% sukcesu)
- Liczba przegranych transakcji
- Średni zysk na transakcję
- Średnia strata na transakcję
- Największy zysk
- Największa strata
- Wskaźnik Risk/Reward

### 📋 Szczegółowy rozkład transakcji
Dla każdej zamkniętej transakcji:
- Data i czas
- Typ (CLOSE_LONG, CLOSE_SHORT, STOP_LOSS, TAKE_PROFIT)
- Cena wejścia
- Cena wyjścia
- P/L w % i USDT

## Jak bot podejmuje decyzje (przypomnienie)

Bot analizuje rynek i generuje sygnały zgodnie z następującymi regułami:

### Sygnał BUY (min. 3 warunki spełnione, min. 40% pewności)
1. Trend zwyżkowy (MA10 > MA30 > MA60) - **+2 punkty**
2. OBV w trendzie wzrostowym - **+1 punkt**
3. Wysoki i rosnący wolumen - **+1 punkt**
4. Cena powyżej kluczowych średnich - **+1 punkt**

### Sygnał SELL (min. 3 warunki spełnione, min. 40% pewności)
1. Trend spadkowy (MA10 < MA30 < MA60) - **+2 punkty**
2. OBV w trendzie spadkowym - **+1 punkt**
3. Cena poniżej kluczowych średnich - **+1 punkt**
4. Wykryta dywergencja OBV - **+1 punkt**

### Zarządzanie pozycjami
- **Stop Loss:** Automatyczne zamknięcie przy stracie 2%
- **Take Profit:** Automatyczne zamknięcie przy zysku 4%
- **Dwukierunkowy handel:** Bot może otwierać LONG i SHORT

## Interpretacja wyników

### Dobry wynik backtestingu:
- ✅ Win rate > 50%
- ✅ Risk/Reward ratio > 1.5
- ✅ Total P/L > 0 USDT
- ✅ Średni zysk > średnia strata

### Sygnały ostrzegawcze:
- ⚠️ Win rate < 40%
- ⚠️ Bardzo dużo sygnałów HOLD (> 80%) - strategia zbyt konserwatywna
- ⚠️ Bardzo mało sygnałów HOLD (< 10%) - strategia zbyt agresywna
- ⚠️ Duże straty z stop-loss - zbyt niski próg SL

## Dostosowanie strategii

Jeśli wyniki nie są zadowalające, możesz zmienić parametry w `config.py`:

```python
# Zarządzanie ryzykiem
STOP_LOSS_PERCENT = 2.0      # Zwiększ jeśli zbyt częste SL
TAKE_PROFIT_PERCENT = 4.0    # Zmniejsz dla szybszego zbierania zysków

# Okresy średnich kroczących
MA_PERIODS = [10, 30, 60]    # Dostosuj do timeframe'a
```

Lub w `price_action.py`:

```python
# Wymagana liczba warunków dla sygnału (linia 182-186)
if buy_conditions >= 3:      # Zmniejsz dla więcej sygnałów
if sell_conditions >= 3:     # Zwiększ dla większej pewności

# Minimalna pewność sygnału (linia 184, 187)
confidence = min(buy_conditions * 20, 100)  # Dostosuj mnożnik
```

## Lokalizacja raportów

Wszystkie raporty są zapisywane w katalogu `reports/`:
- Format nazwy: `performance_YYYYMMDD_HHMMSS.txt` (rzeczywiste dane)
- Format nazwy: `demo_performance_YYYYMMDD_HHMMSS.txt` (dane symulowane)

## Przykładowe użycie

### Analiza ostatniego tygodnia:
```bash
# Pobierz dane z ostatniego tygodnia i przeanalizuj
python performance_analysis.py
```

### Analiza ostatnich 3 dni:
Edytuj `performance_analysis.py`:
```python
# W funkcji main(), zmień:
data = analyzer.download_historical_data(hours=72)  # 3 dni = 72 godziny
```

### Porównanie z okresem handlu bota:
Jeśli bot działał np. od 2025-11-22 09:00 do 2025-11-22 14:00:
```python
# Pobierz 5 godzin danych
data = analyzer.download_historical_data(hours=5)
```

## Rozwiązywanie problemów

### Błąd: "ModuleNotFoundError: No module named 'ccxt'"
```bash
pip install -r requirements.txt
```

### Błąd: "NetworkError" lub "Timeout"
- Sprawdź połączenie z internetem
- API Binance może być tymczasowo niedostępne - spróbuj ponownie
- Zmień na demo: `python demo_analysis.py`

### Błąd: "Insufficient data"
- Bot wymaga minimum 60 świeczek do analizy
- Zwiększ parametr `hours` w `download_historical_data()`

### Brak transakcji w raporcie
- Strategia może być zbyt konserwatywna
- Okres może być zbyt krótki
- Rynek był w konsolidacji (brak wyraźnego trendu)
- Rozważ dostosowanie parametrów strategii

## Dalsze kroki

1. **Uruchom rzeczywistą analizę:**
   ```bash
   python performance_analysis.py
   ```

2. **Przejrzyj raport** w katalogu `reports/`

3. **Porównaj wyniki** z oczekiwaniami

4. **Dostosuj strategię** jeśli potrzeba

5. **Testuj ponownie** na różnych okresach

6. **Po optymalizacji** - uruchom bota na testnet

7. **Po sukcesie na testnet** - rozważ prawdziwy handel (z ostrożnością!)

## Uwagi bezpieczeństwa

⚠️ **WAŻNE:**
- Backtesting NIE gwarantuje przyszłych wyników
- Wyniki historyczne mogą różnić się od rzeczywistego handlu
- Zawsze testuj na testnet przed prawdziwym handlem
- Nigdy nie inwestuj więcej niż możesz stracić
- Monitoruj bota regularnie podczas handlu

## Wsparcie

Jeśli masz pytania lub problemy:
1. Sprawdź logi bota w katalogu `logs/`
2. Przejrzyj dokumentację w `README.md`
3. Sprawdź konfigurację w `.env`
4. Zweryfikuj parametry w `config.py`
