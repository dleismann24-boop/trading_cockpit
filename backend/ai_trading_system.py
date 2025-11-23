"""
Erweitertes Multi-Agent Trading System
Mit Kosten-Tracking, Diskussion und Konsens
"""
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
from datetime import datetime
import logging
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY')

# Kosten pro 1000 Tokens (geschätzt)
MODEL_COSTS = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "claude-3-7-sonnet-20250219": {"input": 0.003, "output": 0.015},
    "gemini-2.5-flash": {"input": 0.0001, "output": 0.0003},
}

class TradingAgent:
    """Erweiterte Trading AI Agent Klasse"""
    def __init__(self, name: str, personality: str, provider: str, model: str, character_description: str):
        self.name = name
        self.personality = personality
        self.provider = provider
        self.model = model
        self.character_description = character_description
        self.chat = None
        self.total_cost = 0.0
        self.message_count = 0
    
    def initialize(self, session_id: str, system_message: str):
        """Initialize the LLM chat"""
        if not EMERGENT_LLM_KEY:
            logger.error("EMERGENT_LLM_KEY not set!")
            return False
        
        try:
            self.chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=session_id,
                system_message=system_message
            ).with_model(self.provider, self.model)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.name}: {e}")
            return False
    
    async def analyze(self, prompt: str) -> Dict:
        """Send analysis request and track costs"""
        if not self.chat:
            return {
                "response": f"Error: {self.name} not initialized",
                "cost": 0.0,
                "tokens": 0
            }
        
        try:
            user_message = UserMessage(text=prompt)
            response = await self.chat.send_message(user_message)
            
            # Geschätzte Token-Anzahl (sehr grob)
            estimated_tokens = len(prompt.split()) + len(str(response).split())
            cost = self.calculate_cost(estimated_tokens)
            
            self.total_cost += cost
            self.message_count += 1
            
            return {
                "response": response,
                "cost": cost,
                "tokens": estimated_tokens
            }
        except Exception as e:
            logger.error(f"{self.name} analysis error: {e}")
            return {
                "response": f"Error: {str(e)}",
                "cost": 0.0,
                "tokens": 0
            }
    
    def calculate_cost(self, tokens: int) -> float:
        """Calculate cost based on tokens"""
        model_cost = MODEL_COSTS.get(self.model, {"input": 0.001, "output": 0.002})
        # Vereinfacht: 50/50 input/output
        cost = (tokens / 2000) * (model_cost["input"] + model_cost["output"])
        return cost
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        return {
            "name": self.name,
            "total_cost": round(self.total_cost, 4),
            "message_count": self.message_count,
            "cost_per_message": round(self.total_cost / max(self.message_count, 1), 4)
        }


# Vordefinierte Charaktere (editierbar)
DEFAULT_CHARACTERS = {
    "jordan": {
        "name": "Jordan",
        "personality": "aggressive_winner",
        "provider": "openai",
        "model": "gpt-4",
        "description": "Michael Jordan - Der Champion. Aggressiv, gewinnorientiert, risikobereit. Fokus auf maximale Rendite."
    },
    "bohlen": {
        "name": "Bohlen",
        "personality": "direct_honest",
        "provider": "anthropic",
        "model": "claude-3-7-sonnet-20250219",
        "description": "Dieter Bohlen - Der Realist. Brutal ehrlich, direkt, schützt Kapital. Sagt wenn etwas Mist ist."
    },
    "frodo": {
        "name": "Frodo",
        "personality": "wise_patient",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "description": "Frodo - Der Weise. Geduldig, langfristig orientiert, Risikomanagement. Denkt an die Reise."
    }
}


class EnhancedMultiAgentSystem:
    """Erweitertes Multi-Agent System mit Diskussion und Konsens"""
    def __init__(self, characters: Dict = None):
        self.characters = characters or DEFAULT_CHARACTERS
        self.agents = {}
        self.conversation_history = []
        self.total_system_cost = 0.0
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all agents"""
        for key, char in self.characters.items():
            self.agents[key] = TradingAgent(
                name=char["name"],
                personality=char["personality"],
                provider=char["provider"],
                model=char["model"],
                character_description=char["description"]
            )
    
    async def deep_research(self, query: str, portfolio_context: str, trading_costs: float = 0.0) -> Dict:
        """
        Phase 1: Deep Research mit Trading-Kosten
        """
        research_prompt = f"""Analysiere folgende Frage: {query}

Portfolio-Kontext: {portfolio_context}

WICHTIG: Berücksichtige Trading-Kosten von ${trading_costs:.2f} pro Trade in deiner Analyse.

