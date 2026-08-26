"""
Assistant de due diligence documentaire — v1
=============================================

Principe (RAG "par empilement de contexte", sans base vectorielle) :
1. On lit tous les documents du dossier data/ (.txt et .pdf)
2. On assemble leur contenu dans le contexte du prompt, avec des balises
   qui identifient clairement chaque document
3. On pose une question à l'API Mistral, en lui demandant de répondre
   UNIQUEMENT à partir des documents fournis, en citant sa source

Pourquoi pas un vrai RAG avec embeddings dès la v1 ?
-----------------------------------------------------
Le "context stuffing" (empiler les documents dans le prompt) fonctionne très
bien tant que le volume de documents tient dans la fenêtre de contexte du
modèle — c'est le cas ici avec 3 documents courts. Pour un vrai data room de
dizaines ou centaines de documents, il faudrait passer à un RAG complet
(découpage en chunks + embeddings + recherche par similarité) pour ne
sélectionner que les passages pertinents avant de les envoyer au modèle.
C'est l'évolution naturelle "v2" de ce projet, une fois cette mécanique de
base comprise et maîtrisée.
"""

import os
import sys
from pathlib import Path

try:
    from mistralai import Mistral
except ImportError:
    # Selon la version du SDK installée, la classe Mistral peut se trouver
    # à cet emplacement alternatif.
    from mistralai.client import Mistral
from pypdf import PdfReader

DATA_DIR = Path(__file__).parent / "data"
MODEL = "mistral-large-latest"

SYSTEM_PROMPT = """Tu es un assistant de due diligence pour une équipe de private equity.
Réponds UNIQUEMENT à partir des documents fournis ci-dessous.
Si l'information demandée n'est pas présente dans les documents, dis-le clairement
plutôt que d'inventer une réponse.
Cite systématiquement le document source de chaque information (ex: [financials.txt])."""


def load_documents() -> dict[str, str]:
    """Lit tous les fichiers .txt et .pdf du dossier data/ et retourne
    un dictionnaire {nom_du_fichier: contenu_texte}.

    Le support des PDF (via pypdf) permet de brancher de vrais documents
    de data room sans changer le reste du code — les fichiers .txt ne
    servent qu'à simplifier ce projet de démonstration.
    """
    documents = {}
    for path in sorted(DATA_DIR.iterdir()):
        if path.suffix == ".txt":
            documents[path.name] = path.read_text(encoding="utf-8")
        elif path.suffix == ".pdf":
            reader = PdfReader(str(path))
            documents[path.name] = "\n".join(page.extract_text() or "" for page in reader.pages)
    return documents


def build_context(documents: dict[str, str]) -> str:
    """Assemble les documents en un seul bloc de texte, avec des séparateurs
    explicites pour que le modèle puisse identifier et citer sa source."""
    blocks = [
        f"--- DEBUT DOCUMENT: {name} ---\n{content}\n--- FIN DOCUMENT: {name} ---"
        for name, content in documents.items()
    ]
    return "\n\n".join(blocks)


def ask(question: str, context: str, client: Mistral) -> str:
    """Envoie la question et le contexte documentaire au modèle Mistral
    et retourne la réponse textuelle."""
    response = client.chat.complete(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"DOCUMENTS:\n\n{context}\n\nQUESTION: {question}"},
        ],
    )
    return response.choices[0].message.content


def main():
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        sys.exit(
            "Erreur : variable d'environnement MISTRAL_API_KEY manquante.\n"
            "1. Crée une clé gratuite sur https://console.mistral.ai\n"
            "2. Dans ton terminal : export MISTRAL_API_KEY='ta_cle'\n"
            "3. Relance : python ask_documents.py"
        )

    documents = load_documents()
    if not documents:
        sys.exit(f"Aucun document trouvé dans {DATA_DIR}")

    print(f"{len(documents)} document(s) chargé(s) : {', '.join(documents)}\n")
    context = build_context(documents)
    client = Mistral(api_key=api_key)

    print("Assistant de due diligence prêt. Tape 'quit' pour quitter.\n")
    while True:
        question = input("Ta question > ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        if not question:
            continue
        answer = ask(question, context, client)
        print(f"\n{answer}\n")


if __name__ == "__main__":
    main()
