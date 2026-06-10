"""
Endpoint unifié : combine l'Agent LLM (lseillier) + RAG (from scratch).
Le planner décide automatiquement quel pipeline utiliser.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from backend.app.database import get_db
from backend.app.services.rag import chat as rag_chat, index_all_tweets

router = APIRouter(prefix="/assistant", tags=["Assistant Unifié"])


# Intentions qui déclenchent l'agent (collecte + dashboard)
AGENT_INTENTS = {"collect_analyze_summarize", "collect_analyze_examples"}

# Mots-clés qui forcent le mode agent (même si le planner se trompe)
AGENT_KEYWORDS = {"récupère", "recupere", "collecte", "collecter", "ajoute", "crée", "cree"}

# Mots-clés qui déclenchent une requête BDD
DB_KEYWORDS = {"mes cibles", "ma base", "combien de tweets", "quelles cibles", "mes données",
               "répartition", "langues", "statistiques globales"}

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
    db: Session = Depends(get_db),
):
    """
    Chat unifié : le planner LLM from scratch décide s'il faut :
    - Collecter des tweets (Agent) → stocke en BDD + retourne des stats
    - Répondre à une question (RAG) → cherche les tweets pertinents + génère une réponse

    Les deux pipelines travaillent ensemble.
    """
    question = request.question
    user_id = 1  # user système par défaut quand pas connecté

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
    # MODE DATABASE : interroge la BDD
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

    return {
        "mode": "rag",
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "total_retrieved": result.get("total_retrieved", 0),
        "mcp_used": result.get("mcp_used", False),
        "generator": result.get("generator"),
        "plan": result.get("plan") or plan,
        "metrics": result.get("metrics"),
    }
