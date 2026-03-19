import torch
from transformers import pipeline
from typing import Dict, List
import re


class SentimentAnalyzer:
    """Analyseur de sentiment multilingue avec XLM-RoBERTa"""
    
    # Mapping des labels vers français
    LABEL_MAP = {
        "joy": "joie",
        "anger": "colere",
        "sadness": "tristesse",
        "fear": "peur",
        "surprise": "surprise",
        "disgust": "degout",
        "neutral": "neutre",
        # Labels alternatifs selon les modèles
        "happy": "joie",
        "angry": "colere",
        "sad": "tristesse",
        "scared": "peur",
        "love": "joie",
        "optimism": "joie",
        "pessimism": "tristesse",
    }
    
    LABELS = ["joie", "colere", "tristesse", "peur", "surprise", "degout", "neutre"]
    
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        
        # Modèle multilingue pour les émotions
        self.classifier = pipeline(
            "text-classification",
            model="MilaNLProc/xlm-emo-t",
            top_k=None,
            device=self.device
        )
    
    def preprocess(self, text: str) -> str:
        """Nettoie le texte du tweet"""
        # Supprimer URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        # Supprimer mentions
        text = re.sub(r'@\w+', '', text)
        # Supprimer hashtags (garder le mot)
        text = re.sub(r'#(\w+)', r'\1', text)
        # Normaliser espaces
        text = ' '.join(text.split())
        return text.strip()[:512]
    
    def predict(self, text: str) -> Dict[str, float]:
        """Prédit le sentiment d'un texte"""
        clean_text = self.preprocess(text)
        
        if not clean_text:
            return {label: 0.0 for label in self.LABELS}
        
        results = self.classifier(clean_text)[0]
        
        # Initialiser tous les scores à 0
        scores = {label: 0.0 for label in self.LABELS}
        
        # Convertir les résultats
        for item in results:
            label_en = item["label"].lower()
            label_fr = self.LABEL_MAP.get(label_en, "neutre")
            # Additionner si plusieurs labels mappent vers le même
            scores[label_fr] = max(scores[label_fr], round(item["score"], 4))
        
        return scores
    
    def predict_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """Prédit le sentiment pour plusieurs textes"""
        clean_texts = [self.preprocess(t) for t in texts]
        clean_texts = [t if t else "text" for t in clean_texts]
        
        results = self.classifier(clean_texts)
        
        all_scores = []
        for result in results:
            scores = {label: 0.0 for label in self.LABELS}
            for item in result:
                label_en = item["label"].lower()
                label_fr = self.LABEL_MAP.get(label_en, "neutre")
                scores[label_fr] = max(scores[label_fr], round(item["score"], 4))
            all_scores.append(scores)
        
        return all_scores
    
    def get_dominant_sentiment(self, scores: Dict[str, float]) -> tuple[str, float]:
        """Retourne le sentiment dominant et son score"""
        dominant = max(scores, key=scores.get)
        return dominant, scores[dominant]


# Singleton
_analyzer = None

def get_analyzer() -> SentimentAnalyzer:
    """Retourne l'instance singleton de l'analyseur"""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer
