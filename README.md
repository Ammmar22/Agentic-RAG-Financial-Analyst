# Lumina Luxury AI - Agent RAG Agentique

Ce projet implémente un assistant intelligent capable d'analyser des rapports financiers complexes (PDF) pour la marque **Lumina Luxury**.

##  Fonctionnalités Clés
- **RAG Agentique** : L'agent ne se contente pas de chercher, il réfléchit.
- **Auto-Correction** : Système d'audit anti-hallucination intégré.
- **Streaming** : Interface en temps réel pour une meilleure UX.
- **FastAPI & Docker** : Prêt pour la production et conteneurisé.

##  Stack Technique
- **LLM** : Google Gemini 1.5 Flash
- **Base Vectorielle** : ChromaDB (Embeddings: gemini-embedding-001)
- **Framework** : Python, FastAPI, Pydantic
- **DevOps** : Docker

##  Comment l'utiliser ?
1. Clonez le dépôt.
2. Ajoutez votre `GEMINI_API_KEY` dans un fichier `.env`.
3. Lancez avec Docker :
   ```bash
   docker build -t lumina-ai .
   docker run -p 8000:8000 lumina-ai

###  4. Les commandes pour le "Push" sur GitHub

Ouvre ton terminal dans le dossier du projet et tape ces commandes :

1.  **Initialiser le dépôt** :
    `git init`
2.  **Ajouter tous les fichiers** (grâce au `.gitignore`, la clé .env sera ignorée) :
    `git add .`
3.  **Créer ton premier message** :
    `git commit -m "Initial commit: Agentic RAG with Streaming and FastAPI"`
4.  **Lier à ton GitHub** (Remplace par l'URL de ton dépôt créé sur GitHub.com) :
    `git remote add origin https://github.com/TON_PSEUDO/Lumina-AI.git`
5.  **Envoyer le code** :
    `git push -u origin main`
