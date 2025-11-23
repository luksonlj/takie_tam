"""
Analiza opłacalności stakingu kryptowalut
Ile trzeba zainwestować, żeby staking miał sens?
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Tuple
from datetime import datetime


@dataclass
class StakingCoin:
    """Dane o stakingu konkretnej kryptowaluty"""
    symbol: str
    name: str
    price_usd: float
    apy_min: float  # Minimalna roczna stopa zwrotu (%)
    apy_max: float  # Maksymalna roczna stopa zwrotu (%)
    min_stake: float  # Minimalna kwota do stakingu (w monetach)
    lock_period_days: int  # Okres blokady (0 = brak blokady)
    staking_type: str  # 'native', 'exchange', 'liquid', 'defi'
    platform: str  # Gdzie stakować
    risk_level: str  # 'low', 'medium', 'high'
    additional_info: str


@dataclass
class InvestmentGoal:
    """Cel inwestycyjny"""
    monthly_income_pln: float
    yearly_income_pln: float


class StakingAnalyzer:
    """Analizator opłacalności stakingu"""

    def __init__(self, usd_to_pln: float = 4.0):
        self.usd_to_pln = usd_to_pln
        self.coins = self.setup_staking_coins()

    def setup_staking_coins(self) -> Dict[str, StakingCoin]:
        """Konfiguracja popularnych monet do stakingu (dane z listopada 2024)"""

        return {
            'ETH': StakingCoin(
                symbol='ETH',
                name='Ethereum',
                price_usd=3100.0,
                apy_min=2.5,
                apy_max=4.5,
                min_stake=0.01,  # Na giełdach typu Binance, Kraken
                lock_period_days=0,  # Liquid staking bez blokady
                staking_type='native/liquid',
                platform='Lido, Rocket Pool, Binance, Kraken',
                risk_level='low',
                additional_info='Najbezpieczniejszy, największa kapitalizacja'
            ),
            'ETH_SOLO': StakingCoin(
                symbol='ETH',
                name='Ethereum (Solo Staking)',
                price_usd=3100.0,
                apy_min=3.0,
                apy_max=5.0,
                min_stake=32.0,  # Wymagane do własnego walidatora
                lock_period_days=0,
                staking_type='native',
                platform='Własny node',
                risk_level='medium',
                additional_info='Wymaga 32 ETH + techniczne umiejętności'
            ),
            'SOL': StakingCoin(
                symbol='SOL',
                name='Solana',
                price_usd=145.0,
                apy_min=6.0,
                apy_max=8.5,
                min_stake=0.01,
                lock_period_days=0,
                staking_type='native',
                platform='Phantom, Binance, Kraken',
                risk_level='medium',
                additional_info='Wysoki APY, ale większa zmienność'
            ),
            'ADA': StakingCoin(
                symbol='ADA',
                name='Cardano',
                price_usd=0.60,
                apy_min=2.5,
                apy_max=4.5,
                min_stake=10.0,
                lock_period_days=0,
                staking_type='native',
                platform='Daedalus, Yoroi, Binance',
                risk_level='low',
                additional_info='Brak blokady, można wypłacić w każdej chwili'
            ),
            'DOT': StakingCoin(
                symbol='DOT',
                name='Polkadot',
                price_usd=7.0,
                apy_min=10.0,
                apy_max=14.0,
                min_stake=1.0,  # Na giełdach
                lock_period_days=28,  # 28 dni unbonding period
                staking_type='native',
                platform='Polkadot.js, Binance, Kraken',
                risk_level='medium',
                additional_info='Wysoki APY, ale 28 dni blokady przy unbonding'
            ),
            'ATOM': StakingCoin(
                symbol='ATOM',
                name='Cosmos',
                price_usd=9.5,
                apy_min=15.0,
                apy_max=20.0,
                min_stake=0.1,
                lock_period_days=21,  # 21 dni unbonding
                staking_type='native',
                platform='Keplr, Cosmostation, Binance',
                risk_level='medium',
                additional_info='Bardzo wysoki APY, ekosystem Cosmos'
            ),
            'MATIC': StakingCoin(
                symbol='MATIC',
                name='Polygon',
                price_usd=0.90,
                apy_min=4.0,
                apy_max=6.5,
                min_stake=1.0,
                lock_period_days=3,
                staking_type='native',
                platform='Binance, Lido',
                risk_level='medium',
                additional_info='Layer 2 dla Ethereum, średni APY'
            ),
            'AVAX': StakingCoin(
                symbol='AVAX',
                name='Avalanche',
                price_usd=38.0,
                apy_min=6.0,
                apy_max=9.0,
                min_stake=25.0,  # Dla własnego walidatora
                lock_period_days=14,
                staking_type='native',
                platform='Avalanche Wallet, Binance',
                risk_level='medium',
                additional_info='Szybka sieć, rosnący ekosystem DeFi'
            ),
            'BNB': StakingCoin(
                symbol='BNB',
                name='Binance Coin',
                price_usd=620.0,
                apy_min=4.0,
                apy_max=7.0,
                min_stake=0.1,
                lock_period_days=7,  # Zależy od produktu
                staking_type='exchange',
                platform='Binance (DeFi Staking, Locked Staking)',
                risk_level='low',
                additional_info='Natywny token Binance, różne opcje stakingu'
            ),
            'ALGO': StakingCoin(
                symbol='ALGO',
                name='Algorand',
                price_usd=0.25,
                apy_min=5.0,
                apy_max=7.5,
                min_stake=1.0,
                lock_period_days=0,
                staking_type='native',
                platform='Algorand Wallet, Binance',
                risk_level='medium',
                additional_info='Governance rewards, szybka finalizacja'
            ),
            'TIA': StakingCoin(
                symbol='TIA',
                name='Celestia',
                price_usd=6.5,
                apy_min=12.0,
                apy_max=16.0,
                min_stake=1.0,
                lock_period_days=21,
                staking_type='native',
                platform='Keplr, Binance',
                risk_level='high',
                additional_info='Nowy projekt (modular blockchain), wysokie APY'
            ),
            'USDT_CEFI': StakingCoin(
                symbol='USDT',
                name='Tether (CeFi)',
                price_usd=1.0,
                apy_min=3.0,
                apy_max=6.0,
                min_stake=100.0,
                lock_period_days=0,  # Flexible
                staking_type='lending',
                platform='Binance Earn, Crypto.com, Nexo',
                risk_level='low',
                additional_info='Stabilna wartość, brak zmienności ceny'
            ),
            'USDC_DEFI': StakingCoin(
                symbol='USDC',
                name='USD Coin (DeFi)',
                price_usd=1.0,
                apy_min=4.0,
                apy_max=12.0,
                min_stake=100.0,
                lock_period_days=0,
                staking_type='defi',
                platform='Aave, Compound, Curve',
                risk_level='medium',
                additional_info='DeFi lending, wyższe APY ale smart contract risk'
            ),
        }

    def calculate_staking_returns(
        self,
        coin: StakingCoin,
        investment_usd: float,
        use_max_apy: bool = False
    ) -> Dict:
        """Oblicza zwroty ze stakingu"""

        apy = coin.apy_max if use_max_apy else coin.apy_min
        investment_pln = investment_usd * self.usd_to_pln

        # Ile monet można kupić
        coins_amount = investment_usd / coin.price_usd

        # Sprawdź czy spełnia minimum
        meets_minimum = coins_amount >= coin.min_stake

        if not meets_minimum:
            return {
                'meets_minimum': False,
                'minimum_required_usd': coin.min_stake * coin.price_usd,
                'minimum_required_pln': coin.min_stake * coin.price_usd * self.usd_to_pln
            }

        # Roczne zwroty
        yearly_return_usd = investment_usd * (apy / 100)
        yearly_return_pln = yearly_return_usd * self.usd_to_pln

        # Miesięczne zwroty
        monthly_return_usd = yearly_return_usd / 12
        monthly_return_pln = yearly_return_usd / 12 * self.usd_to_pln

        # Dzienne zwroty
        daily_return_usd = yearly_return_usd / 365
        daily_return_pln = daily_return_usd * self.usd_to_pln

        # Po 5 latach (compound interest)
        # A = P(1 + r)^t
        years = 5
        future_value_usd = investment_usd * ((1 + apy/100) ** years)
        total_earnings_5y_usd = future_value_usd - investment_usd
        total_earnings_5y_pln = total_earnings_5y_usd * self.usd_to_pln

        return {
            'meets_minimum': True,
            'coin_symbol': coin.symbol,
            'coin_name': coin.name,
            'investment_usd': investment_usd,
            'investment_pln': investment_pln,
            'coins_amount': coins_amount,
            'apy': apy,
            'daily_return_usd': daily_return_usd,
            'daily_return_pln': daily_return_pln,
            'monthly_return_usd': monthly_return_usd,
            'monthly_return_pln': monthly_return_pln,
            'yearly_return_usd': yearly_return_usd,
            'yearly_return_pln': yearly_return_pln,
            'future_value_5y_usd': future_value_usd,
            'total_earnings_5y_usd': total_earnings_5y_usd,
            'total_earnings_5y_pln': total_earnings_5y_pln,
            'lock_period_days': coin.lock_period_days,
            'platform': coin.platform,
            'risk_level': coin.risk_level,
            'staking_type': coin.staking_type,
            'additional_info': coin.additional_info
        }

    def calculate_required_investment(
        self,
        coin: StakingCoin,
        target_monthly_pln: float,
        use_max_apy: bool = False
    ) -> Dict:
        """Oblicza wymaganą inwestycję dla osiągnięcia celu miesięcznego"""

        apy = coin.apy_max if use_max_apy else coin.apy_min

        # Miesięczny zwrot = (Investment * APY) / 12
        # target_monthly_pln = (Investment_USD * usd_to_pln * APY) / 12 / 100
        # Investment_USD = (target_monthly_pln * 12 * 100) / (usd_to_pln * APY)

        target_monthly_usd = target_monthly_pln / self.usd_to_pln
        required_investment_usd = (target_monthly_usd * 12 * 100) / apy
        required_investment_pln = required_investment_usd * self.usd_to_pln

        # Ile monet
        coins_needed = required_investment_usd / coin.price_usd

        # Czy spełnia minimum
        actual_investment_usd = required_investment_usd
        if coins_needed < coin.min_stake:
            coins_needed = coin.min_stake
            actual_investment_usd = coin.min_stake * coin.price_usd

        return {
            'coin_symbol': coin.symbol,
            'coin_name': coin.name,
            'target_monthly_pln': target_monthly_pln,
            'apy': apy,
            'required_investment_usd': actual_investment_usd,
            'required_investment_pln': actual_investment_usd * self.usd_to_pln,
            'coins_needed': coins_needed,
            'min_stake': coin.min_stake,
            'actual_monthly_return_pln': (actual_investment_usd * apy / 100 / 12) * self.usd_to_pln,
            'platform': coin.platform,
            'risk_level': coin.risk_level,
        }

    def analyze_investment_levels(self):
        """Analizuje różne poziomy inwestycji"""

        print("=" * 100)
        print("ANALIZA STAKINGU - ILE TRZEBA ZAINWESTOWAĆ?")
        print("=" * 100)
        print()

        # Różne poziomy miesięcznego dochodu
        targets_pln = [500, 1000, 2000, 3000, 5000, 10000]

        print("🎯 CELE MIESIĘCZNEGO DOCHODU I WYMAGANE INWESTYCJE\n")

        for target in targets_pln:
            print(f"\n{'═' * 100}")
            print(f"CEL: {target:,} PLN/miesiąc ({target*12:,} PLN/rok)")
            print(f"{'═' * 100}\n")

            results = []
            for symbol, coin in self.coins.items():
                calc = self.calculate_required_investment(coin, target, use_max_apy=False)
                results.append(calc)

            # Sortuj po wymaganej inwestycji
            results.sort(key=lambda x: x['required_investment_pln'])

            print(f"{'Moneta':<12} {'Inwestycja PLN':>18} {'Inwestycja USD':>18} {'APY':>8} {'Ryzyko':>10} {'Platforma':<30}")
            print(f"{'-' * 100}")

            for r in results[:8]:  # Top 8
                risk_emoji = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🔴'
                }
                print(
                    f"{r['coin_symbol']:<12} "
                    f"{r['required_investment_pln']:>17,.0f} "
                    f"{r['required_investment_usd']:>17,.0f} "
                    f"{r['apy']:>7.1f}% "
                    f"{risk_emoji.get(r['risk_level'], '⚪')} {r['risk_level']:<8} "
                    f"{r['platform'][:28]:<30}"
                )

        print("\n" + "=" * 100)

    def detailed_comparison(self, investment_usd: float):
        """Szczegółowe porównanie wszystkich monet dla konkretnej inwestycji"""

        print("\n" + "=" * 100)
        print(f"SZCZEGÓŁOWE PORÓWNANIE DLA INWESTYCJI: ${investment_usd:,.0f} USD ({investment_usd * self.usd_to_pln:,.0f} PLN)")
        print("=" * 100)

        results = []
        for symbol, coin in self.coins.items():
            calc_min = self.calculate_staking_returns(coin, investment_usd, use_max_apy=False)
            calc_max = self.calculate_staking_returns(coin, investment_usd, use_max_apy=True)

            if calc_min.get('meets_minimum'):
                results.append((coin, calc_min, calc_max))

        # Sortuj po miesięcznym zwrocie (max APY)
        results.sort(key=lambda x: x[2]['monthly_return_pln'], reverse=True)

        for i, (coin, calc_min, calc_max) in enumerate(results, 1):
            print(f"\n{'─' * 100}")
            print(f"#{i}. {coin.name} ({coin.symbol})")
            print(f"{'─' * 100}")

            print(f"\n💰 INWESTYCJA:")
            print(f"  Kwota:              ${calc_min['investment_usd']:,.2f} ({calc_min['investment_pln']:,.2f} PLN)")
            print(f"  Ilość monet:        {calc_min['coins_amount']:,.4f} {coin.symbol}")
            print(f"  Min. wymagane:      {coin.min_stake} {coin.symbol}")

            print(f"\n📊 ZWROTY (konserwatywne - {calc_min['apy']}% APY):")
            print(f"  Dziennie:           ${calc_min['daily_return_usd']:,.2f} ({calc_min['daily_return_pln']:,.2f} PLN)")
            print(f"  Miesięcznie:        ${calc_min['monthly_return_usd']:,.2f} ({calc_min['monthly_return_pln']:,.2f} PLN)")
            print(f"  Rocznie:            ${calc_min['yearly_return_usd']:,.2f} ({calc_min['yearly_return_pln']:,.2f} PLN)")

            print(f"\n📈 ZWROTY (optymistyczne - {calc_max['apy']}% APY):")
            print(f"  Dziennie:           ${calc_max['daily_return_usd']:,.2f} ({calc_max['daily_return_pln']:,.2f} PLN)")
            print(f"  Miesięcznie:        ${calc_max['monthly_return_usd']:,.2f} ({calc_max['monthly_return_pln']:,.2f} PLN)")
            print(f"  Rocznie:            ${calc_max['yearly_return_usd']:,.2f} ({calc_max['yearly_return_pln']:,.2f} PLN)")

            print(f"\n🚀 PROJEKCJA 5 LAT (compound, {calc_max['apy']}% APY):")
            print(f"  Wartość końcowa:    ${calc_max['future_value_5y_usd']:,.2f} ({calc_max['future_value_5y_usd'] * self.usd_to_pln:,.2f} PLN)")
            print(f"  Całkowity zysk:     ${calc_max['total_earnings_5y_usd']:,.2f} ({calc_max['total_earnings_5y_pln']:,.2f} PLN)")
            print(f"  ROI:                {((calc_max['total_earnings_5y_usd'] / investment_usd) * 100):.1f}%")

            risk_emoji = {'low': '🟢 NISKIE', 'medium': '🟡 ŚREDNIE', 'high': '🔴 WYSOKIE'}
            print(f"\n⚠️  PARAMETRY:")
            print(f"  Okres blokady:      {coin.lock_period_days} dni")
            print(f"  Typ:                {coin.staking_type}")
            print(f"  Ryzyko:             {risk_emoji.get(coin.risk_level, coin.risk_level)}")
            print(f"  Platforma:          {coin.platform}")
            print(f"  Info:               {coin.additional_info}")

        print("\n" + "=" * 100)

    def print_recommendations(self):
        """Wyświetla rekomendacje i porównanie z tradycyjnymi inwestycjami"""

        print("\n" + "=" * 100)
        print("REKOMENDACJE I PORÓWNANIA")
        print("=" * 100)

        print("""
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                           PORÓWNANIE Z TRADYCYJNYMI INWESTYCJAMI                             ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝

