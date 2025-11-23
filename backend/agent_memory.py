"""
Agent Memory System
Tracked Performance, Historie und "Lessons Learned" für jeden Agenten
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)


class AgentMemory:
    """Memory-System für Trading-Agenten"""
    
    def __init__(self, agent_name: str, db_client):
        self.agent_name = agent_name
        self.db = db_client.trading_db
        self.collection = self.db.agent_memory
    
    async def record_trade(self, trade_data: Dict):
        """
        Speichert einen Trade in der Historie
        
        Args:
            trade_data: {
                'symbol': str,
                'action': 'BUY/SELL/HOLD',
                'confidence': float,
                'price': float,
                'quantity': int,
                'reasoning': str,
                'sentiment_score': float,
                'technical_signal': str,
                'timestamp': datetime
            }
        """
        try:
            document = {
                'agent': self.agent_name,
                'trade': trade_data,
                'recorded_at': datetime.utcnow()
            }
            
            await self.collection.insert_one(document)
            logger.info(f"{self.agent_name}: Trade recorded - {trade_data['action']} {trade_data['symbol']}")
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error recording trade: {e}")
    
    async def update_trade_outcome(self, trade_id: str, outcome: Dict):
        """
        Aktualisiert ein Trade mit dem Ergebnis
        
        Args:
            outcome: {
                'profit_loss': float,
                'profit_loss_percent': float,
                'exit_price': float,
                'exit_date': datetime,
                'holding_period_days': int,
                'success': bool
            }
        """
        try:
            await self.collection.update_one(
                {'_id': trade_id},
                {'$set': {'outcome': outcome, 'updated_at': datetime.utcnow()}}
            )
            
        except Exception as e:
            logger.error(f"Error updating trade outcome: {e}")
    
    async def get_recent_trades(self, limit: int = 20) -> List[Dict]:
        """Holt die letzten N Trades des Agenten"""
        try:
            cursor = self.collection.find(
                {'agent': self.agent_name}
            ).sort('recorded_at', -1).limit(limit)
            
            trades = await cursor.to_list(length=limit)
            return trades
            
        except Exception as e:
            logger.error(f"Error fetching recent trades: {e}")
            return []
    
    async def get_performance_stats(self, days: int = 30) -> Dict:
        """
        Berechnet Performance-Metriken für die letzten N Tage
        
        Returns:
            {
                'total_trades': int,
                'successful_trades': int,
                'win_rate': float,
                'avg_profit': float,
                'avg_loss': float,
                'total_profit_loss': float,
                'best_trade': Dict,
                'worst_trade': Dict,
                'avg_confidence': float
            }
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            cursor = self.collection.find({
                'agent': self.agent_name,
                'recorded_at': {'$gte': since_date},
                'outcome': {'$exists': True}
            })
            
            trades = await cursor.to_list(length=None)
            
            if not trades:
                return {
                    'total_trades': 0,
                    'successful_trades': 0,
                    'win_rate': 0.0,
                    'avg_profit': 0.0,
                    'avg_loss': 0.0,
                    'total_profit_loss': 0.0,
                    'best_trade': None,
                    'worst_trade': None,
                    'avg_confidence': 0.0
                }
            
            # Calculate stats
            successful = [t for t in trades if t['outcome'].get('success', False)]
            failed = [t for t in trades if not t['outcome'].get('success', False)]
            
            profits = [t['outcome']['profit_loss'] for t in successful]
            losses = [t['outcome']['profit_loss'] for t in failed]
            
            all_pl = [t['outcome']['profit_loss'] for t in trades]
            
            stats = {
                'total_trades': len(trades),
                'successful_trades': len(successful),
                'failed_trades': len(failed),
                'win_rate': len(successful) / len(trades) if trades else 0.0,
                'avg_profit': sum(profits) / len(profits) if profits else 0.0,
                'avg_loss': sum(losses) / len(losses) if losses else 0.0,
                'total_profit_loss': sum(all_pl),
                'best_trade': max(trades, key=lambda t: t['outcome']['profit_loss']) if trades else None,
                'worst_trade': min(trades, key=lambda t: t['outcome']['profit_loss']) if trades else None,
                'avg_confidence': sum(t['trade']['confidence'] for t in trades) / len(trades)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating performance: {e}")
            return {}
    
    async def generate_lessons_learned(self) -> str:
        """
        Generiert "Lessons Learned" basierend auf Trade-Historie
        
        Returns:
            String mit Erkenntnissen aus vergangenen Trades
        """
        try:
            stats = await self.get_performance_stats(days=30)
            recent_trades = await self.get_recent_trades(limit=10)
            
            if stats['total_trades'] == 0:
                return "Noch keine Trading-Historie vorhanden."
            
            lessons = []
            
            # Win-Rate Lesson
            if stats['win_rate'] < 0.4:
                lessons.append(f"⚠️ Niedrige Win-Rate ({stats['win_rate']:.1%}) - Vorsichtiger handeln")
            elif stats['win_rate'] > 0.6:
                lessons.append(f"✅ Gute Win-Rate ({stats['win_rate']:.1%}) - Strategie funktioniert")
            
            # Confidence vs Success
            high_conf_trades = [t for t in recent_trades if t['trade']['confidence'] > 0.8]
            if high_conf_trades:
                high_conf_success = sum(1 for t in high_conf_trades if t.get('outcome', {}).get('success', False))
                if high_conf_success / len(high_conf_trades) < 0.5:
                    lessons.append("⚠️ Hohe Confidence korreliert nicht mit Erfolg - Überdenken")
            
            # Symbol-spezifische Lessons
            symbol_performance = {}
            for trade in recent_trades:
                if 'outcome' in trade:
                    symbol = trade['trade']['symbol']
                    if symbol not in symbol_performance:
                        symbol_performance[symbol] = {'wins': 0, 'losses': 0}
                    
                    if trade['outcome'].get('success'):
                        symbol_performance[symbol]['wins'] += 1
                    else:
                        symbol_performance[symbol]['losses'] += 1
            
            # Finde beste und schlechteste Symbole
            for symbol, perf in symbol_performance.items():
                total = perf['wins'] + perf['losses']
                if total >= 3:  # Mindestens 3 Trades
                    win_rate = perf['wins'] / total
                    if win_rate > 0.7:
                        lessons.append(f"✅ Stark bei {symbol} ({win_rate:.0%} Win-Rate)")
                    elif win_rate < 0.3:
                        lessons.append(f"⚠️ Schwach bei {symbol} ({win_rate:.0%} Win-Rate) - Vermeiden")
            
            # Sentiment Correlation
            trades_with_sentiment = [
                t for t in recent_trades 
                if 'sentiment_score' in t['trade'] and 'outcome' in t
            ]
            
            if len(trades_with_sentiment) >= 5:
                # Check ob positive Sentiment = erfolgreiche Trades
                positive_sentiment = [t for t in trades_with_sentiment if t['trade']['sentiment_score'] > 0.3]
                if positive_sentiment:
                    success_with_pos_sentiment = sum(
                        1 for t in positive_sentiment if t['outcome'].get('success', False)
                    ) / len(positive_sentiment)
                    
                    if success_with_pos_sentiment > 0.65:
                        lessons.append("✅ Positives Sentiment ist guter Indikator - Nutzen!")
                    elif success_with_pos_sentiment < 0.35:
                        lessons.append("⚠️ Positives Sentiment führt oft zu Fehlern - Konträr denken?")
            
            if not lessons:
                lessons.append("📊 Noch zu wenig Daten für konkrete Lessons")
            
            return "\n".join(lessons)
            
        except Exception as e:
            logger.error(f"Error generating lessons: {e}")
            return "Fehler beim Generieren der Lessons"
    
    async def get_memory_summary(self) -> str:
        """
        Generiert kompakte Zusammenfassung für Agenten-Prompt
        
        Returns:
            String der direkt in LLM-Prompt eingefügt werden kann
        """
        try:
            stats = await self.get_performance_stats(days=7)  # Letzte Woche
            lessons = await self.generate_lessons_learned()
            
            summary = f"""
📊 Deine Performance (Letzte 7 Tage):
- Trades: {stats['total_trades']} (davon {stats['successful_trades']} erfolgreich)
- Win-Rate: {stats['win_rate']:.1%}
- Durchschn. Gewinn: ${stats['avg_profit']:.2f}
- Durchschn. Verlust: ${stats['avg_loss']:.2f}
- Gesamt P&L: ${stats['total_profit_loss']:.2f}

💡 Lessons Learned:
{lessons}
"""
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating memory summary: {e}")
            return "Keine Memory-Daten verfügbar"


# Global Memory Instances
_memory_instances = {}

def get_agent_memory(agent_name: str, db_client) -> AgentMemory:
    """Get or create agent memory instance"""
    if agent_name not in _memory_instances:
        _memory_instances[agent_name] = AgentMemory(agent_name, db_client)
    return _memory_instances[agent_name]
