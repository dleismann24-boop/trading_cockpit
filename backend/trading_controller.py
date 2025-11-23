"""
Trading Controller
Orchestriert alle 3 autonomen Agenten
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import os

from autonomous_agents import JordanAgent, BohlenAgent, FrodoAgent
from sentiment_analyzer import get_sentiment_analyzer

logger = logging.getLogger(__name__)


class TradingMode(str, Enum):
    SOLO = "solo"  # Jeder Agent handelt unabhängig
    CONSENSUS = "consensus"  # Trade nur bei Mehrheitsentscheidung
    GUIDED = "guided"  # Berücksichtigt User-Vorgaben


class TradingController:
    """Hauptsteuerung für autonome Trading-Agenten"""
    
    def __init__(self, trading_client, data_client, total_budget: float = 100000):
        self.trading_client = trading_client
        self.data_client = data_client
        self.total_budget = total_budget
        
        # Budget aufteilen
        budget_per_agent = total_budget / 3
        
        # Agenten initialisieren
        self.agents = {
            'jordan': JordanAgent(budget_per_agent, trading_client, data_client),
            'bohlen': BohlenAgent(budget_per_agent, trading_client, data_client),
            'frodo': FrodoAgent(budget_per_agent, trading_client, data_client)
        }
        
        # Status
        self.mode = TradingMode.CONSENSUS  # Gemeinsames Portfolio mit Abstimmung
        self.autopilot_enabled = False
        self.watchlist = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']
        self.user_constraints = []  # z.B. ["avoid_tech", "max_risk_low"]
        
        # Tracking
        self.trading_sessions = []
        self.last_run = None
        self.next_run = None
    
    async def run_trading_cycle(self, dry_run: bool = False, max_trade_percentage: float = 10.0) -> Dict:
        """
        Führt einen Trading-Zyklus aus mit GEMEINSAMER Portfolio-Verwaltung
        Alle Agenten analysieren, diskutieren und stimmen ab
        
        Args:
            dry_run: Wenn True, werden keine echten Trades ausgeführt (Simulation)
        """
        logger.info("=" * 60)
        logger.info(f"🤖 Trading Cycle gestartet - Modus: GEMEINSAMES PORTFOLIO")
        if dry_run:
            logger.info("🧪 DRY-RUN MODUS - Nur Simulation, keine echten Trades")
        logger.info("=" * 60)
        
        cycle_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'mode': 'shared_portfolio',
            'dry_run': dry_run,
            'agents': {},
            'trades_executed': 0,
            'trades_proposed': 0,
            'total_cost': 0.0,
            'consensus_decisions': []
        }
        
        # Durch Watchlist gehen - GEMEINSAME Diskussion pro Symbol
        for symbol in self.watchlist:
            try:
                logger.info(f"\n{'='*50}")
                logger.info(f"💬 Diskussion über {symbol}")
                logger.info(f"{'='*50}")
                
                # User-Constraints prüfen
                if self._should_skip_symbol(symbol):
                    logger.info(f"⏭️  Überspringe {symbol} (User-Constraint)")
                    continue
                
                # Alle Agenten analysieren und geben ihre Meinung ab
                proposals = []
                for agent_name, agent in self.agents.items():
                    logger.info(f"\n🤔 {agent.name} analysiert {symbol}...")
                    
                    # Get agent's analysis (ohne Trade-Ausführung)
                    prices = await agent._get_price_history(symbol)
                    if not prices:
                        continue
                    
                    current_price = prices[-1]
                    technical_signal = agent.strategy_analyzer.analyze_momentum_strategy(prices)
                    
                    account = self.trading_client.get_account()
                    current_cash = float(account.cash)
                    portfolio_value = float(account.portfolio_value)
                    
                    # LLM consultation
                    decision = await agent._consult_llm(
                        symbol, current_price, technical_signal,
                        current_cash, portfolio_value
                    )
                    
                    proposals.append({
                        'agent': agent.name,
                        'action': decision['action'],
                        'confidence': decision['confidence'],
                        'reason': decision['reason'],
                        'price': current_price
                    })
                    
                    logger.info(f"   → {agent.name}: {decision['action']} (Confidence: {decision['confidence']:.2f})")
                    logger.info(f"      Begründung: {decision['reason']}")
                
                cycle_results['trades_proposed'] += len(proposals)
                
                # Konsens-Entscheidung: Mehrheit (2/3) muss zustimmen
                buy_votes = sum(1 for p in proposals if p['action'] == 'BUY')
                sell_votes = sum(1 for p in proposals if p['action'] == 'SELL')
                hold_votes = sum(1 for p in proposals if p['action'] == 'HOLD')
                
                logger.info(f"\n📊 Abstimmung: BUY={buy_votes}, SELL={sell_votes}, HOLD={hold_votes}")
                
                consensus = None
                if buy_votes >= 2:
                    consensus = 'BUY'
                    avg_confidence = sum(p['confidence'] for p in proposals if p['action'] == 'BUY') / buy_votes
                elif sell_votes >= 2:
                    consensus = 'SELL'
                    avg_confidence = sum(p['confidence'] for p in proposals if p['action'] == 'SELL') / sell_votes
                else:
                    logger.info(f"❌ Kein Konsens erreicht - HOLD")
                    continue
                
                logger.info(f"✅ Konsens erreicht: {consensus} (Avg. Confidence: {avg_confidence:.2f})")
                
                # Trade ausführen (nur wenn nicht dry-run)
                # Positionsgröße berechnen basierend auf konfiguriertem Limit
                trade_percentage = max_trade_percentage / 100.0  # Convert from percentage
                max_trade_value = portfolio_value * trade_percentage
                quantity = int(max_trade_value / current_price)
                
                logger.info(f"💰 Trade-Budget: ${max_trade_value:.2f} ({max_trade_percentage}% von ${portfolio_value:.2f})")
                
                if not dry_run:
                    if quantity > 0:
                        # Führe Trade aus
                        from alpaca.trading.requests import MarketOrderRequest
                        from alpaca.trading.enums import OrderSide, TimeInForce
                        
                        side = OrderSide.BUY if consensus == 'BUY' else OrderSide.SELL
                        order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=quantity,
                            side=side,
                            time_in_force=TimeInForce.DAY
                        )
                        
                        order = self.trading_client.submit_order(order_data)
                        logger.info(f"🚀 Trade ausgeführt: {consensus} {quantity} {symbol} @ ${current_price:.2f}")
                        
                        cycle_results['trades_executed'] += 1
                else:
                    logger.info(f"🧪 DRY-RUN: Würde {consensus} {quantity} {symbol} @ ${current_price:.2f} ausführen")
                
                cycle_results['consensus_decisions'].append({
                    'symbol': symbol,
                    'consensus': consensus,
                    'confidence': avg_confidence,
                    'proposals': proposals,
                    'executed': not dry_run
                })
                
            except Exception as e:
                logger.error(f"Error bei {symbol}: {e}")
        
        # Session speichern
        self.trading_sessions.append(cycle_results)
        self.last_run = datetime.utcnow()
        
        logger.info("=" * 60)
        logger.info(f"✅ Trading Cycle abgeschlossen")
        logger.info(f"   Vorschläge: {cycle_results['trades_proposed']}")
        logger.info(f"   Ausgeführt: {cycle_results['trades_executed']}")
        logger.info("=" * 60)
        
        return cycle_results
    
    async def run_consensus_mode(self, symbol: str) -> Optional[Dict]:
        """
        Konsens-Modus: Alle Agenten stimmen ab
        Trade nur wenn Mehrheit (2/3) zustimmt
        """
        logger.info(f"\n🗳️  Konsens-Abstimmung für {symbol}")
        
        votes = []
        
        for agent_name, agent in self.agents.items():
            decision = await agent.make_trading_decision(symbol)
            if decision:
                votes.append({
                    'agent': agent_name,
                    'action': decision['action'],
                    'confidence': decision.get('confidence', 0.5),
                    'reason': decision.get('reason', '')
                })
        
        # Mehrheitsentscheidung
        buy_votes = sum(1 for v in votes if v['action'] == 'BUY')
        sell_votes = sum(1 for v in votes if v['action'] == 'SELL')
        
        if buy_votes >= 2:
            logger.info(f"✅ Konsens: KAUFEN ({buy_votes}/3 Stimmen)")
            # Führe Trade mit gemittelter Confidence aus
            avg_confidence = sum(v['confidence'] for v in votes if v['action'] == 'BUY') / buy_votes
            return {
                'action': 'BUY',
                'votes': votes,
                'consensus': True,
                'confidence': avg_confidence
            }
        elif sell_votes >= 2:
            logger.info(f"✅ Konsens: VERKAUFEN ({sell_votes}/3 Stimmen)")
            avg_confidence = sum(v['confidence'] for v in votes if v['action'] == 'SELL') / sell_votes
            return {
                'action': 'SELL',
                'votes': votes,
                'consensus': True,
                'confidence': avg_confidence
            }
        else:
            logger.info(f"❌ Kein Konsens erreicht")
            return {
                'action': 'HOLD',
                'votes': votes,
                'consensus': False
            }
    
    def _should_skip_symbol(self, symbol: str) -> bool:
        """Prüft User-Constraints"""
        for constraint in self.user_constraints:
            if constraint == "avoid_tech":
                tech_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA']
                if symbol in tech_symbols:
                    return True
            # Weitere Constraints hier...
        return False
    
    def set_user_constraints(self, constraints: List[str]):
        """User gibt Vorgaben (Guided Mode)"""
        self.user_constraints = constraints
        logger.info(f"User-Constraints gesetzt: {constraints}")
    
    def get_leaderboard(self) -> List[Dict]:
        """Performance-Ranking der Agenten"""
        leaderboard = []
        
        for agent_name, agent in self.agents.items():
            stats = agent.get_performance_stats()
            leaderboard.append({
                'agent': agent_name,
                'total_trades': stats['total_trades'],
                'success_rate': stats['success_rate'],
                'total_pnl': stats['total_pnl'],
                'rank': 0  # Wird später berechnet
            })
        
        # Sortiere nach PnL
        leaderboard.sort(key=lambda x: x['total_pnl'], reverse=True)
        
        # Ränge zuweisen
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1
        
        return leaderboard
    
    def get_status(self) -> Dict:
        """Aktueller Status des Controllers"""
        return {
            'mode': self.mode,
            'autopilot_enabled': self.autopilot_enabled,
            'watchlist': self.watchlist,
            'user_constraints': self.user_constraints,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'total_sessions': len(self.trading_sessions),
            'agents_status': {
                name: agent.get_performance_stats()
                for name, agent in self.agents.items()
            }
        }


# Global Controller Instance
_controller_instance = None

def get_trading_controller(trading_client=None, data_client=None):
    """Get or create global trading controller"""
    global _controller_instance
    if _controller_instance is None and trading_client and data_client:
        _controller_instance = TradingController(trading_client, data_client)
    return _controller_instance
