# Correctif collecte explicite SentiFlow — v2

Cette archive est volontairement structurée **sans dossier parent supplémentaire**.
Extrayez son contenu directement à la racine du dépôt SentiFlow et acceptez le remplacement des fichiers.

## Problèmes corrigés

- `récupère ...` déclenche toujours une collecte réelle, même si le petit Transformer produit un mauvais plan.
- Une collecte demandée manuellement n'est plus bloquée par l'option d'abonnement `auto_collect`.
- `2 derniers jours` est interprété comme `days: 2`.
- Les intentions, actions, périodes et filtres de sentiment halluciné par le checkpoint sont remplacés par les éléments déterministes de la question.
- Le plan expose `planner_guardrail_version: semantic_guardrails_v3` pour vérifier que le correctif chargé est le bon.
- Le frontend n'affiche plus « données déjà disponibles » lorsque la vraie raison est une interdiction de collecte.

## Application avec Docker Compose

À la racine du projet :

```powershell
docker compose restart api
docker compose up -d --build frontend
```

Le backend est monté comme volume dans `docker-compose.yml`, donc un redémarrage de `api` suffit pour recharger Python. Le frontend doit être reconstruit.

## Vérification

```powershell
Invoke-RestMethod http://localhost:8000/llm/model-info | ConvertTo-Json
```

La réponse doit contenir :

```json
"guardrail_version": "semantic_guardrails_v3"
```

Ensuite, le plan de :

```text
récupère les tweets des 2 derniers jours du #Nice
```

doit contenir :

```json
{
  "intent": "collect_analyze_summarize",
  "targets": ["#nice"],
  "days": 2,
  "actions": [
    "create_missing_targets",
    "collect_tweets",
    "analyze_sentiments",
    "summarize",
    "generate_dashboard"
  ],
  "sentiment_filter": null,
  "force_refresh": true,
  "planner_guardrail_version": "semantic_guardrails_v3"
}
```

## Tests

Depuis la racine du dépôt :

```powershell
$env:PYTHONPATH = "."
pytest -q tests/test_llm_planner_guardrails.py tests/test_twitter_service.py
```

Résultat attendu : `11 passed`.
