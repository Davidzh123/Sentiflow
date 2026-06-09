# Document des Exigences - SentiFlow

## Introduction

SentiFlow est une plateforme d'analyse de sentiments pour Twitter/X conçue comme projet de fin d'année de 5ème année. La plateforme permet de collecter, analyser et visualiser les sentiments exprimés dans les tweets, avec des fonctionnalités avancées incluant un LLM développé from scratch, la génération automatique de contenu, et l'optimisation par Deep Reinforcement Learning.

## Glossaire

- **Tweet_Collector**: Module responsable de la collecte des tweets via l'API Twitter/X
- **Sentiment_Analyzer**: Module d'analyse des sentiments utilisant le LLM développé from scratch
- **Alert_Manager**: Système de gestion des alertes définies par l'utilisateur
- **Content_Generator**: Module de génération automatique de contenu pour publication
- **DRL_Optimizer**: Module de Deep Reinforcement Learning pour l'optimisation du timing et du filtrage
- **MCP_Bridge**: Interface Model Context Protocol pour connecter le LLM aux outils externes
- **Sentiment_Category**: Classification des sentiments (joie, tristesse, colère, peur, surprise, neutre)
- **Hashtag**: Mot-clé précédé du symbole # utilisé pour catégoriser les tweets
- **Account**: Compte Twitter/X identifié par un @username
- **Time_Series**: Série temporelle des sentiments analysés sur une période donnée
- **Publication_Window**: Fenêtre temporelle optimale pour la publication de contenu

## Exigences

### Exigence 1 : Collecte et Filtrage Intelligent des Tweets

**User Story:** En tant qu'analyste, je veux filtrer intelligemment les tweets collectés, afin de ne traiter que les données pertinentes pour mon analyse.

#### Critères d'Acceptation

1. WHEN un utilisateur configure un filtre par hashtag ou compte THEN le Tweet_Collector SHALL collecter uniquement les tweets correspondant aux critères spécifiés
2. WHEN un tweet est collecté THEN le Tweet_Collector SHALL stocker les métadonnées (auteur, date, engagement, langue) dans PostgreSQL
3. WHEN le volume de tweets dépasse le seuil configuré THEN le Tweet_Collector SHALL utiliser Redis pour mettre en cache les tweets récents
4. WHEN un tweet contient du spam ou du contenu non pertinent THEN le Tweet_Collector SHALL le filtrer automatiquement via le modèle DRL
5. WHILE la collecte est active THEN le Tweet_Collector SHALL maintenir une connexion streaming avec l'API Twitter/X
6. IF l'API Twitter/X retourne une erreur de rate limiting THEN le Tweet_Collector SHALL implémenter un backoff exponentiel et notifier l'utilisateur

### Exigence 2 : Analyse Temporelle des Sentiments

**User Story:** En tant qu'analyste, je veux visualiser l'évolution des sentiments dans le temps, afin de détecter des tendances et des patterns.

#### Critères d'Acceptation

1. WHEN un tweet est collecté THEN le Sentiment_Analyzer SHALL classifier le sentiment parmi les 6 catégories (joie, tristesse, colère, peur, surprise, neutre)
2. WHEN l'analyse est complète THEN le Sentiment_Analyzer SHALL retourner un score de confiance entre 0 et 1 pour chaque catégorie
3. WHEN un utilisateur sélectionne une période THEN le système SHALL afficher une série temporelle des sentiments agrégés
4. WHEN les données temporelles sont affichées THEN le système SHALL permettre un zoom sur des intervalles (heure, jour, semaine, mois)
5. THE Sentiment_Analyzer SHALL traiter chaque tweet en moins de 100ms en moyenne
6. WHEN le LLM analyse un tweet THEN le Sentiment_Analyzer SHALL stocker le résultat avec le vecteur d'embedding associé

### Exigence 3 : Comparaison de Hashtags et Comptes

