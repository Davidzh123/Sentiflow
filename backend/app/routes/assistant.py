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
from backend.app.models.target import Target
from backend.app.models.tweet import Tweet

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
DB_KEYWORDS = {"mes cibles", "ma base", "combien de tweets", "combien de tweet", "nombre de tweet",
               "nombre de tweets", "quelles cibles", "mes données",
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
    model: Optional[str] = Field(default="auto", description="Modèle de génération (auto, llama-3.1-8b-instant, tinygpt, fallback...)")
    conversation_id: Optional[int] = Field(default=None, description="Conversation à laquelle rattacher l'échange")


def _save_conv(db, user_id, conversation_id, question, answer, meta):
    """Enregistre l'échange dans l'historique (best-effort). Retourne l'id de conversation."""
    try:
        from backend.app.routes.conversations import save_exchange
        return save_exchange(db, user_id, conversation_id, question, answer, meta)
    except Exception:
        return conversation_id


@router.get("/models")
def list_models():
    """Liste des modèles de génération disponibles (pour le sélecteur)."""
    from backend.app.services.rag import AVAILABLE_MODELS
    return {"models": AVAILABLE_MODELS}


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

    # Garde-fou : bloquer les questions nuisibles / hors cadre
    from backend.app.services.moderation import check_question
    try:
        from backend.app.models.blocked_keyword import BlockedKeyword
        _extra_blocked = [b.word for b in db.query(BlockedKeyword).all()]
    except Exception:
        _extra_blocked = []
    allowed, reason, _cat = check_question(question, _extra_blocked)
    if not allowed:
        return {"mode": "blocked", "answer": reason, "plan": None}

    # Récupérer le user connecté
    user_id = _get_user_id_from_request(raw_request, db)

    # Quota d'appels IA + gating selon l'abonnement
    from backend.app.models.user import User as _User
    from backend.app.services.plans import consume_ai_call, has_feature
    current_user_obj = db.query(_User).filter(_User.id == user_id).first()
    can_auto_collect = True
    if current_user_obj is not None:
        consume_ai_call(db, current_user_obj)  # lève 429 si quota dépassé
        can_auto_collect = has_feature(current_user_obj, "auto_collect")

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
    # MODE DATABASE : interroge la BDD directement (filtré par user)
    # ============================================
    if mode == "database":
        from sqlalchemy import func as sqlfunc
        import re as _re

        q_lower = question.lower()

        # Cible éventuellement mentionnée (#x / @x ou nom de cible connu).
        # Recherche GLOBALE par nom (le RAG voit déjà toutes les cibles) pour un
        # comptage ciblé cohérent, même si la cible appartient à un autre utilisateur.
        all_targets = db.query(Target).all()
        explicit_names = [e.lstrip("#@") for e in _re.findall(r"[#@][\wÀ-ÿ]+", q_lower)]
        question_words = set(_re.findall(r"[\wÀ-ÿ]{3,}", q_lower))
        mentioned_targets = []
        for t in all_targets:
            tname = t.name.lower().lstrip("#@")
            if tname and (tname in explicit_names or tname in question_words):
                mentioned_targets.append(t)

        user_targets = db.query(Target).filter(Target.user_id == user_id).all()

        if "langue" in q_lower:
            query_type = "languages"
        elif "cible" in q_lower or "quelles" in q_lower or "quels sont" in q_lower:
            query_type = "targets"
        elif "combien" in q_lower or "nombre" in q_lower or "total" in q_lower:
            query_type = "tweet_count"
        elif "colère" in q_lower or "colere" in q_lower or "négatif" in q_lower or "negatif" in q_lower:
            query_type = "anger_by_target"
        else:
            query_type = "targets"

        answer_parts = []

        if query_type == "targets":
            total_tweets = 0
            for t in user_targets:
                count = db.query(sqlfunc.count(Tweet.id)).filter(Tweet.target_id == t.id).scalar() or 0
                analyzed = db.query(sqlfunc.count(Tweet.id)).filter(Tweet.target_id == t.id, Tweet.sentiment.isnot(None)).scalar() or 0
                total_tweets += count
                t_type = t.target_type.value if hasattr(t.target_type, 'value') else str(t.target_type)
                answer_parts.append(f"• {t.name} ({t_type}) : {count} tweets ({analyzed} analysés)")
            answer_parts.insert(0, f"📊 {len(user_targets)} cibles suivies, {total_tweets} tweets au total\n")

        elif query_type == "tweet_count":
            if mentioned_targets:
                # Comptage ciblé (ex: "#bts nombre de tweets ?") — somme sur les cibles de ce nom
                tids = [t.id for t in mentioned_targets]
                name = mentioned_targets[0].name
                total = db.query(sqlfunc.count(Tweet.id)).filter(Tweet.target_id.in_(tids)).scalar() or 0
                analyzed = db.query(sqlfunc.count(Tweet.id)).filter(Tweet.target_id.in_(tids), Tweet.sentiment.isnot(None)).scalar() or 0
                answer_parts.append(f"📊 {name} : {total} tweets ({analyzed} analysés, {total - analyzed} en attente)")
            else:
                target_ids = [t.id for t in user_targets]
                total = db.query(sqlfunc.count(Tweet.id)).filter(Tweet.target_id.in_(target_ids)).scalar() if target_ids else 0
                analyzed = db.query(sqlfunc.count(Tweet.id)).filter(Tweet.target_id.in_(target_ids), Tweet.sentiment.isnot(None)).scalar() if target_ids else 0
                answer_parts.append(f"📊 Total : {total} tweets ({analyzed} analysés, {total - analyzed} en attente)")

        elif query_type == "anger_by_target":
            answer_parts.append("📊 Cibles avec le plus de tweets négatifs (colère/tristesse/peur) :")
            for t in user_targets:
                neg_count = db.query(sqlfunc.count(Tweet.id)).filter(
                    Tweet.target_id == t.id,
                    Tweet.sentiment.in_(["colere", "tristesse", "peur"])
                ).scalar() or 0
                if neg_count > 0:
                    answer_parts.append(f"   • {t.name} : {neg_count} tweets négatifs")
            if len(answer_parts) == 1:
                answer_parts.append("   Aucun tweet négatif trouvé.")

        elif query_type == "languages":
            answer_parts.append(
                "La langue des tweets n'est pas encore enregistrée en base, je ne peux donc "
                "pas faire de répartition par langue pour le moment."
            )
        else:
            answer_parts.append(
                "Je peux répondre à : le nombre de tweets (par cible ou global), la liste de vos "
                "cibles, ou les cibles avec le plus de tweets négatifs."
            )

        _db_answer = "\n".join(answer_parts)
        _conv_id = _save_conv(db, user_id, request.conversation_id, question, _db_answer, {"mode": "database"})
        return {
            "mode": "database",
            "answer": _db_answer,
            "plan": plan,
            "conversation_id": _conv_id,
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
                allow_auto_collect=can_auto_collect,
                allow_auto_analyze=True,
            )

            # Après la collecte, indexer pour que le RAG puisse utiliser les données
            index_all_tweets(db)

            from backend.app.services.notifications import notify
            notify(db, user_id, "collect", "Collecte effectuée",
                   f"Collecte et analyse terminées pour : {question[:80]}")

            _conv_id = _save_conv(db, user_id, request.conversation_id, question, result.get("answer", ""),
                                  {"mode": "agent", "dashboard_url": result.get("dashboard_url")})
            return {
                "mode": "agent",
                "answer": result.get("answer", ""),
                "dashboard_id": result.get("dashboard_id"),
                "dashboard_url": result.get("dashboard_url"),
                "execution_log": result.get("execution_log", []),
                "plan": result.get("plan"),
                "model_info": result.get("model_info"),
                "targets": result.get("targets", []),
                "conversation_id": _conv_id,
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
        user_id=user_id,
        model=request.model,
    )

    # Si pas assez de résultats et qu'on a des cibles identifiées → basculer en mode Agent
    _targets_from_plan = (plan.get("targets") if plan else None) or []
    if (result.get("total_retrieved", 0) < 3) and _targets_from_plan:
        logger.info(f"[ASSISTANT] RAG insuffisant ({result.get('total_retrieved', 0)} tweets), bascule en Agent pour collecter")
        try:
            from backend.app.services.llm_agent import run_sentiflow_agent
            agent_result = await run_sentiflow_agent(
                db=db,
                user_id=user_id,
                question=question,
                generate_dashboard=True,
                allow_auto_collect=can_auto_collect,
                allow_auto_analyze=True,
            )
            index_all_tweets(db)
            _conv_id = _save_conv(db, user_id, request.conversation_id, question, agent_result.get("answer", ""),
                                  {"mode": "agent", "dashboard_url": agent_result.get("dashboard_url")})
            return {
                "mode": "agent",
                "answer": agent_result.get("answer", ""),
                "dashboard_id": agent_result.get("dashboard_id"),
                "dashboard_url": agent_result.get("dashboard_url"),
                "execution_log": agent_result.get("execution_log", []),
                "plan": agent_result.get("plan"),
                "model_info": agent_result.get("model_info"),
                "sources": [],
                "total_retrieved": 0,
                "conversation_id": _conv_id,
            }
        except Exception as e:
            logger.warning(f"[ASSISTANT] Bascule Agent échouée: {e}")
            # Continuer avec le résultat RAG même partiel

    # Sauvegarder un dashboard généré pour le mode RAG aussi
    dashboard_id = None
    dashboard_url = None
    try:
        from backend.app.models.generated_dashboard import GeneratedDashboard
        from backend.app.services.dashboard_builder import build_dashboard_config
        answer = result.get("answer", "")
        sources = result.get("sources", [])

        # Résoudre les cibles : d'abord via les sources, sinon via les cibles du plan
        target_ids = list({s.get("target_id") for s in sources if s.get("target_id")})
        if not target_ids and plan and plan.get("targets"):
            from backend.app.models.target import Target as _Target
            names = [str(n).lower().lstrip("#@") for n in plan.get("targets", [])]
            rows = db.query(_Target).filter(_Target.user_id == user_id).all()
            target_ids = [r.id for r in rows if r.name.lower().lstrip("#@") in names]

        if sources and len(sources) >= 2 and target_ids:
            # Construire un VRAI dashboard (widgets) à partir des tweets en base
            config = build_dashboard_config(db, target_ids, question)
            config["mode"] = "rag"
            config["metrics"] = result.get("metrics")
            dashboard = GeneratedDashboard(
                user_id=user_id,
                title=f"Dashboard — {question[:70]}",
                question=question,
                answer=answer,
                target_ids=target_ids,
                config_json=config,
                plan_json=plan,
            )
            db.add(dashboard)
            db.commit()
            db.refresh(dashboard)
            dashboard_id = dashboard.id
            dashboard_url = f"/dashboards/generated/{dashboard.id}"
            from backend.app.services.notifications import notify
            notify(db, user_id, "pdf_export", "Dashboard généré",
                   f"Un nouveau rapport IA a été créé : « {dashboard.title} ». Disponible dans Mes rapports IA.")
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

    _conv_id = _save_conv(db, user_id, request.conversation_id, question, result.get("answer", ""),
                          {"mode": "rag", "dashboard_url": dashboard_url, "generator": result.get("generator")})

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
        "conversation_id": _conv_id,
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
    raw_request: FastAPIRequest,
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
        user_id = _get_user_id_from_request(raw_request, db)
        result = await rag_chat(db=db, question=request.question, enable_mcp=True, user_id=user_id)
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
