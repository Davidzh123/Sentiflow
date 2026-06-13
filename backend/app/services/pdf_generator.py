"""
Générateur de PDF pour les dashboards SentiFlow.
Utilise fpdf2 (pas de dépendance lourde).
"""
import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sentiflow.pdf")

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


def generate_dashboard_pdf(
    title: str,
    question: str,
    answer: str,
    sources: List[Dict[str, Any]],
    metrics: Optional[Dict[str, Any]] = None,
    sentiment_stats: Optional[Dict[str, Any]] = None,
) -> Optional[bytes]:
    """
    Génère un PDF du dashboard/rapport.
    Retourne les bytes du PDF ou None si fpdf2 n'est pas installé.
    """
    if not FPDF_AVAILABLE:
        logger.warning("[PDF] fpdf2 non installé. pip install fpdf2")
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Titre
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "SentiFlow - Rapport d'Analyse", ln=True, align="C")
    pdf.ln(5)

    # Date
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generé le {datetime.utcnow().strftime('%d/%m/%Y a %H:%M')}", ln=True, align="C")
    pdf.ln(10)

    # Question
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Question :", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, _safe_text(question))
    pdf.ln(5)

    # Réponse
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Reponse :", ln=True)
    pdf.set_font("Helvetica", "", 10)
    # Tronquer la réponse si trop longue
    answer_text = _safe_text(answer[:2000])
    pdf.multi_cell(0, 5, answer_text)
    pdf.ln(5)

    # Stats sentiments
    if sentiment_stats:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Distribution des sentiments :", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for sent, count in sentiment_stats.items():
            pdf.cell(0, 6, f"  - {sent} : {count}", ln=True)
        pdf.ln(5)

    # Sources
    if sources:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, f"Sources ({len(sources)} tweets) :", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for i, s in enumerate(sources[:10], 1):
            author = s.get("author", "?")
            sentiment = s.get("sentiment", "?")
            confidence = s.get("confidence", 0)
            text = _safe_text(str(s.get("text", ""))[:150])
            pdf.multi_cell(0, 4, f"{i}. @{author} | {sentiment} ({confidence:.0%}) | \"{text}\"")
            pdf.ln(2)

    # Métriques
    if metrics:
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Metriques RAG :", ln=True)
        pdf.set_font("Helvetica", "", 9)
        retrieval = metrics.get("retrieval", {})
        timing = metrics.get("timing", {})
        pdf.cell(0, 5, f"  Relevance: {retrieval.get('relevance', 0):.4f}", ln=True)
        pdf.cell(0, 5, f"  Coherence: {retrieval.get('coherence', 0):.4f}", ln=True)
        pdf.cell(0, 5, f"  MRR: {retrieval.get('mrr', 0):.4f}", ln=True)
        pdf.cell(0, 5, f"  Temps total: {timing.get('total', 0):.2f}s", ln=True)

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "SentiFlow - RAG from scratch + MCP + Groq LLM", ln=True, align="C")

    return pdf.output()


def _safe_text(text: str) -> str:
    """Nettoie le texte pour le PDF (enlève les caractères non-latin1)."""
    # fpdf2 avec Helvetica ne supporte que latin-1
    result = ""
    for ch in text:
        try:
            ch.encode("latin-1")
            result += ch
        except (UnicodeEncodeError, UnicodeDecodeError):
            result += "?"
    return result
