# Assistant de due diligence documentaire

Petit projet de démonstration : un assistant qui répond, en langage naturel
et avec citation de source, à des questions posées sur un jeu de documents
de due diligence (teaser, synthèse financière, mémo de risques), en
s'appuyant sur l'API Mistral.

**Documents de test :** un dossier fictif ("Projet Meridian", société
industrielle imaginaire) inspiré du type de dossiers manipulés en private
equity — aucune donnée réelle ou confidentielle n'est utilisée.

## Pourquoi ce projet

Ce n'est pas un projet IA générique : c'est la transposition d'un problème
que je connais de l'intérieur (répondre vite et avec justesse à une question
sur un data room, en citant précisément sa source) en outil déployable —
soit exactement l'exercice que couvre le poste d'AI Deployment Strategist :
prendre un besoin métier concret et l'implémenter avec les modèles Mistral.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Créer une clé API gratuite sur [console.mistral.ai](https://console.mistral.ai)
2. L'exporter dans le terminal :
   ```bash
   export MISTRAL_API_KEY="ta_cle"
   ```

## Utilisation

```bash
python ask_documents.py
```

Exemples de questions à tester :
- "Quelle est la marge d'EBITDA en 2025 et comment a-t-elle évolué depuis 2023 ?"
- "Quel est le principal risque de concentration client identifié ?"
- "Y a-t-il des litiges sociaux en cours ? Quel est le montant provisionné ?"
- "Quel est le rationale de la transaction pour le fondateur ?"
- "Quel est le montant du plan de capex prévu et à quoi sert-il ?" (test volontaire
  d'une question dont la réponse n'est que partiellement dans les documents,
  pour vérifier que l'assistant ne survend pas ce qu'il ne sait pas)

## Comment ça marche (architecture v1)

```
data/*.txt, data/*.pdf
        │
        ▼
  load_documents()      → lit chaque fichier (texte brut ou extraction PDF via pypdf)
        │
        ▼
  build_context()        → assemble tous les documents en un seul bloc,
        │                   avec des balises DEBUT/FIN DOCUMENT par fichier
        ▼
  ask()                   → envoie {system prompt + documents + question}
        │                   à l'API Mistral (mistral-large-latest)
        ▼
  réponse avec citation de la source
```

Choix volontaire de la v1 : pas de base vectorielle. Les trois documents
tiennent largement dans la fenêtre de contexte du modèle, donc on les
transmet tous à chaque question ("context stuffing"). C'est la solution la
plus simple qui fonctionne pour ce volume de documents.

## Pistes d'évolution (v2)

- **RAG avec embeddings** : pour un data room de dizaines/centaines de
  documents qui ne tiendraient plus dans le contexte — découpage en chunks,
  calcul d'embeddings, recherche par similarité pour ne récupérer que les
  passages pertinents avant de les transmettre au modèle.
- **Interface web** (Streamlit) plutôt qu'un prompt en ligne de commande.
- **Évaluation** : un petit jeu de questions/réponses de référence pour
  mesurer la fiabilité des réponses avant tout usage réel.
- **Traçabilité** : logger chaque question/réponse pour permettre une revue
  humaine systématique — indispensable dans un contexte réglementé.

## Points à savoir expliquer en entretien

- Pourquoi "context stuffing" plutôt que RAG en v1 : simplicité, adapté au
  volume de documents, évite une complexité (embeddings, base vectorielle)
  non justifiée à cette échelle.
- Pourquoi le prompt système impose de citer la source et d'admettre
  l'absence d'information plutôt que d'halluciner — un choix de conception
  directement lié aux exigences de fiabilité d'un environnement réglementé.
- Les limites actuelles (pas de vraie gestion de PDF scannés/images, pas
  d'évaluation automatisée de la qualité des réponses) et comment on y
  répondrait en v2.
