$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\docker-compose.yml")) {
    throw "Lance ce script depuis la racine du projet SentiFlow, là où se trouve docker-compose.yml."
}

$plannerFile = ".\backend\app\services\llm_from_scratch.py"
if (-not (Test-Path $plannerFile)) {
    throw "Le fichier $plannerFile est introuvable. Vérifie que l'archive a été extraite directement à la racine du projet."
}

$marker = Select-String -Path $plannerFile -Pattern 'semantic_guardrails_v3' -Quiet
if (-not $marker) {
    throw "Le correctif n'a pas remplacé le bon fichier. Réextrais l'archive à la racine en acceptant le remplacement."
}

Write-Host "Redémarrage de l'API..."
docker compose restart api

Write-Host "Reconstruction du frontend..."
docker compose up -d --build frontend

Write-Host "Vérification de la version du garde-fou..."
Start-Sleep -Seconds 2
try {
    $info = Invoke-RestMethod "http://localhost:8000/llm/model-info"
    $info | ConvertTo-Json -Depth 5
    if ($info.guardrail_version -ne "semantic_guardrails_v3") {
        throw "L'API ne charge pas encore semantic_guardrails_v3. Vérifie le conteneur et le volume backend."
    }
    Write-Host "Correctif chargé correctement." -ForegroundColor Green
}
catch {
    Write-Warning "L'API n'a pas pu être vérifiée automatiquement : $($_.Exception.Message)"
    Write-Host "Consulte les logs avec : docker compose logs --tail=100 api"
}
