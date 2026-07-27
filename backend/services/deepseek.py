import httpx
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

SYSTEM_PROMPTS = {
    "generate_quiz": """You are a language teaching assistant. Generate a multiple-choice question (QCM) for language learning.
Return ONLY valid JSON in this exact format:
{
  "question_text": "What is the English translation of '...'?",
  "correct_answer": "...",
  "wrong_answers": ["...", "...", "..."],
  "explanation": "..."
}
The wrong_answers should be plausible but incorrect. Include 3 wrong answers.""",

    "generate_sentences": """You are a language teaching assistant. Generate example sentences for a word.
Return ONLY valid JSON in this exact format:
{
  "sentences": [
    {"fr": "...", "target": "..."},
    {"fr": "...", "target": "..."},
    {"fr": "...", "target": "..."}
  ]
}
Provide 3 different example sentences showing different contexts.""",

    "explain_grammar": """You are a language teaching assistant. Explain a grammar point or word usage.
Return ONLY valid JSON in this exact format:
{
  "explanation": "...",
  "examples": [
    {"fr": "...", "target": "..."},
    {"fr": "...", "target": "..."}
  ],
  "tips": ["...", "..."]
}
Keep explanations clear and practical.""",

    "phonetics": """You are a phonetics expert. Provide pronunciation guide for words.
Return ONLY valid JSON in this exact format:
{
  "phonetic_simple": "...",
  "phonetic_ipa": "...",
  "pronunciation_tips": "...",
  "audio_description": "..."
}
Use simplified phonetic notation (readable by French speakers).""",

    "translate_context": """You are a translator. Translate the given French word/phrase into the target language with context notes.
Return ONLY valid JSON in this exact format:
{
  "translation": "...",
  "alternative_translations": ["...", "..."],
  "usage_context": "...",
  "register": "formal/informal/neutral",
  "common_mistakes": "..."
}""",
}

async def call_deepseek(prompt_type: str, user_message: str) -> dict:
    if not DEEPSEEK_API_KEY:
        return {"error": "DeepSeek API key not configured. Please set the DEEPSEEK_API_KEY environment variable."}

    system_prompt = SYSTEM_PROMPTS.get(prompt_type, SYSTEM_PROMPTS["generate_quiz"])

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
            },
        )

        if response.status_code != 200:
            return {"error": f"DeepSeek API error: {response.status_code} - {response.text}"}

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        import json
        content_clean = content.strip()
        if content_clean.startswith("```"):
            content_clean = content_clean.split("\n", 1)[1]
            content_clean = content_clean.rsplit("```", 1)[0].strip()
        if content_clean.startswith("json"):
            content_clean = content_clean[4:].strip()

        try:
            return json.loads(content_clean)
        except json.JSONDecodeError:
            return {"raw": content_clean}
