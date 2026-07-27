from fastapi import APIRouter
from database import get_sync_conn
from services.deepseek import call_deepseek
from pydantic import BaseModel
import json, random, asyncio

router = APIRouter(prefix="/api/ai", tags=["ai"])

class AIChatMessage(BaseModel):
    role: str
    content: str

class AIChatRequest(BaseModel):
    messages: list[AIChatMessage]
    context: dict = {}

@router.post("/chat")
async def ai_chat(request: AIChatRequest):
    user_msg = request.messages[-1].content if request.messages else ""
    context_info = ""
    if request.context.get("word"):
        context_info += f"\nContext word: {json.dumps(request.context['word'], ensure_ascii=False)}"
    if request.context.get("language"):
        context_info += f"\nTarget language: {request.context['language']}"

    system = """You are a helpful language learning assistant for Michel, a French native speaker.
Respond in French unless asked otherwise.
You can help with vocabulary, grammar, pronunciation, translations, and generating exercises.
Be concise, practical, and encouraging. Use examples when helpful."""

    response = await call_deepseek_raw(system, request.messages, context_info)
    return {"response": response}

async def call_deepseek_raw(system_prompt: str, messages: list, context: str = ""):
    from services.deepseek import DEEPSEEK_URL, DEEPSEEK_API_KEY, DEEPSEEK_MODEL
    import httpx
    if not DEEPSEEK_API_KEY:
        return {"error": "DeepSeek API key not configured"}

    msgs = [{"role": "system", "content": system_prompt + context}]
    for m in messages:
        msgs.append({"role": m.role, "content": m.content})

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            DEEPSEEK_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": DEEPSEEK_MODEL, "messages": msgs, "temperature": 0.7, "max_tokens": 1024},
        )
        if resp.status_code != 200:
            return {"error": f"API error: {resp.status_code}"}
        data = resp.json()
        return {"content": data["choices"][0]["message"]["content"]}

@router.post("/generate-quiz")
async def generate_ai_quiz(language: str = "en", word_id: int = None, count: int = 3):
    word_context = ""
    if word_id:
        def _get():
            conn = get_sync_conn()
            w = conn.execute("SELECT french FROM words WHERE id = ?", (word_id,)).fetchone()
            t = conn.execute("SELECT translation FROM translations WHERE word_id = ? AND language = ?", (word_id, language)).fetchone()
            conn.close()
            return (w["french"] if w else "", t["translation"] if t else "")
        fr, trans = await asyncio.to_thread(_get)
        if fr:
            word_context = f"Word: {fr} → {trans}"

    user_msg = f"Generate {count} quiz questions for learning {language} (French native speaker). {word_context}"
    result = await call_deepseek("generate_quiz", user_msg)
    if "error" in result:
        return {"error": result.get("error", "Unknown error")}

    def _save(q_text, correct, wrongs, explanation):
        conn = get_sync_conn()
        cur = conn.execute(
            "INSERT INTO quiz_questions (language, question_type, question_text, correct_answer, wrong_answers, explanation, source) VALUES (?, 'ai_generated', ?, ?, ?, ?, 'deepseek')",
            (language, q_text, correct, json.dumps(wrongs), explanation),
        )
        qid = cur.lastrowid
        conn.commit()
        conn.close()
        return qid

    questions = []
    if isinstance(result, dict) and "question_text" in result:
        qid = await asyncio.to_thread(_save, result["question_text"], result["correct_answer"], result.get("wrong_answers", []), result.get("explanation", ""))
        options = [result["correct_answer"]] + result.get("wrong_answers", [])
        random.shuffle(options)
        questions.append({"id": qid, "question_text": result["question_text"], "correct_answer": result["correct_answer"], "wrong_answers": result.get("wrong_answers", []), "options": options, "explanation": result.get("explanation", "")})

    return {"questions": questions}

@router.post("/explain")
async def ai_explain(word: str, language: str = "en"):
    result = await call_deepseek("explain_grammar", f"Explain the word/expression '{word}' for a French speaker learning {language}. Include usage, register, and common mistakes.")
    return result

@router.post("/sentences")
async def ai_sentences(word: str, language: str = "en"):
    result = await call_deepseek("generate_sentences", f"Generate 3 example sentences with the word '{word}' for a French speaker learning {language}.")
    return result

@router.post("/phonetics")
async def ai_phonetics(word: str, language: str = "en"):
    result = await call_deepseek("phonetics", f"Provide phonetic pronunciation for '{word}' in {language}. Target audience: French speaker.")
    return result

@router.post("/translate")
async def ai_translate_context(word: str, language: str = "en"):
    result = await call_deepseek("translate_context", f"Translate '{word}' from French to {language} with context, alternatives, and usage notes.")
    return result
