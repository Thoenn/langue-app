import re, os, unicodedata
from database import get_sync_conn
from config import LANGUE_FILES_DIR

LANG_MAP = [('en','EN'),('la','LA'),('es','ES'),('de','DE'),('it','IT'),
            ('ru','RU'),('zh','CN'),('ja','JP'),('kr','KR'),('km','KM')]
LANG_CODES = [c[0] for c in LANG_MAP]
CATEGORY_ORDER = [
    "salutations","approbation","expressions","connecteurs","verbes","questions",
    "quotidienne","technologie","developpement","architecture","ia","jeux",
    "travail","banque","pedagogie","sports","lecture","graphisme","faux amis","erreurs",
]
CATEGORY_EMOJI = {
    "salutations":"👋","approbation":"✅","expressions":"🗣️","connecteurs":"🔗",
    "verbes":"🔄","questions":"🎯","quotidienne":"🏠","technologie":"📱",
    "developpement":"💻","architecture":"🏗️","ia":"🤖","jeux":"🎮",
    "travail":"💼","banque":"🏦","pedagogie":"📚","sports":"🎾",
    "lecture":"📖","graphisme":"🎨","faux amis":"⚠️","erreurs":"✏️",
}

FR_CORRECTIONS = {
    "c'est": "c'est", "c est": "c'est", "j'ai": "j'ai", "j ai": "j'ai",
    "n'est": "n'est", "n est": "n'est", "c'est quoi": "c'est quoi",
    "comment faire": "comment faire", "je ne sais pas": "je ne sais pas",
    "s'il te plaît": "s'il te plaît", "s'il vous plaît": "s'il vous plaît",
    "deso": "désolé", "ducoup": "du coup", "stp": "s.t.p.",
    "pcq": "p.c.q.", "pk": "pourquoi", "qd": "quand",
    "desolé": "désolé", "desole": "désolé",
    "appart": "appartement", "mdp": "mot de passe",
    "voiture": "voiture", "téléphone": "téléphone",
    "deménagement": "déménagement", "apéro": "apéritif",
}

def fix_french(text):
    t = text.strip().strip('"').strip('"').strip("'").strip("«").strip("»").strip()
    if t.startswith('"') or t.startswith("'"):
        t = t[1:]
    if t.endswith('"') or t.endswith("'"):
        t = t[:-1]
    t = re.sub(r'\s+', ' ', t).strip()
    for wrong, correct in FR_CORRECTIONS.items():
        t = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, t)
    return t

def is_pertinent(text):
    t = text.strip().strip('"').strip("'")
    if len(t) < 2: return False
    if t.startswith('"') or t.startswith("'") or t.startswith("«"):
        return False
    if re.match(r'^["\'"«].{10,}["\'"»]?$', t):
        return False
    if t.count(' ') > 15: return False
    non_relevant = [
        "Cc c carole", "Cc g fini", "Cc je peux", "Cc tu pourrais",
        "Cc demain", "T chez toi", "D'acc mettre", "Dite moi",
        "Elle répond", "Hey pour", "Non c bon", "O final",
        "Sinon ça va", "Super c toi", "Un peu la flemme",
        "Yep vous allez", "Bah sa a été", "A deso o",
        "A ouais pq", "Coucou est-ce",
    ]
    for nr in non_relevant:
        if nr.lower() in t.lower():
            return False
    if re.search(r'[😀-🙏🀄-🃏]', t) and len(t) > 30:
        return False
    return True

