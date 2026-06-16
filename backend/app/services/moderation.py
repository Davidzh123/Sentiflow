"""
Garde-fou (modération) pour les questions envoyées à l'assistant / RAG.
Bloque les demandes nuisibles, extrêmes ou hors-cadre avant tout traitement.
Approche from scratch : normalisation + listes de motifs, zéro dépendance.

Deux niveaux :
- une liste de base (catégories sensibles) codée ici ;
- des mots/thèmes personnalisés ajoutés par l'admin (passés via `extra_words`).
"""

from __future__ import annotations

import re
import unicodedata


def _normalize(text: str) -> str:
    text = str(text or "").lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text


# Catégories interdites -> motifs (mots entiers ou expressions).
BLOCKLIST: dict[str, list[str]] = {
    "violence": [
        "comment tuer", "comment tue", "how to kill", "assassiner", "egorger", "decapiter",
        "massacre", "faire du mal a quelqu", "agresser quelqu", "torturer", "lyncher", "meurtre",
    ],
    "armes_explosifs": [
        "fabriquer une bombe", "faire une bombe", "make a bomb", "build a bomb", "explosif", "explosifs",
        "fabriquer une arme", "arme a feu maison", "ghost gun", "cocktail molotov", "fabriquer un fusil",
        "kalachnikov",
    ],
    "terrorisme": [
        "terrorisme", "terroriste", "terroristes", "attentat", "attentats", "djihad", "djihadiste",
        "daesh", "etat islamique", "rejoindre daesh",
    ],
    "auto_mutilation": [
        "me suicider", "comment me tuer", "methode suicide", "suicide", "how to kill myself", "automutilation",
        "me faire du mal", "comment se suicider", "envie d en finir", "scarification",
    ],
    "drogues": [
        "fabriquer de la drogue", "synthetiser", "faire de la meth", "fabriquer de la meth", "methamphetamine",
        "cultiver du cannabis pour vendre", "fabriquer de l ecstasy", "produire de la cocaine", "trafic de drogue",
    ],
    "cyber_malveillant": [
        "pirater", "hacker un compte", "voler un mot de passe", "voler des donnees",
        "ddos", "ransomware", "creer un virus", "creer un malware", "carte bancaire volee",
    ],
    "haine_discrimination": [
        "sale race", "exterminer les", "mort aux", "tous les juifs", "tous les arabes", "tous les noirs",
        "propos racistes", "purifier la race", "nazisme", "genocide", "suprematie blanche",
    ],
    "contenu_sexuel_extreme": [
        "pedophile", "pedophilie", "mineur sexuel", "enfant sexuel", "child porn", "porno",
        "pornographique", "viol", "scene de viol", "zoophilie",
    ],
    "fraude": [
        "faux billet", "faux billets", "arnaquer", "monter une arnaque", "blanchir de l argent",
        "faux papiers", "fausse carte d identite", "carding",
    ],
}


def _matches(pattern: str, text: str) -> bool:
    """Mot entier si le motif est un seul mot, sous-chaîne si c'est une expression."""
    if " " in pattern:
        return pattern in text
    return re.search(r"\b" + re.escape(pattern) + r"\b", text) is not None


def check_question(question: str, extra_words: list[str] | None = None) -> tuple[bool, str | None, str | None]:
    """
    Retourne (autorisé, message_si_bloqué, catégorie).
    """
    q = _normalize(question)

    if len(q.strip()) < 3:
        return False, "Question trop courte.", "invalide"

    refus = (
        "Cette demande enfreint nos règles d'utilisation (contenu sensible, extrême ou hors cadre) "
        "et ne peut pas être traitée. SentiFlow analyse l'opinion publique sur des sujets, marques "
        "ou comptes — reformulez votre question dans ce cadre."
    )

    # Liste de base
    for category, patterns in BLOCKLIST.items():
        for p in patterns:
            if _matches(p, q):
                return False, refus, category

    # Mots/thèmes personnalisés de l'admin (sous-chaîne : l'admin choisit explicitement)
    for w in (extra_words or []):
        w_norm = _normalize(w).strip()
        if w_norm and w_norm in q:
            return False, refus, "personnalise"

    return True, None, None


def get_base_categories() -> dict[str, list[str]]:
    """Pour affichage admin : les catégories et exemples de la liste de base."""
    return {cat: words for cat, words in BLOCKLIST.items()}
