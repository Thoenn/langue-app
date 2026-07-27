"""
Batch translate missing translations using DeepSeek Flash API.
Processes words that only have English translations.
"""
import asyncio, json, re, sys
from database import get_sync_conn
from services.deepseek import call_deepseek

LANGUAGES = {
    "la": "Latin", "es": "Spanish", "de": "German", "it": "Italian",
    "ru": "Russian", "zh": "Chinese", "ja": "Japanese", "kr": "Korean", "km": "Khmer",
}
BATCH_SIZE = 15

def get_words_needing_translation(lang_code):
    conn = get_sync_conn()
    rows = conn.execute("""
        SELECT w.id, w.french
        FROM words w
        WHERE w.id IN (SELECT word_id FROM translations WHERE language = 'en')
        AND w.id NOT IN (SELECT word_id FROM translations WHERE language = ?)
        ORDER BY w.id
    """, (lang_code,)).fetchall()
    conn.close()
    return [(r["id"], r["french"]) for r in rows]

async def translate_batch(batch, lang_code, lang_name):
    words_text = "\n".join(f"{i+1}. {fr}" for i, (_, fr) in enumerate(batch))
    prompt = f"""Translate these French words/phrases into {lang_name}.
Return ONLY valid JSON array: [{{"id": index, "translation": "...", "phonetic_simple": "..."}}]
For phonetic_simple, provide a pronunciation guide readable by French speakers (not IPA).
Keep translations concise. For {lang_name} ({lang_code}), use native script + phonetic where applicable.

Words to translate:
{words_text}"""

    result = await call_deepseek("translate_context", prompt)
    return result

def save_translations(word_id, lang, translation, phonetic):
    conn = get_sync_conn()
    existing = conn.execute(
        "SELECT id FROM translations WHERE word_id = ? AND language = ?",
        (word_id, lang)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE translations SET translation = ?, phonetic = ? WHERE word_id = ? AND language = ?",
            (translation, phonetic, word_id, lang),
        )
    else:
        conn.execute(
            "INSERT INTO translations (word_id, language, translation, phonetic) VALUES (?, ?, ?, ?)",
            (word_id, lang, translation, phonetic),
        )
    conn.commit()
    conn.close()

async def process_all():
    for lang_code, lang_name in LANGUAGES.items():
        words = get_words_needing_translation(lang_code)
        total = len(words)
        if total == 0:
            print(f"\n✅ {lang_name} ({lang_code}): déjà complet")
            continue
        print(f"\n🌍 Traduction vers {lang_name} ({lang_code}) — {total} mots")
        done = 0

        for i in range(0, len(words), BATCH_SIZE):
            batch = words[i:i + BATCH_SIZE]
            sys.stdout.write(f"\r  Lot {i//BATCH_SIZE + 1}/{(total-1)//BATCH_SIZE + 1} ({done}/{total})")
            sys.stdout.flush()

            try:
                result = await translate_batch(batch, lang_code, lang_name)
                translations = []

                if isinstance(result, list):
                    translations = result
                elif isinstance(result, dict):
                    if "translations" in result:
                        translations = result["translations"]
                    elif "sentences" in result:
                        continue
                    elif "raw" in result:
                        raw = result["raw"]
                        try:
                            raw_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.DOTALL).strip()
                            translations = json.loads(raw_clean)
                        except:
                            print(f"\n  ⚠️ Parse error for batch {i//BATCH_SIZE}: {raw[:100]}")
                            continue
                    elif "error" in result:
                        print(f"\n  ⚠️ API error: {result['error']}")
                        await asyncio.sleep(5)
                        continue
                    else:
                        continue

                for item in translations:
                    idx = item.get("id", 0) - 1
                    if 0 <= idx < len(batch):
                        wid, _ = batch[idx]
                        trans = item.get("translation", "")
                        phon = item.get("phonetic_simple", "")
                        if trans and trans.strip():
                            save_translations(wid, lang_code, trans.strip(), phon.strip())
                            done += 1

                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"\n  ❌ Error: {e}")
                await asyncio.sleep(2)

        print(f"\n  ✅ {lang_name}: {done} traductions ajoutées")

    print(f"\n🎉 Terminé!")

if __name__ == "__main__":
    asyncio.run(process_all())