1. 🏦 LOKATA BANKOWA (Polska, 2024):
   - Oprocentowanie:      ~5-6% rocznie
   - Ryzyko:              Minimalne (gwarancja BFG do 100k EUR)
   - Blokada:             3-12 miesięcy
   - Podatek:             19% (Belka)
   - Realny zwrot:        ~4-4.8% po podatku

2. 📊 OBLIGACJE SKARBOWE (Polska):
   - EDO (10 lat):        ~6.5% (zmienne)
   - COI (2 lata):        ~6.0% (zmienne)
   - Ryzyko:              Bardzo niskie
   - Podatek:             19%
   - Realny zwrot:        ~4.8-5.3% po podatku

3. 📈 FUNDUSZE INDEKSOWE (S&P 500, WIG20):
   - Średni zwrot:        8-10% rocznie (długoterminowo)
   - Ryzyko:              Średnie (zmienność)
   - Podatek:             19%
   - Realny zwrot:        ~6.5-8% po podatku (średnia historyczna)

4. 🏠 NIERUCHOMOŚCI (wynajem):
   - Zwrot z wynajmu:     4-6% rocznie (bez wzrostu wartości)
   - Ryzyko:              Średnie
   - Płynność:            Niska
   - Podatek:             Ryczałt lub skala podatkowa

╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                              STAKING KRYPTOWALUT - PRZEWAGI                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝

✅ ZALETY:
  1. Wyższe zwroty niż tradycyjne produkty (3-20% APY)
  2. Często brak blokady lub krótka blokada (0-28 dni)
  3. Płynność - można sprzedać w każdej chwili (po unbonding)
  4. Automatyczne compound (w większości przypadków)
  5. Dostęp 24/7, globalna dostępność
  6. Możliwość dywersyfikacji (wiele monet)

❌ WADY I RYZYKA:
  1. 🔴 ZMIENNOŚĆ CENY - największe ryzyko!
     - Zarabiasz 10% APY, ale cena może spaść 30%
     - Zysk ze stakingu może nie zrekompensować spadku wartości

  2. 🟡 Ryzyko techniczne:
     - Smart contract risk (DeFi)
     - Slashing risk (walidatorzy)
     - Exchange risk (giełda może upaść - FTX, Celsius)

  3. 🟡 Ryzyko regulacyjne:
     - Zmiany w przepisach
     - Opodatkowanie (w Polsce - niejasne)

  4. 🟡 Brak gwarancji:
     - Nie ma ochrony typu BFG
     - Strata klucza = strata środków

╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                  STRATEGIE STAKINGOWE                                        ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝

🎯 KONSERWATYWNA (niskie ryzyko):
   Portfel: 100% stablecoiny (USDT, USDC, BUSD)
   Gdzie:   Binance Earn, Nexo, Crypto.com
   APY:     3-6%
   Kwota:   10,000-50,000 PLN minimum
   Cel:     Miesięczny dochód ~200-400 PLN

   ✅ Brak zmienności ceny
   ✅ Przewidywalne zwroty
   ❌ Niższe APY
   ❌ Exchange risk

