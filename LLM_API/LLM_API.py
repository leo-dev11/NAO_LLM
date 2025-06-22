from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
app = FastAPI()
load_dotenv()
# Usa tu propia API key (Puede ser de OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Puedes setearla directamente aquí para pruebas:
# OPENROUTER_API_KEY = "tu_api_key_aquí"

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_with_model(request: ChatRequest):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",  # Cambia esto si usas un dominio personalizado
        "X-Title": "Mi Proyecto con DeepSeek",
    }

    data = {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "max_tokens": 100,
        "messages": [
            {"role": "system", "content": (
                "Eres un robot llamado NAO. Responde siempre de forma breve, clara y amistosa. "
                "Habla como si estuvieras teniendo una conversación en persona. No uses palabras difíciles, "
                "y asegúrate de que tus respuestas sean fáciles de decir en voz alta y fáciles de entender. "
                "Nunca digas más de 2 o 3 frases."
                "Genera las respuestas en inglés"
            )},
            {"role": "user", "content": request.prompt}
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=data,
                headers=headers
            )

            response.raise_for_status()
            result = response.json()
            return ChatResponse(response=result["choices"][0]["message"]["content"])

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=str(e))

#Usar uvicorn LLM_API:app --host 0.0.0.0 --port 5000
#http://10.11.149.154:5000/chat