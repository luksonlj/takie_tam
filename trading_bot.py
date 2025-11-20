"""
BTC/USDT Trading Bot
Main trading bot implementation with price action and technical indicators
"""
import ccxt
import pandas as pd
import time
from datetime import datetime
from typing import Optional, Dict
import config
from indicators import TechnicalIndicators
from price_action import PriceActionAnalyzer


class BTCTradingBot:
    """Main trading bot class for BTC/USDT trading"""

    def __init__(self):
        """Initialize the trading bot"""
        self.exchange = self._initialize_exchange()
        self.symbol = config.SYMBOL
        self.timeframe = config.TIMEFRAME
        self.position = None
        self.entry_price = 0
        self.indicators = TechnicalIndicators()
        self.analyzer = PriceActionAnalyzer()

        print(f"🤖 BTC Trading Bot initialized")
        print(f"Exchange: {config.EXCHANGE}")
        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {self.timeframe}")
        print(f"Test Mode: {config.TESTNET}")
        print("-" * 50)

    def _initialize_exchange(self) -> ccxt.Exchange:
        """
        Initialize exchange connection

        Returns:
            Exchange instance
        """
        exchange_class = getattr(ccxt, config.EXCHANGE)
        exchange = exchange_class({
            'apiKey': config.API_KEY,
            'secret': config.API_SECRET,
            'enableRateLimit': True,
        })

        if config.TESTNET:
            if hasattr(exchange, 'set_sandbox_mode'):
                exchange.set_sandbox_mode(True)
                print("⚠️  Testnet mode enabled")

        return exchange

    def fetch_ohlcv_data(self, limit: int = config.LOOKBACK_PERIOD) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from exchange

        Args:
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol,
                timeframe=self.timeframe,
                limit=limit
            )

            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            print(f"❌ Error fetching OHLCV data: {e}")
            return None

    def get_balance(self, currency: str = 'USDT') -> float:
        """
        Get account balance

        Args:
            currency: Currency to check

        Returns:
            Available balance
        """
        try:
            balance = self.exchange.fetch_balance()
            return balance['free'].get(currency, 0)
        except Exception as e:
            print(f"❌ Error fetching balance: {e}")
            return 0

    def place_order(self, side: str, amount: float) -> Optional[Dict]:
        """
        Place a market order

        Args:
            side: 'buy' or 'sell'
            amount: Amount to trade

        Returns:
            Order information
        """
        try:
            if config.TESTNET:
                print(f"📝 TESTNET: {side.upper()} order for {amount} BTC")
                return {
                    'id': f'test_{int(time.time())}',
                    'symbol': self.symbol,
                    'side': side,
                    'amount': amount,
                    'price': 0,
                    'status': 'closed'
                }

            order = self.exchange.create_market_order(
                symbol=self.symbol,
                side=side,
                amount=amount
            )
            print(f"✅ {side.upper()} order executed: {order['id']}")
            return order

        except Exception as e:
            print(f"❌ Error placing {side} order: {e}")
            return None

    def execute_trade(self, signal: Dict):
        """
        Execute trade based on signal

        Args:
            signal: Trading signal dictionary
        """
        signal_type = signal['signal']
        confidence = signal['confidence']
        min_confidence = 40  # Reduced for more active trading

        # BUY Signal - Open LONG or Close SHORT
        if signal_type == 'BUY' and confidence >= min_confidence:

            # Close SHORT position if exists
            if self.position == 'short':
                print(f"\n🟢 CLOSING SHORT (Confidence: {confidence}%)")
                print(f"Reasons: {', '.join(signal['reasons'])}")
                print(f"Price: ${signal['price']:.2f}")

                if self.entry_price > 0:
                    pnl_percent = ((self.entry_price - signal['price']) / self.entry_price) * 100
                    print(f"P/L: {pnl_percent:+.2f}%")

                trade_amount = config.TRADE_AMOUNT
                order = self.place_order('buy', trade_amount)
                if order:
                    self.position = None
                    self.entry_price = 0
                    print(f"✅ SHORT position closed at ${signal['price']:.2f}")

            # Open LONG position if no position
            elif self.position is None:
                print(f"\n🟢 BUY SIGNAL - Opening LONG (Confidence: {confidence}%)")
                print(f"Reasons: {', '.join(signal['reasons'])}")
                print(f"Price: ${signal['price']:.2f}")

                usdt_balance = self.get_balance('USDT')
                trade_amount = min(config.TRADE_AMOUNT, config.MAX_POSITION_SIZE)

                if usdt_balance > signal['price'] * trade_amount:
                    order = self.place_order('buy', trade_amount)
                    if order:
                        self.position = 'long'
                        self.entry_price = signal['price']
                        print(f"✅ LONG position opened at ${self.entry_price:.2f}")
                else:
                    print(f"⚠️  Insufficient balance: ${usdt_balance:.2f} USDT")

        # SELL Signal - Close LONG or Open SHORT
        elif signal_type == 'SELL' and confidence >= min_confidence:

            # Close LONG position if exists
            if self.position == 'long':
                print(f"\n🔴 CLOSING LONG (Confidence: {confidence}%)")
                print(f"Reasons: {', '.join(signal['reasons'])}")
                print(f"Price: ${signal['price']:.2f}")

                if self.entry_price > 0:
                    pnl_percent = ((signal['price'] - self.entry_price) / self.entry_price) * 100
                    print(f"P/L: {pnl_percent:+.2f}%")

                btc_balance = self.get_balance('BTC')
                if btc_balance > 0:
                    order = self.place_order('sell', btc_balance)
                    if order:
                        self.position = None
                        self.entry_price = 0
                        print(f"✅ LONG position closed at ${signal['price']:.2f}")
                else:
                    print(f"⚠️  No BTC balance to sell")

            # Open SHORT position if no position
            elif self.position is None:
                print(f"\n🔴 SELL SIGNAL - Opening SHORT (Confidence: {confidence}%)")
                print(f"Reasons: {', '.join(signal['reasons'])}")
                print(f"Price: ${signal['price']:.2f}")
                print(f"ℹ️  Note: SHORT requires margin/futures trading")

                # For spot trading, we can't really SHORT
                # For futures/margin, implement SHORT logic here
                btc_balance = self.get_balance('BTC')
                trade_amount = config.TRADE_AMOUNT

                if config.TESTNET:
                    # Simulate SHORT in testnet
                    self.position = 'short'
                    self.entry_price = signal['price']
                    print(f"✅ SHORT position opened at ${self.entry_price:.2f} (SIMULATED)")
                elif btc_balance >= trade_amount:
                    order = self.place_order('sell', trade_amount)
                    if order:
                        self.position = 'short'
                        self.entry_price = signal['price']
                        print(f"✅ SHORT position opened at ${self.entry_price:.2f}")
                else:
                    print(f"⚠️  Cannot open SHORT: insufficient BTC or use margin/futures")

    def check_stop_loss_take_profit(self, current_price: float):
        """
        Check stop loss and take profit levels

        Args:
            current_price: Current market price
        """
        if self.position is None or self.entry_price == 0:
            return

        # Calculate P/L based on position type
        if self.position == 'long':
            pnl_percent = ((current_price - self.entry_price) / self.entry_price) * 100
        elif self.position == 'short':
            pnl_percent = ((self.entry_price - current_price) / self.entry_price) * 100
        else:
            return

        # Check stop loss
        if pnl_percent <= -config.STOP_LOSS_PERCENT:
            print(f"\n🛑 STOP LOSS triggered at {pnl_percent:.2f}%")

            if self.position == 'long':
                btc_balance = self.get_balance('BTC')
                if btc_balance > 0:
                    self.place_order('sell', btc_balance)
                    self.position = None
                    self.entry_price = 0
            elif self.position == 'short':
                trade_amount = config.TRADE_AMOUNT
                self.place_order('buy', trade_amount)
                self.position = None
                self.entry_price = 0

        # Check take profit
        elif pnl_percent >= config.TAKE_PROFIT_PERCENT:
            print(f"\n💰 TAKE PROFIT triggered at {pnl_percent:.2f}%")

            if self.position == 'long':
                btc_balance = self.get_balance('BTC')
                if btc_balance > 0:
                    self.place_order('sell', btc_balance)
                    self.position = None
                    self.entry_price = 0
            elif self.position == 'short':
                trade_amount = config.TRADE_AMOUNT
                self.place_order('buy', trade_amount)
                self.position = None
                self.entry_price = 0

    def print_analysis(self, signal: Dict):
        """
        Print detailed analysis

        Args:
            signal: Signal dictionary with analysis
        """
        print(f"\n{'='*50}")
        print(f"📊 Analysis at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        print(f"Price: ${signal['price']:.2f}")
        print(f"Trend: {signal['trend'].upper()}")
        print(f"Signal: {signal['signal']} (Confidence: {signal['confidence']}%)")
        print(f"\n📈 Moving Averages:")
        print(f"  MA10: ${signal['ma10']:.2f}")
        print(f"  MA30: ${signal['ma30']:.2f}")
        print(f"  MA60: ${signal['ma60']:.2f}")
        print(f"\n📊 Volume Analysis:")
        print(f"  Volume Ratio: {signal['volume_analysis']['volume_ratio']:.2f}x")
        print(f"  High Volume: {signal['volume_analysis']['high_volume']}")
        print(f"\n💹 OBV Analysis:")
        print(f"  OBV Trend: {signal['obv_analysis']['obv_trend']}")
        print(f"  Divergence: {signal['obv_analysis']['obv_divergence']}")
        print(f"\n📝 Reasons:")
        for reason in signal['reasons']:
            print(f"  • {reason}")

        if self.position:
            # Calculate P/L based on position type
            if self.position == 'long':
                pnl = ((signal['price'] - self.entry_price) / self.entry_price) * 100
            elif self.position == 'short':
                pnl = ((self.entry_price - signal['price']) / self.entry_price) * 100
            else:
                pnl = 0

            print(f"\n💼 Position: {self.position.upper()}")
            print(f"  Entry: ${self.entry_price:.2f}")
            print(f"  Current: ${signal['price']:.2f}")
            print(f"  P/L: {pnl:+.2f}%")

        print(f"{'='*50}\n")

    def run(self, iterations: int = None, sleep_time: int = 30):
        """
        Run the trading bot

        Args:
            iterations: Number of iterations (None for infinite)
            sleep_time: Sleep time between iterations in seconds
        """
        print("\n🚀 Starting BTC Trading Bot...")
        print(f"Running with {sleep_time}s interval\n")

        iteration = 0
        try:
            while iterations is None or iteration < iterations:
                iteration += 1

                # Fetch market data
                data = self.fetch_ohlcv_data()

                if data is not None and len(data) >= 60:
                    # Add indicators
                    data = self.indicators.add_all_indicators(
                        data,
                        ma_periods=[config.MA_SHORT, config.MA_MEDIUM, config.MA_LONG]
                    )

                    # Generate signal
                    signal = self.analyzer.generate_signal(data)

                    # Print analysis
                    self.print_analysis(signal)

                    # Check stop loss / take profit
                    self.check_stop_loss_take_profit(signal['price'])

                    # Execute trade
                    self.execute_trade(signal)

                else:
                    print("⚠️  Insufficient data, waiting...")

                # Sleep before next iteration
                if iterations is None or iteration < iterations:
                    print(f"💤 Sleeping for {sleep_time} seconds...")
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\n⚠️  Bot stopped by user")
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    bot = BTCTradingBot()

    # Run bot with 30 second intervals for active trading
    # Bot will check market conditions and trade both BUY and SELL signals
    bot.run(sleep_time=30)  # Check every 30 seconds


if __name__ == "__main__":
    main()
