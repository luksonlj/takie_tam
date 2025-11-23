"""
Price Action Analysis Module
Analyzes price action patterns using technical indicators
"""
import pandas as pd
from typing import Dict, Optional


class PriceActionAnalyzer:
    """Analyze price action and generate trading signals"""

    @staticmethod
    def detect_trend(data: pd.DataFrame) -> str:
        """
        Detect market trend using moving averages

        Args:
            data: DataFrame with price and indicator data

        Returns:
            'bullish', 'bearish', or 'neutral'
        """
        if len(data) < 60:
            return 'neutral'

        last_row = data.iloc[-1]
        close = last_row['close']
        ma10 = last_row.get('ma_10', None)
        ma30 = last_row.get('ma_30', None)
        ma60 = last_row.get('ma_60', None)

        if ma10 is None or ma30 is None or ma60 is None:
            return 'neutral'

        # Golden cross pattern: MA10 > MA30 > MA60 and price above all MAs
        if ma10 > ma30 > ma60 and close > ma10:
            return 'bullish'

        # Death cross pattern: MA10 < MA30 < MA60 and price below all MAs
        if ma10 < ma30 < ma60 and close < ma10:
            return 'bearish'

        return 'neutral'

    @staticmethod
    def analyze_volume(data: pd.DataFrame) -> Dict[str, bool]:
        """
        Analyze volume conditions

        Args:
            data: DataFrame with volume data

        Returns:
            Dictionary with volume analysis
        """
        if len(data) < 2:
            return {'high_volume': False, 'increasing_volume': False}

        last_row = data.iloc[-1]
        prev_row = data.iloc[-2]

        volume_ratio = last_row.get('volume_ratio', 1.0)
        high_volume = volume_ratio > 1.5  # Volume 50% above average

        increasing_volume = last_row['volume'] > prev_row['volume']

        return {
            'high_volume': high_volume,
            'increasing_volume': increasing_volume,
            'volume_ratio': volume_ratio
        }

    @staticmethod
    def analyze_obv(data: pd.DataFrame) -> Dict[str, any]:
        """
        Analyze OBV trend

        Args:
            data: DataFrame with OBV data

        Returns:
            Dictionary with OBV analysis
        """
        if len(data) < 20:
            return {'obv_trend': 'neutral', 'obv_divergence': False}

        last_row = data.iloc[-1]
        obv = last_row.get('obv', 0)
        obv_ma = last_row.get('obv_ma', 0)

        # OBV trend
        if obv > obv_ma:
            obv_trend = 'bullish'
        elif obv < obv_ma:
            obv_trend = 'bearish'
        else:
            obv_trend = 'neutral'

        # Check for divergence (simplified)
        price_trend = 'up' if data['close'].iloc[-1] > data['close'].iloc[-5] else 'down'
        obv_change = obv - data['obv'].iloc[-5]
        obv_price_trend = 'up' if obv_change > 0 else 'down'

        divergence = price_trend != obv_price_trend

        return {
            'obv_trend': obv_trend,
            'obv_divergence': divergence,
            'obv_value': obv
        }

    @staticmethod
    def detect_main_trend(data: pd.DataFrame) -> str:
        """
        Detect main market trend using longer-term moving averages

        Args:
            data: DataFrame with price and indicator data

        Returns:
            'strong_bullish', 'bullish', 'bearish', 'strong_bearish', or 'neutral'
        """
        if len(data) < 60:
            return 'neutral'

        last_row = data.iloc[-1]
        ma30 = last_row.get('ma_30', None)
        ma60 = last_row.get('ma_60', None)

        if ma30 is None or ma60 is None:
            return 'neutral'

        # Check MA30 vs MA60 for main trend
        diff_percent = ((ma30 - ma60) / ma60) * 100

        if diff_percent > 2:  # MA30 significantly above MA60
            return 'strong_bullish'
        elif diff_percent > 0.5:
            return 'bullish'
        elif diff_percent < -2:  # MA30 significantly below MA60
            return 'strong_bearish'
        elif diff_percent < -0.5:
            return 'bearish'
        else:
            return 'neutral'

    @staticmethod
    def generate_signal(data: pd.DataFrame) -> Dict[str, any]:
        """
        Generate trading signal based on price action and indicators
        IMPROVED VERSION with stricter requirements and trend filtering

        Args:
            data: DataFrame with all indicators

        Returns:
            Dictionary with signal and analysis
        """
        if len(data) < 60:
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'reason': 'Insufficient data'
            }

        # Analyze components
        trend = PriceActionAnalyzer.detect_trend(data)
        main_trend = PriceActionAnalyzer.detect_main_trend(data)
        volume_analysis = PriceActionAnalyzer.analyze_volume(data)
        obv_analysis = PriceActionAnalyzer.analyze_obv(data)

        last_row = data.iloc[-1]
        close = last_row['close']
        ma10 = last_row.get('ma_10', 0)
        ma30 = last_row.get('ma_30', 0)
        ma60 = last_row.get('ma_60', 0)

        # Initialize signal
        signal = 'HOLD'
        confidence = 0
        reasons = []

        # BUY Signal Logic - More selective
        buy_conditions = 0

        # Strong requirement: bullish trend
        if trend == 'bullish':
            buy_conditions += 2
            reasons.append('Bullish trend detected')

        # OBV confirmation
        if obv_analysis['obv_trend'] == 'bullish':
            buy_conditions += 1
            reasons.append('OBV trending up')

        # Volume confirmation - now more important
        if volume_analysis['high_volume']:
            buy_conditions += 1
            reasons.append('High volume')

        if volume_analysis['increasing_volume']:
            buy_conditions += 1
            reasons.append('Increasing volume')

        # Price position
        if close > ma10 > ma30:
            buy_conditions += 1
            reasons.append('Price above key MAs')

        # Additional: Price momentum
        if close > ma60:
            buy_conditions += 1
            reasons.append('Price above long-term MA')

        # SELL Signal Logic - Much more strict with trend filter
        sell_conditions = 0

        # CRITICAL: Don't SHORT in strong uptrend!
        if main_trend in ['strong_bullish', 'bullish']:
            sell_conditions = 0  # Block all SHORT signals in uptrend
            reasons = ['Main trend is bullish - avoiding SHORT']
        else:
            # Strong requirement: bearish trend
            if trend == 'bearish':
                sell_conditions += 2
                reasons.append('Bearish trend detected')

            # OBV confirmation
            if obv_analysis['obv_trend'] == 'bearish':
                sell_conditions += 1
                reasons.append('OBV trending down')

            # Price position
            if close < ma10 < ma30:
                sell_conditions += 1
                reasons.append('Price below key MAs')

            # Price below long-term MA
            if close < ma60:
                sell_conditions += 1
                reasons.append('Price below long-term MA')

            # Divergence as additional confirmation
            if obv_analysis['obv_divergence']:
                sell_conditions += 1
                reasons.append('OBV divergence detected')

            # Volume requirement for SHORT - must have confirmation
            if volume_analysis['high_volume']:
                sell_conditions += 1
                reasons.append('High volume confirmation')

        # Determine signal - STRICTER REQUIREMENTS
        # Require 4+ conditions AND 60%+ confidence
        if buy_conditions >= 4:
            signal = 'BUY'
            confidence = min(buy_conditions * 15, 100)  # 15% per condition
        elif sell_conditions >= 4:
            signal = 'SELL'
            confidence = min(sell_conditions * 15, 100)
        else:
            signal = 'HOLD'
            confidence = 0
            reasons = [f'Waiting for stronger confirmation (BUY:{buy_conditions}/4, SELL:{sell_conditions}/4)']

        return {
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons,
            'trend': trend,
            'main_trend': main_trend,
            'volume_analysis': volume_analysis,
            'obv_analysis': obv_analysis,
            'price': close,
            'ma10': ma10,
            'ma30': ma30,
            'ma60': ma60
        }