🎯 ZRÓWNOWAŻONA (średnie ryzyko):
   Portfel: 50% stablecoiny, 30% ETH, 20% BNB/SOL/ADA
   APY:     4-7% (średnio)
   Kwota:   20,000-100,000 PLN minimum
   Cel:     Miesięczny dochód ~500-1,500 PLN + potencjalny wzrost wartości

   ✅ Dywersyfikacja
   ✅ Balans ryzyko/zwrot
   ❌ Zmienność częściowo obecna

🎯 AGRESYWNA (wysokie ryzyko):
   Portfel: 20% stablecoiny, 40% ETH, 40% altcoiny (DOT, ATOM, TIA)
   APY:     8-15% (średnio)
   Kwota:   50,000+ PLN
   Cel:     Wysokie zwroty + wzrost wartości

   ✅ Najwyższe APY
   ✅ Potencjał dużych zysków (cena + staking)
   ❌ Wysoka zmienność
   ❌ Ryzyko dużych strat

╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                             KONKRETNE REKOMENDACJE DLA CIEBIE                                ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝

💡 SCENARIUSZ 1: "Chcę zastąpić kopanie (50-100 PLN/miesiąc)"
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Inwestycja:   ~10,000-15,000 PLN
   Strategia:    USDT/USDC staking na Binance (4-5% APY)
   Zwrot:        ~40-60 PLN/miesiąc
   Ryzyko:       Niskie (stabilna wartość)

   LEPIEJ NIŻ KOPANIE BO:
   ✅ Brak zużycia laptopa
   ✅ Brak kosztów energii
   ✅ Pasywny dochód
   ✅ Wyjście w każdej chwili

