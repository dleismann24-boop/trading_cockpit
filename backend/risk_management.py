"""
Advanced Risk Management System
Implementiert Drawdown-Limits, Volatilitäts-basiertes Position-Sizing,
Sektor-Limits und Emergency Stop-Loss
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class AdvancedRiskManager:
    """Fortgeschrittenes Risk Management für Trading"""
    
    def __init__(self, 
                 max_drawdown_pct: float = 15.0,
                 daily_loss_limit_pct: float = 5.0,
                 max_sector_exposure_pct: float = 30.0,
                 max_position_size_pct: float = 10.0):
        """
        Args:
            max_drawdown_pct: Max erlaubter Drawdown in % (z.B. 15%)
            daily_loss_limit_pct: Max Verlust pro Tag in % (z.B. 5%)
            max_sector_exposure_pct: Max % in einem Sektor (z.B. 30%)
            max_position_size_pct: Max % pro Position (z.B. 10%)
        """
        self.max_drawdown_pct = max_drawdown_pct
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_sector_exposure_pct = max_sector_exposure_pct
        self.max_position_size_pct = max_position_size_pct
        
        # Tracking
        self.peak_portfolio_value = 0.0
        self.daily_start_value = 0.0
        self.daily_start_date = None
        
        # Sector mapping (vereinfacht)
        self.sector_map = {
            'AAPL': 'Technology',
            'MSFT': 'Technology',
            'GOOGL': 'Technology',
            'NVDA': 'Technology',
            'TSLA': 'Automotive',
            'META': 'Technology',
            'AMZN': 'Technology',
            'JPM': 'Finance',
            'BAC': 'Finance',
            'V': 'Finance'
        }
    
    def calculate_current_drawdown(self, current_value: float, peak_value: float) -> float:
        """
        Berechnet aktuellen Drawdown in %
        
        Returns:
            Drawdown in % (z.B. 10.5 für 10.5% Verlust vom Peak)
        """
        if peak_value == 0:
            return 0.0
        
        drawdown = ((peak_value - current_value) / peak_value) * 100
        return max(0, drawdown)
    
    def check_drawdown_limit(self, current_value: float) -> Tuple[bool, str]:
        """
        Prüft ob Drawdown-Limit überschritten
        
        Returns:
            (is_ok: bool, message: str)
        """
        # Update peak
        if current_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_value
        
        # Calculate drawdown
        drawdown = self.calculate_current_drawdown(current_value, self.peak_portfolio_value)
        
        if drawdown > self.max_drawdown_pct:
            return False, f"⛔ Max Drawdown überschritten! Aktuell: {drawdown:.1f}% (Limit: {self.max_drawdown_pct}%)"
        
        if drawdown > self.max_drawdown_pct * 0.8:  # Warning bei 80% vom Limit
            return True, f"⚠️ Drawdown-Warnung: {drawdown:.1f}% (Limit: {self.max_drawdown_pct}%)"
        
        return True, f"✅ Drawdown OK: {drawdown:.1f}%"
    
    def check_daily_loss_limit(self, current_value: float) -> Tuple[bool, str]:
        """
        Prüft ob Daily Loss Limit überschritten
        
        Returns:
            (is_ok: bool, message: str)
        """
        # Reset bei neuem Tag
        today = datetime.now().date()
        if self.daily_start_date != today:
            self.daily_start_value = current_value
            self.daily_start_date = today
        
        # Calculate daily loss
        if self.daily_start_value == 0:
            return True, "✅ Daily Loss: Initialisierung"
        
        daily_change_pct = ((current_value - self.daily_start_value) / self.daily_start_value) * 100
        
        if daily_change_pct < -self.daily_loss_limit_pct:
            return False, f"⛔ Daily Loss Limit überschritten! {daily_change_pct:.1f}% (Limit: -{self.daily_loss_limit_pct}%)"
        
        if daily_change_pct < -self.daily_loss_limit_pct * 0.8:
            return True, f"⚠️ Daily Loss Warnung: {daily_change_pct:.1f}%"
        
        return True, f"✅ Daily P&L: {daily_change_pct:+.1f}%"
    
    def calculate_volatility_based_position_size(
        self,
        symbol: str,
        price_history: List[float],
        portfolio_value: float,
        risk_per_trade_pct: float = 2.0
    ) -> int:
        """
        Berechnet Position Size basierend auf Volatilität (ATR)
        
        Args:
            symbol: Ticker Symbol
            price_history: Liste der letzten Preise
            portfolio_value: Aktueller Portfolio-Wert
            risk_per_trade_pct: Risiko pro Trade in % (Default 2%)
        
        Returns:
            Anzahl Aktien (quantity)
        """
        if len(price_history) < 14:
            # Fallback: Standard Position Size
            current_price = price_history[-1]
            quantity = int((portfolio_value * (self.max_position_size_pct / 100)) / current_price)
            return max(1, quantity)
        
        # Calculate ATR (Average True Range) als Volatilitäts-Indikator
        atr = self._calculate_atr(price_history)
        current_price = price_history[-1]
        
        # Position Size basierend auf Volatilität
        # Risiko pro Trade = risk_per_trade_pct% des Portfolios
        risk_amount = portfolio_value * (risk_per_trade_pct / 100)
        
        # Quantity = Risk Amount / (ATR * Multiplikator)
        # ATR * 2 = Stop-Loss Distanz (2x ATR)
        stop_distance = atr * 2
        
        if stop_distance > 0:
            quantity = int(risk_amount / stop_distance)
        else:
            quantity = int((portfolio_value * (self.max_position_size_pct / 100)) / current_price)
        
        # Max limit enforcement
        max_quantity = int((portfolio_value * (self.max_position_size_pct / 100)) / current_price)
        quantity = min(quantity, max_quantity)
        
        logger.info(f"{symbol}: Volatility-based sizing - ATR: ${atr:.2f}, Quantity: {quantity}")
        
        return max(1, quantity)
    
    def _calculate_atr(self, prices: List[float], period: int = 14) -> float:
        """
        Berechnet Average True Range (ATR)
        
        Args:
            prices: Liste der Closing Prices
            period: Periode für ATR (Default 14)
        
        Returns:
            ATR Wert
        """
        if len(prices) < period + 1:
            # Fallback: Standard Deviation
            return np.std(prices) if len(prices) > 1 else prices[-1] * 0.02
        
        # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
        # Vereinfacht: Wir nutzen nur Closing Prices
        # TR ≈ abs(close[i] - close[i-1])
        
        true_ranges = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
        
        # ATR = Average der letzten N True Ranges
        atr = np.mean(true_ranges[-period:])
        
        return atr
    
    def check_sector_limits(
        self,
        symbol: str,
        proposed_position_value: float,
        current_positions: List[Dict],
        portfolio_value: float
    ) -> Tuple[bool, str]:
        """
        Prüft ob Sektor-Limits eingehalten werden
        
        Args:
            symbol: Neues Symbol
            proposed_position_value: Wert der neuen Position
            current_positions: Liste aktueller Positionen
            portfolio_value: Gesamtwert Portfolio
        
        Returns:
            (is_ok: bool, message: str)
        """
        # Get sector für neues Symbol
        new_sector = self.sector_map.get(symbol, 'Unknown')
        
        # Calculate current sector exposure
        sector_exposure = {}
        
        for pos in current_positions:
            pos_symbol = pos.get('symbol')
            pos_value = pos.get('market_value', 0)
            sector = self.sector_map.get(pos_symbol, 'Unknown')
            
            sector_exposure[sector] = sector_exposure.get(sector, 0) + pos_value
        
        # Add proposed position
        sector_exposure[new_sector] = sector_exposure.get(new_sector, 0) + proposed_position_value
        
        # Check limit
        new_sector_pct = (sector_exposure[new_sector] / portfolio_value) * 100
        
        if new_sector_pct > self.max_sector_exposure_pct:
            return False, f"⛔ Sektor-Limit überschritten! {new_sector}: {new_sector_pct:.1f}% (Limit: {self.max_sector_exposure_pct}%)"
        
        if new_sector_pct > self.max_sector_exposure_pct * 0.9:
            return True, f"⚠️ Sektor-Warnung: {new_sector} bei {new_sector_pct:.1f}%"
        
        return True, f"✅ Sektor OK: {new_sector} bei {new_sector_pct:.1f}%"
    
    def calculate_risk_score(
        self,
        symbol: str,
        confidence: float,
        sentiment_score: float,
        technical_score: float,
        volatility: float
    ) -> Dict:
        """
        Berechnet Risk Score für einen Trade
        
        Args:
            symbol: Ticker
            confidence: Agent Confidence (0-1)
            sentiment_score: Sentiment Score (-1 bis +1)
            technical_score: Technischer Score (-1 bis +1)
            volatility: Volatilität (ATR oder Std Dev)
        
        Returns:
            {
                'risk_score': float (0-100),
                'risk_level': str (LOW/MEDIUM/HIGH),
                'factors': Dict,
                'recommendation': str
            }
        """
        # Score-Komponenten (0-25 Punkte jeweils)
        
        # 1. Confidence Score (höher = weniger Risiko)
        confidence_score = confidence * 25
        
        # 2. Sentiment Score (positiver = weniger Risiko)
        sentiment_score_normalized = ((sentiment_score + 1) / 2) * 25  # -1..1 → 0..25
        
        # 3. Technical Score (positiver = weniger Risiko)
        technical_score_normalized = ((technical_score + 1) / 2) * 25
        
        # 4. Volatility Score (niedriger = weniger Risiko)
        # Annahme: Volatilität > 5% ist hoch, < 1% ist niedrig
        vol_pct = volatility * 100
        if vol_pct < 1:
            volatility_score = 25
        elif vol_pct < 3:
            volatility_score = 15
        elif vol_pct < 5:
            volatility_score = 10
        else:
            volatility_score = 5
        
        # Gesamt-Score (0-100)
        total_score = confidence_score + sentiment_score_normalized + technical_score_normalized + volatility_score
        
        # Risk Level
        if total_score >= 75:
            risk_level = 'LOW'
            recommendation = '✅ Gutes Risk/Reward-Verhältnis'
        elif total_score >= 50:
            risk_level = 'MEDIUM'
            recommendation = '⚠️ Moderates Risiko - Vorsicht'
        else:
            risk_level = 'HIGH'
            recommendation = '⛔ Hohes Risiko - Nicht empfohlen'
        
        return {
            'risk_score': round(total_score, 1),
            'risk_level': risk_level,
            'factors': {
                'confidence': round(confidence_score, 1),
                'sentiment': round(sentiment_score_normalized, 1),
                'technical': round(technical_score_normalized, 1),
                'volatility': round(volatility_score, 1)
            },
            'recommendation': recommendation
        }
    
    def should_emergency_stop(
        self,
        current_value: float,
        open_positions: List[Dict]
    ) -> Tuple[bool, str, List[str]]:
        """
        Prüft ob Emergency Stop-Loss ausgelöst werden sollte
        
        Returns:
            (should_stop: bool, reason: str, symbols_to_close: List[str])
        """
        symbols_to_close = []
        reasons = []
        
        # Check 1: Max Drawdown
        is_ok, msg = self.check_drawdown_limit(current_value)
        if not is_ok:
            reasons.append(msg)
            symbols_to_close = [pos['symbol'] for pos in open_positions]
            return True, "Emergency Stop: " + msg, symbols_to_close
        
        # Check 2: Daily Loss
        is_ok, msg = self.check_daily_loss_limit(current_value)
        if not is_ok:
            reasons.append(msg)
            symbols_to_close = [pos['symbol'] for pos in open_positions]
            return True, "Emergency Stop: " + msg, symbols_to_close
        
        # Check 3: Individual Position Losses (> 15%)
        for pos in open_positions:
            unrealized_plpc = pos.get('unrealized_plpc', 0)
            if unrealized_plpc < -15.0:  # Mehr als 15% Verlust
                symbols_to_close.append(pos['symbol'])
                reasons.append(f"{pos['symbol']}: {unrealized_plpc:.1f}% Verlust")
        
        if symbols_to_close:
            return True, f"Emergency Stop: Große Einzelverluste - {', '.join(reasons)}", symbols_to_close
        
        return False, "✅ Alle Risk Checks OK", []


# Global Risk Manager Instance
_risk_manager = None

def get_risk_manager() -> AdvancedRiskManager:
    """Get or create global risk manager"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = AdvancedRiskManager()
    return _risk_manager