Gib eine prägnante Analyse mit konkreten Empfehlungen."""

        # Initialize agents
        session_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        results = {}
        total_cost = 0.0
        
        for key, agent in self.agents.items():
            char = self.characters[key]
            system_msg = f"""{char['description']}

Du analysierst Aktien und Trading-Strategien. Berücksichtige IMMER Trading-Kosten.
Antworte auf Deutsch und halte dich kurz (max 150 Wörter)."""
            
            if agent.initialize(f"{session_id}_{agent.name}", system_msg):
                result = await agent.analyze(research_prompt)
                results[key] = {
                    "agent": agent.name,
                    "response": result["response"],
                    "cost": result["cost"]
                }
                total_cost += result["cost"]
        
        self.total_system_cost += total_cost
        
        return {
            "phase": "research",
            "results": results,
            "total_cost": round(total_cost, 4),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def ai_discussion(self, research_results: Dict, user_input: str = None) -> Dict:
        """
        Phase 2: KIs diskutieren untereinander
        """
        # Erstelle Diskussions-Prompt basierend auf Research
        discussion_prompt = f"""Basierend auf der vorherigen Analyse:

Jordan sagt: {research_results['results']['jordan']['response'][:200]}
Bohlen sagt: {research_results['results']['bohlen']['response'][:200]}
Frodo sagt: {research_results['results']['frodo']['response'][:200]}

"""
        
        if user_input:
            discussion_prompt += f"\nUser-Kommentar: {user_input}\n"
        
        discussion_prompt += """
Diskutiere mit den anderen KIs und komme zu einem gemeinsamen Vorschlag:
1. Was soll getradet werden?
2. Wie viel? (max 10% des Portfolios)
3. Warum?

Antworte kurz und konkret auf Deutsch (max 100 Wörter)."""

        session_id = f"discussion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        discussion = []
        total_cost = 0.0
        
        # Jede KI gibt Statement ab
        for key, agent in self.agents.items():
            char = self.characters[key]
            system_msg = f"""{char['description']}
            
Du diskutierst mit Jordan, Bohlen und Frodo über Trading-Entscheidungen.
Sei du selbst und vertrete deinen Standpunkt auf Deutsch."""
            
            if agent.initialize(f"{session_id}_{agent.name}", system_msg):
                result = await agent.analyze(discussion_prompt)
                discussion.append({
                    "agent": agent.name,
                    "statement": result["response"],
                    "cost": result["cost"]
                })
                total_cost += result["cost"]
        
        self.total_system_cost += total_cost
        
        return {
            "phase": "discussion",
            "discussion": discussion,
            "total_cost": round(total_cost, 4),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def generate_consensus(self, discussion_results: Dict) -> Dict:
        """
        Generate consensus recommendation from discussion
        """
        # Nutze Bohlen für Konsens (am realistischsten)
        agent = self.agents["bohlen"]
        char = self.characters["bohlen"]
        
        statements = "\n".join([
            f"{d['agent']}: {d['statement'][:150]}" 
            for d in discussion_results['discussion']
        ])
        
        consensus_prompt = f"""Basierend auf dieser Diskussion:

{statements}

Fasse den Konsens zusammen und gib eine KONKRETE Handelsempfehlung:
- Symbol: [TICKER]
- Aktion: KAUFEN/VERKAUFEN/HALTEN
- Menge: [Anzahl Aktien]
- Begründung: [1 Satz]

Format: Symbol | Aktion | Menge | Begründung
Antworte NUR mit diesem Format auf Deutsch."""

        session_id = f"consensus_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        system_msg = f"""{char['description']}
        
Du fasst die Diskussion zusammen und gibst die finale Empfehlung."""
        
        if agent.initialize(session_id, system_msg):
            result = await agent.analyze(consensus_prompt)
            self.total_system_cost += result["cost"]
            
            return {
                "consensus": result["response"],
                "cost": result["cost"],
                "can_execute": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {"consensus": "Fehler beim Konsens", "cost": 0.0, "can_execute": False}
    
    def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        agent_stats = {key: agent.get_stats() for key, agent in self.agents.items()}
        
        return {
            "total_system_cost": round(self.total_system_cost, 4),
            "agents": agent_stats,
            "conversation_count": len(self.conversation_history)
        }
    
    def update_character(self, agent_key: str, new_description: str):
        """Update character description"""
        if agent_key in self.characters:
            self.characters[agent_key]["description"] = new_description
            return True
        return False


# Global instance
_enhanced_system = None

def get_enhanced_system() -> EnhancedMultiAgentSystem:
    """Get or create the enhanced system"""
    global _enhanced_system
    if _enhanced_system is None:
        _enhanced_system = EnhancedMultiAgentSystem()
    return _enhanced_system
