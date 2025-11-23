from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import openai
from ai_trading_system import get_enhanced_system, DEFAULT_CHARACTERS

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Alpaca clients (Paper Trading)
try:
    trading_client = TradingClient(
        api_key=os.getenv('ALPACA_API_KEY', 'paper_key'),
        secret_key=os.getenv('ALPACA_SECRET_KEY', 'paper_secret'),
        paper=True
    )
    data_client = StockHistoricalDataClient(
        api_key=os.getenv('ALPACA_API_KEY', 'paper_key'),
        secret_key=os.getenv('ALPACA_SECRET_KEY', 'paper_secret')
    )
except Exception as e:
    logging.error(f"Alpaca client initialization failed: {e}")
    trading_client = None
    data_client = None

# OpenAI client with Emergent LLM Key
openai.api_key = os.getenv('EMERGENT_LLM_KEY', '')

# Create the main app
app = FastAPI(title="Rooky & Funky Trading API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============ MODELS ============

class PlaceOrderRequest(BaseModel):
    symbol: str
    quantity: float
    side: str  # buy or sell
    order_type: str = "market"  # market or limit
    limit_price: Optional[float] = None

class OrderResponse(BaseModel):
    order_id: str
    symbol: str
    quantity: float
    side: str
    status: str
    created_at: str

class PositionResponse(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pl: float
    unrealized_plpc: float

class AccountResponse(BaseModel):
    cash: float
    portfolio_value: float
    buying_power: float
    equity: float

class QuoteResponse(BaseModel):
    symbol: str
    price: float
    bid: float
    ask: float
    timestamp: str

class ChatMessage(BaseModel):
    message: str
    user: str = "Wookie Mann & Funky Danki"

class ChatResponse(BaseModel):
    response: str
    timestamp: str

# Mock data for development
MOCK_POSITIONS = [
    {
        "symbol": "AAPL",
        "quantity": 10,
        "avg_price": 175.50,
        "current_price": 178.25,
        "market_value": 1782.50,
        "unrealized_pl": 27.50,
        "unrealized_plpc": 1.57
    },
    {
        "symbol": "TSLA",
        "quantity": 5,
        "avg_price": 245.00,
        "current_price": 250.75,
        "market_value": 1253.75,
        "unrealized_pl": 28.75,
        "unrealized_plpc": 2.35
    },
    {
        "symbol": "NVDA",
        "quantity": 8,
        "avg_price": 485.00,
        "current_price": 492.30,
        "market_value": 3938.40,
        "unrealized_pl": 58.40,
        "unrealized_plpc": 1.51
    }
]

MOCK_ACCOUNT = {
    "cash": 25420.75,
    "portfolio_value": 32395.40,
    "buying_power": 50841.50,
    "equity": 32395.40
}

# ============ ROUTES ============

@api_router.get("/")
async def root():
    return {"message": "Welcome to the Court, Wookie Mann & Funky Danki 🏀"}

@api_router.get("/market/status")
async def get_market_status():
    """Get current market status (open/closed) from Alpaca"""
    try:
        if trading_client:
            clock = trading_client.get_clock()
            return {
                "success": True,
                "is_open": clock.is_open,
                "next_open": str(clock.next_open),
                "next_close": str(clock.next_close),
                "timestamp": str(clock.timestamp)
            }
        else:
            # Mock für Dev
            now = datetime.utcnow()
            is_weekend = now.weekday() >= 5  # Samstag oder Sonntag
            return {
                "success": True,
                "is_open": not is_weekend and 14 <= now.hour < 21,  # 9:30-16:00 EST = 14:30-21:00 UTC
                "next_open": "Mock data",
                "next_close": "Mock data",
                "timestamp": str(now)
            }
    except Exception as e:
        logging.error(f"Error fetching market status: {e}")
        return {
            "success": False,
            "is_open": False,
            "error": str(e)
        }

# Account endpoints
@api_router.get("/account", response_model=AccountResponse)
async def get_account():
    """Get account information including cash and portfolio value"""
    try:
        if trading_client:
            account = trading_client.get_account()
            return AccountResponse(
                cash=float(account.cash),
                portfolio_value=float(account.portfolio_value),
                buying_power=float(account.buying_power),
                equity=float(account.equity)
            )
        else:
            # Return mock data if Alpaca not configured
            return AccountResponse(**MOCK_ACCOUNT)
    except Exception as e:
        logging.error(f"Error fetching account: {e}")
        return AccountResponse(**MOCK_ACCOUNT)

# Portfolio endpoints
@api_router.get("/positions", response_model=List[PositionResponse])
async def get_positions():
    """Get all open positions"""
    try:
        if trading_client:
            positions = trading_client.get_all_positions()
            
            # Falls keine Positionen (Markt geschlossen), zeige Mock-Daten
            if len(positions) == 0:
                logging.info("No positions found, returning mock data (market closed)")
                return [PositionResponse(**pos) for pos in MOCK_POSITIONS]
            
            return [
                PositionResponse(
                    symbol=pos.symbol,
                    quantity=float(pos.qty),
                    avg_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price),
                    market_value=float(pos.market_value),
                    unrealized_pl=float(pos.unrealized_pl),
                    unrealized_plpc=float(pos.unrealized_plpc) * 100
                )
                for pos in positions
            ]
        else:
            return [PositionResponse(**pos) for pos in MOCK_POSITIONS]
    except Exception as e:
        logging.error(f"Error fetching positions: {e}")
        return [PositionResponse(**pos) for pos in MOCK_POSITIONS]

# Trading endpoints
@api_router.post("/orders", response_model=OrderResponse)
async def place_order(request: PlaceOrderRequest):
    """Place a trading order"""
    try:
        side = OrderSide.BUY if request.side.lower() == "buy" else OrderSide.SELL
        
        if trading_client:
            if request.order_type == "market":
                order_data = MarketOrderRequest(
                    symbol=request.symbol,
                    qty=request.quantity,
                    side=side,
                    time_in_force=TimeInForce.DAY
                )
            elif request.order_type == "limit":
                if not request.limit_price:
                    raise HTTPException(status_code=400, detail="Limit price required")
                order_data = LimitOrderRequest(
                    symbol=request.symbol,
                    qty=request.quantity,
                    limit_price=request.limit_price,
                    side=side,
                    time_in_force=TimeInForce.DAY
                )
            
            order = trading_client.submit_order(order_data)
            return OrderResponse(
                order_id=str(order.id),
                symbol=order.symbol,
                quantity=float(order.qty),
                side=order.side.value,
                status=order.status.value,
                created_at=str(order.created_at)
            )
        else:
            # Mock order
            return OrderResponse(
                order_id=str(uuid.uuid4()),
                symbol=request.symbol,
                quantity=request.quantity,
                side=request.side,
                status="filled",
                created_at=str(datetime.utcnow())
            )
    except Exception as e:
        logging.error(f"Error placing order: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Quote endpoints
@api_router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(symbol: str):
    """Get latest quote for a stock"""
    try:
        if data_client:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = data_client.get_stock_latest_quote(request)
            
            if symbol in quotes:
                quote = quotes[symbol]
                return QuoteResponse(
                    symbol=symbol,
                    price=float(quote.ask_price),
                    bid=float(quote.bid_price),
                    ask=float(quote.ask_price),
                    timestamp=str(quote.timestamp)
                )
        
        # Mock quote
        import random
        base_prices = {"AAPL": 178.25, "TSLA": 250.75, "NVDA": 492.30, "MSFT": 415.50}
        base_price = base_prices.get(symbol, 100.0)
        return QuoteResponse(
            symbol=symbol,
            price=base_price,
            bid=base_price - 0.05,
            ask=base_price + 0.05,
            timestamp=str(datetime.utcnow())
        )
    except Exception as e:
        logging.error(f"Error fetching quote: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# AI Chat endpoint
@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(message: ChatMessage):
    """Chat with the AI trading assistant"""
    try:
        # Get current portfolio context
        try:
            if trading_client:
                account = trading_client.get_account()
                positions = trading_client.get_all_positions()
                context = f"Account Balance: ${float(account.cash):.2f}, Portfolio Value: ${float(account.portfolio_value):.2f}. "
                context += f"Current Holdings: {', '.join([f'{pos.symbol} ({pos.qty} shares)' for pos in positions[:5]])}"
            else:
                context = f"Account Balance: $25,420.75, Portfolio Value: $32,395.40. Current Holdings: AAPL (10 shares), TSLA (5 shares), NVDA (8 shares)"
        except:
            context = "Mock trading account with demo positions."
        
        # Call OpenAI with portfolio context
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are 'The Coach', an AI trading advisor for Wookie Mann and Funky Danki. You help manage their stock portfolio with wisdom and a touch of basketball flair. Current portfolio context: {context}. Keep responses concise and actionable. Add subtle basketball references when appropriate."},
                {"role": "user", "content": message.message}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Save to database
        chat_doc = {
            "user": message.user,
            "message": message.message,
            "response": ai_response,
            "timestamp": datetime.utcnow()
        }
        await db.chat_history.insert_one(chat_doc)
        
        return ChatResponse(
            response=ai_response,
            timestamp=str(datetime.utcnow())
        )
    except Exception as e:
        logging.error(f"Error in AI chat: {e}")
        # Fallback response
        return ChatResponse(
            response="Hey team! I'm currently getting warmed up. In the meantime, your portfolio is looking solid. Keep that long-term vision! 🏀",
            timestamp=str(datetime.utcnow())
        )

# Market search endpoint
@api_router.get("/search/{query}")
async def search_stocks(query: str):
    """Search for stocks by symbol or name"""
    # Mock search results
    mock_results = [
        {"symbol": "AAPL", "name": "Apple Inc.", "price": 178.25},
        {"symbol": "TSLA", "name": "Tesla Inc.", "price": 250.75},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "price": 492.30},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "price": 415.50},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": 142.80},
    ]
    
    # Filter results based on query
    results = [
        stock for stock in mock_results
        if query.upper() in stock["symbol"] or query.lower() in stock["name"].lower()
    ]
    
    return results[:5]

# ============ MULTI-AGENT AI ENDPOINTS ============

class DeepResearchRequest(BaseModel):
    query: str
    symbols: Optional[List[str]] = []

@api_router.post("/ai/deep-research")
async def deep_research(request: DeepResearchRequest):
    """
    Deep Research Mode - All 3 AIs analyze in parallel
    Jordan (GPT-4) + Bohlen (Claude) + Frodo (Gemini)
    """
    try:
        # Get portfolio context
        try:
            if trading_client:
                account = trading_client.get_account()
                positions = trading_client.get_all_positions()
                portfolio_context = f"Cash: ${float(account.cash):.2f}, Portfolio: ${float(account.portfolio_value):.2f}. "
                portfolio_context += f"Holdings: {', '.join([f'{pos.symbol}' for pos in positions[:5]])}"
            else:
                portfolio_context = "Paper trading account with $100,000 starting capital"
        except:
            portfolio_context = "Paper trading account"
        
        # Get multi-agent system
        multi_agent = get_multi_agent_system()
        
        # Run deep research
        results = await multi_agent.deep_research(
            query=request.query,
            portfolio_context=portfolio_context
        )
        
        # Save to database
        research_doc = {
            "query": request.query,
            "results": results,
            "portfolio_context": portfolio_context,
            "timestamp": datetime.utcnow()
        }
        await db.ai_research.insert_one(research_doc)
        
        return {
            "success": True,
            "research": results,
            "timestamp": results["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Deep research error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class AutoPilotToggle(BaseModel):
    enabled: bool

class AutoPilotStatus(BaseModel):
    enabled: bool
    last_action: Optional[str] = None
    last_run: Optional[str] = None

# Auto-pilot state (in production, use database)
autopilot_state = {
    "enabled": False,
    "last_action": None,
    "last_run": None
}

@api_router.post("/ai/autopilot/toggle")
async def toggle_autopilot(toggle: AutoPilotToggle):
    """Enable/Disable Auto-Pilot"""
    autopilot_state["enabled"] = toggle.enabled
    autopilot_state["last_run"] = str(datetime.utcnow()) if toggle.enabled else None
    
    return AutoPilotStatus(**autopilot_state)

@api_router.get("/ai/autopilot/status")
async def get_autopilot_status():
    """Get Auto-Pilot status"""
    return AutoPilotStatus(**autopilot_state)

@api_router.post("/ai/autopilot/analyze")
async def autopilot_analyze():
    """
    Auto-Pilot Analysis - AIs suggest trades
    Max 10% of portfolio per trade
    """
    try:
        if not autopilot_state["enabled"]:
            return {
                "success": False,
                "message": "Auto-pilot is disabled"
            }
        
        # Get portfolio context
        try:
            if trading_client:
                account = trading_client.get_account()
                positions = trading_client.get_all_positions()
                portfolio_value = float(account.portfolio_value)
                portfolio_context = f"Cash: ${float(account.cash):.2f}, Total Portfolio: ${portfolio_value:.2f}"
                
                # Get market data for top positions
                market_data = {
                    "portfolio_value": portfolio_value,
                    "positions": [
                        {
                            "symbol": pos.symbol,
                            "quantity": float(pos.qty),
                            "value": float(pos.market_value),
                            "pl_percent": float(pos.unrealized_plpc) * 100
                        }
                        for pos in positions[:5]
                    ]
                }
            else:
                portfolio_context = "Paper trading account"
                market_data = {"portfolio_value": 100000, "positions": []}
        except:
            portfolio_context = "Paper trading account"
            market_data = {"portfolio_value": 100000, "positions": []}
        
        # Get multi-agent system
        multi_agent = get_multi_agent_system()
        
        # Run auto-pilot analysis
        results = await multi_agent.auto_pilot_analyze(
            portfolio_context=portfolio_context,
            market_data=market_data
        )
        
        # Save analysis
        autopilot_state["last_action"] = results.get("recommendation", "HOLD")
        autopilot_state["last_run"] = str(datetime.utcnow())
        
        # Save to database
        analysis_doc = {
            "results": results,
            "portfolio_context": portfolio_context,
            "market_data": market_data,
            "timestamp": datetime.utcnow()
        }
        await db.autopilot_analysis.insert_one(analysis_doc)
        
        return {
            "success": True,
            "analysis": results,
            "recommendation": results.get("recommendation"),
            "consensus_strength": results.get("consensus_strength"),
            "max_trade_size_usd": market_data["portfolio_value"] * 0.1  # 10% max
        }
        
    except Exception as e:
        logger.error(f"Auto-pilot analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ NEUE AI ENDPOINTS ============

@api_router.get("/ai/test")
async def test_ai():
    """Test endpoint"""
    return {"success": True, "message": "AI Endpoints funktionieren!"}

@api_router.get("/ai/stats")
async def get_ai_stats():
    """KI-Statistiken"""
    try:
        system = get_enhanced_system()
        stats = system.get_system_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============ AUTONOME TRADING ENDPOINTS ============

from trading_controller import get_trading_controller, TradingMode
from autopilot_scheduler import get_autopilot_scheduler

@api_router.post("/autonomous/start-cycle")
async def start_trading_cycle():
    """Startet einen Trading-Zyklus mit allen Agenten"""
    try:
        controller = get_trading_controller(trading_client, data_client)
        if not controller:
            raise HTTPException(status_code=500, detail="Controller nicht initialisiert")
        
        results = await controller.run_trading_cycle()
        
        # Speicher in DB
        await db.trading_cycles.insert_one({
            **results,
            'saved_at': datetime.utcnow()
        })
        
        return {"success": True, "results": results}
    except Exception as e:
        logger.error(f"Trading cycle error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/autonomous/status")
async def get_autonomous_status():
    """Status der autonomen Agenten"""
    try:
        controller = get_trading_controller(trading_client, data_client)
        if not controller:
            return {"success": False, "error": "Controller nicht initialisiert"}
        
        return {"success": True, "status": controller.get_status()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@api_router.get("/autonomous/leaderboard")
async def get_leaderboard():
    """Performance-Ranking der Agenten"""
    try:
        controller = get_trading_controller(trading_client, data_client)
        if not controller:
            return {"success": False, "error": "Controller nicht initialisiert"}
        
        return {"success": True, "leaderboard": controller.get_leaderboard()}
    except Exception as e:
        return {"success": False, "error": str(e)}

class ModeChangeRequest(BaseModel):
    mode: str  # "solo", "consensus", "guided"

@api_router.post("/autonomous/set-mode")
async def set_trading_mode(request: ModeChangeRequest):
    """Trading-Modus ändern"""
    try:
        controller = get_trading_controller(trading_client, data_client)
        if not controller:
            raise HTTPException(status_code=500, detail="Controller nicht initialisiert")
        
        controller.mode = TradingMode(request.mode)
        return {"success": True, "mode": request.mode}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class ConstraintsRequest(BaseModel):
    constraints: List[str]

@api_router.post("/autonomous/set-constraints")
async def set_user_constraints(request: ConstraintsRequest):
    """User-Vorgaben setzen (Guided Mode)"""
    try:
        controller = get_trading_controller(trading_client, data_client)
        if not controller:
            raise HTTPException(status_code=500, detail="Controller nicht initialisiert")
        
        controller.set_user_constraints(request.constraints)
        return {"success": True, "constraints": request.constraints}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class AutopilotConfigRequest(BaseModel):
    enabled: bool
    interval_minutes: int = 60  # Standard: jede Stunde

autopilot_config = {
    'enabled': False,
    'interval_minutes': 60,
    'last_run': None,
    'next_run': None
}

@api_router.post("/autonomous/autopilot/configure")
async def configure_autopilot(request: AutopilotConfigRequest):
    """Autopilot konfigurieren"""
    try:
        autopilot_config['enabled'] = request.enabled
        autopilot_config['interval_minutes'] = request.interval_minutes
        
        # Get scheduler
        scheduler = get_autopilot_scheduler()
        
        # Set trading controller if not set
        controller = get_trading_controller(trading_client, data_client)
        if controller:
            scheduler.set_trading_controller(controller)
            scheduler.set_trading_client(trading_client)
        
        if request.enabled:
            # Start scheduler
            success = scheduler.start_autopilot(request.interval_minutes)
            if success:
                next_run = scheduler.get_next_run()
                autopilot_config['next_run'] = next_run.isoformat() if next_run else None
                autopilot_config['last_run'] = None
                logger.info(f"✅ Autopilot aktiviert - {request.interval_minutes}min Intervall")
            else:
                raise HTTPException(status_code=500, detail="Scheduler konnte nicht gestartet werden")
        else:
            # Stop scheduler
            scheduler.stop_autopilot()
            autopilot_config['next_run'] = None
            logger.info("⏸️  Autopilot deaktiviert")
        
        return {"success": True, "config": autopilot_config}
    except Exception as e:
        logger.error(f"Autopilot config error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/autonomous/autopilot/status")
async def get_autonomous_autopilot_status():
    """Autopilot-Status abrufen"""
    scheduler = get_autopilot_scheduler()
    scheduler_status = scheduler.get_status()
    
    # Update next_run from actual scheduler
    if scheduler_status['next_run']:
        autopilot_config['next_run'] = scheduler_status['next_run']
    
    return {
        "success": True, 
        "config": autopilot_config,
        "scheduler_status": scheduler_status
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize autopilot scheduler on startup"""
    logger.info("🚀 Initializing Autopilot Scheduler...")
    scheduler = get_autopilot_scheduler()
    
    # Set trading client for market checks
    if trading_client:
        scheduler.set_trading_client(trading_client)
    
    # Initialize trading controller
    controller = get_trading_controller(trading_client, data_client)
    if controller:
        scheduler.set_trading_controller(controller)
    
    # Restore autopilot config from DB
    try:
        saved_config = await db.autopilot_config.find_one({"_id": "main"})
        if saved_config and saved_config.get('enabled'):
            autopilot_config['enabled'] = saved_config['enabled']
            autopilot_config['interval_minutes'] = saved_config['interval_minutes']
            
            # Restart scheduler
            scheduler.start_autopilot(saved_config['interval_minutes'])
            logger.info(f"✅ Autopilot wiederhergestellt - {saved_config['interval_minutes']}min Intervall")
    except Exception as e:
        logger.error(f"Fehler beim Wiederherstellen des Autopilots: {e}")
    
    logger.info("✅ Autopilot Scheduler ready")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("Shutting down services...")
    
    # Shutdown scheduler
    scheduler = get_autopilot_scheduler()
    scheduler.shutdown()
    
    # Close DB
    client.close()
    
    logger.info("Services shut down complete")