**User Story:** En tant qu'analyste, je veux comparer les sentiments entre différents hashtags ou comptes, afin d'identifier des différences de perception.

#### Critères d'Acceptation

1. WHEN un utilisateur sélectionne plusieurs hashtags THEN le système SHALL afficher une comparaison côte à côte des distributions de sentiments
2. WHEN un utilisateur sélectionne plusieurs comptes THEN le système SHALL afficher une comparaison côte à côte des distributions de sentiments
3. WHEN une comparaison est demandée THEN le système SHALL calculer et afficher les métriques de divergence entre les distributions
4. WHEN les données de comparaison sont affichées THEN le système SHALL permettre l'export en CSV et JSON
5. THE système SHALL supporter la comparaison simultanée de jusqu'à 10 hashtags ou comptes

### Exigence 4 : Système d'Alertes Automatiques

**User Story:** En tant qu'utilisateur, je veux définir des alertes personnalisées, afin d'être notifié automatiquement lors d'événements significatifs.

#### Critères d'Acceptation

1. WHEN un utilisateur crée une alerte THEN le Alert_Manager SHALL permettre de définir des conditions sur les sentiments (seuil, tendance, anomalie)
2. WHEN une condition d'alerte est satisfaite THEN le Alert_Manager SHALL envoyer une notification via le canal configuré (email, webhook, dashboard)
3. WHEN une alerte est déclenchée THEN le Alert_Manager SHALL inclure le contexte (tweets déclencheurs, métriques, timestamp)
4. WHILE une alerte est active THEN le Alert_Manager SHALL vérifier les conditions en temps réel via le pipeline Celery/Kafka
5. IF plusieurs alertes sont déclenchées simultanément THEN le Alert_Manager SHALL les regrouper pour éviter le spam de notifications
6. WHEN un utilisateur modifie une alerte THEN le Alert_Manager SHALL appliquer les changements immédiatement sans redémarrage

### Exigence 5 : LLM Conversationnel pour Interrogation des Données

**User Story:** En tant qu'utilisateur, je veux interroger l'activité des comptes et hashtags en langage naturel, afin d'obtenir des insights sans écrire de requêtes complexes.

#### Critères d'Acceptation

1. WHEN un utilisateur pose une question en langage naturel THEN le LLM SHALL interpréter l'intention et générer une réponse contextuelle
2. WHEN une question concerne plusieurs comptes ou hashtags THEN le LLM SHALL agréger les données pertinentes avant de répondre
3. WHEN le LLM génère une réponse THEN il SHALL citer les sources (tweets, périodes, comptes) utilisées
4. THE LLM SHALL être développé from scratch en PyTorch avec une architecture Transformer
5. WHEN le LLM ne peut pas répondre avec certitude THEN il SHALL indiquer son niveau de confiance et suggérer des reformulations
6. WHILE le LLM traite une requête THEN il SHALL utiliser le MCP_Bridge pour accéder aux outils externes si nécessaire

### Exigence 6 : Génération et Publication Automatique de Contenu

**User Story:** En tant qu'utilisateur, je veux générer automatiquement du contenu basé sur les analyses, afin de publier des insights sur mon compte Twitter/X.

#### Critères d'Acceptation

1. WHEN un utilisateur demande une génération de contenu THEN le Content_Generator SHALL créer un tweet basé sur les analyses récentes
2. WHEN le contenu est généré THEN le Content_Generator SHALL respecter la limite de 280 caractères et les guidelines Twitter/X
3. WHEN un utilisateur approuve le contenu THEN le système SHALL publier automatiquement sur le compte Twitter/X configuré
4. WHEN le contenu est publié THEN le système SHALL stocker l'historique de publication avec les métriques d'engagement
5. IF le contenu généré contient des informations sensibles THEN le Content_Generator SHALL avertir l'utilisateur avant publication
6. WHEN un utilisateur configure la publication automatique THEN le DRL_Optimizer SHALL déterminer le timing optimal

