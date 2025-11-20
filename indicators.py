"""
Technical Indicators Module
Calculates OBV, Volume, and Moving Averages for trading analysis
"""
import pandas as pd
import numpy as np


class TechnicalIndicators:
    """Calculate technical indicators for trading decisions"""

    @staticmethod
    def calculate_ma(data: pd.DataFrame, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average

        Args:
            data: DataFrame with OHLCV data
            period: MA period

        Returns:
            Series with MA values
        """
        return data['close'].rolling(window=period).mean()

    @staticmethod
    def calculate_obv(data: pd.DataFrame) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV)

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with OBV values
        """
        obv = [0]
        for i in range(1, len(data)):
            if data['close'].iloc[i] > data['close'].iloc[i - 1]:
                obv.append(obv[-1] + data['volume'].iloc[i])
            elif data['close'].iloc[i] < data['close'].iloc[i - 1]:
                obv.append(obv[-1] - data['volume'].iloc[i])
            else:
                obv.append(obv[-1])

        return pd.Series(obv, index=data.index)

    @staticmethod
    def calculate_volume_sma(data: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate Volume Simple Moving Average

        Args:
            data: DataFrame with OHLCV data
            period: SMA period for volume

        Returns:
            Series with volume SMA values
        """
        return data['volume'].rolling(window=period).mean()

    @staticmethod
    def add_all_indicators(data: pd.DataFrame, ma_periods: list = [10, 30, 60]) -> pd.DataFrame:
        """
        Add all technical indicators to the dataframe

        Args:
            data: DataFrame with OHLCV data
            ma_periods: List of MA periods to calculate

        Returns:
            DataFrame with all indicators added
        """
        df = data.copy()

        # Add Moving Averages
        for period in ma_periods:
            df[f'ma_{period}'] = TechnicalIndicators.calculate_ma(df, period)

        # Add OBV
        df['obv'] = TechnicalIndicators.calculate_obv(df)

        # Add OBV MA for trend detection
        df['obv_ma'] = df['obv'].rolling(window=20).mean()

        # Add Volume indicators
        df['volume_sma'] = TechnicalIndicators.calculate_volume_sma(df, 20)
        df['volume_ratio'] = df['volume'] / df['volume_sma']

        return df
