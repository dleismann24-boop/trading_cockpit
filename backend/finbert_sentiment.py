"""
FinBERT Sentiment Analyzer
Spezialisiertes Finanz-NLP-Modell für präzise Sentiment-Analyse
"""
import logging
from typing import Dict, List
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

logger = logging.getLogger(__name__)


class FinBERTSentiment:
    """FinBERT-basierte Sentiment-Analyse für Finanztexte"""
    
    def __init__(self):
        self.model_name = "ProsusAI/finbert"
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.labels = ['positive', 'negative', 'neutral']
        
        logger.info(f"FinBERT wird initialisiert (Device: {self.device})...")
        self._load_model()
    
    def _load_model(self):
        """Lädt FinBERT Modell und Tokenizer"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("✅ FinBERT erfolgreich geladen!")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von FinBERT: {e}")
            self.model = None
            self.tokenizer = None
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analysiert einen einzelnen Text
        
        Args:
            text: Finanztext (News, Tweet, etc.)
        
        Returns:
            {
                'sentiment': 'positive' | 'negative' | 'neutral',
                'score': float (0-1),
                'confidence': float (0-1),
                'probabilities': {
                    'positive': float,
                    'negative': float,
                    'neutral': float
                }
            }
        """
        if not self.model or not self.tokenizer:
            logger.warning("FinBERT nicht verfügbar - Fallback")
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'probabilities': {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
            }
        
        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)
            
            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Get probabilities
            probs = predictions[0].cpu().numpy()
            
            # Get dominant sentiment
            max_idx = np.argmax(probs)
            sentiment = self.labels[max_idx]
            confidence = float(probs[max_idx])
            
            # Calculate normalized score (-1 bis +1)
            # positive = +1, negative = -1, neutral = 0
            score = float(probs[0] - probs[1])  # positive - negative
            
            result = {
                'sentiment': sentiment,
                'score': round(score, 3),
                'confidence': round(confidence, 3),
                'probabilities': {
                    'positive': round(float(probs[0]), 3),
                    'negative': round(float(probs[1]), 3),
                    'neutral': round(float(probs[2]), 3)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei FinBERT-Analyse: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'probabilities': {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
            }
    
    def analyze_texts(self, texts: List[str]) -> Dict:
        """
        Analysiert mehrere Texte und aggregiert
        
        Args:
            texts: Liste von Finanztexten
        
        Returns:
            {
                'overall_sentiment': 'positive' | 'negative' | 'neutral',
                'overall_score': float (-1 bis +1),
                'avg_confidence': float (0-1),
                'individual_results': List[Dict],
                'sentiment_distribution': {
                    'positive': int,
                    'negative': int,
                    'neutral': int
                }
            }
        """
        if not texts:
            return {
                'overall_sentiment': 'neutral',
                'overall_score': 0.0,
                'avg_confidence': 0.0,
                'individual_results': [],
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0}
            }
        
        # Analyze all texts
        results = [self.analyze_text(text) for text in texts]
        
        # Aggregate
        scores = [r['score'] for r in results]
        confidences = [r['confidence'] for r in results]
        sentiments = [r['sentiment'] for r in results]
        
        overall_score = np.mean(scores)
        avg_confidence = np.mean(confidences)
        
        # Determine overall sentiment
        if overall_score > 0.2:
            overall_sentiment = 'positive'
        elif overall_score < -0.2:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        # Count distribution
        sentiment_distribution = {
            'positive': sentiments.count('positive'),
            'negative': sentiments.count('negative'),
            'neutral': sentiments.count('neutral')
        }
        
        return {
            'overall_sentiment': overall_sentiment,
            'overall_score': round(float(overall_score), 3),
            'avg_confidence': round(float(avg_confidence), 3),
            'individual_results': results,
            'sentiment_distribution': sentiment_distribution,
            'text_count': len(texts)
        }
    
    def analyze_news_headlines(self, headlines: List[str]) -> Dict:
        """
        Spezialisierte Analyse für News-Headlines
        
        Args:
            headlines: Liste von News-Headlines
        
        Returns:
            Aggregiertes Sentiment-Ergebnis
        """
        result = self.analyze_texts(headlines)
        
        # Add interpretation
        score = result['overall_score']
        if score > 0.5:
            interpretation = "🟢 Sehr positiv - Starke Kaufsignale"
        elif score > 0.2:
            interpretation = "🟢 Leicht positiv - Gute Aussichten"
        elif score < -0.5:
            interpretation = "🔴 Sehr negativ - Vorsicht geboten"
        elif score < -0.2:
            interpretation = "🔴 Leicht negativ - Risiko vorhanden"
        else:
            interpretation = "⚪ Neutral - Keine klare Richtung"
        
        result['interpretation'] = interpretation
        
        return result


# Global FinBERT Instance
_finbert = None

def get_finbert() -> FinBERTSentiment:
    """Get or create global FinBERT instance"""
    global _finbert
    if _finbert is None:
        _finbert = FinBERTSentiment()
    return _finbert