### Exigence 7 : Optimisation par Deep Reinforcement Learning

**User Story:** En tant qu'utilisateur, je veux que le système optimise automatiquement le filtrage et le timing de publication, afin de maximiser la pertinence et l'engagement.

#### Critères d'Acceptation

1. WHEN le DRL_Optimizer est entraîné THEN il SHALL utiliser les métriques d'engagement comme signal de récompense
2. WHEN le DRL_Optimizer recommande un timing THEN il SHALL fournir une fenêtre de publication avec un score de confiance
3. WHILE le système collecte des tweets THEN le DRL_Optimizer SHALL affiner continuellement le modèle de filtrage
4. WHEN le DRL_Optimizer détecte une anomalie de performance THEN il SHALL alerter l'utilisateur et proposer un réentraînement
5. THE DRL_Optimizer SHALL être implémenté from scratch en PyTorch avec un algorithme PPO ou DQN
6. WHEN un utilisateur consulte les recommandations THEN le DRL_Optimizer SHALL expliquer les facteurs de décision

### Exigence 8 : Intégration MCP (Model Context Protocol)

**User Story:** En tant que développeur, je veux connecter le LLM à des outils externes via MCP, afin d'étendre ses capacités d'analyse.

#### Critères d'Acceptation

1. WHEN le LLM nécessite des données externes THEN le MCP_Bridge SHALL router la requête vers l'outil approprié
2. WHEN un outil externe est appelé THEN le MCP_Bridge SHALL formater la réponse pour le LLM
3. THE MCP_Bridge SHALL supporter les outils : recherche web, calcul, accès base de données, API Twitter/X
4. WHEN une erreur survient dans un outil externe THEN le MCP_Bridge SHALL retourner un message d'erreur structuré au LLM
5. WHILE le MCP_Bridge traite une requête THEN il SHALL logger toutes les interactions pour le debugging
6. IF un outil externe est indisponible THEN le MCP_Bridge SHALL utiliser un fallback ou informer le LLM de l'indisponibilité

### Exigence 9 : Interface Utilisateur Streamlit

**User Story:** En tant qu'utilisateur, je veux une interface simple et intuitive, afin de naviguer facilement dans les fonctionnalités de la plateforme.

#### Critères d'Acceptation

1. WHEN un utilisateur accède au dashboard THEN le système SHALL afficher un résumé des métriques clés (tweets collectés, sentiments dominants, alertes actives)
2. WHEN un utilisateur navigue entre les pages THEN le système SHALL maintenir le contexte de session
3. WHEN les données sont mises à jour THEN le système SHALL rafraîchir l'affichage en temps réel via WebSocket ou polling
4. THE interface SHALL être responsive et fonctionner sur desktop et tablette
5. WHEN un utilisateur effectue une action THEN le système SHALL fournir un feedback visuel immédiat
6. IF une erreur survient THEN le système SHALL afficher un message d'erreur compréhensible avec des suggestions de résolution

### Exigence 10 : Persistance et Performance des Données

**User Story:** En tant qu'administrateur, je veux que les données soient stockées de manière fiable et performante, afin de garantir la disponibilité du service.

#### Critères d'Acceptation

1. THE système SHALL utiliser PostgreSQL pour le stockage persistant des tweets, analyses et configurations
2. THE système SHALL utiliser Redis pour le cache des données temps réel et les files de messages
3. WHEN le volume de données dépasse 1 million de tweets THEN le système SHALL maintenir des temps de requête inférieurs à 500ms
4. WHEN une transaction échoue THEN le système SHALL implémenter un mécanisme de retry avec rollback
5. THE système SHALL effectuer des backups automatiques quotidiens de la base PostgreSQL
6. WHILE le pipeline temps réel est actif THEN le système SHALL garantir une latence maximale de 5 secondes entre collecte et analyse
