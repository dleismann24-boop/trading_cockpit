"""
Trading Strategies Module
Technische Indikatoren und Analysen für autonome Agenten
"""
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Berechnet technische Indikatoren"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """
        Relative Strength Index
        Returns: 0-100 (>70 = overbought, <30 = oversold)
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """
        Moving Average Convergence Divergence
        Returns: {'macd': float, 'signal': float, 'histogram': float}
        """
        if len(prices) < slow:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        prices_arr = np.array(prices)
        
        # EMA berechnen
        ema_fast = prices_arr[-fast:].mean()  # Vereinfacht
        ema_slow = prices_arr[-slow:].mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line * 0.8  # Vereinfacht
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_momentum(prices: List[float], period: int = 10) -> float:
        """
        Momentum Indicator
        Returns: % change over period
        """
        if len(prices) < period:
            return 0.0
        
        return ((prices[-1] - prices[-period]) / prices[-period]) * 100


class TradingSignal:
    """Handelssignal mit Begründung"""
    def __init__(self, action: str, confidence: float, reason: str, indicators: Dict):
        self.action = action  # 'BUY', 'SELL', 'HOLD'
        self.confidence = confidence  # 0-1
        self.reason = reason
        self.indicators = indicators
        self.timestamp = datetime.utcnow()


class StrategyAnalyzer:
    """Kombiniert verschiedene Strategien zu Handelssignalen"""
    
    def __init__(self):
        self.ti = TechnicalIndicators()
    
    def analyze_momentum_strategy(self, prices: List[float]) -> TradingSignal:
        """Momentum-basierte Strategie"""
        if len(prices) < 20:
            return TradingSignal('HOLD', 0.5, 'Nicht genug Daten', {})
        
        rsi = self.ti.calculate_rsi(prices)
        momentum = self.ti.calculate_momentum(prices)
        macd = self.ti.calculate_macd(prices)
        
        indicators = {
            'rsi': rsi,
            'momentum': momentum,
            'macd': macd['histogram']
        }
        
        # Kaufsignal
        if rsi < 35 and momentum > 0 and macd['histogram'] > 0:
            return TradingSignal(
                'BUY', 
                0.8,
                f'RSI überverkauft ({rsi:.1f}), positives Momentum ({momentum:.1f}%), MACD bullish',
                indicators
            )
        
        # Verkaufssignal
        if rsi > 65 and momentum < 0 and macd['histogram'] < 0:
            return TradingSignal(
                'SELL',
                0.8,
                f'RSI überkauft ({rsi:.1f}), negatives Momentum ({momentum:.1f}%), MACD bearish',
                indicators
            )
        
        # Halten
        return TradingSignal(
            'HOLD',
            0.6,
            f'Keine klaren Signale (RSI: {rsi:.1f}, Momentum: {momentum:.1f}%)',
            indicators
        )
    
    def analyze_value_strategy(self, price: float, avg_price: float) -> TradingSignal:
        """Value-basierte Strategie (vereinfacht)"""
        deviation = ((price - avg_price) / avg_price) * 100
        
        indicators = {
            'current_price': price,
            'average_price': avg_price,
            'deviation': deviation
        }
        
        # Unterbewertet
        if deviation < -5:
            return TradingSignal(
                'BUY',
                0.7,
                f'Preis {abs(deviation):.1f}% unter Durchschnitt - potenziell unterbewertet',
                indicators
            )
        
        # Überbewertet
        if deviation > 5:
            return TradingSignal(
                'SELL',
                0.7,
                f'Preis {deviation:.1f}% über Durchschnitt - potenziell überbewertet',
                indicators
            )
        
        return TradingSignal('HOLD', 0.5, 'Preis im normalen Bereich', indicators)
    
    def get_market_sentiment(self, symbol: str) -> str:
        """
        Markt-Sentiment (Mock - in Produktion: News-API nutzen)
        """
        # In Produktion: News-API, Social Media, etc.
        sentiments = ['bullish', 'neutral', 'bearish']
        # Vereinfacht: Zufällig für Demo
        import random
        return random.choice(sentiments)


class RiskManager:
    """Risikomanagement für Trading-Agenten"""
    
    def __init__(self, total_budget: float, max_position_size_pct: float = 0.15):
        self.total_budget = total_budget
        self.max_position_size_pct = max_position_size_pct
        self.max_position_size = total_budget * max_position_size_pct
        self.max_drawdown_pct = 0.20  # Max 20% Verlust
    
    def validate_trade(
        self, 
        action: str, 
        quantity: int, 
        price: float, 
        current_cash: float,
        current_portfolio_value: float
    ) -> Dict:
        """
        Validiert einen Trade gegen Risiko-Regeln
        Returns: {'approved': bool, 'reason': str, 'adjusted_quantity': int}
        """
        trade_value = quantity * price
        
        # Check 1: Genug Cash?
        if action == 'BUY' and trade_value > current_cash:
            max_affordable = int(current_cash / price)
            return {
                'approved': False,
                'reason': f'Nicht genug Cash (${current_cash:.2f})',
                'adjusted_quantity': max_affordable
            }
        
        # Check 2: Position zu groß?
        if trade_value > self.max_position_size:
            max_quantity = int(self.max_position_size / price)
            return {
                'approved': False,
                'reason': f'Position zu groß (max ${self.max_position_size:.2f})',
                'adjusted_quantity': max_quantity
            }
        
        # Check 3: Drawdown-Limit
        if current_portfolio_value < self.total_budget * (1 - self.max_drawdown_pct):
            return {
                'approved': False,
                'reason': f'Drawdown-Limit erreicht ({self.max_drawdown_pct*100}%)',
                'adjusted_quantity': 0
            }
        
        return {
            'approved': True,
            'reason': 'Trade approved',
            'adjusted_quantity': quantity
        }
    
    def calculate_position_size(
        self, 
        confidence: float, 
        current_cash: float, 
        price: float
    ) -> int:
        """
        Berechnet optimale Positionsgröße basierend auf Confidence
        Higher confidence = larger position (up to max)
        """
        # Base position: 5% of budget
        base_size = self.total_budget * 0.05
        
        # Scale with confidence (0.5-1.0)
        scaled_size = base_size * (confidence / 0.5)
        
        # Cap at max position size
        final_size = min(scaled_size, self.max_position_size)
        
        # Cap at available cash
        final_size = min(final_size, current_cash * 0.9)  # Keep 10% buffer
        
        # Convert to quantity
        quantity = int(final_size / price)
        
        return max(1, quantity)  # At least 1 share
