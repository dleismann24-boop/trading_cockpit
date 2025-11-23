"""
Autonomous Trading Agents
Jordan, Bohlen, Frodo - jeder mit eigener Persönlichkeit und Strategie
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os

from trading_strategies import StrategyAnalyzer, RiskManager, TradingSignal

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY')


class AutonomousAgent:
    """Base class for autonomous trading agents"""
    
    def __init__(
        self,
        name: str,
        personality: str,
        llm_provider: str,
        llm_model: str,
        budget: float,
        trading_client: TradingClient,
        data_client: StockHistoricalDataClient
    ):
        self.name = name
        self.personality = personality
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.budget = budget
        self.trading_client = trading_client
        self.data_client = data_client
        
        # Strategy & Risk
        self.strategy_analyzer = StrategyAnalyzer()
        self.risk_manager = RiskManager(budget)
        
        # Tracking
        self.trades_executed = []
        self.total_trades = 0
        self.successful_trades = 0
        self.total_pnl = 0.0
        
        # LLM Chat
        self.llm_chat = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM for decision-making"""
        if not EMERGENT_LLM_KEY:
            logger.warning(f"{self.name}: No LLM key, using fallback logic")
            return
        
        try:
            session_id = f"agent_{self.name}_{datetime.now().strftime('%Y%m%d')}"
            system_message = self._get_system_message()
            
            self.llm_chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=session_id,
                system_message=system_message
            ).with_model(self.llm_provider, self.llm_model)
            
            logger.info(f"{self.name}: LLM initialized ({self.llm_model})")
        except Exception as e:
            logger.error(f"{self.name}: LLM init failed: {e}")
    
    def _get_system_message(self) -> str:
        """Get personality-specific system message"""
        raise NotImplementedError("Subclass must implement")
    
    async def make_trading_decision(self, symbol: str, sentiment_data: Dict = None) -> Optional[Dict]:
        """
        Main decision-making process
        1. Get market data
        2. Technical analysis
        3. LLM consultation
        4. Risk validation
        5. Execute or reject
        """
        try:
            # 1. Get historical data
            prices = await self._get_price_history(symbol)
            if not prices:
                logger.warning(f"{self.name}: No price data for {symbol}")
                return None
            
            current_price = prices[-1]
            
            # 2. Technical analysis
            technical_signal = self.strategy_analyzer.analyze_momentum_strategy(prices)
            
            # 3. Get current account state
            account = self.trading_client.get_account()
            current_cash = float(account.cash)
            portfolio_value = float(account.portfolio_value)
            
            # 4. LLM decision (if available)
            final_decision = await self._consult_llm(
                symbol, 
                current_price, 
                technical_signal,
                current_cash,
                portfolio_value,
                sentiment_data
            )
            
            if final_decision['action'] == 'HOLD':
                logger.info(f"{self.name}: Decided to HOLD {symbol}")
                return None
            
            # 5. Calculate position size
            quantity = self.risk_manager.calculate_position_size(
                confidence=final_decision['confidence'],
                current_cash=current_cash,
                price=current_price
            )
            
            # 6. Risk validation
            validation = self.risk_manager.validate_trade(
                action=final_decision['action'],
                quantity=quantity,
                price=current_price,
                current_cash=current_cash,
                current_portfolio_value=portfolio_value
            )
            
            if not validation['approved']:
                logger.warning(f"{self.name}: Trade rejected - {validation['reason']}")
                return None
            
            # 7. Execute trade
            order = await self._execute_trade(
                symbol=symbol,
                action=final_decision['action'],
                quantity=validation['adjusted_quantity'],
                price=current_price,
                reason=final_decision['reason']
            )
            
            return order
            
        except Exception as e:
            logger.error(f"{self.name}: Decision error for {symbol}: {e}")
            return None
    
    async def _get_price_history(self, symbol: str, days: int = 30) -> List[float]:
        """Get historical prices for analysis"""
        try:
            # Mock für jetzt - in Produktion: echte Alpaca-Daten
            # Simuliere Preisbewegung
            import random
            base_price = {'AAPL': 178, 'TSLA': 250, 'NVDA': 492, 'MSFT': 415}.get(symbol, 100)
            prices = []
            price = base_price
            
            for _ in range(30):
                change = random.uniform(-0.02, 0.02)
                price = price * (1 + change)
                prices.append(price)
            
            return prices
        except Exception as e:
            logger.error(f"{self.name}: Price history error: {e}")
            return []
    
    async def _consult_llm(
        self, 
        symbol: str, 
        price: float, 
        signal: TradingSignal,
        cash: float,
        portfolio_value: float,
        sentiment_data: Dict = None
    ) -> Dict:
        """Consult LLM for final decision"""
        
        # Fallback: Use technical signal if no LLM
        if not self.llm_chat:
            return {
                'action': signal.action,
                'confidence': signal.confidence,
                'reason': signal.reason
            }
        
        try:
            # Build sentiment section if available
            sentiment_section = ""
            if sentiment_data:
                sentiment_section = f"""
Market Sentiment:
- Overall Score: {sentiment_data.get('overall_score', 0):.2f} ({"Bullish" if sentiment_data.get('overall_score', 0) > 0 else "Bearish"})
- Twitter Sentiment: {sentiment_data.get('twitter_sentiment', 0):.2f}
- News Sentiment: {sentiment_data.get('news_sentiment', 0):.2f}
- Social Volume: {sentiment_data.get('social_volume', 0)} Mentions
- Summary: {sentiment_data.get('summary', 'N/A')}
- Signals: {', '.join(sentiment_data.get('signals', []))}
"""
            
            prompt = f"""Aktuelle Trading-Situation:

Symbol: {symbol}
Aktueller Preis: ${price:.2f}
Verfügbares Cash: ${cash:.2f}
Portfolio-Wert: ${portfolio_value:.2f}

Technische Analyse:
- Signal: {signal.action}
- Confidence: {signal.confidence}
- Begründung: {signal.reason}
- RSI: {signal.indicators.get('rsi', 'N/A')}
- Momentum: {signal.indicators.get('momentum', 'N/A')}
{sentiment_section}
Entscheide basierend auf deiner Persönlichkeit ({self.personality}):
Berücksichtige SOWOHL technische Indikatoren ALS AUCH Sentiment-Daten.

Antworte NUR mit: BUY|SELL|HOLD|<confidence 0-1>|<kurze Begründung>

Beispiel: BUY|0.75|Starkes Momentum + positives Sentiment"""

            user_message = UserMessage(text=prompt)
            response = await self.llm_chat.send_message(user_message)
            
            # Parse response
            parts = str(response).split('|')
            if len(parts) >= 3:
                return {
                    'action': parts[0].strip().upper(),
                    'confidence': float(parts[1].strip()),
                    'reason': parts[2].strip()
                }
            
        except Exception as e:
            logger.error(f"{self.name}: LLM consultation error: {e}")
        
        # Fallback to technical signal
        return {
            'action': signal.action,
            'confidence': signal.confidence,
            'reason': f"{signal.reason} (LLM fallback)"
        }
    
    async def _execute_trade(
        self, 
        symbol: str, 
        action: str, 
        quantity: int, 
        price: float,
        reason: str
    ) -> Dict:
        """Execute trade via Alpaca"""
        try:
            side = OrderSide.BUY if action == 'BUY' else OrderSide.SELL
            
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.trading_client.submit_order(order_data)
            
            # Log trade
            trade_log = {
                'agent': self.name,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'reason': reason,
                'order_id': str(order.id),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.trades_executed.append(trade_log)
            self.total_trades += 1
            
            logger.info(f"{self.name}: ✅ Executed {action} {quantity} {symbol} @ ${price:.2f}")
            logger.info(f"{self.name}: Reason: {reason}")
            
            return trade_log
            
        except Exception as e:
            logger.error(f"{self.name}: Trade execution error: {e}")
            return {}
    
    def get_performance_stats(self) -> Dict:
        """Get agent performance statistics"""
        return {
            'agent': self.name,
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'success_rate': self.successful_trades / max(self.total_trades, 1),
            'total_pnl': self.total_pnl,
            'recent_trades': self.trades_executed[-5:]
        }


class JordanAgent(AutonomousAgent):
    """Jordan - Aggressiv, gewinnorientiert (GPT-4)"""
    
    def __init__(self, budget, trading_client, data_client):
        super().__init__(
            name="Jordan",
            personality="aggressive_winner",
            llm_provider="openai",
            llm_model="gpt-4",
            budget=budget,
            trading_client=trading_client,
            data_client=data_client
        )
    
    def _get_system_message(self) -> str:
        return f"""Du bist Jordan - ein aggressiver Trading-Agent mit Championship-Mentalität.

Dein Budget: ${self.budget:.2f}

Deine Eigenschaften:
- AGGRESSIV: Du gehst Risiken ein für höhere Renditen
- GEWINNORIENTIERT: Du willst maximalen Profit
- MOMENTUM-FOKUS: Du reitest Trends
- SCHNELL: Du handelst entschlossen

Du bevorzugst: High-Growth-Stocks, Momentum-Plays, größere Positionen

Antworte IMMER im Format: ACTION|CONFIDENCE|REASON
Beispiel: BUY|0.85|Starkes Momentum, will gewinnen!"""


class BohlenAgent(AutonomousAgent):
    """Bohlen - Realistisch, kapitalschützend (Claude)"""
    
    def __init__(self, budget, trading_client, data_client):
        super().__init__(
            name="Bohlen",
            personality="realistic_protector",
            llm_provider="anthropic",
            llm_model="claude-3-7-sonnet-20250219",
            budget=budget,
            trading_client=trading_client,
            data_client=data_client
        )
    
    def _get_system_message(self) -> str:
        return f"""Du bist Bohlen - ein realistischer Trading-Agent, brutal ehrlich.

Dein Budget: ${self.budget:.2f}

Deine Eigenschaften:
- REALISTISCH: Keine Illusionen, klare Sicht
- KAPITAL-SCHÜTZEND: Verluste vermeiden ist Priorität
- DIREKT: Sagst wenn etwas Mist ist
- FUNDAMENTAL: Schaust auf echte Werte

Du bevorzugst: Solide Unternehmen, defensive Positionen, kleinere Risiken

Antworte IMMER im Format: ACTION|CONFIDENCE|REASON
Beispiel: SELL|0.70|Überbewertet, zu riskant jetzt"""


class FrodoAgent(AutonomousAgent):
    """Frodo - Langfristig, geduldig (Gemini)"""
    
    def __init__(self, budget, trading_client, data_client):
        super().__init__(
            name="Frodo",
            personality="patient_longterm",
            llm_provider="gemini",
            llm_model="gemini-2.5-flash",
            budget=budget,
            trading_client=trading_client,
            data_client=data_client
        )
    
    def _get_system_message(self) -> str:
        return f"""Du bist Frodo - ein geduldiger Trading-Agent mit langfristiger Vision.

Dein Budget: ${self.budget:.2f}

Deine Eigenschaften:
- GEDULDIG: Du wartest auf die richtigen Gelegenheiten
- LANGFRISTIG: Du denkst in Quartalen, nicht Minuten
- WEISE: Du lernst aus Fehlern
- RISIKO-BEWUSST: Du managst Downside aktiv

Du bevorzugst: Quality-Stocks, diversifizierte Positionen, nachhaltiges Wachstum

Antworte IMMER im Format: ACTION|CONFIDENCE|REASON
Beispiel: HOLD|0.60|Warten auf besseren Einstieg, keine Eile"""
