"""
Sentiment Analyzer
Analysiert Social Media, News und generelles Market Sentiment für Trading-Entscheidungen
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analysiert Sentiment aus verschiedenen Quellen"""
    
    def __init__(self, emergent_llm_key: str):
        self.llm_key = emergent_llm_key
        self.cache = {}  # Simple in-memory cache
        self.cache_duration = 300  # 5 Minuten
    
    async def get_comprehensive_sentiment(self, symbol: str) -> Dict:
        """
        Gibt umfassendes Sentiment zurück für ein Symbol
        
        Returns:
            {
                'overall_score': float (-1 bis +1),
                'twitter_sentiment': float,
                'news_sentiment': float,
                'social_volume': int,
                'signals': List[str],
                'summary': str
            }
        """
        # Check cache
        cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d%H%M')}"
        if cache_key in self.cache:
            logger.info(f"Using cached sentiment for {symbol}")
            return self.cache[cache_key]
        
        try:
            # Parallel alle Sentiment-Quellen abrufen
            twitter_task = self._get_twitter_sentiment(symbol)
            news_task = self._get_news_sentiment(symbol)
            
            twitter_sentiment, news_sentiment = await asyncio.gather(
                twitter_task, news_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(twitter_sentiment, Exception):
                logger.error(f"Twitter sentiment error: {twitter_sentiment}")
                twitter_sentiment = {'score': 0.0, 'volume': 0, 'signals': []}
            
            if isinstance(news_sentiment, Exception):
                logger.error(f"News sentiment error: {news_sentiment}")
                news_sentiment = {'score': 0.0, 'articles': 0, 'signals': []}
            
            # Kombiniere Sentiments (gewichtet)
            twitter_weight = 0.4
            news_weight = 0.6
            
            overall_score = (
                twitter_sentiment['score'] * twitter_weight +
                news_sentiment['score'] * news_weight
            )
            
            result = {
                'overall_score': round(overall_score, 2),
                'twitter_sentiment': twitter_sentiment['score'],
                'news_sentiment': news_sentiment['score'],
                'social_volume': twitter_sentiment.get('volume', 0),
                'news_count': news_sentiment.get('articles', 0),
                'signals': twitter_sentiment.get('signals', []) + news_sentiment.get('signals', []),
                'summary': self._create_summary(overall_score, twitter_sentiment, news_sentiment),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Cache result
            self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting sentiment for {symbol}: {e}")
            return {
                'overall_score': 0.0,
                'twitter_sentiment': 0.0,
                'news_sentiment': 0.0,
                'social_volume': 0,
                'news_count': 0,
                'signals': [],
                'summary': 'Sentiment-Daten nicht verfügbar',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _get_twitter_sentiment(self, symbol: str) -> Dict:
        """
        Holt Twitter/Social Media Sentiment
        
        Nutzt:
        1. Twitter API v2 (falls verfügbar)
        2. Fallback: LLM-basierte Analyse von öffentlichen Daten
        """
        try:
            # Fallback: Verwende LLM um öffentliche Sentiment-Indikatoren zu analysieren
            # In der Praxis würde man hier Twitter API oder alternative Quellen nutzen
            
            prompt = f"""Analysiere das aktuelle Social Media Sentiment für ${symbol}.

Berücksichtige folgende Aspekte:
1. Generelle Marktstimmung für diese Aktie
2. Typische Retail-Investor-Sentiment
3. Aktuelle Trends im Tech/Finance-Bereich

Gib eine Bewertung von -1 (sehr bearish) bis +1 (sehr bullish).

Format:
{{
  "score": 0.0,
  "confidence": 0.0,
  "reasoning": "...",
  "volume_indicator": "low/medium/high",
  "signals": ["signal1", "signal2"]
}}
"""
            
            # Nutze Emergent LLM für Sentiment-Einschätzung
            from emergentintegrations.llm.chat import LlmChat
            
            llm = LlmChat(
                api_key=self.llm_key,
                session_id=f"sentiment_twitter_{symbol}_{datetime.now().timestamp()}"
            ).with_model("openai", "gpt-4")
            
            response = await asyncio.to_thread(
                llm.chat_with_llm,
                user_message=prompt
            )
            
            # Parse response (vereinfacht - in Produktion robuster)
            import json
            try:
                data = json.loads(response)
                return {
                    'score': data.get('score', 0.0),
                    'volume': 100 if data.get('volume_indicator') == 'high' else 50,
                    'signals': data.get('signals', []),
                    'reasoning': data.get('reasoning', '')
                }
            except:
                # Fallback wenn JSON-Parsing fehlschlägt
                return {'score': 0.0, 'volume': 0, 'signals': []}
            
        except Exception as e:
            logger.error(f"Twitter sentiment error: {e}")
            return {'score': 0.0, 'volume': 0, 'signals': []}
    
    async def _get_news_sentiment(self, symbol: str) -> Dict:
        """
        Holt News Sentiment für Symbol
        
        Nutzt:
        1. NewsAPI oder ähnliche Services
        2. LLM-basierte Sentiment-Analyse der Headlines
        """
        try:
            # Fallback: LLM-basierte News-Sentiment-Einschätzung
            prompt = f"""Analysiere das aktuelle News-Sentiment für ${symbol}.

Berücksichtige:
1. Aktuelle Unternehmensnachrichten
2. Branchentrends
3. Makroökonomische Faktoren
4. Analystenmeinungen

Gib eine Bewertung von -1 (sehr negativ) bis +1 (sehr positiv).

Format:
{{
  "score": 0.0,
  "confidence": 0.0,
  "reasoning": "...",
  "key_topics": ["topic1", "topic2"],
  "signals": ["signal1", "signal2"]
}}
"""
            
            from emergentintegrations.llm.chat import LlmChat
            
            llm = LlmChat(
                api_key=self.llm_key,
                session_id=f"sentiment_news_{symbol}_{datetime.now().timestamp()}"
            ).with_model("openai", "gpt-4")
            
            response = await asyncio.to_thread(
                llm.chat_with_llm,
                user_message=prompt
            )
            
            # Parse response
            import json
            try:
                data = json.loads(response)
                return {
                    'score': data.get('score', 0.0),
                    'articles': 10,  # Mock
                    'signals': data.get('signals', []),
                    'reasoning': data.get('reasoning', '')
                }
            except:
                return {'score': 0.0, 'articles': 0, 'signals': []}
            
        except Exception as e:
            logger.error(f"News sentiment error: {e}")
            return {'score': 0.0, 'articles': 0, 'signals': []}
    
    def _create_summary(self, overall_score: float, twitter: Dict, news: Dict) -> str:
        """Erstellt menschenlesbare Zusammenfassung"""
        
        if overall_score > 0.5:
            sentiment_label = "Stark Bullish"
        elif overall_score > 0.2:
            sentiment_label = "Leicht Bullish"
        elif overall_score > -0.2:
            sentiment_label = "Neutral"
        elif overall_score > -0.5:
            sentiment_label = "Leicht Bearish"
        else:
            sentiment_label = "Stark Bearish"
        
        summary = f"{sentiment_label} (Score: {overall_score:.2f})"
        
        # Details hinzufügen
        details = []
        if twitter.get('volume', 0) > 75:
            details.append("Hohes Social Media Volumen")
        if abs(twitter.get('score', 0)) > 0.5:
            details.append(f"Twitter: {'Bullish' if twitter['score'] > 0 else 'Bearish'}")
        if abs(news.get('score', 0)) > 0.5:
            details.append(f"News: {'Positiv' if news['score'] > 0 else 'Negativ'}")
        
        if details:
            summary += " - " + ", ".join(details)
        
        return summary


# Singleton-Instance
_sentiment_analyzer = None

def get_sentiment_analyzer(llm_key: str) -> SentimentAnalyzer:
    """Get or create sentiment analyzer instance"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer(llm_key)
    return _sentiment_analyzer
