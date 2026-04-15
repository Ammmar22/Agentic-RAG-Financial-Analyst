from fastapi import FastAPI , Request
import logging
import time
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from Rag_Avance import run_agent, run_agent_stream, run_agent_stream

# Configuration du log
logging.basicConfig(filename='api_usage.log', level=logging.INFO)

app = FastAPI(title="Lumina Luxury AI support", description="AI support for Lumina Luxury", version="1.0.0")

# --- 2. FONCTIONS UTILITAIRES ---
class Query(BaseModel):
    user_input: str
    


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # On log le temps de réponse
    logging.info(f"Path: {request.url.path} | Time: {process_time:.2f}s")
    return response

@app.post("/ask")
async def ask_ai(query: Query):
    print(f"Received query: {query.user_input}")
    # Here you would call your AI agent with the query.user_input and get the response

    response = run_agent(query.user_input)
    return {"status": "success", "response": response}


@app.post("/ask/stream")
async def ask_ai_stream(query: Query):
    # On crée un générateur qui va envoyer les bouts de texte un par un
    def generate():
        for text_chunk in run_agent_stream(query.user_input):
            # Format standard pour le streaming : "data: texte\n\n"
            yield f"data: {text_chunk}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

# --- 1. INITIALISATION ---
