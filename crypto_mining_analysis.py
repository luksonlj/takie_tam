"""
Analiza opłacalności kopania kryptowalut
Sprzęt: AMD Ryzen 7 PRO 5850U + Radeon Graphics + 32GB RAM
"""

import json
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime


@dataclass
class HardwareSpec:
    """Specyfikacja sprzętu"""
    cpu_model: str
    cpu_cores: int
    cpu_threads: int
    cpu_base_freq: float  # GHz
    gpu_model: str
    gpu_compute_units: int
    ram_gb: int
    tdp_cpu: int  # Watts
    tdp_gpu: int  # Watts


@dataclass
class MiningAlgorithm:
    """Algorytm kopania"""
    name: str
    hashrate_cpu: float  # H/s lub KH/s
    hashrate_unit: str
    hashrate_gpu: float
    power_consumption: int  # Watts
    coins: List[str]


@dataclass
class CoinData:
    """Dane o monecie"""
    symbol: str
    name: str
    algorithm: str
    block_reward: float
    network_hashrate: float  # w jednostkach hashrate_unit
    network_hashrate_unit: str
    difficulty: float
    price_usd: float  # aktualna cena w USD
    exchange_fee: float  # prowizja giełdy (%)


class MiningProfitabilityAnalyzer:
    """Analizator opłacalności kopania"""

    def __init__(self, hardware: HardwareSpec, electricity_cost_kwh: float = 0.15):
        """
        Args:
            hardware: Specyfikacja sprzętu
            electricity_cost_kwh: Koszt 1 kWh w USD (domyślnie ~0.60 PLN/kWh)
        """
        self.hardware = hardware
        self.electricity_cost_kwh = electricity_cost_kwh
        self.usd_to_pln = 4.0  # Przybliżony kurs

        # Specyfikacja sprzętu użytkownika
        self.setup_hardware()

        # Algorytmy i ich wydajność
        self.setup_algorithms()

        # Dane o popularnych altcoinach do kopania
        self.setup_coins()

    def setup_hardware(self):
        """Konfiguracja sprzętu użytkownika"""
        # AMD Ryzen 7 PRO 5850U - laptop CPU Zen 3
        # 8 rdzeni, 16 wątków, 1.9 GHz base, 4.4 GHz boost
        # TDP 15W (configurable 10-25W)
        # Radeon Graphics (Vega 8) - 8 CU, ~2000 MHz

        print("=" * 80)
        print("SPECYFIKACJA SPRZĘTU")
        print("=" * 80)
        print(f"CPU: {self.hardware.cpu_model}")
        print(f"  - Rdzenie/Wątki: {self.hardware.cpu_cores}/{self.hardware.cpu_threads}")
        print(f"  - Częstotliwość bazowa: {self.hardware.cpu_base_freq} GHz")
        print(f"  - TDP: {self.hardware.tdp_cpu}W (laptop, configurable 10-25W)")
        print(f"\nGPU: {self.hardware.gpu_model}")
        print(f"  - Compute Units: {self.hardware.gpu_compute_units}")
        print(f"  - TDP: ~{self.hardware.tdp_gpu}W")
        print(f"\nRAM: {self.hardware.ram_gb} GB")
        print(f"\nKoszt energii: ${self.electricity_cost_kwh}/kWh ({self.electricity_cost_kwh * self.usd_to_pln:.2f} PLN/kWh)")
        print("=" * 80)
        print()

    def setup_algorithms(self):
        """Konfiguracja algorytmów i ich wydajności dla danego sprzętu"""

        # Oszacowania hashrate dla AMD Ryzen 7 PRO 5850U
        # Bazowane na benchmarkach podobnych CPU (Ryzen 7 5800U, 5700U)

        self.algorithms = {
            'RandomX': MiningAlgorithm(
                name='RandomX (CPU-friendly)',
                hashrate_cpu=3500,  # ~3.5 KH/s dla Ryzen 5850U
                hashrate_unit='H/s',
                hashrate_gpu=0,  # RandomX to algorytm CPU
                power_consumption=25,  # Full load laptop TDP
                coins=['XMR', 'ZEPHYR', 'ARQMA']
            ),
            'KawPow': MiningAlgorithm(
                name='KawPow (GPU)',
                hashrate_cpu=0,
                hashrate_unit='MH/s',
                hashrate_gpu=2.5,  # ~2.5 MH/s dla Vega 8 iGPU (bardzo optymistyczne)
                power_consumption=35,  # CPU + GPU
                coins=['RVN']
            ),
            'Ethash': MiningAlgorithm(
                name='Ethash (GPU) - legacy',
                hashrate_cpu=0,
                hashrate_unit='MH/s',
                hashrate_gpu=3.0,  # ~3 MH/s dla Vega 8 (optymistyczne)
                power_consumption=35,
                coins=['ETC', 'ETHW']
            ),
            'EtcHash': MiningAlgorithm(
                name='EtcHash (GPU)',
                hashrate_cpu=0,
                hashrate_unit='MH/s',
                hashrate_gpu=3.0,
                power_consumption=35,
                coins=['ETC']
            ),
            'CryptoNightGPU': MiningAlgorithm(
                name='CryptoNight GPU',
                hashrate_cpu=0,
                hashrate_unit='H/s',
                hashrate_gpu=150,  # ~150 H/s dla Vega 8
                power_consumption=30,
                coins=['XMR-variants']
            ),
            'VertHash': MiningAlgorithm(
                name='VertHash (requires 2GB+ VRAM)',
                hashrate_cpu=100,  # KH/s
                hashrate_unit='KH/s',
                hashrate_gpu=0,
                power_consumption=25,
                coins=['VTC']
            ),
            'YescryptR16': MiningAlgorithm(
                name='YescryptR16 (CPU)',
                hashrate_cpu=2.5,  # KH/s
                hashrate_unit='KH/s',
                hashrate_gpu=0,
                power_consumption=25,
                coins=['YENTEN']
            ),
            'GhostRider': MiningAlgorithm(
                name='GhostRider (CPU+GPU hybrid)',
                hashrate_cpu=1200,  # H/s
                hashrate_unit='H/s',
                hashrate_gpu=200,
                power_consumption=35,
                coins=['RTM']
            ),
        }

    def setup_coins(self):
        """Dane o popularnych altcoinach (przykładowe dane - wymagają aktualizacji)"""

        # UWAGA: Te dane są przykładowe i wymagają aktualizacji z API
        # W rzeczywistości należy pobierać dane z WhatToMine, CoinWarz itp.

        self.coins = {
            'XMR': CoinData(
                symbol='XMR',
                name='Monero',
                algorithm='RandomX',
                block_reward=0.6,
                network_hashrate=2.8e9,  # ~2.8 GH/s
                network_hashrate_unit='H/s',
                difficulty=280e9,
                price_usd=155.0,
                exchange_fee=0.5
            ),
            'RVN': CoinData(
                symbol='RVN',
                name='Ravencoin',
                algorithm='KawPow',
                block_reward=2500,
                network_hashrate=5000,  # ~5 TH/s
                network_hashrate_unit='MH/s',
                difficulty=85000,
                price_usd=0.022,
                exchange_fee=0.5
            ),
            'ETC': CoinData(
                symbol='ETC',
                name='Ethereum Classic',
                algorithm='EtcHash',
                block_reward=2.56,
                network_hashrate=180000,  # ~180 TH/s
                network_hashrate_unit='MH/s',
                difficulty=2.5e15,
                price_usd=26.5,
                exchange_fee=0.5
            ),
            'RTM': CoinData(
                symbol='RTM',
                name='Raptoreum',
                algorithm='GhostRider',
                block_reward=2500,
                network_hashrate=1.5e9,  # ~1.5 GH/s
                network_hashrate_unit='H/s',
                difficulty=150000,
                price_usd=0.0015,
                exchange_fee=0.5
            ),
            'ZEPH': CoinData(
                symbol='ZEPH',
                name='Zephyr Protocol',
                algorithm='RandomX',
                block_reward=6.0,
                network_hashrate=150e6,  # ~150 MH/s
                network_hashrate_unit='H/s',
                difficulty=150e9,
                price_usd=2.5,
                exchange_fee=0.5
            ),
        }

    def calculate_mining_stats(self, coin: CoinData, algorithm: MiningAlgorithm) -> Dict:
        """Oblicza statystyki kopania dla danej monety"""

        # Całkowity hashrate (CPU + GPU)
        total_hashrate = algorithm.hashrate_cpu + algorithm.hashrate_gpu

        if total_hashrate == 0:
            return None

        # Udział w sieci
        network_share = total_hashrate / coin.network_hashrate

        # Szacowane dzienne wydobycie (uproszczone obliczenia)
        # Bloki dziennie w sieci zależą od czasu bloku (dla większości ~1-2 min)
        # Przyjmijmy średnio 720 bloków dziennie (2 min/blok)
        blocks_per_day = 720
        daily_blocks_mined = blocks_per_day * network_share
        daily_coins = daily_blocks_mined * coin.block_reward

        # Przychody
        daily_revenue_usd = daily_coins * coin.price_usd
        daily_revenue_pln = daily_revenue_usd * self.usd_to_pln

        # Koszty energii
        daily_power_kwh = (algorithm.power_consumption * 24) / 1000
        daily_electricity_cost_usd = daily_power_kwh * self.electricity_cost_kwh
        daily_electricity_cost_pln = daily_electricity_cost_usd * self.usd_to_pln

        # Zysk netto (przed prowizją giełdy)
        daily_profit_gross_usd = daily_revenue_usd - daily_electricity_cost_usd
        exchange_fee_usd = daily_revenue_usd * (coin.exchange_fee / 100)
        daily_profit_net_usd = daily_profit_gross_usd - exchange_fee_usd
        daily_profit_net_pln = daily_profit_net_usd * self.usd_to_pln

        # Miesięczne i roczne projekcje
        monthly_profit_net_pln = daily_profit_net_pln * 30
        yearly_profit_net_pln = daily_profit_net_pln * 365

        # ROI (return on investment) - czas zwrotu sprzętu
        # Zakładając, że laptop już posiadasz, więc ROI = nieskończoność :)
        # Ale dla nowego sprzętu dedykowanego:
        hardware_cost_pln = 0  # Masz już sprzęt

        return {
            'coin': coin.symbol,
            'algorithm': algorithm.name,
            'hashrate': total_hashrate,
            'hashrate_unit': algorithm.hashrate_unit,
            'network_share': network_share * 100,  # w procentach
            'daily_coins': daily_coins,
            'daily_revenue_usd': daily_revenue_usd,
            'daily_revenue_pln': daily_revenue_pln,
            'daily_power_kwh': daily_power_kwh,
            'daily_electricity_cost_usd': daily_electricity_cost_usd,
            'daily_electricity_cost_pln': daily_electricity_cost_pln,
            'daily_profit_gross_usd': daily_profit_gross_usd,
            'daily_profit_net_usd': daily_profit_net_usd,
            'daily_profit_net_pln': daily_profit_net_pln,
            'monthly_profit_net_pln': monthly_profit_net_pln,
            'yearly_profit_net_pln': yearly_profit_net_pln,
            'power_consumption_w': algorithm.power_consumption,
            'coin_price_usd': coin.price_usd,
        }

    def analyze_all_coins(self) -> List[Dict]:
        """Analizuje wszystkie dostępne monety"""
        results = []

        for coin_symbol, coin_data in self.coins.items():
            algorithm = self.algorithms.get(coin_data.algorithm)
            if algorithm:
                stats = self.calculate_mining_stats(coin_data, algorithm)
                if stats:
                    results.append(stats)

        # Sortuj po zysku netto malejąco
        results.sort(key=lambda x: x['daily_profit_net_pln'], reverse=True)
        return results

    def print_detailed_report(self, results: List[Dict]):
        """Wyświetla szczegółowy raport"""

        print("\n" + "=" * 80)
        print("SZCZEGÓŁOWA ANALIZA OPŁACALNOŚCI KOPANIA")
        print("=" * 80)
        print()

        for i, stats in enumerate(results, 1):
            print(f"\n{'─' * 80}")
            print(f"#{i}. {stats['coin']} ({stats['algorithm']})")
            print(f"{'─' * 80}")

            print(f"\n📊 WYDAJNOŚĆ:")
            print(f"  Hashrate:          {stats['hashrate']:,.2f} {stats['hashrate_unit']}")
            print(f"  Udział w sieci:    {stats['network_share']:.8f}%")
            print(f"  Zużycie energii:   {stats['power_consumption_w']}W ({stats['daily_power_kwh']:.2f} kWh/dzień)")

            print(f"\n💰 PRZYCHODY (dziennie):")
            print(f"  Wydobyte monety:   {stats['daily_coins']:.6f} {stats['coin']}")
            print(f"  Wartość (USD):     ${stats['daily_revenue_usd']:.4f}")
            print(f"  Wartość (PLN):     {stats['daily_revenue_pln']:.2f} zł")

            print(f"\n⚡ KOSZTY (dziennie):")
            print(f"  Energia (USD):     ${stats['daily_electricity_cost_usd']:.4f}")
            print(f"  Energia (PLN):     {stats['daily_electricity_cost_pln']:.2f} zł")

            print(f"\n💵 ZYSK NETTO:")
            print(f"  Dziennie (USD):    ${stats['daily_profit_net_usd']:.4f}")
            print(f"  Dziennie (PLN):    {stats['daily_profit_net_pln']:.2f} zł")
            print(f"  Miesięcznie (PLN): {stats['monthly_profit_net_pln']:.2f} zł")
            print(f"  Rocznie (PLN):     {stats['yearly_profit_net_pln']:.2f} zł")

            # Ocena opłacalności
            if stats['daily_profit_net_pln'] > 5:
                verdict = "✅ OPŁACALNE"
            elif stats['daily_profit_net_pln'] > 0:
                verdict = "⚠️  MINIMALNIE OPŁACALNE"
            else:
                verdict = "❌ NIEOPŁACALNE"

            print(f"\n🎯 OCENA: {verdict}")

    def print_summary(self, results: List[Dict]):
        """Wyświetla podsumowanie"""

        print("\n" + "=" * 80)
        print("PODSUMOWANIE I REKOMENDACJE")
        print("=" * 80)

        if not results:
            print("\n❌ Brak opłacalnych opcji kopania.")
            return

        best = results[0]

        print(f"\n🏆 NAJLEPSZA OPCJA: {best['coin']}")
        print(f"   Dzienny zysk: {best['daily_profit_net_pln']:.2f} PLN")
        print(f"   Miesięczny zysk: {best['monthly_profit_net_pln']:.2f} PLN")
        print(f"   Roczny zysk: {best['yearly_profit_net_pln']:.2f} PLN")

        print("\n" + "─" * 80)
        print("📋 RANKING OPŁACALNOŚCI (dziennie):")
        print("─" * 80)
        for i, stats in enumerate(results, 1):
            profit_indicator = "🟢" if stats['daily_profit_net_pln'] > 0 else "🔴"
            print(f"{i}. {profit_indicator} {stats['coin']:8s} | {stats['daily_profit_net_pln']:>8.2f} PLN/dzień | "
                  f"{stats['monthly_profit_net_pln']:>9.2f} PLN/miesiąc")

        print("\n" + "=" * 80)
        print("⚠️  WAŻNE UWAGI:")
        print("=" * 80)
        print("""
1. 💻 SPRZĘT LAPTOPOWY:
   - Ryzen 7 PRO 5850U to procesor laptopowy o niskiej mocy (TDP 15W)
   - Długotrwałe kopanie może skrócić żywotność laptopa
   - Ryzyko przegrzania i uszkodzenia komponentów
   - Głośna praca wentylatorów (24/7)
   - Zużycie baterii (jeśli nie podłączony do zasilania)

2. 💰 OPŁACALNOŚĆ:
   - Obliczenia bazują na aktualnych cenach monet (bardzo zmienne!)
   - Trudność sieci stale rośnie (zyski maleją)
   - Nie uwzględniono kosztów pool fees (1-2%)
   - Ceny energii mogą się różnić w zależności od regionu

3. ⚡ ZUŻYCIE ENERGII:
   - Laptop przy pełnym obciążeniu: ~25-35W
   - To około 0.6-0.84 kWh dziennie
   - Przy 0.60 PLN/kWh = ~0.36-0.50 PLN/dzień kosztów energii

4. 🔧 ALTERNATYWY:
   - Kopanie na laptopie: NIE ZALECANE
   - Lepsze opcje:
     * Dedykowany mining rig (ASIC lub GPU)
     * Cloud mining (jeśli opłacalne)
     * Staking (Proof-of-Stake coins)
     * Trading (jak obecny bot w repo)

5. 🎯 REKOMENDACJA KOŃCOWA:
   - Dla Twojego sprzętu: KOPANIE NIE MA SENSU
   - Przychody: bardzo niskie (grosze dziennie)
   - Koszty: zużycie sprzętu > zyski
   - Ryzyko: uszkodzenie laptopa
   - Lepiej: zostań przy tradingu lub stakingu
        """)

        print("=" * 80)

    def generate_custom_mining_script_analysis(self):
        """Analiza sensu tworzenia custom skryptu do kopania"""

        print("\n" + "=" * 80)
        print("CZY WARTO TWORZYĆ CUSTOM SKRYPT DO KOPANIA?")
        print("=" * 80)

        print("""
🔍 ANALIZA TWORZENIA WŁASNEGO SKRYPTU:

1. ❌ MINING CORE/ALGORYTM:
   - Algorytmy kopania (SHA-256, Ethash, RandomX, etc.) są BARDZO zoptymalizowane
   - Istniejące minery (XMRig, T-Rex, lolMiner) są w C++/CUDA/Assembly
   - Python/skrypt interpretowany będzie 100-1000x wolniejszy
   - Tworzenie własnej implementacji = brak sensu ekonomicznego

   Przykład:
   - XMRig (C++):           3,500 H/s na Ryzen 7 5850U
   - Własny skrypt Python:  ~50 H/s (99% wolniej!)

2. ⚠️  CO MOŻNA ZROBIĆ (ma sens):

   a) 📊 MONITORING I AUTOMATYZACJA:
      - Skrypt monitorujący rentowność różnych monet
      - Automatyczne przełączanie między poolami
      - Alerty gdy trudność/cena spadnie
      - Zbieranie statystyk wydajności

   b) 🤖 PROFIT SWITCHING:
      - Analiza NiceHash/WhatToMine API
      - Automatyczny wybór najbardziej opłacalnej monety
      - Restart minera z nowymi parametrami
      - Logging i raporty

   c) ⚙️  ZARZĄDZANIE MINEREM:
      - Auto-start/stop w oparciu o:
        * Cenę energii (taryfy dzień/noc)
        * Cenę monety
        * Temperaturę CPU/GPU
        * Obciążenie systemu
      - Integracja z giełdami (auto-sell)

   d) 📈 ANALITYKA:
      - Dashboard z statystykami
      - Wykresy hashrate, zysków, temperatury
      - Predykcja zysków
      - ROI calculator

3. ✅ PRZYKŁADOWY SENSOWNY SKRYPT:

   Zamiast implementować algorytm kopania, stwórz:

   ```python
   # mining_manager.py

   class MiningManager:
       def __init__(self):
           self.miners = {
               'xmrig': '/path/to/xmrig',
               'trex': '/path/to/t-rex',
           }

       def get_most_profitable_coin(self):
           '''Pobiera dane z WhatToMine API'''
           # Zwraca najbardziej opłacalną monetę

       def switch_mining(self, coin):
           '''Przełącza minera na inną monetę'''
           # Zatrzymuje obecny miner
           # Uruchamia nowy z odpowiednimi parametrami

       def monitor_profitability(self):
           '''Monitoruje opłacalność co X minut'''
           # Jeśli inna moneta jest >10% bardziej opłacalna
           # Automatycznie przełącz
   ```

4. 🎯 KONKRETNA REKOMENDACJA DLA CIEBIE:

   ❌ NIE TWÓRZ:
      - Własnej implementacji algorytmu kopania
      - Custom block solver
      - Niskopoziomowych optymalizacji

   ✅ MOŻESZ STWORZYĆ:
      - Skrypt automatyzujący istniejące minery
      - System monitorowania opłacalności
      - Auto-switching między monetami
      - Dashboard z analityką

   Ale pamiętaj: Nawet z najlepszym skryptem,
   kopanie na laptopie Ryzen 7 5850U to NIE JEST opłacalne!

5. 💡 LEPSZE ALTERNATYWY:

   Zamiast kopania na laptopie:

   a) 🤖 TRADING BOT (już masz w repo!):
      - Lepsza opłacalność
      - Brak zużycia sprzętu
      - Można na tym realnie zarobić
      - Skalowalne

   b) 💎 STAKING:
      - ETH staking (4-5% rocznie)
      - Polkadot, Cardano, Solana
      - Brak kosztów energii
      - Brak zużycia sprzętu

   c) 📊 ARBITRAŻ:
      - Różnice cen między giełdami
      - Można zautomatyzować
      - Niskie ryzyko
      - Szybkie zyski

PODSUMOWANIE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tworzenie custom skryptu do KOPANIA BLOKÓW = ❌ Bez sensu
Tworzenie skryptu do ZARZĄDZANIA KOPANIEM = ✅ Może mieć sens
Kopanie na Twoim laptopie = ❌ Nieopłacalne i ryzykowne
Zostań przy trading bocie = ✅ Znacznie lepszy pomysł!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)


def main():
    """Główna funkcja analizy"""

    # Konfiguracja sprzętu użytkownika
    hardware = HardwareSpec(
        cpu_model="AMD Ryzen 7 PRO 5850U with Radeon Graphics",
        cpu_cores=8,
        cpu_threads=16,
        cpu_base_freq=1.9,
        gpu_model="Radeon Graphics (Vega 8)",
        gpu_compute_units=8,
        ram_gb=32,
        tdp_cpu=15,  # Laptop TDP (configurable 10-25W)
        tdp_gpu=15,  # Integrated GPU share of TDP
    )

    # Koszt energii w Polsce: ~0.60-0.80 PLN/kWh = ~$0.15-0.20/kWh
    analyzer = MiningProfitabilityAnalyzer(
        hardware=hardware,
        electricity_cost_kwh=0.15  # $0.15/kWh (~0.60 PLN/kWh)
    )

    # Analiza wszystkich monet
    results = analyzer.analyze_all_coins()

    # Wyświetl szczegółowy raport
    analyzer.print_detailed_report(results)

    # Wyświetl podsumowanie
    analyzer.print_summary(results)

    # Analiza sensu tworzenia custom skryptu
    analyzer.generate_custom_mining_script_analysis()

    # Zapisz wyniki do JSON
    output_file = 'mining_analysis_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Wyniki zapisane do: {output_file}")


if __name__ == "__main__":
    main()