def parse_multilang(content):
    entries = []
    blocks = content.split("\n\n---\n\n")
    current_cat = "expressions"
    for block in blocks:
        lines = block.strip().split("\n")
        if not lines: continue
        h = lines[0].strip()
        if h.startswith("#"):
            hl = h.lower()
            if any(w in hl for w in ["salutation","politesse","bonjour"]): current_cat = "salutations"
            elif any(w in hl for w in ["approbation","négation","oui"]): current_cat = "approbation"
            elif any(w in hl for w in ["expression","tournure"]): current_cat = "expressions"
            elif any(w in hl for w in ["verbe"]): current_cat = "verbes"
            elif any(w in hl for w in ["question"]): current_cat = "questions"
            elif any(w in hl for w in ["technologie","informatique"]): current_cat = "technologie"
            elif any(w in hl for w in ["jeu","mmo"]): current_cat = "jeux"
            elif any(w in hl for w in ["intelligence artificielle","ia"]): current_cat = "ia"
            elif any(w in hl for w in ["faux ami"]): current_cat = "faux amis"
            elif any(w in hl for w in ["erreur"]): current_cat = "erreurs"
            elif any(w in hl for w in ["mot de liaison","connecteur"]): current_cat = "connecteurs"
            elif any(w in hl for w in ["pédagogie","apprentissage"]): current_cat = "pedagogie"
            elif any(w in hl for w in ["tennis","sport"]): current_cat = "sports"
            elif any(w in hl for w in ["lecture","roman"]): current_cat = "lecture"
            elif any(w in hl for w in ["travail","professionnel"]): current_cat = "travail"
            elif any(w in hl for w in ["vie quotidienne","quotidienne"]): current_cat = "quotidienne"
            elif any(w in hl for w in ["développement","logiciel"]): current_cat = "developpement"
            elif any(w in hl for w in ["architecture","concept"]): current_cat = "architecture"
            elif any(w in hl for w in ["graphisme","3d","audio"]): current_cat = "graphisme"

        fr_word = ""
        translations = {}; phonetics = {}; examples = {}; example_fr = ""
        for line in lines:
            ls = line.strip()
            if ls.startswith("**FR :**"):
                fr_word = ls.replace("**FR :**","").strip()
                fr_word = re.sub(r'\*\*.*?\*\*','',fr_word).strip()
            for code, upper in LANG_MAP:
                m = re.search(rf'\*\*{re.escape(upper)}\s*:\s*\*\*(.*?)(?:\s*$|\s*—)', ls)
                if m:
                    val = m.group(1).strip()
                    translations[code] = val
                ph = re.search(rf'\*\*{re.escape(upper)}\s*:\s*\*\*.*?\(([^)]+)\)', ls)
                if ph:
                    phonetics[code] = ph.group(1).strip()
            ex = re.search(r'>\s*\*Ex:\s*(.*?)(?:\*|$)', ls)
            if ex:
                ex_text = ex.group(1).strip()
                if "→" in ex_text:
                    parts = ex_text.split("→",1)
                    example_fr = parts[0].strip()
                    examples["en"] = parts[1].strip()
                else:
                    example_fr = ex_text
        if fr_word and len(translations) >= 3:
            entries.append({"french": fr_word, "category": current_cat,
                "translations": translations, "phonetics": phonetics,
                "example_fr": example_fr, "examples": examples})
    return entries

def parse_fr_en(content):
    entries = []; lines = content.split("\n"); current_cat = "expressions"; in_table = False
    for line in lines:
        s = line.strip()
        if s.startswith("#") or s.startswith("###"):
            hl = s.lower()
            if any(w in hl for w in ["salutation","politesse"]): current_cat = "salutations"
            elif any(w in hl for w in ["approbation","négation"]): current_cat = "approbation"
            elif any(w in hl for w in ["expression","tournure"]): current_cat = "expressions"
            elif any(w in hl for w in ["mot de liaison","connecteur"]): current_cat = "connecteurs"
            elif any(w in hl for w in ["verbe","modaux","auxiliaire","action"]): current_cat = "verbes"
            elif any(w in hl for w in ["question"]): current_cat = "questions"
            elif any(w in hl for w in ["technologie","informatique"]): current_cat = "technologie"
            elif any(w in hl for w in ["développement"]): current_cat = "developpement"
            elif any(w in hl for w in ["architecture"]): current_cat = "architecture"
            elif any(w in hl for w in ["ia","intelligence artificielle"]): current_cat = "ia"
            elif any(w in hl for w in ["jeu"]): current_cat = "jeux"
            elif any(w in hl for w in ["travail","professionnel","expérience","compétence","formation"]): current_cat = "travail"
            elif any(w in hl for w in ["banque","administratif"]): current_cat = "banque"
            elif any(w in hl for w in ["vie quotidienne","quotidienne"]): current_cat = "quotidienne"
            elif any(w in hl for w in ["pédagogie","apprentissage"]): current_cat = "pedagogie"
            elif any(w in hl for w in ["graphisme","3d","audio"]): current_cat = "graphisme"
            elif any(w in hl for w in ["tennis","sport"]): current_cat = "sports"
            elif any(w in hl for w in ["lecture","créatif"]): current_cat = "lecture"
            elif any(w in hl for w in ["message texto"]): current_cat = None
            elif any(w in hl for w in ["erreur","fréquentes"]): current_cat = "erreurs"
            elif any(w in hl for w in ["faux ami","piège"]): current_cat = "faux amis"
            elif any(w in hl for w in ["mot essentiel","top 50"]): current_cat = None
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not in_table: in_table = True; continue
            if s.replace("|","").replace("-","").replace(":","").strip() == "": continue
            if current_cat is None: continue
            if len(cells) >= 2:
                first = cells[0].strip()
                # Skip numbered rows (e.g., "1 | oui / non | yes / no")
                if first.isdigit() and len(cells) >= 3:
                    fr = cells[1].strip()
                    target = cells[2].strip()
                else:
                    fr = first
                    target = cells[1].strip()
                if (fr and target and len(fr) < 150 and not fr.startswith("**")
                    and fr not in ["Français","----------","Mot/Expression","Mot","Expression","Verbe","Message"]):
                    fr_clean = fr.split("(")[0].strip() if "(" in fr and fr.count("(") == 1 else fr
                    if is_pertinent(fr_clean):
                        entries.append({"french": fix_french(fr_clean), "category": current_cat or "expressions",
                            "translations": {"en": target.split("(")[0].strip() if "(" in target and target.count("(") == 1 else target},
                            "phonetics": {}, "example_fr": "", "examples": {}, "notes": cells[-1] if len(cells) > (3 if first.isdigit() else 2) else ""})
        else: in_table = False
    return entries

