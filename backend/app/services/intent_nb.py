"""
Classifieur d'intention FROM SCRATCH (Naïve Bayes multinomial) pour le routage
des questions de l'assistant.

- Algorithme : Naïve Bayes (théorème de Bayes + hypothèse d'indépendance des mots).
- Modèle : probabilités P(mot|action) et P(action) apprises sur TRAINING_DATA.

Il décide de l'ACTION à effectuer :
  count     -> compter des tweets                 (mode base de données)
  stats     -> lister cibles / stats globales     (mode base de données)
  sentiment -> sentiment / résumé / opinion        (mode RAG)
  compare   -> comparer plusieurs cibles           (mode RAG)
  timeline  -> évolution dans le temps             (mode RAG)
  examples  -> exemples de tweets                  (mode RAG)
  collect   -> collecter / ajouter une cible       (mode agent)

Aucune dépendance externe (pas de sklearn). 100% maison.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict


def _normalize(text: str) -> str:
    text = str(text or "").lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return text


def _tokenize(text: str) -> list[str]:
    # On retire les cibles (#x / @x) : elles ne portent pas l'intention, juste l'entité.
    text = re.sub(r"[#@][\w-]+", " ", _normalize(text))
    return re.findall(r"[a-z0-9]+", text)


# ============================================
# JEU D'ENTRAÎNEMENT (question -> action)
# ============================================
TRAINING_DATA: list[tuple[str, str]] = [
    # ---- count ----
    ("combien de tweets", "count"),
    ("combien de tweets sur ce hashtag", "count"),
    ("il y a combien de tweets", "count"),
    ("il y en a combien", "count"),
    ("nombre de tweets", "count"),
    ("nombre de tweets collectes", "count"),
    ("quel est le nombre de tweets", "count"),
    ("combien de posts au total", "count"),
    ("ca fait combien de tweets", "count"),
    ("total de tweets en base", "count"),
    ("how many tweets", "count"),
    ("combien de tweets analyses", "count"),
    ("quel volume de tweets", "count"),
    ("combien tu en as collecte", "count"),

    # ---- stats / list_targets ----
    ("quelles sont mes cibles", "stats"),
    ("liste de mes cibles", "stats"),
    ("montre mes cibles", "stats"),
    ("quelles cibles je suis", "stats"),
    ("mes hashtags suivis", "stats"),
    ("statistiques globales", "stats"),
    ("vue d ensemble de ma base", "stats"),
    ("c est quoi mes cibles", "stats"),
    ("quels comptes je surveille", "stats"),
    ("etat de la base de donnees", "stats"),
    ("resume de mes donnees", "stats"),

    # ---- sentiment / résumé ----
    ("quel est le sentiment", "sentiment"),
    ("quel est le sentiment dominant", "sentiment"),
    ("quel sentiment sur ce hashtag", "sentiment"),
    ("comment les gens reagissent", "sentiment"),
    ("est ce que les gens aiment", "sentiment"),
    ("quelle est l opinion sur", "sentiment"),
    ("fais une synthese des sentiments", "sentiment"),
    ("resume l opinion", "sentiment"),
    ("donne moi le ressenti general", "sentiment"),
    ("les gens sont ils contents", "sentiment"),
    ("c est positif ou negatif", "sentiment"),
    ("pourquoi les gens sont en colere", "sentiment"),
    ("quel est l avis du public", "sentiment"),
    ("analyse le sentiment", "sentiment"),
    ("ca dit quoi les gens", "sentiment"),
    ("what do people think", "sentiment"),
    ("le sentiment le plus present", "sentiment"),

    # ---- compare ----
    ("compare ces deux hashtags", "compare"),
    ("compare les sentiments", "compare"),
    ("comparaison entre les comptes", "compare"),
    ("lequel est le plus positif", "compare"),
    ("qui a le plus de colere", "compare"),
    ("quelle cible est la mieux percue", "compare"),
    ("difference entre les deux", "compare"),
    ("versus", "compare"),
    ("oppose les deux sujets", "compare"),
    ("lequel est meilleur", "compare"),
    ("compare a", "compare"),

    # ---- timeline ----
    ("evolution des sentiments", "timeline"),
    ("comment ca evolue dans le temps", "timeline"),
    ("tendance sur les derniers jours", "timeline"),
    ("est ce que la colere augmente", "timeline"),
    ("est ce que la joie baisse", "timeline"),
    ("montre l evolution", "timeline"),
    ("analyse temporelle", "timeline"),
    ("evolution sur 14 jours", "timeline"),
    ("comment ca a change cette semaine", "timeline"),
    ("la tendance recente", "timeline"),

    # ---- examples ----
    ("montre des exemples de tweets", "examples"),
    ("donne des tweets representatifs", "examples"),
    ("exemples de tweets negatifs", "examples"),
    ("montre moi les tweets les plus positifs", "examples"),
    ("quels tweets expliquent ce sentiment", "examples"),
    ("affiche quelques tweets", "examples"),
    ("des exemples concrets", "examples"),
    ("montre les tweets en colere", "examples"),

    # ---- collect ----
    ("recupere les tweets de ce hashtag", "collect"),
    ("collecte des tweets", "collect"),
    ("ajoute cette cible", "collect"),
    ("cree la cible et analyse", "collect"),
    ("va chercher des tweets", "collect"),
    ("recolte les derniers tweets", "collect"),
    ("scrape ce compte", "collect"),
    ("recupere et analyse", "collect"),
    ("ajoute le hashtag et collecte", "collect"),
    ("mets a jour les tweets", "collect"),
]


class NaiveBayesIntent:
    """Naïve Bayes multinomial codé à la main."""

    def __init__(self):
        self.word_counts: dict[str, Counter] = defaultdict(Counter)
        self.action_counts: Counter = Counter()
        self.action_token_totals: Counter = Counter()
        self.vocab: set[str] = set()
        self.total = 0
        self.fitted = False

    def fit(self, data: list[tuple[str, str]]) -> None:
        for text, action in data:
            tokens = _tokenize(text)
            if not tokens:
                continue
            self.action_counts[action] += 1
            self.total += 1
            for tok in tokens:
                self.word_counts[action][tok] += 1
                self.action_token_totals[action] += 1
                self.vocab.add(tok)
        self.fitted = True

    def predict(self, question: str) -> tuple[str, float]:
        tokens = _tokenize(question)
        if not tokens or not self.fitted:
            return "sentiment", 0.0  # défaut raisonnable

        vocab_size = max(len(self.vocab), 1)
        scores: dict[str, float] = {}
        for action in self.action_counts:
            # log P(action)
            score = math.log(self.action_counts[action] / self.total)
            denom = self.action_token_totals[action] + vocab_size
            for tok in tokens:
                count = self.word_counts[action][tok]
                # lissage de Laplace
                score += math.log((count + 1) / denom)
            scores[action] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_action, best_score = ranked[0]
        # Confiance = écart (en proba) entre top1 et top2
        if len(ranked) >= 2:
            gap = best_score - ranked[1][1]
            confidence = round(min(1.0, gap / 3.0), 3)  # normalisation douce
        else:
            confidence = 1.0
        return best_action, confidence


# Instance entraînée au démarrage (le "modèle")
INTENT_NB = NaiveBayesIntent()
INTENT_NB.fit(TRAINING_DATA)


# Mapping action -> mode de l'assistant
ACTION_TO_MODE = {
    "count": "database",
    "stats": "database",
    "sentiment": "rag",
    "compare": "rag",
    "timeline": "rag",
    "examples": "rag",
    "collect": "agent",
}


def classify_question(question: str) -> tuple[str, str, float]:
    """Retourne (action, mode, confiance)."""
    action, confidence = INTENT_NB.predict(question)
    mode = ACTION_TO_MODE.get(action, "rag")
    return action, mode, confidence
