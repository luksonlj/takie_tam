"""
Demo Performance Analysis Script
Demonstrates bot performance analysis using simulated data
Run performance_analysis.py on your local machine for real data from Binance
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config
from indicators import TechnicalIndicators
from price_action import PriceActionAnalyzer
import os


class DemoAnalyzer:
    """Demo analyzer using simulated market data"""

    def __init__(self):
        """Initialize the analyzer"""
        self.symbol = config.SYMBOL
        self.timeframe = config.TIMEFRAME
        self.indicators = TechnicalIndicators()
        self.analyzer = PriceActionAnalyzer()

    def generate_simulated_data(self, hours: int = 168, base_price: float = 84000) -> pd.DataFrame:
        """
        Generate simulated OHLCV data for demonstration

        Args:
            hours: Number of hours of data to generate
            base_price: Base BTC price

        Returns:
            DataFrame with simulated OHLCV data
        """
        print(f"📊 Generating {hours} hours of simulated data for demonstration...")

        # For 1h timeframe
        num_candles = hours

        # Generate timestamps
        timestamps = [datetime.now() - timedelta(hours=hours-i) for i in range(num_candles)]

        # Generate realistic price movement with trend
        np.random.seed(42)  # For reproducibility

        prices = []
        volumes = []
        current_price = base_price

        # Simulate market with different phases
        for i in range(num_candles):
            # Add some trend and volatility
            if i < num_candles // 3:
                # Bullish phase
                trend = np.random.normal(50, 200)
            elif i < 2 * num_candles // 3:
                # Sideways phase
                trend = np.random.normal(0, 150)
            else:
                # Bearish phase
                trend = np.random.normal(-50, 200)

            current_price += trend
            current_price = max(current_price, base_price * 0.8)  # Don't drop too much
            current_price = min(current_price, base_price * 1.2)  # Don't rise too much

            # Generate OHLC from current price
            high = current_price + abs(np.random.normal(0, 100))
            low = current_price - abs(np.random.normal(0, 100))
            open_price = current_price + np.random.normal(0, 50)
            close_price = current_price + np.random.normal(0, 50)

            prices.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price
            })

            # Generate volume
            volume = np.random.uniform(50, 200)
            volumes.append(volume)

        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': [p['open'] for p in prices],
            'high': [p['high'] for p in prices],
            'low': [p['low'] for p in prices],
            'close': [p['close'] for p in prices],
            'volume': volumes
        })

        print(f"✅ Generated {len(df)} candles")
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
        print("📊 PERFORMANCE REPORT (DEMO WITH SIMULATED DATA)")
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
                max_win = max(t['pnl_usdt'] for t in winning_trades)
                print(f"   Average win: ${avg_win:.2f} USDT")
                print(f"   Largest win: ${max_win:.2f} USDT")

            if losing_trades:
                avg_loss = sum(t['pnl_usdt'] for t in losing_trades) / len(losing_trades)
                max_loss = min(t['pnl_usdt'] for t in losing_trades)
                print(f"   Average loss: ${avg_loss:.2f} USDT")
                print(f"   Largest loss: ${max_loss:.2f} USDT")

            # Risk/Reward ratio
            if losing_trades and winning_trades:
                risk_reward = abs(avg_win / avg_loss)
                print(f"   Risk/Reward Ratio: {risk_reward:.2f}")

            # Trade breakdown (show first 10)
            print(f"\n📋 Trade Breakdown (showing first 10):")
            for i, trade in enumerate(close_trades[:10], 1):
                print(f"\n   Trade #{i}:")
                print(f"      Time: {trade['timestamp']}")
                print(f"      Type: {trade['type']}")
                print(f"      Entry: ${trade['entry_price']:.2f}")
                print(f"      Exit: ${trade['exit_price']:.2f}")
                print(f"      P/L: {trade['pnl_percent']:+.2f}% (${trade['pnl_usdt']:+.2f} USDT)")

            if len(close_trades) > 10:
                print(f"\n   ... and {len(close_trades) - 10} more trades")

        else:
            print("   No closed trades yet")

        # Save report to file
        report_dir = 'reports'
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

        report_file = os.path.join(report_dir, f"demo_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("PERFORMANCE REPORT (DEMO WITH SIMULATED DATA)\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Symbol: {self.symbol}\n")
            f.write(f"Timeframe: {self.timeframe}\n")
            f.write(f"Data Type: SIMULATED (for demonstration)\n\n")

            f.write("NOTE: This is a demo with simulated data.\n")
            f.write("Run performance_analysis.py on your local machine with internet\n")
            f.write("access to analyze real Binance data.\n\n")

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
    print("🔍 BTC/USDT Trading Bot - DEMO Performance Analysis")
    print("=" * 70)
    print("\nNOTE: This demo uses simulated data for demonstration.")
    print("Run 'performance_analysis.py' on your local machine to analyze")
    print("real data from Binance.\n")

    try:
        analyzer = DemoAnalyzer()

        # Generate simulated data (last 168 hours = 1 week)
        data = analyzer.generate_simulated_data(hours=168, base_price=84000)

        # Run backtest
        results = analyzer.backtest_strategy(data)

        # Generate report
        analyzer.generate_report(results)

        print("\n✅ Demo analysis complete!")
        print("\n💡 Next Steps:")
        print("   1. Copy performance_analysis.py to your local machine")
        print("   2. Make sure you have internet access")
        print("   3. Run: python performance_analysis.py")
        print("   4. This will download real Binance data and analyze it")

    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
