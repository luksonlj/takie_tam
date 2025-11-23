"""
Performance Analysis Script
Downloads historical data from Binance and analyzes bot's performance
"""
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import config
from indicators import TechnicalIndicators
from price_action import PriceActionAnalyzer
import os


class PerformanceAnalyzer:
    """Analyze bot performance using historical data"""

    def __init__(self):
        """Initialize the analyzer"""
        self.exchange = self._initialize_exchange()
        self.symbol = config.SYMBOL
        self.timeframe = config.TIMEFRAME
        self.indicators = TechnicalIndicators()
        self.analyzer = PriceActionAnalyzer()

    def _initialize_exchange(self) -> ccxt.Exchange:
        """Initialize exchange connection"""
        exchange_class = getattr(ccxt, config.EXCHANGE)
        exchange = exchange_class({
            'enableRateLimit': True,
        })

        if config.EXCHANGE.lower() == 'binance':
            exchange.options['defaultType'] = 'future'

        # Always use production API for historical data download (no trading)
        # Historical data is publicly available and doesn't require API keys

        return exchange

    def download_historical_data(self, hours: int = 24) -> pd.DataFrame:
        """
        Download historical OHLCV data from Binance

        Args:
            hours: Number of hours of historical data to download

        Returns:
            DataFrame with OHLCV data
        """
        print(f"📥 Downloading {hours} hours of historical data for {self.symbol}...")

        # Calculate timestamp
        since = self.exchange.milliseconds() - (hours * 60 * 60 * 1000)

        # Fetch OHLCV data
        ohlcv = self.exchange.fetch_ohlcv(
            self.symbol,
            self.timeframe,
            since=since,
            limit=1000
        )

        # Convert to DataFrame
        df = pd.DataFrame(
            ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        print(f"✅ Downloaded {len(df)} candles")
        print(f"   Period: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
        print(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")

        return df

    def backtest_strategy(self, data: pd.DataFrame) -> dict:
        """
        Backtest the trading strategy on historical data

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Dictionary with backtest results
        """
        print("\n🔬 Running backtest...")

        # Add indicators
        data = self.indicators.add_all_indicators(data)

        # Track positions and trades
        position = None  # 'LONG' or 'SHORT'
        entry_price = 0
        position_size = 0
        trades = []
        signals_log = []

        # Simulate trading
        for i in range(config.LOOKBACK_PERIOD, len(data)):
            # Get data up to current point
            current_data = data.iloc[:i+1].copy()

            # Generate signal
            signal = self.analyzer.generate_signal(current_data)

            # Log signal
            signals_log.append({
                'timestamp': current_data.iloc[-1]['timestamp'],
                'price': signal['price'],
                'signal': signal['signal'],
                'confidence': signal['confidence'],
                'trend': signal['trend'],
                'position': position
            })

            # Execute trades based on signal (60% minimum confidence)
            if signal['signal'] == 'BUY' and signal['confidence'] >= 60:
                # Close SHORT position if open
                if position == 'SHORT':
                    pnl_percent = ((entry_price - signal['price']) / entry_price) * 100
                    pnl_usdt = position_size * (entry_price - signal['price'])
                    trades.append({
                        'timestamp': current_data.iloc[-1]['timestamp'],
                        'type': 'CLOSE_SHORT',
                        'entry_price': entry_price,
                        'exit_price': signal['price'],
                        'position_size': position_size,
                        'pnl_percent': pnl_percent,
                        'pnl_usdt': pnl_usdt
                    })
                    position = None

                # Open LONG position
                if position is None:
                    entry_price = signal['price']
                    position_size = config.TRADE_AMOUNT
                    position = 'LONG'
                    trades.append({
                        'timestamp': current_data.iloc[-1]['timestamp'],
                        'type': 'OPEN_LONG',
                        'entry_price': entry_price,
                        'position_size': position_size,
                        'confidence': signal['confidence']
                    })

            elif signal['signal'] == 'SELL' and signal['confidence'] >= 60:
                # Close LONG position if open
                if position == 'LONG':
                    pnl_percent = ((signal['price'] - entry_price) / entry_price) * 100
                    pnl_usdt = position_size * (signal['price'] - entry_price)
                    trades.append({
                        'timestamp': current_data.iloc[-1]['timestamp'],
                        'type': 'CLOSE_LONG',
                        'entry_price': entry_price,
                        'exit_price': signal['price'],
                        'position_size': position_size,
                        'pnl_percent': pnl_percent,
                        'pnl_usdt': pnl_usdt
                    })
                    position = None

                # Open SHORT position
                if position is None:
                    entry_price = signal['price']
                    position_size = config.TRADE_AMOUNT
                    position = 'SHORT'
                    trades.append({
                        'timestamp': current_data.iloc[-1]['timestamp'],
                        'type': 'OPEN_SHORT',
                        'entry_price': entry_price,
                        'position_size': position_size,
                        'confidence': signal['confidence']
                    })

            # Check stop loss and take profit
            if position == 'LONG':
                pnl_percent = ((signal['price'] - entry_price) / entry_price) * 100
                if pnl_percent <= -config.STOP_LOSS_PERCENT:
                    pnl_usdt = position_size * (signal['price'] - entry_price)
                    trades.append({
                        'timestamp': current_data.iloc[-1]['timestamp'],
                        'type': 'STOP_LOSS_LONG',
                        'entry_price': entry_price,
                        'exit_price': signal['price'],
                        'position_size': position_size,
                        'pnl_percent': pnl_percent,
                        'pnl_usdt': pnl_usdt
                    })
                    position = None
                elif pnl_percent >= config.TAKE_PROFIT_PERCENT:
                    pnl_usdt = position_size * (signal['price'] - entry_price)
                    trades.append({
                        'timestamp': current_data.iloc[-1]['timestamp'],
                        'type': 'TAKE_PROFIT_LONG',
                        'entry_price': entry_price,
                        'exit_price': signal['price'],
                        'position_size': position_size,
                        'pnl_percent': pnl_percent,
                        'pnl_usdt': pnl_usdt
                    })
                    position = None

            elif position == 'SHORT':
                pnl_percent = ((entry_price - signal['price']) / entry_price) * 100
                if pnl_percent <= -config.STOP_LOSS_PERCENT:
                    pnl_usdt = position_size * (entry_price - signal['price'])
                    trades.append({
                        'timestamp': current_data.iloc[-1]['timestamp'],
                        'type': 'STOP_LOSS_SHORT',
                        'entry_price': entry_price,
                        'exit_price': signal['price'],
                        'position_size': position_size,
                        'pnl_percent': pnl_percent,
                        'pnl_usdt': pnl_usdt
                    })
                    position = None
                elif pnl_percent >= config.TAKE_PROFIT_PERCENT:
                    pnl_usdt = position_size * (entry_price - signal['price'])
                    trades.append({
                        'timestamp': current_data.iloc[-1]['timestamp'],
                        'type': 'TAKE_PROFIT_SHORT',
                        'entry_price': entry_price,
                        'exit_price': signal['price'],
                        'position_size': position_size,
                        'pnl_percent': pnl_percent,
                        'pnl_usdt': pnl_usdt
                    })
                    position = None

        return {
            'trades': trades,
            'signals': signals_log,
            'final_position': position
        }

    def generate_report(self, backtest_results: dict) -> None:
        """
        Generate performance report

        Args:
            backtest_results: Results from backtest_strategy
        """
        trades = backtest_results['trades']
        signals = backtest_results['signals']

        print("\n" + "=" * 70)
        print("📊 PERFORMANCE REPORT")
        print("=" * 70)

        # Signal statistics
        signal_counts = pd.Series([s['signal'] for s in signals]).value_counts()
        print(f"\n📈 Signal Statistics:")
        print(f"   Total signals analyzed: {len(signals)}")
        for signal_type, count in signal_counts.items():
            percentage = (count / len(signals)) * 100
            print(f"   {signal_type}: {count} ({percentage:.1f}%)")

        # Trade statistics
        print(f"\n💼 Trade Statistics:")
        print(f"   Total trades executed: {len(trades)}")

        # Separate open and close trades
        open_trades = [t for t in trades if 'OPEN' in t['type']]
        close_trades = [t for t in trades if 'CLOSE' in t['type'] or 'STOP' in t['type'] or 'TAKE' in t['type']]

        print(f"   Positions opened: {len(open_trades)}")
        print(f"   Positions closed: {len(close_trades)}")

        if close_trades:
            # P/L analysis
            total_pnl_usdt = sum(t['pnl_usdt'] for t in close_trades)
            winning_trades = [t for t in close_trades if t['pnl_usdt'] > 0]
            losing_trades = [t for t in close_trades if t['pnl_usdt'] < 0]

            print(f"\n💰 Profit & Loss:")
            print(f"   Total P/L: ${total_pnl_usdt:+.2f} USDT")
            print(f"   Winning trades: {len(winning_trades)} ({len(winning_trades)/len(close_trades)*100:.1f}%)")
            print(f"   Losing trades: {len(losing_trades)} ({len(losing_trades)/len(close_trades)*100:.1f}%)")

            if winning_trades:
                avg_win = sum(t['pnl_usdt'] for t in winning_trades) / len(winning_trades)
                print(f"   Average win: ${avg_win:.2f} USDT")

            if losing_trades:
                avg_loss = sum(t['pnl_usdt'] for t in losing_trades) / len(losing_trades)
                print(f"   Average loss: ${avg_loss:.2f} USDT")

            # Trade breakdown
            print(f"\n📋 Trade Breakdown:")
            for i, trade in enumerate(close_trades, 1):
                print(f"\n   Trade #{i}:")
                print(f"      Time: {trade['timestamp']}")
                print(f"      Type: {trade['type']}")
                print(f"      Entry: ${trade['entry_price']:.2f}")
                print(f"      Exit: ${trade['exit_price']:.2f}")
                print(f"      P/L: {trade['pnl_percent']:+.2f}% (${trade['pnl_usdt']:+.2f} USDT)")

        else:
            print("   No closed trades yet")

        # Save report to file
        report_dir = 'reports'
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

        report_file = os.path.join(report_dir, f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("PERFORMANCE REPORT\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Symbol: {self.symbol}\n")
            f.write(f"Timeframe: {self.timeframe}\n\n")

            # Write all statistics
            f.write("SIGNAL STATISTICS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total signals: {len(signals)}\n")
            for signal_type, count in signal_counts.items():
                f.write(f"{signal_type}: {count}\n")

            f.write("\nTRADE STATISTICS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total trades: {len(trades)}\n")
            f.write(f"Positions opened: {len(open_trades)}\n")
            f.write(f"Positions closed: {len(close_trades)}\n")

            if close_trades:
                f.write(f"\nTotal P/L: ${total_pnl_usdt:+.2f} USDT\n")
                f.write(f"Winning trades: {len(winning_trades)}\n")
                f.write(f"Losing trades: {len(losing_trades)}\n")

                f.write("\nDETAILED TRADES\n")
                f.write("-" * 70 + "\n")
                for i, trade in enumerate(close_trades, 1):
                    f.write(f"\nTrade #{i}:\n")
                    f.write(f"  Time: {trade['timestamp']}\n")
                    f.write(f"  Type: {trade['type']}\n")
                    f.write(f"  Entry: ${trade['entry_price']:.2f}\n")
                    f.write(f"  Exit: ${trade['exit_price']:.2f}\n")
                    f.write(f"  P/L: {trade['pnl_percent']:+.2f}% (${trade['pnl_usdt']:+.2f} USDT)\n")

        print(f"\n📄 Report saved to: {report_file}")
        print("=" * 70)


def main():
    """Main function"""
    print("=" * 70)
    print("🔍 BTC/USDT Trading Bot - Performance Analysis")
    print("=" * 70)

    try:
        analyzer = PerformanceAnalyzer()

        # Download historical data (last 168 hours = 1 week)
        data = analyzer.download_historical_data(hours=168)

        # Run backtest
        results = analyzer.backtest_strategy(data)

        # Generate report
        analyzer.generate_report(results)

        print("\n✅ Analysis complete!")

    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
