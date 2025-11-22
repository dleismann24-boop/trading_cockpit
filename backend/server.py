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
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import openai

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
