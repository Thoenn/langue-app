import asyncio, json, sys, re
sys.path.insert(0, "/app")
from services.deepseek import call_deepseek

LANGS = [
    ("la", "Latin", "Focus on 5 declensions, cases, verb conjugations."),
    ("es", "Spanish", "Focus on ser/estar, subjunctive, preterite vs imperfect."),
    ("de", "German", "Focus on 4 cases, der/die/das, verb-second rule."),
    ("it", "Italian", "Focus on passato prossimo, articles, double consonants."),
    ("ru", "Russian", "Focus on Cyrillic, 6 cases, aspects, verbs of motion."),
    ("zh", "Chinese", "Focus on 4 tones, pinyin, measure words, radicals."),
    ("ja", "Japanese", "Focus on hiragana/katakana, politeness, particles."),
    ("kr", "Korean", "Focus on hangul, honorifics, verb conjugation."),
    ("km", "Khmer", "Focus on alphabet, subscript consonants, register."),
    ("en", "English", "Focus on 12 tenses, phrasal verbs, articles."),
]

def extract_from_raw(raw):
    """Extract course data from raw AI output without relying on JSON parsing."""
    title = "Cours"
    m = re.search(r'"title"\s*[:=]\s*"([^"]+)"', raw)
    if m:
        title = m.group(1)

    sections = []
    # Split by section blocks
    blocks = re.split(r'\}\s*,\s*\{', raw)
    if len(blocks) < 2:
        # Try different pattern
        blocks = re.findall(r'\{"title"\s*[:=]\s*"([^"]+)"\s*[,;]\s*"content"\s*[:=]\s*"([^"]+)"', raw)
        for t, c in blocks:
            sections.append({"title": t, "content": c.replace("\\n", "\n")})
    else:
        for block in blocks:
            t = None
            c = None
            tm = re.search(r'"title"\s*[:=]\s*"([^"]+)"', block)
            if tm:
                t = tm.group(1)
            cm = re.search(r'"content"\s*[:=]\s*"((?:[^"\\]|\\.)*?)"', block)
            if cm:
                c = cm.group(1).replace("\\n", "\n")
            if t and c:
                sections.append({"title": t, "content": c})

    if not sections:
        # Last resort: find all title/content pairs sequentially
        parts = raw.split('"title"')
        for part in parts[1:]:
            t = None
            c = None
            tm = re.search(r'["\']?\s*[:=]\s*["\']([^"\']+)["\']', part[:200])
            if tm:
                t = tm.group(1)
            ci = part.find('"content"')
            if ci > 0:
                rest = part[ci+9:]
                cm = re.search(r'[:=]\s*"((?:[^"\\]|\\.)*?)"', rest[:500])
                if cm:
                    c = cm.group(1).replace("\\n", "\n")
            if t and c:
                sections.append({"title": t, "content": c})

    return {"title": title, "sections": sections}

async def generate(code, name, focus):
    prompt = (
        'Create a COMPREHENSIVE language course in FRENCH for French speakers learning ' + name + '.\n'
        'Return ONLY valid JSON.\n\n'
        'Format:\n'
        '{"title":"' + name + ' - Cours complet","sections":[\n'
        '{"title":"Alphabet et prononciation","content":"4-6 paragraphs. Cover alphabet, pronunciation rules, tricky sounds for French speakers. Include examples."},\n'
        '{"title":"Grammaire fondamentale","content":"4-6 paragraphs. ' + focus + ' Compare with French."},\n'
        '{"title":"Conjugaison et verbes","content":"4-6 paragraphs. Explain verb system, tenses, patterns."},\n'
        '{"title":"Structure de phrase","content":"4-6 paragraphs. Word order, questions, negation."},\n'
        '{"title":"Pieges pour francophones","content":"4-6 paragraphs. Common mistakes, false friends."},\n'
        '{"title":"Expressions et vocabulaire","content":"4-6 paragraphs. Key phrases, greetings, numbers."},\n'
        '{"title":"Methode d apprentissage","content":"4-6 paragraphs. Advice, resources, memorization tips."}\n'
        ']}'
    )
    result = await call_deepseek("generate_course", prompt)
    if isinstance(result, dict) and "sections" in result:
        for sec in result["sections"]:
            if "content" in sec:
                sec["content"] = re.sub(r'(?<=[.!?])\s+(?=[A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ])', '\n', sec["content"])
        return result
    if isinstance(result, dict) and "raw" in result:
        parsed = extract_from_raw(result["raw"])
        for sec in parsed.get("sections", []):
            if "content" in sec:
                sec["content"] = re.sub(r'(?<=[.!?])\s+(?=[A-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ])', '\n', sec["content"])
        return parsed
    return result

async def main():
    courses = {}
    for code, name, focus in LANGS:
        sys.stdout.write(name + "... ")
        sys.stdout.flush()
        try:
            result = await generate(code, name, focus)
            courses[code] = result
            secs = len(result.get("sections", []))
            chars = sum(len(s.get("content", "")) for s in result.get("sections", []))
            sys.stdout.write(str(secs) + " sections, " + str(chars) + " chars\n")
        except Exception as e:
            sys.stdout.write("ERROR: " + str(e) + "\n")
            courses[code] = {"title": name + " - Cours complet", "sections": []}
        with open("/app/data/langue_courses.json", "w") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        await asyncio.sleep(0.5)
    sys.stdout.write("Done: " + str(len(courses)) + " courses\n")

if __name__ == "__main__":
    asyncio.run(main())