💡 SCENARIUSZ 2: "Chcę sensowny miesięczny dochód (500-1000 PLN)"
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Inwestycja:   ~100,000-200,000 PLN
   Strategia:    Portfel zrównoważony
                 - 50k PLN w USDT (Binance) - ~200 PLN/miesiąc
                 - 80k PLN w ETH (Lido) - ~250 PLN/miesiąc
                 - 70k PLN w SOL/ADA - ~450 PLN/miesiąc
   Zwrot:        ~900 PLN/miesiąc (średnio 5.4% APY)
   Ryzyko:       Średnie

   UWAGA: Zmienność ceny może znacząco wpłynąć na wartość!

💡 SCENARIUSZ 3: "Chcę żyć ze stakingu (3000-5000 PLN/miesiąc)"
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Inwestycja:   ~600,000-1,000,000 PLN (!!!)
   Strategia:    Zdywersyfikowany portfel:
                 - 300k PLN stablecoiny (bezpieczeństwo) - ~1,200 PLN/miesiąc
                 - 400k PLN ETH/BNB - ~1,600 PLN/miesiąc
                 - 300k PLN wysokie APY (DOT/ATOM) - ~3,000 PLN/miesiąc
   Zwrot:        ~5,800 PLN/miesiąc (średnio 7% APY)
   Ryzyko:       Średnie do wysokiego

   ⚠️  TO WYMAGA DUŻEGO KAPITAŁU!

╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                    PRAKTYCZNE KROKI                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝

📋 KROK PO KROKU:

1. OKREŚL BUDŻET:
   - Ile możesz zainwestować? (tylko nadwyżka, nie ostatnie pieniądze!)
   - Na jak długo możesz zamrozić środki?
   - Jaki poziom ryzyka akceptujesz?

2. WYBIERZ PLATFORMĘ:
   Dla początkujących:
   ✅ Binance - łatwy, bezpieczny, różne opcje
   ✅ Kraken - bezpieczny, regulowany
   ✅ Lido (ETH) - liquid staking, brak blokady

   Dla zaawansowanych:
   - Własne portfele (MetaMask, Phantom)
   - DeFi (Aave, Compound) - wyższe APY, wyższe ryzyko

3. ZACZNIJ MAŁĄ KWOTĄ:
   - Przetestuj z 1,000-5,000 PLN
   - Sprawdź jak działa staking
   - Poczuj zmienność rynku
   - Dopiero potem skaluj

4. DYWERSYFIKUJ:
   - Nie trzymaj wszystkiego w jednej monecie
   - Nie trzymaj wszystkiego na jednej giełdze
   - Rozłóż ryzyko

5. MONITORUJ:
   - Sprawdzaj zwroty co miesiąc
   - Śledź zmiany APY
   - Bądź gotowy na rebalancing

╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                  OPODATKOWANIE (POLSKA)                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝

⚠️  UWAGA: Prawo podatkowe dla krypto w Polsce jest NIEJASNE!

Według obecnych przepisów (2024):
- Przychód ze stakingu = przychód z kapitałów pieniężnych?
- Podatek: prawdopodobnie 19% (PIT-38)
- Moment opodatkowania: sprzedaż/wymiana na PLN?
- Brak jasnych wytycznych MF

REKOMENDACJA: Skonsultuj z doradcą podatkowym specjalizującym się w krypto!

╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                   FINALNE WNIOSKI                                            ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝

✅ STAKING MA SENS JEŚLI:
   - Masz kapitał minimum 10,000-20,000 PLN nadwyżki
   - Akceptujesz ryzyko zmienności (albo stakujesz stablecoiny)
   - Myślisz długoterminowo (min. 1-2 lata)
   - Rozumiesz technologię i ryzyka
   - Nie potrzebujesz szybkiego dostępu do środków

❌ STAKING NIE MA SENSU JEŚLI:
   - To Twoje ostatnie pieniądze
   - Liczysz na szybkie zyski
   - Nie akceptujesz zmienności -30% do +50%
   - Nie rozumiesz krypto i blockchain
   - Potrzebujesz gwarancji zwrotu (lokata jest lepsza)

