# BTC Trading Bot - Strategy Guide

## 📚 Spis Treści
1. [Podstawowa Strategia](#podstawowa-strategia)
2. [Piramidowanie Pozycji](#piramidowanie-pozycji)
3. [Kontrariańskie Wejścia](#kontrariańskie-wejścia)
4. [Parametry Konfiguracyjne](#parametry-konfiguracyjne)
5. [Przykłady Tradów](#przykłady-tradów)

---

## 📊 Podstawowa Strategia

Bot wykorzystuje analizę price action i wskaźniki techniczne do generowania sygnałów.

### Wskaźniki:
- **MA10, MA30, MA60**: Średnie kroczące dla wykrywania trendu
- **OBV (On-Balance Volume)**: Potwierdzenie trendu wolumenem
- **Main Trend**: Długoterminowy trend (MA60)
- **Volume Analysis**: Analiza wolumenu vs średnia

### Warunki Wejścia (BUY):
Wymaga **4/4 warunków** dla 80% confidence:
1. ✅ Trend BULLISH (MA10 > MA30 > MA60)
2. ✅ OBV trending up
3. ✅ Price above key MAs
4. ✅ Main trend BULLISH

### Zarządzanie Ryzykiem:
- **Stop Loss**: 3% od ceny wejścia
- **Take Profit**: 6% od ceny wejścia
- **Risk/Reward**: 1:2 ratio

---

## 📈 Piramidowanie Pozycji

**Cel**: Zwiększanie pozycji gdy trend się potwierdza

### Jak Działa:
1. **Pierwsze wejście**: Zgodnie z podstawową strategią (0.001 BTC)
2. **Warunek piramidowania**: Zysk +1.5% od ostatniej pozycji
3. **Dodatkowe poziomy**: Max 3 dolewki (łącznie 4 pozycje)
4. **Wielkość**: Każda dolewka 0.001 BTC (równa wielkość)

### Przykład LONG:
```
Wejście #1: $85,000 (0.001 BTC)
↓ Cena rośnie do $86,275 (+1.5%)
Wejście #2: $86,275 (0.001 BTC) - PYRAMID LEVEL 1
↓ Cena rośnie do $87,570 (+1.5% od $86,275)
Wejście #3: $87,570 (0.001 BTC) - PYRAMID LEVEL 2
↓ Cena rośnie do $88,885 (+1.5% od $87,570)
Wejście #4: $88,885 (0.001 BTC) - PYRAMID LEVEL 3 (MAX)

Średnia cena wejścia: $86,933
Całkowita pozycja: 0.004 BTC
```

### Zalety:
- ✅ Maksymalizuje zyski w silnym trendzie
- ✅ Wchodzi tylko gdy trend się potwierdza
- ✅ Zachowuje średnią cenę wejścia

### Ograniczenia:
- ⚠️ Max 3 poziomy (zabezpieczenie przed overleveraging)
- ⚠️ Wymaga kontynuacji trendu
- ⚠️ SL/TP obliczane od średniej ceny

---

## 🎯 Kontrariańskie Wejścia

**Cel**: Kupowanie spadków w trendzie wzrostowym (buying the dip)

### Jak Działa:

#### Bullish Contrarian (Buy the Dip):
1. **Warunek trendu**: Main Trend = BULLISH
2. **Warunek korekty**: Cena spadła -1% od lokalnego szczytu
3. **Potwierdzenie**: OBV nadal bullish (trend nie przerwany)
4. **Akcja**: Otwórz LONG mimo braku zwykłego sygnału BUY

#### Bearish Contrarian (Sell the Rip):
1. **Warunek trendu**: Main Trend = BEARISH
2. **Warunek korekty**: Cena wzrosła +1% od lokalnego dołka
3. **Potwierdzenie**: OBV nadal bearish (trend nie przerwany)
4. **Akcja**: Otwórz SHORT mimo braku zwykłego sygnału SELL

### Przykład Buy the Dip:
```
Main Trend: BULLISH
Lokalny szczyt: $87,500
↓ Cena spada do $86,625 (-1.0%)
OBV: BULLISH (trend nie przerwany) ✅
→ KONTRARIAŃSKIE WEJŚCIE LONG

Racjonale:
- Główny trend nadal wzrostowy
- To tylko korekta (pullback)
- Lepsza cena wejścia niż szczyt
- OBV potwierdza kontynuację trendu
```

### Zalety:
- ✅ Lepsze ceny wejścia (kupujesz taniej)
- ✅ Wykorzystuje naturalne korekty w trendzie
- ✅ OBV chroni przed fałszywymi sygnałami

### Ograniczenia:
- ⚠️ Tylko w kierunku głównego trendu
- ⚠️ Wymaga potwierdzenia OBV
- ⚠️ Nie działa w trendless market

---

## ⚙️ Parametry Konfiguracyjne

### Podstawowe (config.py):
```python
STOP_LOSS_PERCENT = 3.0      # 3% stop loss
TAKE_PROFIT_PERCENT = 6.0    # 6% take profit
TRADE_AMOUNT = 0.001         # Wielkość pozycji w BTC
MIN_CONFIDENCE = 60          # Minimalny confidence %
```

### Piramidowanie (trading_bot.py):
```python
max_pyramid_levels = 3       # Max 3 dolewki
pyramid_step_percent = 1.5   # Co +1.5% zysku
```

### Kontrarian (trading_bot.py):
```python
pullback_percent = 1.0       # -1% pullback w uptrend
bounce_percent = 1.0         # +1% bounce w downtrend
```

---

## 💡 Przykłady Tradów

### 1. Prosty Trade (bez piramidowania):
```
19:00 - BUY Signal: $85,000 (80% confidence)
       → Otwórz LONG 0.001 BTC

19:30 - Cena: $87,600 (+3.06%)
       → Trend nadal BULLISH, trzymaj

20:00 - Cena: $90,100 (+6.0%)
       → TAKE PROFIT triggered
       → Zamknij LONG: +$5.10 USDT zysk
```

### 2. Trade z Piramidowaniem:
```
10:00 - BUY Signal: $85,000 (80% confidence)
       → Otwórz LONG #1: 0.001 BTC @ $85,000

10:30 - Cena: $86,275 (+1.5% od $85,000)
       → Pyramid trigger!
       → Dodaj LONG #2: 0.001 BTC @ $86,275
       → Pozycja: 0.002 BTC, średnia $85,638

11:00 - Cena: $87,570 (+1.5% od $86,275)
       → Pyramid trigger!
       → Dodaj LONG #3: 0.001 BTC @ $87,570
       → Pozycja: 0.003 BTC, średnia $86,282

12:00 - Cena: $91,459 (+6% od średniej $86,282)
       → TAKE PROFIT triggered
       → Zamknij całą pozycję: +$15.53 USDT zysk
```

### 3. Kontrariańskie Wejście:
```
14:00 - Main Trend: BULLISH
       → Lokalny szczyt: $88,000

14:15 - Cena spadła do $87,120 (-1.0% pullback)
       → OBV: BULLISH ✅
       → Kontrariańskie wejście!
       → Otwórz LONG: 0.001 BTC @ $87,120

14:30 - Cena: $88,500 (+1.58%)
       → Trend wznowiony

15:00 - Cena: $92,347 (+6.0%)
       → TAKE PROFIT
       → Zysk: +$5.23 USDT

Vs normalny trade:
- Gdyby czekał na zwykły sygnał BUY @ $88,500
- Take profit @ $93,810
- Zysk: +$5.31 USDT
- ALE: Kontrarian dał lepszą cenę wejścia!
```

---

## 🎓 Najlepsze Praktyki

### Kiedy Strategia Działa Najlepiej:
1. ✅ **Silny trending market** - piramidowanie maksymalizuje zyski
2. ✅ **Zdrowe korekty** - kontrarian wykorzystuje pullbacki
3. ✅ **Wysoki volume** - potwierdza siłę trendów
4. ✅ **Wyraźne OBV trends** - chroni przed fałszywymi sygnałami

### Kiedy Uważać:
1. ⚠️ **Choppy/sideways market** - dużo fałszywych sygnałów
2. ⚠️ **Niski volume** - słabe potwierdzenie
3. ⚠️ **News events** - nagłe odwrócenia mogą aktywować SL
4. ⚠️ **Extremalne volatility** - może przeskoczyć SL/TP

### Monitoring:
- Sprawdzaj **4-godzinne raporty** w folderze `reports/`
- Śledź **win rate** - powinien być >50%
- Monitoruj **średni P/L** - powinien być pozytywny
- Obserwuj **pyramid effectiveness** - ile poziomów się udaje

---

## 📖 Dalsze Kroki

1. **Testuj strategię** - minimum 1 tydzień paper trading
2. **Analizuj raporty** - sprawdź co działa, co nie
3. **Dostrajaj parametry** - jeśli potrzeba (ostrożnie!)
4. **Rozważ live trading** - tylko po udanych testach
5. **Start small** - zacznij od minimalnych kwot

**Powodzenia! 🚀**
