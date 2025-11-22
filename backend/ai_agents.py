"""
Multi-Agent AI Trading System
Jordan (GPT-4) + Bohlen (Claude) + Frodo (Gemini)
"""
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY')

class TradingAgent:
    """Base class for trading AI agents"""
    def __init__(self, name: str, personality: str, provider: str, model: str):
        self.name = name
        self.personality = personality
        self.provider = provider
        self.model = model
        self.chat = None
    
    def initialize(self, session_id: str, system_message: str):
        """Initialize the LLM chat"""
        self.chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_message
        ).with_model(self.provider, self.model)
    
    async def analyze(self, prompt: str) -> str:
        """Send analysis request and get response"""
        if not self.chat:
            raise Exception(f"{self.name} not initialized")
        
        try:
            user_message = UserMessage(text=prompt)
            response = await self.chat.send_message(user_message)
            return response
        except Exception as e:
            logger.error(f"{self.name} analysis error: {e}")
            return f"Error: Unable to get response from {self.name}"


class JordanAgent(TradingAgent):
    """Michael Jordan - Aggressive, winning-focused"""
    def __init__(self):
        super().__init__(
            name="Jordan",
            personality="aggressive_winner",
            provider="openai",
            model="gpt-4"
        )
    
    def get_system_message(self, portfolio_context: str) -> str:
        return f"""You are Michael Jordan - the ultimate champion with a killer instinct for winning.
In trading, you focus on:
- AGGRESSIVE growth strategies
- High-conviction plays
- "Win at all costs" mentality
- Taking calculated risks for big gains
- Never settling for mediocrity

Portfolio Context: {portfolio_context}

Analyze opportunities with your championship mindset. Be direct, confident, and focus on WINNING.
Keep responses under 150 words. Sign as "🏀 Jordan" """


class BohlenAgent(TradingAgent):
    """Dieter Bohlen - Direct, honest, no-nonsense"""
    def __init__(self):
        super().__init__(
            name="Bohlen",
            personality="direct_honest",
            provider="anthropic",
            model="claude-3-7-sonnet-20250219"
        )
    
    def get_system_message(self, portfolio_context: str) -> str:
        return f"""You are Dieter Bohlen - brutally honest, direct, and always tell it like it is.
In trading, you focus on:
- REALISTIC assessments (no sugar-coating)
- Cutting through the hype
- Protecting capital first
- Calling out bad ideas immediately
- Clear yes/no decisions

Portfolio Context: {portfolio_context}

Give your honest opinion. If something's trash, say it. If it's good, say why.
Keep responses under 150 words. Sign as "🎤 Bohlen" """


class FrodoAgent(TradingAgent):
    """Frodo - Wise, patient, long-term focused"""
    def __init__(self):
        super().__init__(
            name="Frodo",
            personality="wise_patient",
            provider="gemini",
            model="gemini-2.5-flash"
        )
    
    def get_system_message(self, portfolio_context: str) -> str:
        return f"""You are Frodo - humble, wise, and focused on the long journey ahead.
In trading, you focus on:
- LONG-TERM wealth building
- Risk management and preservation
- Sustainable growth strategies
- Learning from mistakes
- Patience over quick wins

Portfolio Context: {portfolio_context}

Provide thoughtful, measured advice. Think about the journey, not just the destination.
Keep responses under 150 words. Sign as "🧙 Frodo" """


class MultiAgentSystem:
    """Coordinates all 3 AI agents"""
    def __init__(self):
        self.jordan = JordanAgent()
        self.bohlen = BohlenAgent()
        self.frodo = FrodoAgent()
        self.agents = [self.jordan, self.bohlen, self.frodo]
    
    def initialize_agents(self, portfolio_context: str):
        """Initialize all agents with portfolio context"""
        session_id = f"trading_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for agent in self.agents:
            agent.initialize(
                session_id=f"{session_id}_{agent.name}",
                system_message=agent.get_system_message(portfolio_context)
            )
    
    async def deep_research(self, query: str, portfolio_context: str) -> dict:
        """
        Deep research mode - all 3 AIs analyze in parallel
        Returns consensus and individual opinions
        """
        self.initialize_agents(portfolio_context)
        
        # Get all analyses in parallel
        tasks = [
            self.jordan.analyze(query),
            self.bohlen.analyze(query),
            self.frodo.analyze(query)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "jordan": results[0] if not isinstance(results[0], Exception) else "Error",
            "bohlen": results[1] if not isinstance(results[1], Exception) else "Error",
            "frodo": results[2] if not isinstance(results[2], Exception) else "Error",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def auto_pilot_analyze(self, portfolio_context: str, market_data: dict) -> dict:
        """
        Auto-pilot mode - AIs collaborate to suggest trades
        Returns trade recommendation with consensus
        """
        self.initialize_agents(portfolio_context)
        
        prompt = f"""Auto-Pilot Trading Analysis:

Market Data: {market_data}

Based on the current market and portfolio, should we make any trades?
- What to buy/sell?
- How much (max 10% of portfolio per trade)?
- Why?

Be specific with ticker symbols and amounts."""

        # Get all recommendations
        results = await self.deep_research(prompt, portfolio_context)
        
        # Calculate consensus (simplified - you can make this more sophisticated)
        buy_signals = sum([
            1 for r in results.values() 
            if isinstance(r, str) and any(word in r.lower() for word in ['buy', 'kaufen', 'long'])
        ])
        
        return {
            **results,
            "consensus_strength": buy_signals / 3,  # 0-1 scale
            "recommendation": "BUY" if buy_signals >= 2 else "HOLD",
        }


# Global instance
_multi_agent_system = None

def get_multi_agent_system() -> MultiAgentSystem:
    """Get or create the global multi-agent system"""
    global _multi_agent_system
    if _multi_agent_system is None:
        _multi_agent_system = MultiAgentSystem()
    return _multi_agent_system
