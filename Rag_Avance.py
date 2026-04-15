import os
import json
import chromadb
from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader

# --- 1. CONFIGURATION ---
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, '.env'))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
chroma_client = chromadb.PersistentClient(path=os.path.join(script_dir, "chroma_db"))
collection = chroma_client.get_or_create_collection(name="ma_base_connaissance")

# --- 2. FONCTIONS DE TRAITEMENT (ETL) ---

def ingest_pdf(pdf_path):
    """Extrait, découpe et indexe le PDF dans ChromaDB."""
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier {pdf_path} introuvable.")
        return

    reader = PdfReader(pdf_path)
    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    # Chunking intelligent
    chunk_size, overlap = 1000, 150
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

    print(f"📦 Indexation de {len(chunks)} morceaux...")
    for idx, chunk in enumerate(chunks):
        res = client.models.embed_content(
            model="gemini-embedding-001",
            contents=chunk,
            config={'task_type': 'RETRIEVAL_DOCUMENT'}
        )
        collection.add(
            ids=[f"{os.path.basename(pdf_path)}_{idx}"],
            embeddings=[res.embeddings[0].values],
            documents=[chunk]
        )
    print(f"✅ Rapport '{pdf_path}' prêt pour l'analyse.")

# --- 3. FONCTIONS AGENTIQUES ---

def get_context(query, n):
    """Récupère les documents dans ChromaDB."""
    res = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config={'task_type': 'RETRIEVAL_QUERY'}
    )
    results = collection.query(query_embeddings=[res.embeddings[0].values], n_results=n)
    return "\n\n".join(results['documents'][0])

def grade_relevance(question, docs):
    """Nœud de décision : Est-ce que les docs sont utiles ?"""
    print("--- 🔍 ÉVALUATION DE LA PERTINENCE ---")
    prompt = f"Question: {question}\nDocs: {docs}\nRéponds en JSON: {{\"score\": \"OUI\"}} ou {{\"score\": \"NON\"}}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={'response_mime_type': 'application/json'}
    )
    return json.loads(response.text).get('score', 'NON')

def rewrite_query(query):
    """Nœud de correction : Reformule la recherche."""
    print("--- 🔄 REFORMULATION ---")
    prompt = f"Réécris cette question pour une recherche financière : {query}. Réponds juste la question."
    return client.models.generate_content(model="gemini-2.5-flash", contents=prompt).text.strip()

def generate_answer(query, context):
    """Génère la réponse initiale."""
    prompt = f"CONTEXTE: {context}\nQUESTION: {query}\nRéponds de manière factuelle."
    return client.models.generate_content(model="gemini-2.5-flash", contents=prompt).text

def audit_hallucination(answer, context):
    """Nœud de contrôle : La réponse est-elle vraie ?"""
    print("--- ⚖️ AUDIT ANTI-HALLUCINATION ---")
    prompt = f"CONTEXTE: {context}\nRÉPONSE: {answer}\nLa réponse est-elle supportée par le contexte ? JSON: {{\"score\": \"OUI\"/\"NON\", \"raison\": \"...\"}}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={'response_mime_type': 'application/json'}
    )
    return json.loads(response.text)

# --- 4. LE CERVEAU (PIPELINE) ---

def run_agent(user_query):
    # 1. Première tentative
    context = get_context(user_query, n=3)
    relevance = grade_relevance(user_query, context)
    
    if relevance == "NON":
        # 2. Boucle de reformulation si échec
        new_query = rewrite_query(user_query)
        print(f"🔎 Nouvelle recherche : {new_query}")
        context = get_context(new_query, n=5) # On cherche plus large
        user_query = new_query

    # 3. Génération
    answer = generate_answer(user_query, context)
    
    # 4. Audit final
    audit = audit_hallucination(answer, context)
    
    if audit['score'] == "NON":
        print(f"❌ Erreur détectée : {audit['raison']}")
        print("🔄 Auto-correction...")
        correction_prompt = f"ERREUR: {audit['raison']}\nCONTEXTE: {context}\nFournis une réponse corrigée et vérifiée."
        answer = client.models.generate_content(model="gemini-2.5-flash", contents=correction_prompt).text
    else:
        print("✅ Réponse certifiée conforme.")
        
    return answer


def run_agent_stream(user_query):
    # 1. Étapes de réflexion
    context = get_context(user_query, n=3)
    relevance = grade_relevance(user_query, context)
    
    if relevance == "NON":
        new_query = rewrite_query(user_query)
        yield f"🔎 *Reformulation : {new_query}...*\n\n"
        context = get_context(new_query, n=5)
        user_query = new_query

    print("--- ✍️ GÉNÉRATION EN COURS ---")
    full_text = ""
    
    try:
        # On utilise 'models.generate_content_stream' qui est la méthode dédiée
        # Cela évite d'utiliser l'argument 'stream=True' qui semble bloquer chez toi
        response_stream = client.models.generate_content_stream(
            model="gemini-2.5-flash", 
            contents=f"CONTEXTE: {context}\nQUESTION: {user_query}"
        )

        for chunk in response_stream:
            # On vérifie si le chunk contient du texte
            if chunk.text:
                full_text += chunk.text
                yield chunk.text
                
    except Exception as e:
        # Si 'generate_content_stream' n'existe pas non plus, on tente le fallback ultime
        yield f"\n❌ Erreur technique : {str(e)}"
        return



# --- 5. MAIN ---
# --- 5. MAIN ---
if __name__ == "__main__":
    # ingest_pdf("data/rapport.pdf")

    while True:
        query = input("\n❓ Question : ")
        if query.lower() in ['exit', 'quit']: 
            break
        
        print("\n🤖 Gemini Agent : ", end="", flush=True)
        
        # On boucle sur le générateur de streaming
        # Chaque 'chunk' est un morceau de texte envoyé par le yield
        for chunk in run_agent_stream(query):
            print(chunk, end="", flush=True) # Affiche sans sauter de ligne
        
        print("\n") # Saute une ligne à la fin de la réponse