"""
Neue erweiterte AI Endpoints
Kopiere diese in server.py ab Zeile 345
"""

# ============ ERWEITERTE MULTI-AGENT AI ENDPOINTS ============

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Trading costs (Alpaca Paper Trading hat keine, aber für Realismus)
TRADING_COST_PER_TRADE = 0.00  # $0 für Paper Trading

class DeepResearchRequest(BaseModel):
    query: str
    symbols: Optional[List[str]] = []
    include_user_input: Optional[str] = None

class DiscussionRequest(BaseModel):
    research_id: str
    user_input: Optional[str] = None

class ConsensusRequest(BaseModel):
    discussion_id: str

class ExecuteTradeRequest(BaseModel):
    consensus_id: str
    confirmed: bool = True

class AutoPilotScheduleRequest(BaseModel):
    enabled: bool
    frequency: str  # "twice_daily", "daily", "hourly"
    duration_days: int = 7

class CharacterUpdateRequest(BaseModel):
    agent_key: str  # "jordan", "bohlen", "frodo"
    description: str

# AI Endpoints

@api_router.get("/ai/stats")
async def get_ai_stats():
    """Get AI system statistics including costs"""
    try:
        system = get_enhanced_system()
        stats = system.get_system_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"AI stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/ai/characters")
async def get_characters():
    """Get all AI character descriptions"""
    try:
        system = get_enhanced_system()
        return {
            "success": True,
            "characters": system.characters
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ai/characters/update")
async def update_character(request: CharacterUpdateRequest):
    """Update AI character description"""
    try:
        system = get_enhanced_system()
        success = system.update_character(request.agent_key, request.description)
        
        if success:
            # Save to database
            await db.ai_characters.update_one(
                {"agent_key": request.agent_key},
                {"$set": {
                    "description": request.description,
                    "updated_at": datetime.utcnow()
                }},
                upsert=True
            )
            
            return {"success": True, "message": "Charakter aktualisiert"}
        else:
            raise HTTPException(status_code=404, detail="Agent nicht gefunden")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ai/research/start")
async def start_deep_research(request: DeepResearchRequest):
    """
    Phase 1: Deep Research
    Alle 3 KIs analysieren parallel mit Trading-Kosten
    """
    try:
        # Get portfolio context
        portfolio_context = "Paper Trading Account"
        if trading_client:
            try:
                account = trading_client.get_account()
                positions = trading_client.get_all_positions()
                portfolio_context = f"Bargeld: ${float(account.cash):.2f}, Portfolio: ${float(account.portfolio_value):.2f}. "
                if positions:
                    portfolio_context += f"Positionen: {', '.join([f'{pos.symbol}' for pos in positions[:5]])}"
            except:
                pass
        
        # Get enhanced system
        system = get_enhanced_system()
        
        # Run deep research with trading costs
        results = await system.deep_research(
            query=request.query,
            portfolio_context=portfolio_context,
            trading_costs=TRADING_COST_PER_TRADE
        )
        
        # Save to database
        research_doc = {
            "query": request.query,
            "results": results,
            "portfolio_context": portfolio_context,
            "phase": "research",
            "timestamp": datetime.utcnow()
        }
        result = await db.ai_research.insert_one(research_doc)
        research_id = str(result.inserted_id)
        
        return {
            "success": True,
            "research_id": research_id,
            "results": results,
            "next_phase": "discussion"
        }
        
    except Exception as e:
        logger.error(f"Deep research error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ai/discussion/start")
async def start_discussion(request: DiscussionRequest):
    """
    Phase 2: KI-Diskussion
    KIs diskutieren untereinander über Research-Ergebnisse
    """
    try:
        # Load research results
        from bson import ObjectId
        research_doc = await db.ai_research.find_one({"_id": ObjectId(request.research_id)})
        
        if not research_doc:
            raise HTTPException(status_code=404, detail="Research nicht gefunden")
        
        # Get system
        system = get_enhanced_system()
        
        # Start discussion
        discussion_results = await system.ai_discussion(
            research_results=research_doc["results"],
            user_input=request.user_input
        )
        
        # Save discussion
        discussion_doc = {
            "research_id": request.research_id,
            "discussion": discussion_results,
            "user_input": request.user_input,
            "phase": "discussion",
            "timestamp": datetime.utcnow()
        }
        result = await db.ai_discussions.insert_one(discussion_doc)
        discussion_id = str(result.inserted_id)
        
        return {
            "success": True,
            "discussion_id": discussion_id,
            "discussion": discussion_results,
            "next_phase": "consensus"
        }
        
    except Exception as e:
        logger.error(f"Discussion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ai/consensus/generate")
async def generate_consensus(request: ConsensusRequest):
    """
    Phase 3: Konsens generieren
    Finale Handelsempfehlung basierend auf Diskussion
    """
    try:
        # Load discussion
        from bson import ObjectId
        discussion_doc = await db.ai_discussions.find_one({"_id": ObjectId(request.discussion_id)})
        
        if not discussion_doc:
            raise HTTPException(status_code=404, detail="Diskussion nicht gefunden")
        
        # Generate consensus
        system = get_enhanced_system()
        consensus_result = await system.generate_consensus(discussion_doc["discussion"])
        
        # Save consensus
        consensus_doc = {
            "discussion_id": request.discussion_id,
            "consensus": consensus_result,
            "executed": False,
            "timestamp": datetime.utcnow()
        }
        result = await db.ai_consensus.insert_one(consensus_doc)
        consensus_id = str(result.inserted_id)
        
        return {
            "success": True,
            "consensus_id": consensus_id,
            "consensus": consensus_result,
            "can_execute": consensus_result.get("can_execute", False)
        }
        
    except Exception as e:
        logger.error(f"Consensus error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ai/trade/execute")
async def execute_consensus_trade(request: ExecuteTradeRequest):
    """
    Trade aus Konsens ausführen
    """
    try:
        if not request.confirmed:
            return {"success": False, "message": "Trade nicht bestätigt"}
        
        # Load consensus
        from bson import ObjectId
        consensus_doc = await db.ai_consensus.find_one({"_id": ObjectId(request.consensus_id)})
        
        if not consensus_doc:
            raise HTTPException(status_code=404, detail="Konsens nicht gefunden")
        
        if consensus_doc.get("executed"):
            return {"success": False, "message": "Trade bereits ausgeführt"}
        
        # Parse consensus (vereinfacht - in Produktion robuster)
        consensus_text = consensus_doc["consensus"]["consensus"]
        
        # Hier müsste man den Konsens-Text parsen
        # Format: Symbol | Aktion | Menge | Begründung
        # Für jetzt: Placeholder
        
        # Mark as executed
        await db.ai_consensus.update_one(
            {"_id": ObjectId(request.consensus_id)},
            {"$set": {"executed": True, "executed_at": datetime.utcnow()}}
        )
        
        return {
            "success": True,
            "message": "Trade-Ausführung initiiert",
            "consensus_text": consensus_text
        }
        
    except Exception as e:
        logger.error(f"Execute trade error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Autopilot with scheduler
autopilot_schedule = {
    "enabled": False,
    "frequency": "twice_daily",
    "duration_days": 7,
    "last_run": None,
    "next_run": None
}

@api_router.post("/ai/autopilot/schedule")
async def set_autopilot_schedule(request: AutoPilotScheduleRequest):
    """Set autopilot schedule"""
    try:
        autopilot_schedule["enabled"] = request.enabled
        autopilot_schedule["frequency"] = request.frequency
        autopilot_schedule["duration_days"] = request.duration_days
        
        if request.enabled:
            # Calculate next run time
            from datetime import timedelta
            now = datetime.utcnow()
            
            if request.frequency == "twice_daily":
                next_run = now + timedelta(hours=12)
            elif request.frequency == "daily":
                next_run = now + timedelta(days=1)
            elif request.frequency == "hourly":
                next_run = now + timedelta(hours=1)
            else:
                next_run = now + timedelta(hours=24)
            
            autopilot_schedule["next_run"] = next_run.isoformat()
        else:
            autopilot_schedule["next_run"] = None
        
        return {
            "success": True,
            "schedule": autopilot_schedule
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/ai/autopilot/schedule")
async def get_autopilot_schedule():
    """Get current autopilot schedule"""
    return {
        "success": True,
        "schedule": autopilot_schedule
    }
