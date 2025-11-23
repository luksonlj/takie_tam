"""
Configuration module for BTC/USDT Trading Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Exchange Configuration
EXCHANGE = os.getenv('EXCHANGE', 'binance')
API_KEY = os.getenv('API_KEY', '')
API_SECRET = os.getenv('API_SECRET', '')

# Trading Configuration
SYMBOL = os.getenv('SYMBOL', 'BTC/USDT')
TIMEFRAME = os.getenv('TIMEFRAME', '1h')
TRADE_AMOUNT = float(os.getenv('TRADE_AMOUNT', '0.001'))
TESTNET = os.getenv('TESTNET', 'true').lower() == 'true'

# Risk Management (Optimized for better performance)
MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '0.01'))
STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '3.0'))  # Increased from 2.0% to reduce false stops
TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '6.0'))  # Increased from 4.0% for better risk/reward (1:2 ratio)

# Indicator Settings
MA_SHORT = 10
MA_MEDIUM = 30
MA_LONG = 60
LOOKBACK_PERIOD = 100