def parse_table_words(content):
    entries = []; lines = content.split("\n"); current_cat = "expressions"; in_table = False
    for line in lines:
        s = line.strip()
        if s.startswith("#"):
            hl = s.lower()
            if any(w in hl for w in ["salutation","politesse"]): current_cat = "salutations"
            elif any(w in hl for w in ["approbation","négation"]): current_cat = "approbation"
            elif any(w in hl for w in ["expression","courante"]): current_cat = "expressions"
            elif any(w in hl for w in ["verbe"]): current_cat = "verbes"
            elif any(w in hl for w in ["question"]): current_cat = "questions"
            elif any(w in hl for w in ["technologie","informatique"]): current_cat = "technologie"
            elif any(w in hl for w in ["jeu","divertissement"]): current_cat = "jeux"
            elif any(w in hl for w in ["vie quotidienne","quotidienne"]): current_cat = "quotidienne"
            elif any(w in hl for w in ["texte typique"]): current_cat = None
            elif any(w in hl for w in ["mot de liaison","connecteur"]): current_cat = "connecteurs"
            elif any(w in hl for w in ["erreur typique"]): current_cat = "erreurs"
            elif any(w in hl for w in ["modaux","auxiliaire"]): current_cat = "verbes"
            elif any(w in hl for w in ["mot utile","100+"]): current_cat = None
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not in_table: in_table = True; continue
            if s.replace("|","").replace("-","").replace(":","").strip() == "": continue
            if current_cat is None: continue
            if len(cells) >= 2:
                fr = cells[0].strip()
                target = cells[1].strip()
                if fr and target and len(fr) < 100 and not fr.startswith("**") and fr not in ["Mot/Expression","Mot","Expression","Verbe","Message"]:
                    if is_pertinent(fr):
                        t_clean = target
                        # Detect if 'target' is actually a French context note, not an English translation
                        fr_indicators = ['très ', 'informel', 'courant', 'abréviation', 'argot', 'anglicisme', 'littéralement', 'familier']
                        if any(fi in target.lower() for fi in fr_indicators):
                            t_clean = ''
                        if t_clean:
                            entries.append({"french": fix_french(fr), "category": current_cat,
                                "translations": {"en": t_clean}, "phonetics": {},
                                "example_fr": "", "examples": {}, "notes": cells[2] if len(cells) > 2 else ""})
        else: in_table = False
    return entries

def seed_sync():
    conn = get_sync_conn()
    if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] > 0:
        conn.close(); return

    for i, name in enumerate(CATEGORY_ORDER):
        conn.execute("INSERT INTO categories (name, emoji, order_index) VALUES (?, ?, ?)",
                     (name, CATEGORY_EMOJI.get(name, "📌"), i))
    conn.commit()

    all_entries = []
    for fname in os.listdir(LANGUE_FILES_DIR):
        fpath = os.path.join(LANGUE_FILES_DIR, fname)
        if not os.path.isfile(fpath): continue
        with open(fpath, "r", encoding="utf-8") as f:
            fc = f.read()
        if "10 Langues" in fc:
            all_entries.extend(parse_multilang(fc))
        elif "vocabulaire_complet" in fname:
            all_entries.extend(parse_fr_en(fc))
        elif "mon-vocabulaire" in fname:
            all_entries.extend(parse_table_words(fc))

    def norm_key(fr):
        k = fr.lower().strip()
        k = re.sub(r'[^a-z0-9éèêëàâùûüôîç\s]', '', k)
        k = re.sub(r'\s+', ' ', k).strip()
        # Normalize "ducoup" → "du coup", "daccord" → "d'accord"
        k = k.replace('ducoup', 'du coup')
        return k

    seen_fr = set()
    deduped = []
    for entry in sorted(all_entries, key=lambda e: -len(e["translations"])):
        key = norm_key(entry["french"])
        if key in seen_fr or not entry["french"].strip():
            continue
        seen_fr.add(key)
        deduped.append(entry)

    seen = set()
    for entry in deduped:
        key = entry["french"].lower().strip()
        if key in seen: continue
        seen.add(key)

        cat_row = conn.execute("SELECT id FROM categories WHERE name = ?", (entry["category"],)).fetchone()
        cat_id = cat_row[0] if cat_row else None

        cur = conn.execute("INSERT INTO words (french, category_id) VALUES (?, ?)",
                          (entry["french"].strip(), cat_id))
        wid = cur.lastrowid

        for lang, trans in entry["translations"].items():
            ph = entry["phonetics"].get(lang, "")
            ex_fr = entry.get("example_fr", "")
            ex_tg = entry["examples"].get(lang, "")
            notes = entry.get("notes", "")
            conn.execute(
                "INSERT INTO translations (word_id, language, translation, phonetic, example_fr, example_target, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (wid, lang, trans, ph, ex_fr, ex_tg, notes))

    conn.commit()
    conn.close()

async def seed_database():
    import asyncio
    await asyncio.to_thread(seed_sync)
