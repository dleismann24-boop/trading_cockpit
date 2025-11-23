# ============ ERWEITERTE AI ENDPOINTS ============

TRADING_COST_PER_TRADE = 0.00  # Paper Trading

@api_router.get("/ai/stats")
async def get_ai_stats():
    """KI-Statistiken mit Kosten"""
    try:
        system = get_enhanced_system()
        stats = system.get_system_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"AI stats error: {e}")
        return {"success": False, "error": str(e)}

@api_router.get("/ai/characters")
async def get_characters():
    """Alle KI-Charaktere"""
    try:
        system = get_enhanced_system()
        return {"success": True, "characters": system.characters}
    except Exception as e:
        return {"success": False, "error": str(e)}

class CharacterUpdateRequest(BaseModel):
    agent_key: str
    description: str

@api_router.post("/ai/characters/update")
async def update_character(request: CharacterUpdateRequest):
    """KI-Charakter bearbeiten"""
    try:
        system = get_enhanced_system()
        success = system.update_character(request.agent_key, request.description)
        if success:
            await db.ai_characters.update_one(
                {"agent_key": request.agent_key},
                {"$set": {"description": request.description, "updated_at": datetime.utcnow()}},
                upsert=True
            )
            return {"success": True, "message": "Charakter aktualisiert"}
        raise HTTPException(status_code=404, detail="Agent nicht gefunden")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ResearchStartRequest(BaseModel):
    query: str

@api_router.post("/ai/research/start")
async def start_research(request: ResearchStartRequest):
    """Phase 1: Deep Research starten"""
    try:
        portfolio_context = "Paper Trading"
        if trading_client:
            try:
                account = trading_client.get_account()
                portfolio_context = f"Bargeld: ${float(account.cash):.2f}, Portfolio: ${float(account.portfolio_value):.2f}"
            except:
                pass
        
        system = get_enhanced_system()
        results = await system.deep_research(
            query=request.query,
            portfolio_context=portfolio_context,
            trading_costs=TRADING_COST_PER_TRADE
        )
        
        research_doc = {
            "query": request.query,
            "results": results,
            "timestamp": datetime.utcnow()
        }
        result = await db.ai_research.insert_one(research_doc)
        
        return {
            "success": True,
            "research_id": str(result.inserted_id),
            "results": results
        }
    except Exception as e:
        logger.error(f"Research error: {e}")
        return {"success": False, "error": str(e)}

class DiscussionStartRequest(BaseModel):
    research_id: str
    user_input: Optional[str] = None

@api_router.post("/ai/discussion/start")
async def start_discussion(request: DiscussionStartRequest):
    """Phase 2: KI-Diskussion"""
    try:
        from bson import ObjectId
        research_doc = await db.ai_research.find_one({"_id": ObjectId(request.research_id)})
        
        if not research_doc:
            return {"success": False, "error": "Research nicht gefunden"}
        
        system = get_enhanced_system()
        discussion = await system.ai_discussion(
            research_results=research_doc["results"],
            user_input=request.user_input
        )
        
        discussion_doc = {
            "research_id": request.research_id,
            "discussion": discussion,
            "user_input": request.user_input,
            "timestamp": datetime.utcnow()
        }
        result = await db.ai_discussions.insert_one(discussion_doc)
        
        return {
            "success": True,
            "discussion_id": str(result.inserted_id),
            "discussion": discussion
        }
    except Exception as e:
        logger.error(f"Discussion error: {e}")
        return {"success": False, "error": str(e)}

class ConsensusRequest(BaseModel):
    discussion_id: str

@api_router.post("/ai/consensus/generate")
async def generate_consensus(request: ConsensusRequest):
    """Phase 3: Konsens"""
    try:
        from bson import ObjectId
        discussion_doc = await db.ai_discussions.find_one({"_id": ObjectId(request.discussion_id)})
        
        if not discussion_doc:
            return {"success": False, "error": "Diskussion nicht gefunden"}
        
        system = get_enhanced_system()
        consensus = await system.generate_consensus(discussion_doc["discussion"])
        
        consensus_doc = {
            "discussion_id": request.discussion_id,
            "consensus": consensus,
            "executed": False,
            "timestamp": datetime.utcnow()
        }
        result = await db.ai_consensus.insert_one(consensus_doc)
        
        return {
            "success": True,
            "consensus_id": str(result.inserted_id),
            "consensus": consensus
        }
    except Exception as e:
        logger.error(f"Consensus error: {e}")
        return {"success": False, "error": str(e)}

autopilot_schedule = {
    "enabled": False,
    "frequency": "twice_daily",
    "duration_days": 7
}

class ScheduleRequest(BaseModel):
    enabled: bool
    frequency: str
    duration_days: int

@api_router.post("/ai/autopilot/schedule")
async def set_schedule(request: ScheduleRequest):
    """Autopilot-Zeitplan"""
    autopilot_schedule.update({
        "enabled": request.enabled,
        "frequency": request.frequency,
        "duration_days": request.duration_days
    })
    return {"success": True, "schedule": autopilot_schedule}

@api_router.get("/ai/autopilot/schedule")
async def get_schedule():
    """Zeitplan abrufen"""
    return {"success": True, "schedule": autopilot_schedule}
