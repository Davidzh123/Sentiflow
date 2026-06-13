"""
Endpoint unifié : combine l'Agent LLM (lseillier) + RAG (from scratch).
Le planner décide automatiquement quel pipeline utiliser.
"""
import logging
import time as _time

from fastapi import APIRouter, Depends, HTTPException, Request as FastAPIRequest
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from backend.app.database import get_db
from backend.app.services.rag import chat as rag_chat, index_all_tweets

logger = logging.getLogger("sentiflow.assistant")

router = APIRouter(prefix="/assistant", tags=["Assistant Unifié"])


def _get_user_id_from_request(request: FastAPIRequest, db: Session) -> int:
    """Extraire le user_id du token JWT si présent, sinon user_id=1."""
    try:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            from backend.app.services.auth import decode_token
            return decode_token(token)
    except Exception:
        pass
    return 1


# Intentions qui déclenchent l'agent (collecte + dashboard)
AGENT_INTENTS = {"collect_analyze_summarize", "collect_analyze_examples"}

# Mots-clés qui forcent le mode agent (même si le planner se trompe)
AGENT_KEYWORDS = {"récupère", "recupere", "collecte", "collecter", "ajoute", "crée", "cree"}

# Mots-clés qui déclenchent une requête BDD
DB_KEYWORDS = {"mes cibles", "ma base", "combien de tweets", "quelles cibles", "mes données",
               "répartition", "langues", "statistiques globales", "cibles que j",
               "quoi comme cible", "les cibles", "en base"}

# Intentions qui déclenchent le RAG (recherche + réponse)
RAG_INTENTS = {"summarize", "compare", "timeline", "examples", "dashboard"}


class AssistantRequest(BaseModel):
    question: str = Field(..., min_length=3)
    enable_mcp: bool = True
    force_mode: Optional[str] = Field(
        default=None,
        description="Forcer un mode: 'agent' ou 'rag'. Si None, le planner décide."
    )


@router.post("/chat")
async def assistant_chat(
    request: AssistantRequest,
    raw_request: FastAPIRequest,
    db: Session = Depends(get_db),
):
    """
    Chat unifié : le planner LLM from scratch décide s'il faut :
    - Collecter des tweets (Agent) → stocke en BDD + retourne des stats
    - Répondre à une question (RAG) → cherche les tweets pertinents + génère une réponse

    Les deux pipelines travaillent ensemble.
    """
    _start_time = _time.time()
    question = request.question

    # Récupérer le user connecté
    user_id = _get_user_id_from_request(raw_request, db)

    logger.info(f"[ASSISTANT] Question: '{question[:80]}' (user_id={user_id})")

    # Essayer de récupérer l'utilisateur connecté (optionnel)
    try:
        from backend.app.services.auth import get_current_user_optional
        # On parse le token manuellement si présent
        pass
    except Exception:
        pass

    # Déterminer le mode (planner ou forcé)
    mode = request.force_mode
    plan = None

    if not mode:
        # Laisser le planner décider
        try:
            from backend.app.services.llm_from_scratch import get_planner
            planner = get_planner()
            plan = planner.plan(question)
            intent = plan.get("intent", "summarize")

            if intent in AGENT_INTENTS or plan.get("force_refresh", False):
                mode = "agent"
            elif intent == "query_database" or "query_database" in plan.get("actions", []):
                mode = "database"
            else:
                mode = "rag"
        except Exception:
            mode = "rag"

        # Fallback : si des mots-clés de collecte sont dans la question, forcer agent
        if mode == "rag":
            q_lower = question.lower()
            if any(kw in q_lower for kw in AGENT_KEYWORDS):
                mode = "agent"
            elif any(kw in q_lower for kw in DB_KEYWORDS):
                mode = "database"

    # ============================================
    # MODE DATABASE : interroge la BDD (rapide, pas de MCP)
    # ============================================
    if mode == "database":
        from backend.app.services.mcp_server import execute_tool as mcp_execute
        import asyncio

        # Déterminer le type de requête
        q_lower = question.lower()
        if "langue" in q_lower or "répartition des langue" in q_lower:
            query_type = "languages"
        elif "cible" in q_lower or "quelles" in q_lower or "quels sont" in q_lower:
            query_type = "targets"
        elif "combien" in q_lower or "nombre" in q_lower or "total" in q_lower:
            query_type = "tweet_count"
        elif "colère" in q_lower or "colere" in q_lower or "négatif" in q_lower or "compte" in q_lower:
            query_type = "anger_by_target"
        else:
            query_type = "targets"

        db_result = await mcp_execute("query_database", {"query_type": query_type})

        # Formater la réponse
        answer_parts = []
        if query_type == "targets":
            answer_parts.append(f"📊 {db_result.get('summary', '')}\n")
            for t in db_result.get("targets", []):
                answer_parts.append(f"• {t['name']} ({t['type']}) : {t['total_tweets']} tweets ({t['analyzed_tweets']} analysés)")
        elif query_type == "tweet_count":
            answer_parts.append(f"📊 Total : {db_result.get('total', 0)} tweets")
            answer_parts.append(f"   Analysés : {db_result.get('analyzed', 0)}")
            if db_result.get("pending", 0) > 0:
                answer_parts.append(f"   En attente : {db_result.get('pending', 0)}")
        elif query_type == "sentiment_stats":
            answer_parts.append("📊 Répartition des sentiments (tous tweets) :")
            for sent, count in sorted(db_result.get("distribution", {}).items(), key=lambda x: -x[1]):
                pct = db_result.get("percentages", {}).get(sent, "?")
                answer_parts.append(f"   • {sent} : {count} tweets ({pct})")
        elif query_type == "languages":
            answer_parts.append("📊 Répartition des langues :")
            for lang, count in sorted(db_result.get("distribution", {}).items(), key=lambda x: -x[1]):
                if count > 0:  # ne pas afficher les 0%
                    pct = db_result.get("percentages", {}).get(lang, "?")
                    answer_parts.append(f"   • {lang} : {count} tweets ({pct})")
        elif query_type == "anger_by_target":
            answer_parts.append("📊 Cibles avec le plus de tweets négatifs (colère/tristesse/peur) :")
            for item in db_result.get("results", []):
                answer_parts.append(f"   • {item['target']} : {item['negative_tweets']} tweets négatifs")
            if not db_result.get("results"):
                answer_parts.append("   Aucun tweet négatif trouvé.")

        return {
            "mode": "database",
            "answer": "\n".join(answer_parts),
            "db_result": db_result,
            "plan": plan,
        }

    # ============================================
    # MODE AGENT : collecte + stocke + dashboard
    # ============================================
    if mode == "agent":
        try:
            from backend.app.services.llm_agent import run_sentiflow_agent
            result = await run_sentiflow_agent(
                db=db,
                user_id=user_id,
                question=question,
                generate_dashboard=True,
                allow_auto_collect=True,
                allow_auto_analyze=True,
            )

            # Après la collecte, indexer pour que le RAG puisse utiliser les données
            index_all_tweets(db)

            return {
                "mode": "agent",
                "answer": result.get("answer", ""),
                "dashboard_id": result.get("dashboard_id"),
                "dashboard_url": result.get("dashboard_url"),
                "execution_log": result.get("execution_log", []),
                "plan": result.get("plan"),
                "model_info": result.get("model_info"),
                "targets": result.get("targets", []),
            }
        except Exception as e:
            # Si l'agent échoue, fallback sur le RAG
            mode = "rag"

    # ============================================
    # MODE RAG : recherche + MCP + génération
    # ============================================
    result = await rag_chat(
        db=db,
        question=question,
        target_id=None,
        enable_mcp=request.enable_mcp,
    )

    # Sauvegarder un dashboard généré pour le mode RAG aussi
    dashboard_id = None
    dashboard_url = None
    try:
        from backend.app.models.generated_dashboard import GeneratedDashboard
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        if sources and len(sources) >= 2:
            target_ids = list(set(s.get("target_id") for s in sources if s.get("target_id")))
            dashboard = GeneratedDashboard(
                user_id=user_id,
                title=f"RAG: {question[:80]}",
                question=question,
                answer=answer,
                target_ids=target_ids,
                config_json={
                    "source_question": question,
                    "target_ids": target_ids,
                    "mode": "rag",
                    "metrics": result.get("metrics"),
                },
                plan_json=plan,
            )
            db.add(dashboard)
            db.commit()
            db.refresh(dashboard)
            dashboard_id = dashboard.id
            dashboard_url = f"/dashboards/generated/{dashboard.id}"
    except Exception as e:
        logger.debug(f"[ASSISTANT] Dashboard save failed (OK): {e}")

    # Log + sauvegarde de la question
    _elapsed_ms = int((_time.time() - _start_time) * 1000)
    logger.info(f"[ASSISTANT] Mode={mode} | Intent={plan.get('intent') if plan else '?'} | {_elapsed_ms}ms")

    # Sauvegarder la question en BDD (pour ré-entraînement futur)
    try:
        from backend.app.models.question_log import QuestionLog
        log_entry = QuestionLog(
            question=question,
            intent_detected=plan.get("intent") if plan else None,
            mode_used="rag",
            targets_detected=plan.get("targets") if plan else None,
            response_time_ms=_elapsed_ms,
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.debug(f"[ASSISTANT] Log question échoué (table pas créée?): {e}")

    return {
        "mode": "rag",
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "total_retrieved": result.get("total_retrieved", 0),
        "mcp_used": result.get("mcp_used", False),
        "generator": result.get("generator"),
        "plan": result.get("plan") or plan,
        "metrics": result.get("metrics"),
        "dashboard_id": dashboard_id,
        "dashboard_url": dashboard_url,
    }


# ============================================
# FEEDBACK LOOP
# ============================================

class FeedbackRequest(BaseModel):
    question: str = Field(..., min_length=3)
    previous_answer: str
    feedback: str = Field(..., min_length=3, description="Ce qui ne va pas dans la réponse")
    regenerate_mode: str = Field(default="auto", description="'groq_only' ou 'full_pipeline' ou 'auto'")


@router.post("/feedback")
async def assistant_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
):
    """
    Feedback loop : l'utilisateur dit ce qui ne va pas → le LLM régénère.
    - groq_only : même données, meilleure rédaction
    - full_pipeline : refait tout (planner + RAG + MCP)
    - auto : décide selon le feedback
    """
    mode = request.regenerate_mode

    # Auto-detect : si le feedback mentionne "mauvaise cible" ou "pas les bons tweets" → full pipeline
    if mode == "auto":
        fb_lower = request.feedback.lower()
        if any(kw in fb_lower for kw in ["mauvaise cible", "mauvais", "pas les bons", "autre", "refais"]):
            mode = "full_pipeline"
        else:
            mode = "groq_only"

    if mode == "full_pipeline":
        # Relancer tout le pipeline
        result = await rag_chat(db=db, question=request.question, enable_mcp=True)
        return {
            "mode": "full_pipeline",
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "feedback_applied": request.feedback,
        }
    else:
        # Juste régénérer avec Groq en incluant le feedback
        from backend.app.services.rag import _generate_with_groq, settings
        groq_key = settings.groq_api_key
        if not groq_key:
            raise HTTPException(status_code=500, detail="Clé Groq non configurée")

        prompt = (
            f"L'utilisateur a posé cette question : {request.question}\n\n"
            f"Tu avais répondu : {request.previous_answer[:500]}\n\n"
            f"L'utilisateur n'est PAS satisfait. Son feedback : {request.feedback}\n\n"
            f"Régénère une meilleure réponse en tenant compte du feedback. "
            f"Sois plus précis, plus détaillé, et corrige ce qui ne va pas."
        )

        answer = _generate_with_groq(prompt, groq_key)
        return {
            "mode": "groq_only",
            "answer": answer or "Erreur lors de la régénération.",
            "feedback_applied": request.feedback,
        }


# ============================================
# EXPORT PDF DU DASHBOARD
# ============================================

class PdfRequest(BaseModel):
    question: str
    answer: str
    sources: list = []
    metrics: Optional[dict] = None


@router.post("/export-pdf")
async def export_pdf(request: PdfRequest):
    """
    Génère un PDF du dashboard/rapport à partir des données.
    """
    from backend.app.services.pdf_generator import generate_dashboard_pdf

    # Extraire les stats des sources
    sentiment_stats = {}
    for s in request.sources:
        sent = s.get("sentiment", "inconnu")
        sentiment_stats[sent] = sentiment_stats.get(sent, 0) + 1

    pdf_bytes = generate_dashboard_pdf(
        title="Rapport SentiFlow",
        question=request.question,
        answer=request.answer,
        sources=request.sources,
        metrics=request.metrics,
        sentiment_stats=sentiment_stats,
    )

    if pdf_bytes is None:
        raise HTTPException(status_code=500, detail="Erreur génération PDF (fpdf2 non installé)")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=sentiflow_rapport.pdf"},
    )
