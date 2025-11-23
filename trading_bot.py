"""
BTC/USDT Trading Bot
Main trading bot implementation with price action and technical indicators
"""
import ccxt
import pandas as pd
import time
import os
import logging
from datetime import datetime
from typing import Optional, Dict
import config
from indicators import TechnicalIndicators
from price_action import PriceActionAnalyzer


def setup_logging():
    """
    Setup logging configuration with file and console handlers

    Returns:
        logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create logger
    logger = logging.getLogger('TradingBot')
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers = []

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter('%(message)s')

    # File handler - daily log file
    log_filename = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y-%m-%d')}.log")
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class BTCTradingBot:
    """Main trading bot class for BTC/USDT trading"""

    def __init__(self):
        """Initialize the trading bot"""
        self.logger = setup_logging()
        self.exchange = self._initialize_exchange()
        self.symbol = config.SYMBOL
        self.timeframe = config.TIMEFRAME
        self.position = None
        self.entry_price = 0
        self.position_size = 0  # Amount of BTC in position
        self.indicators = TechnicalIndicators()
        self.analyzer = PriceActionAnalyzer()

        # Pyramiding tracking
        self.pyramid_levels = []  # List of {price, size} for each entry
        self.max_pyramid_levels = 3  # Max 3 additional entries (4 total)
        self.pyramid_step_percent = 1.5  # Add position every +1.5% profit
        self.last_pyramid_price = 0  # Last price where we added to position

        # Contrarian entry tracking
        self.local_high = 0  # Track local high for pullback entries
        self.local_low = float('inf')  # Track local low for bounce entries
        self.pullback_percent = 1.0  # -1% pullback in uptrend = buy signal
        self.bounce_percent = 1.0  # +1% bounce in downtrend = sell signal

        # Session tracking for 4h reports
        self.session_start = datetime.now()
        self.last_report_time = datetime.now()
        self.session_stats = {
            'total_signals': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'positions_opened': 0,
            'positions_closed': 0,
            'closed_trades': [],  # List of completed trades with P/L
            'max_price': 0,
            'min_price': float('inf'),
            'signals_history': []  # Last 20 signals for context
        }

        self.logger.info("🤖 BTC Trading Bot initialized")
        self.logger.info(f"Exchange: {config.EXCHANGE}")
        self.logger.info(f"Symbol: {self.symbol}")
        self.logger.info(f"Timeframe: {self.timeframe}")
        self.logger.info(f"Test Mode: {config.TESTNET}")
        self.logger.info("-" * 50)

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

        # Enable Futures trading for Binance
        if config.EXCHANGE.lower() == 'binance':
            exchange.options['defaultType'] = 'future'  # Use USDT-M Futures
            self.logger.info("📊 Binance Futures mode enabled")

        # Enable testnet mode
        if config.TESTNET:
            if hasattr(exchange, 'set_sandbox_mode'):
                exchange.set_sandbox_mode(True)
                self.logger.info("⚠️  Testnet mode enabled")
                self.logger.info("🔗 Using: https://testnet.binancefuture.com/")

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
            self.logger.error(f"❌ Error fetching OHLCV data: {e}")
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
            self.logger.info(f"❌ Error fetching balance: {e}")
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
                self.logger.info(f"📝 TESTNET: {side.upper()} order for {amount} BTC")
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
            self.logger.info(f"✅ {side.upper()} order executed: {order['id']}")
            return order

        except Exception as e:
            self.logger.info(f"❌ Error placing {side} order: {e}")
            return None

    def execute_trade(self, signal: Dict):
        """
        Execute trade based on signal

        Args:
            signal: Trading signal dictionary
        """
        signal_type = signal['signal']
        confidence = signal['confidence']
        min_confidence = 60  # Increased for higher quality signals

        # BUY Signal - Open LONG or Close SHORT
        if signal_type == 'BUY' and confidence >= min_confidence:

            # Close SHORT position if exists
            if self.position == 'short':
                self.logger.info(f"\n🟢 CLOSING SHORT (Confidence: {confidence}%)")
                self.logger.info(f"Reasons: {', '.join(signal['reasons'])}")
                self.logger.info(f"Price: ${signal['price']:.2f}")

                if self.entry_price > 0 and self.position_size > 0:
                    pnl_percent = ((self.entry_price - signal['price']) / self.entry_price) * 100
                    pnl_usdt = self.position_size * (self.entry_price - signal['price'])
                    self.logger.info(f"P/L: {pnl_percent:+.2f}% (${pnl_usdt:+.2f} USDT)")

                    # Track closed trade
                    self.session_stats['closed_trades'].append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'CLOSE_SHORT',
                        'entry_price': self.entry_price,
                        'exit_price': signal['price'],
                        'position_size': self.position_size,
                        'pnl_percent': pnl_percent,
                        'pnl_usdt': pnl_usdt
                    })
                    self.session_stats['positions_closed'] += 1

                trade_amount = self.position_size if self.position_size > 0 else config.TRADE_AMOUNT
                order = self.place_order('buy', trade_amount)
                if order:
                    self.reset_position_tracking()
                    self.logger.info(f"✅ SHORT position closed at ${signal['price']:.2f}")

            # Open LONG position if no position
            elif self.position is None:
                self.logger.info(f"\n🟢 BUY SIGNAL - Opening LONG (Confidence: {confidence}%)")
                self.logger.info(f"Reasons: {', '.join(signal['reasons'])}")
                self.logger.info(f"Price: ${signal['price']:.2f}")

                usdt_balance = self.get_balance('USDT')
                trade_amount = min(config.TRADE_AMOUNT, config.MAX_POSITION_SIZE)

                if usdt_balance > signal['price'] * trade_amount:
                    order = self.place_order('buy', trade_amount)
                    if order:
                        self.position = 'long'
                        self.entry_price = signal['price']
                        self.position_size = trade_amount
                        self.session_stats['positions_opened'] += 1
                        self.logger.info(f"✅ LONG position opened at ${self.entry_price:.2f}")
                        self.logger.info(f"Position size: {self.position_size} BTC")
                else:
                    self.logger.info(f"⚠️  Insufficient balance: ${usdt_balance:.2f} USDT")

        # SELL Signal - Close LONG or Open SHORT
        elif signal_type == 'SELL' and confidence >= min_confidence:

            # Close LONG position if exists
            if self.position == 'long':
                self.logger.info(f"\n🔴 CLOSING LONG (Confidence: {confidence}%)")
                self.logger.info(f"Reasons: {', '.join(signal['reasons'])}")
                self.logger.info(f"Price: ${signal['price']:.2f}")

                if self.entry_price > 0 and self.position_size > 0:
                    pnl_percent = ((signal['price'] - self.entry_price) / self.entry_price) * 100
                    pnl_usdt = self.position_size * (signal['price'] - self.entry_price)
                    self.logger.info(f"P/L: {pnl_percent:+.2f}% (${pnl_usdt:+.2f} USDT)")

                    # Track closed trade
                    self.session_stats['closed_trades'].append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'CLOSE_LONG',
                        'entry_price': self.entry_price,
                        'exit_price': signal['price'],
                        'position_size': self.position_size,
                        'pnl_percent': pnl_percent,
                        'pnl_usdt': pnl_usdt
                    })
                    self.session_stats['positions_closed'] += 1

                btc_balance = self.get_balance('BTC')
                if btc_balance > 0:
                    order = self.place_order('sell', btc_balance)
                    if order:
                        self.reset_position_tracking()
                        self.logger.info(f"✅ LONG position closed at ${signal['price']:.2f}")
                else:
                    self.logger.info(f"⚠️  No BTC balance to sell")

            # Open SHORT position if no position
            elif self.position is None:
                self.logger.info(f"\n🔴 SELL SIGNAL - Opening SHORT (Confidence: {confidence}%)")
                self.logger.info(f"Reasons: {', '.join(signal['reasons'])}")
                self.logger.info(f"Price: ${signal['price']:.2f}")
                self.logger.info(f"ℹ️  Note: SHORT requires margin/futures trading")

                # For spot trading, we can't really SHORT
                # For futures/margin, implement SHORT logic here
                btc_balance = self.get_balance('BTC')
                trade_amount = config.TRADE_AMOUNT

                if config.TESTNET:
                    # Simulate SHORT in testnet
                    self.position = 'short'
                    self.entry_price = signal['price']
                    self.position_size = trade_amount
                    self.session_stats['positions_opened'] += 1
                    self.logger.info(f"✅ SHORT position opened at ${self.entry_price:.2f} (SIMULATED)")
                    self.logger.info(f"Position size: {self.position_size} BTC")
                elif btc_balance >= trade_amount:
                    order = self.place_order('sell', trade_amount)
                    if order:
                        self.position = 'short'
                        self.entry_price = signal['price']
                        self.position_size = trade_amount
                        self.session_stats['positions_opened'] += 1
                        self.logger.info(f"✅ SHORT position opened at ${self.entry_price:.2f}")
                        self.logger.info(f"Position size: {self.position_size} BTC")
                else:
                    self.logger.info(f"⚠️  Cannot open SHORT: insufficient BTC or use margin/futures")

    def update_local_extremes(self, current_price: float, signal: Dict):
        """
        Update local high/low for contrarian entry detection

        Args:
            current_price: Current market price
            signal: Current trading signal
        """
        # Update local high in uptrend
        if signal.get('trend') == 'BULLISH' or signal.get('main_trend') == 'BULLISH':
            if current_price > self.local_high:
                self.local_high = current_price

        # Update local low in downtrend
        if signal.get('trend') == 'BEARISH' or signal.get('main_trend') == 'BEARISH':
            if current_price < self.local_low:
                self.local_low = current_price

    def check_pyramid_opportunity(self, current_price: float, signal: Dict) -> bool:
        """
        Check if we should add to existing position (pyramiding)

        Args:
            current_price: Current market price
            signal: Current trading signal

        Returns:
            True if should pyramid, False otherwise
        """
        # Can't pyramid if no position
        if self.position is None:
            return False

        # Can't pyramid if max levels reached
        if len(self.pyramid_levels) >= self.max_pyramid_levels:
            return False

        # Calculate reference price (last pyramid or entry)
        ref_price = self.last_pyramid_price if self.last_pyramid_price > 0 else self.entry_price

        # Check if position is profitable enough to pyramid
        if self.position == 'long':
            gain_percent = ((current_price - ref_price) / ref_price) * 100
            # Must be in profit and signal still bullish
            if gain_percent >= self.pyramid_step_percent:
                if signal['signal'] == 'BUY' and signal.get('main_trend') == 'BULLISH':
                    return True

        elif self.position == 'short':
            gain_percent = ((ref_price - current_price) / ref_price) * 100
            # Must be in profit and signal still bearish
            if gain_percent >= self.pyramid_step_percent:
                if signal['signal'] == 'SELL' and signal.get('main_trend') == 'BEARISH':
                    return True

        return False

    def add_to_position(self, signal: Dict):
        """
        Add to existing position (pyramid)

        Args:
            signal: Current trading signal
        """
        trade_amount = config.TRADE_AMOUNT

        if self.position == 'long':
            self.logger.info(f"\n📈 PYRAMIDING LONG (Level {len(self.pyramid_levels) + 1})")
            self.logger.info(f"Adding {trade_amount} BTC at ${signal['price']:.2f}")

            order = self.place_order('buy', trade_amount)
            if order:
                # Track this pyramid level
                self.pyramid_levels.append({
                    'price': signal['price'],
                    'size': trade_amount
                })
                self.last_pyramid_price = signal['price']

                # Update average entry price
                total_cost = self.entry_price * self.position_size
                for level in self.pyramid_levels:
                    total_cost += level['price'] * level['size']

                self.position_size += trade_amount
                self.entry_price = total_cost / self.position_size

                self.logger.info(f"✅ Position increased to {self.position_size} BTC")
                self.logger.info(f"📊 New average entry: ${self.entry_price:.2f}")

        elif self.position == 'short':
            self.logger.info(f"\n📉 PYRAMIDING SHORT (Level {len(self.pyramid_levels) + 1})")
            self.logger.info(f"Adding {trade_amount} BTC at ${signal['price']:.2f}")

            order = self.place_order('sell', trade_amount)
            if order:
                # Track this pyramid level
                self.pyramid_levels.append({
                    'price': signal['price'],
                    'size': trade_amount
                })
                self.last_pyramid_price = signal['price']

                # Update average entry price
                total_cost = self.entry_price * self.position_size
                for level in self.pyramid_levels:
                    total_cost += level['price'] * level['size']

                self.position_size += trade_amount
                self.entry_price = total_cost / self.position_size

                self.logger.info(f"✅ Position increased to {self.position_size} BTC")
                self.logger.info(f"📊 New average entry: ${self.entry_price:.2f}")

    def check_contrarian_entry(self, current_price: float, signal: Dict) -> bool:
        """
        Check for contrarian entry opportunity (buy the dip / sell the rip)

        Args:
            current_price: Current market price
            signal: Current trading signal

        Returns:
            True if contrarian entry signal, False otherwise
        """
        # Only enter contrarian if no position
        if self.position is not None:
            return False

        # Check for bullish contrarian (buy the dip in uptrend)
        if signal.get('main_trend') == 'BULLISH' and self.local_high > 0:
            pullback = ((self.local_high - current_price) / self.local_high) * 100

            # Price pulled back 1% from local high
            if pullback >= self.pullback_percent:
                # OBV must still be bullish (trend intact)
                if signal.get('obv_trend') == 'bullish':
                    self.logger.info(f"\n🎯 CONTRARIAN BUY OPPORTUNITY")
                    self.logger.info(f"Pullback: {pullback:.2f}% from ${self.local_high:.2f}")
                    self.logger.info(f"Main trend: BULLISH, OBV: {signal.get('obv_trend')}")
                    return True

        # Check for bearish contrarian (sell the rip in downtrend)
        elif signal.get('main_trend') == 'BEARISH' and self.local_low < float('inf'):
            bounce = ((current_price - self.local_low) / self.local_low) * 100

            # Price bounced 1% from local low
            if bounce >= self.bounce_percent:
                # OBV must still be bearish (trend intact)
                if signal.get('obv_trend') == 'bearish':
                    self.logger.info(f"\n🎯 CONTRARIAN SELL OPPORTUNITY")
                    self.logger.info(f"Bounce: {bounce:.2f}% from ${self.local_low:.2f}")
                    self.logger.info(f"Main trend: BEARISH, OBV: {signal.get('obv_trend')}")
                    return True

        return False

    def reset_position_tracking(self):
        """Reset all position-related tracking variables"""
        self.position = None
        self.entry_price = 0
        self.position_size = 0
        self.pyramid_levels = []
        self.last_pyramid_price = 0
        self.local_high = 0
        self.local_low = float('inf')

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
            self.logger.info(f"\n🛑 STOP LOSS triggered at {pnl_percent:.2f}%")

            # Track closed trade before resetting position
            if self.position == 'long':
                pnl_usdt = self.position_size * (current_price - self.entry_price)
                self.session_stats['closed_trades'].append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'STOP_LOSS_LONG',
                    'entry_price': self.entry_price,
                    'exit_price': current_price,
                    'position_size': self.position_size,
                    'pnl_percent': pnl_percent,
                    'pnl_usdt': pnl_usdt
                })
                self.session_stats['positions_closed'] += 1

                btc_balance = self.get_balance('BTC')
                if btc_balance > 0:
                    self.place_order('sell', btc_balance)
                    self.reset_position_tracking()
            elif self.position == 'short':
                pnl_usdt = self.position_size * (self.entry_price - current_price)
                self.session_stats['closed_trades'].append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'STOP_LOSS_SHORT',
                    'entry_price': self.entry_price,
                    'exit_price': current_price,
                    'position_size': self.position_size,
                    'pnl_percent': pnl_percent,
                    'pnl_usdt': pnl_usdt
                })
                self.session_stats['positions_closed'] += 1

                trade_amount = self.position_size if self.position_size > 0 else config.TRADE_AMOUNT
                self.place_order('buy', trade_amount)
                self.reset_position_tracking()

        # Check take profit
        elif pnl_percent >= config.TAKE_PROFIT_PERCENT:
            self.logger.info(f"\n💰 TAKE PROFIT triggered at {pnl_percent:.2f}%")

            # Track closed trade before resetting position
            if self.position == 'long':
                pnl_usdt = self.position_size * (current_price - self.entry_price)
                self.session_stats['closed_trades'].append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'TAKE_PROFIT_LONG',
                    'entry_price': self.entry_price,
                    'exit_price': current_price,
                    'position_size': self.position_size,
                    'pnl_percent': pnl_percent,
                    'pnl_usdt': pnl_usdt
                })
                self.session_stats['positions_closed'] += 1

                btc_balance = self.get_balance('BTC')
                if btc_balance > 0:
                    self.place_order('sell', btc_balance)
                    self.reset_position_tracking()
            elif self.position == 'short':
                pnl_usdt = self.position_size * (self.entry_price - current_price)
                self.session_stats['closed_trades'].append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'TAKE_PROFIT_SHORT',
                    'entry_price': self.entry_price,
                    'exit_price': current_price,
                    'position_size': self.position_size,
                    'pnl_percent': pnl_percent,
                    'pnl_usdt': pnl_usdt
                })
                self.session_stats['positions_closed'] += 1

                trade_amount = self.position_size if self.position_size > 0 else config.TRADE_AMOUNT
                self.place_order('buy', trade_amount)
                self.reset_position_tracking()

    def print_analysis(self, signal: Dict):
        """
        Print detailed analysis

        Args:
            signal: Signal dictionary with analysis
        """
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"📊 Analysis at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"{'='*50}")
        self.logger.info(f"Price: ${signal['price']:.2f}")
        self.logger.info(f"Trend: {signal['trend'].upper()}")
        self.logger.info(f"Main Trend: {signal.get('main_trend', 'N/A').upper()}")
        self.logger.info(f"Signal: {signal['signal']} (Confidence: {signal['confidence']}%)")
        self.logger.info(f"\n📈 Moving Averages:")
        self.logger.info(f"  MA10: ${signal['ma10']:.2f}")
        self.logger.info(f"  MA30: ${signal['ma30']:.2f}")
        self.logger.info(f"  MA60: ${signal['ma60']:.2f}")
        self.logger.info(f"\n📊 Volume Analysis:")
        self.logger.info(f"  Volume Ratio: {signal['volume_analysis']['volume_ratio']:.2f}x")
        self.logger.info(f"  High Volume: {signal['volume_analysis']['high_volume']}")
        self.logger.info(f"\n💹 OBV Analysis:")
        self.logger.info(f"  OBV Trend: {signal['obv_analysis']['obv_trend']}")
        self.logger.info(f"  Divergence: {signal['obv_analysis']['obv_divergence']}")
        self.logger.info(f"\n📝 Reasons:")
        for reason in signal['reasons']:
            self.logger.info(f"  • {reason}")

        if self.position:
            # Calculate P/L based on position type
            if self.position == 'long':
                pnl_percent = ((signal['price'] - self.entry_price) / self.entry_price) * 100
                pnl_usdt = self.position_size * (signal['price'] - self.entry_price)
            elif self.position == 'short':
                pnl_percent = ((self.entry_price - signal['price']) / self.entry_price) * 100
                pnl_usdt = self.position_size * (self.entry_price - signal['price'])
            else:
                pnl_percent = 0
                pnl_usdt = 0

            self.logger.info(f"\n💼 Position: {self.position.upper()}")
            self.logger.info(f"  Entry: ${self.entry_price:.2f}")
            self.logger.info(f"  Current: ${signal['price']:.2f}")
            self.logger.info(f"  Size: {self.position_size} BTC")
            self.logger.info(f"  P/L: {pnl_percent:+.2f}% (${pnl_usdt:+.2f} USDT)")

            # Show pyramid info if any levels added
            if len(self.pyramid_levels) > 0:
                self.logger.info(f"  📈 Pyramid Levels: {len(self.pyramid_levels)}/{self.max_pyramid_levels}")
                for i, level in enumerate(self.pyramid_levels, 1):
                    self.logger.info(f"    Level {i}: ${level['price']:.2f} ({level['size']} BTC)")

        # Show contrarian opportunities
        if self.position is None:
            if signal.get('main_trend') == 'BULLISH' and self.local_high > 0:
                pullback = ((self.local_high - signal['price']) / self.local_high) * 100
                if pullback > 0:
                    self.logger.info(f"\n🎯 Pullback: {pullback:.2f}% from high ${self.local_high:.2f}")
                    if pullback >= self.pullback_percent:
                        self.logger.info(f"  ⚠️  Contrarian BUY opportunity detected!")

            elif signal.get('main_trend') == 'BEARISH' and self.local_low < float('inf'):
                bounce = ((signal['price'] - self.local_low) / self.local_low) * 100
                if bounce > 0:
                    self.logger.info(f"\n🎯 Bounce: {bounce:.2f}% from low ${self.local_low:.2f}")
                    if bounce >= self.bounce_percent:
                        self.logger.info(f"  ⚠️  Contrarian SELL opportunity detected!")

        self.logger.info(f"{'='*50}\n")

    def track_signal(self, signal: Dict):
        """
        Track signal for session statistics

        Args:
            signal: Signal dictionary
        """
        self.session_stats['total_signals'] += 1

        if signal['signal'] == 'BUY':
            self.session_stats['buy_signals'] += 1
        elif signal['signal'] == 'SELL':
            self.session_stats['sell_signals'] += 1
        else:
            self.session_stats['hold_signals'] += 1

        # Track price range
        price = signal['price']
        if price > self.session_stats['max_price']:
            self.session_stats['max_price'] = price
        if price < self.session_stats['min_price']:
            self.session_stats['min_price'] = price

        # Keep last 20 signals for context
        self.session_stats['signals_history'].append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'signal': signal['signal'],
            'confidence': signal['confidence'],
            'price': price,
            'trend': signal['trend'],
            'main_trend': signal.get('main_trend', 'N/A')
        })
        if len(self.session_stats['signals_history']) > 20:
            self.session_stats['signals_history'].pop(0)

    def generate_session_report(self):
        """Generate a session performance report every 4 hours"""
        report_dir = 'reports'
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

        now = datetime.now()
        session_duration = (now - self.session_start).total_seconds() / 3600  # hours
        since_last_report = (now - self.last_report_time).total_seconds() / 3600  # hours

        report_filename = os.path.join(
            report_dir,
            f"session_{now.strftime('%Y%m%d_%H%M%S')}.txt"
        )

        # Calculate statistics
        total_signals = self.session_stats['total_signals']
        buy_pct = (self.session_stats['buy_signals'] / total_signals * 100) if total_signals > 0 else 0
        sell_pct = (self.session_stats['sell_signals'] / total_signals * 100) if total_signals > 0 else 0
        hold_pct = (self.session_stats['hold_signals'] / total_signals * 100) if total_signals > 0 else 0

        # Calculate total P/L from closed trades
        closed_trades = self.session_stats['closed_trades']
        total_pnl_usdt = sum(t['pnl_usdt'] for t in closed_trades)
        winning_trades = [t for t in closed_trades if t['pnl_usdt'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl_usdt'] < 0]
        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0

        # Generate report content
        report = []
        report.append("=" * 80)
        report.append("🤖 BOT SESSION REPORT - AUTO-GENERATED")
        report.append("=" * 80)
        report.append(f"\n📅 Report Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"⏱️  Session Started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"⏱️  Session Duration: {session_duration:.2f} hours")
        report.append(f"⏱️  Since Last Report: {since_last_report:.2f} hours")
        report.append(f"\n{'='*80}")

        # Signal Statistics
        report.append("\n📊 SIGNAL STATISTICS")
        report.append("-" * 80)
        report.append(f"Total Signals Analyzed: {total_signals}")
        report.append(f"  • BUY signals:  {self.session_stats['buy_signals']} ({buy_pct:.1f}%)")
        report.append(f"  • SELL signals: {self.session_stats['sell_signals']} ({sell_pct:.1f}%)")
        report.append(f"  • HOLD signals: {self.session_stats['hold_signals']} ({hold_pct:.1f}%)")

        # Price Range
        if self.session_stats['max_price'] > 0:
            price_change = ((self.session_stats['max_price'] - self.session_stats['min_price']) /
                           self.session_stats['min_price'] * 100)
            report.append(f"\n💹 PRICE RANGE")
            report.append("-" * 80)
            report.append(f"Highest Price: ${self.session_stats['max_price']:.2f}")
            report.append(f"Lowest Price:  ${self.session_stats['min_price']:.2f}")
            report.append(f"Range: {price_change:.2f}%")

        # Position Status
        report.append(f"\n💼 POSITION STATUS")
        report.append("-" * 80)
        if self.position:
            current_price = self.session_stats['signals_history'][-1]['price'] if self.session_stats['signals_history'] else 0
            if self.position == 'long':
                pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
                pnl_usdt = self.position_size * (current_price - self.entry_price)
            else:  # short
                pnl_pct = ((self.entry_price - current_price) / self.entry_price) * 100
                pnl_usdt = self.position_size * (self.entry_price - current_price)

            report.append(f"Position: {self.position.upper()}")
            report.append(f"Entry Price: ${self.entry_price:.2f}")
            report.append(f"Current Price: ${current_price:.2f}")
            report.append(f"Position Size: {self.position_size} BTC")
            report.append(f"Unrealized P/L: {pnl_pct:+.2f}% (${pnl_usdt:+.2f} USDT)")
            report.append(f"Stop Loss: ${self.entry_price * (1 - config.STOP_LOSS_PERCENT/100):.2f} (-{config.STOP_LOSS_PERCENT}%)")
            report.append(f"Take Profit: ${self.entry_price * (1 + config.TAKE_PROFIT_PERCENT/100):.2f} (+{config.TAKE_PROFIT_PERCENT}%)")
        else:
            report.append("Position: NONE (waiting for signal)")
            report.append("Status: Bot is actively monitoring market")

        # Trading Statistics
        report.append(f"\n📈 TRADING STATISTICS")
        report.append("-" * 80)
        report.append(f"Positions Opened: {self.session_stats['positions_opened']}")
        report.append(f"Positions Closed: {self.session_stats['positions_closed']}")

        if closed_trades:
            report.append(f"\n💰 PROFIT & LOSS (Closed Trades Only)")
            report.append("-" * 80)
            report.append(f"Total Realized P/L: ${total_pnl_usdt:+.2f} USDT")
            report.append(f"Winning Trades: {len(winning_trades)} ({win_rate:.1f}% win rate)")
            report.append(f"Losing Trades: {len(losing_trades)}")

            if winning_trades:
                avg_win = sum(t['pnl_usdt'] for t in winning_trades) / len(winning_trades)
                max_win = max(t['pnl_usdt'] for t in winning_trades)
                report.append(f"Average Win: ${avg_win:.2f} USDT")
                report.append(f"Largest Win: ${max_win:.2f} USDT")

            if losing_trades:
                avg_loss = sum(t['pnl_usdt'] for t in losing_trades) / len(losing_trades)
                max_loss = min(t['pnl_usdt'] for t in losing_trades)
                report.append(f"Average Loss: ${avg_loss:.2f} USDT")
                report.append(f"Largest Loss: ${max_loss:.2f} USDT")

            # Recent Trades
            report.append(f"\n📋 RECENT CLOSED TRADES (Last 5)")
            report.append("-" * 80)
            for i, trade in enumerate(reversed(closed_trades[-5:]), 1):
                report.append(f"\nTrade #{len(closed_trades) - i + 1}:")
                report.append(f"  Time: {trade['timestamp']}")
                report.append(f"  Type: {trade['type']}")
                report.append(f"  Entry: ${trade['entry_price']:.2f}")
                report.append(f"  Exit: ${trade['exit_price']:.2f}")
                report.append(f"  P/L: {trade['pnl_percent']:+.2f}% (${trade['pnl_usdt']:+.2f} USDT)")
        else:
            report.append("\nNo closed trades yet - still testing strategy")

        # Recent Signals
        if self.session_stats['signals_history']:
            report.append(f"\n📝 RECENT SIGNALS (Last 10)")
            report.append("-" * 80)
            for sig in reversed(self.session_stats['signals_history'][-10:]):
                conf_str = f"{sig['confidence']}%" if sig['confidence'] > 0 else "0%"
                report.append(f"{sig['time']} | {sig['signal']:4s} ({conf_str:3s}) | "
                            f"${sig['price']:8.2f} | Trend: {sig['trend']:8s} | "
                            f"Main: {sig['main_trend']}")

        # Strategy Settings
        report.append(f"\n⚙️  STRATEGY SETTINGS")
        report.append("-" * 80)
        report.append(f"Timeframe: {config.TIMEFRAME}")
        report.append(f"Trade Amount: {config.TRADE_AMOUNT} BTC")
        report.append(f"Stop Loss: {config.STOP_LOSS_PERCENT}%")
        report.append(f"Take Profit: {config.TAKE_PROFIT_PERCENT}%")
        report.append(f"Min Confidence: 60%")
        report.append(f"Min Conditions: 4/4")

        # Performance Summary
        report.append(f"\n🎯 PERFORMANCE SUMMARY")
        report.append("-" * 80)
        if closed_trades:
            report.append(f"Total Realized P/L: ${total_pnl_usdt:+.2f} USDT")
            report.append(f"Win Rate: {win_rate:.1f}%")
            report.append(f"Total Trades: {len(closed_trades)}")
            if total_pnl_usdt > 0:
                report.append(f"Status: ✅ PROFITABLE")
            else:
                report.append(f"Status: ⚠️  LOSING")
        else:
            report.append(f"Status: 🔍 MONITORING (no trades yet)")
            report.append(f"Signals: {total_signals} analyzed, waiting for high-confidence setup")

        report.append(f"\n{'='*80}")
        report.append(f"End of Report - Next report in ~4 hours")
        report.append(f"{'='*80}\n")

        # Write to file
        report_text = '\n'.join(report)
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_text)

        # Also log to console
        self.logger.info(f"\n📊 4-HOUR SESSION REPORT GENERATED")
        self.logger.info(f"📄 Saved to: {report_filename}")
        self.logger.info(f"⏱️  Session Duration: {session_duration:.2f}h")
        self.logger.info(f"📈 Total Signals: {total_signals} (BUY:{buy_pct:.0f}% SELL:{sell_pct:.0f}% HOLD:{hold_pct:.0f}%)")
        if self.position:
            self.logger.info(f"💼 Position: {self.position.upper()} ({pnl_pct:+.2f}% unrealized)")
        if closed_trades:
            self.logger.info(f"💰 Realized P/L: ${total_pnl_usdt:+.2f} USDT ({win_rate:.0f}% win rate)")
        self.logger.info(f"{'='*50}\n")

        # Update last report time
        self.last_report_time = now

    def run(self, iterations: int = None, sleep_time: int = 30):
        """
        Run the trading bot

        Args:
            iterations: Number of iterations (None for infinite)
            sleep_time: Sleep time between iterations in seconds
        """
        self.logger.info("\n🚀 Starting BTC Trading Bot...")
        self.logger.info(f"Running with {sleep_time}s interval\n")

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

                    # Track signal for session statistics
                    self.track_signal(signal)

                    # Update local price extremes for contrarian entries
                    self.update_local_extremes(signal['price'], signal)

                    # Print analysis
                    self.print_analysis(signal)

                    # Check stop loss / take profit
                    self.check_stop_loss_take_profit(signal['price'])

                    # Check for pyramid opportunity (add to winning position)
                    if self.check_pyramid_opportunity(signal['price'], signal):
                        self.add_to_position(signal)

                    # Check for contrarian entry (buy dip / sell rip)
                    elif self.check_contrarian_entry(signal['price'], signal):
                        # Execute contrarian trade
                        self.execute_trade(signal)

                    # Execute normal trade
                    else:
                        self.execute_trade(signal)

                else:
                    self.logger.info("⚠️  Insufficient data, waiting...")

                # Check if 4 hours have elapsed since last report
                time_since_last_report = (datetime.now() - self.last_report_time).total_seconds() / 3600
                if time_since_last_report >= 4.0:
                    self.generate_session_report()

                # Sleep before next iteration
                if iterations is None or iteration < iterations:
                    self.logger.info(f"💤 Sleeping for {sleep_time} seconds...")
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            self.logger.info("\n\n⚠️  Bot stopped by user")
        except Exception as e:
            self.logger.info(f"\n❌ Error in main loop: {e}")
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