🎯 MOJA OSOBISTA REKOMENDACJA:
   1. Zacznij od małej kwoty (5,000-10,000 PLN)
   2. Stakuj stablecoiny (USDT/USDC) na Binance - bezpieczne, stabilne
   3. Po 3-6 miesiącach zdecyduj czy zwiększyć kapitał
   4. Stopniowo dodawaj ETH i inne monety
   5. Zawsze trzymaj część kapitału w tradycyjnych inwestycjach (lokaty, obligacje)

   NIE INWESTUJ WSZYSTKIEGO W KRYPTO!
   Zasada: max 10-30% portfela w krypto (zależnie od profilu ryzyka)

        """)

        print("=" * 100)

    def quick_reference_table(self):
        """Szybka tabela referencyjna"""

        print("\n" + "=" * 100)
        print("SZYBKA TABELA REFERENCYJNA - ILE TRZEBA ZAINWESTOWAĆ?")
        print("=" * 100)
        print()

        targets = [
            ("Kawa dziennie", 100),
            ("Rachunek za telefon", 500),
            ("Drobne wydatki", 1000),
            ("Częściowe pokrycie kosztów", 2000),
            ("Dodatkowy dochód", 3000),
            ("Poważny dochód pasywny", 5000),
        ]

        for description, target_pln in targets:
            print(f"\n{'═' * 100}")
            print(f"🎯 CEL: {target_pln} PLN/miesiąc - {description}")
            print(f"{'═' * 100}")

            # Przykłady dla różnych monet
            examples = ['USDT_CEFI', 'ETH', 'SOL', 'ATOM']

            print(f"\n{'Moneta':<15} {'APY':<8} {'Wymagana inwestycja PLN':<30} {'Wymagana inwestycja USD':<25} {'Ryzyko':<10}")
            print("-" * 100)

            for symbol in examples:
                if symbol in self.coins:
                    coin = self.coins[symbol]
                    calc = self.calculate_required_investment(coin, target_pln, use_max_apy=False)
                    risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}

                    print(
                        f"{coin.symbol:<15} "
                        f"{calc['apy']:<7.1f}% "
                        f"{calc['required_investment_pln']:<29,.0f} "
                        f"{calc['required_investment_usd']:<24,.0f} "
                        f"{risk_emoji.get(coin.risk_level, '⚪')} {coin.risk_level}"
                    )

        print("\n" + "=" * 100)


def main():
    """Główna funkcja analizy"""

    analyzer = StakingAnalyzer(usd_to_pln=4.0)

    # 1. Szybka tabela referencyjna
    analyzer.quick_reference_table()

    # 2. Analiza poziomów inwestycji
    analyzer.analyze_investment_levels()

    # 3. Przykładowe szczegółowe porównanie
    print("\n" + "=" * 100)
    print("PRZYKŁADY SZCZEGÓŁOWYCH ANALIZ")
    print("=" * 100)

    # Przykład 1: Mała inwestycja
    analyzer.detailed_comparison(2500)  # $2,500 = ~10,000 PLN

    # Przykład 2: Średnia inwestycja
    analyzer.detailed_comparison(12500)  # $12,500 = ~50,000 PLN

    # Przykład 3: Duża inwestycja
    analyzer.detailed_comparison(25000)  # $25,000 = ~100,000 PLN

    # 4. Rekomendacje
    analyzer.print_recommendations()

    # Zapisz do JSON
    print("\n" + "=" * 100)
    print("💾 ZAPIS WYNIKÓW")
    print("=" * 100)

    # Przykładowe dane do zapisu
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'usd_to_pln': analyzer.usd_to_pln,
        'coins': {
            symbol: {
                'name': coin.name,
                'price_usd': coin.price_usd,
                'apy_min': coin.apy_min,
                'apy_max': coin.apy_max,
                'platform': coin.platform,
                'risk_level': coin.risk_level,
            }
            for symbol, coin in analyzer.coins.items()
        },
        'example_calculations': {
            '10k_pln_investment': {
                symbol: analyzer.calculate_staking_returns(coin, 2500, use_max_apy=False)
                for symbol, coin in list(analyzer.coins.items())[:5]
            }
        }
    }

    with open('staking_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

    print("✅ Wyniki zapisane do: staking_analysis_results.json")
    print()


if __name__ == "__main__":
    main()
