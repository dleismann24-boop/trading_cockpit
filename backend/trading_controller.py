"""
Trading Controller
Orchestriert alle 3 autonomen Agenten
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from autonomous_agents import JordanAgent, BohlenAgent, FrodoAgent

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
        self.mode = TradingMode.SOLO
        self.autopilot_enabled = False
        self.watchlist = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']
        self.user_constraints = []  # z.B. ["avoid_tech", "max_risk_low"]
        
        # Tracking
        self.trading_sessions = []
        self.last_run = None
        self.next_run = None
    
    async def run_trading_cycle(self) -> Dict:
        """
        Führt einen Trading-Zyklus aus
        Alle Agenten analysieren Watchlist und treffen Entscheidungen
        """
        logger.info("=" * 60)
        logger.info(f"🤖 Trading Cycle gestartet - Modus: {self.mode}")
        logger.info("=" * 60)
        
        cycle_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'mode': self.mode,
            'agents': {},
            'trades_executed': 0,
            'total_cost': 0.0
        }
        
        # Für jeden Agent
        for agent_name, agent in self.agents.items():
            logger.info(f"\n--- {agent.name} analysiert Markt ---")
            agent_trades = []
            
            # Durch Watchlist gehen
            for symbol in self.watchlist:
                try:
                    # User-Constraints prüfen
                    if self._should_skip_symbol(symbol):
                        logger.info(f"{agent.name}: Skipped {symbol} (User-Constraint)")
                        continue
                    
                    # Agent-Entscheidung
                    decision = await agent.make_trading_decision(symbol)
                    
                    if decision:
                        agent_trades.append(decision)
                        cycle_results['trades_executed'] += 1
                        
                except Exception as e:
                    logger.error(f"{agent.name}: Error analyzing {symbol}: {e}")
            
            cycle_results['agents'][agent_name] = {
                'trades': agent_trades,
                'performance': agent.get_performance_stats()
            }
        
        # Session speichern
        self.trading_sessions.append(cycle_results)
        self.last_run = datetime.utcnow()
        
        logger.info("=" * 60)
        logger.info(f"✅ Trading Cycle abgeschlossen - {cycle_results['trades_executed']} Trades")
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
