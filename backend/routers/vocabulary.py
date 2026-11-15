from fastapi import APIRouter, HTTPException
from database import get_sync_conn, dict_from_row
from pydantic import BaseModel
from typing import Optional, Dict
import asyncio

router = APIRouter(prefix="/api/vocabulary", tags=["vocabulary"])

LANG_NAMES = {"en":"English","la":"Latin","es":"Español","de":"Deutsch","it":"Italiano","ru":"Русский","zh":"中文","ja":"日本語","kr":"한국어","km":"ភាសាខ្មែរ"}

class TranslationData(BaseModel):
    translation: str
    phonetic: str = ""
    example_fr: str = ""
    example_target: str = ""
    notes: str = ""

class WordCreate(BaseModel):
    french: str
    category: Optional[str] = None
    translations: Dict[str, TranslationData] = {}

class WordUpdate(BaseModel):
    french: Optional[str] = None
    category: Optional[str] = None
    translations: Optional[Dict[str, TranslationData]] = None

def _normalize_french(text):
    return text.strip().strip('"').strip("'").strip()

@router.get("/languages")
async def get_languages():
    return LANG_NAMES

@router.get("/categories")
async def get_categories():
    def _q():
        conn = get_sync_conn()
        rows = conn.execute("SELECT c.*, COUNT(w.id) as cnt FROM categories c LEFT JOIN words w ON w.category_id = c.id GROUP BY c.id ORDER BY c.order_index").fetchall()
        conn.close()
        return [{"id": r["id"], "name": r["name"], "emoji": r["emoji"], "count": r["cnt"]} for r in rows]
    return await asyncio.to_thread(_q)

TRI = {
    # « récemment ajouté » d'abord : le tri par défaut quand on vient de saisir du neuf
    "recent": "COALESCE(w.created_at,'') DESC, w.id DESC",
    "modifie": "COALESCE(w.updated_at, w.created_at, '') DESC, w.id DESC",
    "alpha": "w.french COLLATE NOCASE ASC",
    # les favoris remontent, puis le plus récent
    "favoris": "COALESCE(w.favorite,0) DESC, COALESCE(w.created_at,'') DESC, w.id DESC",
}


@router.get("/words")
async def get_words(language: str = "en", category: str = None, search: str = None,
                    page: int = 1, per_page: int = 50, kind: str = None, source: str = None,
                    sort: str = "recent", favorite: int = None, collection: int = None):
    """Liste les entrées.

    kind       : mot / phrase / correction
    source     : recap-it, recap-dev, recap-magistrats, recap-multilingue, app
    sort       : recent (défaut) / modifie / alpha / favoris
    favorite   : 1 pour ne garder que les favoris
    collection : identifiant de collection
    search     : cherche aussi dans les notes — c'est là que vivent les nuances
    """
    def _q():
        conn = get_sync_conn()
        params = [language]
        where = "t.language = ?"
        if category:
            where += " AND c.name = ?"
            params.append(category)
        if kind:
            where += " AND COALESCE(w.kind, 'mot') = ?"
            params.append(kind)
        if source:
            where += " AND COALESCE(w.source, 'app') = ?"
            params.append(source)
        if favorite:
            where += " AND COALESCE(w.favorite,0) = 1"
        if collection:
            where += " AND EXISTS (SELECT 1 FROM word_collections wc WHERE wc.word_id = w.id AND wc.collection_id = ?)"
            params.append(collection)
        if search:
            where += " AND (w.french LIKE ? OR t.translation LIKE ? OR t.notes LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        total = conn.execute(f"SELECT COUNT(*) FROM words w JOIN translations t ON t.word_id = w.id LEFT JOIN categories c ON c.id = w.category_id WHERE {where}", params).fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            f"SELECT w.id, w.french, COALESCE(w.kind,'mot') AS kind, COALESCE(w.source,'app') AS source, COALESCE(w.favorite,0) AS favorite, w.created_at, c.name as cat_name, c.emoji as cat_emoji, w.subcategory, t.translation, t.phonetic, t.example_fr, t.example_target, t.notes FROM words w JOIN translations t ON t.word_id = w.id LEFT JOIN categories c ON c.id = w.category_id WHERE {where} ORDER BY {TRI.get(sort, TRI['recent'])} LIMIT ? OFFSET ?",
            params + [per_page, offset],
        ).fetchall()
        # les appartenances aux collections sont lues avant de fermer la connexion
        liens = {}
        for x in conn.execute("SELECT word_id, collection_id FROM word_collections"):
            liens.setdefault(x["word_id"], []).append(x["collection_id"])
        conn.close()
        return {"items": [{"id": r["id"], "french": r["french"], "category": r["cat_name"], "category_emoji": r["cat_emoji"] or "", "subcategory": r["subcategory"], "kind": r["kind"], "source": r["source"],
                     "favorite": int(r["favorite"] or 0), "created_at": r["created_at"] or "",
                     "collection_ids": liens.get(r["id"], []),
                     "translation": r["translation"], "phonetic": r["phonetic"] or "", "example_fr": r["example_fr"] or "", "example_target": r["example_target"] or "", "notes": r["notes"] or ""} for r in rows], "total": total, "page": page, "per_page": per_page}
    return await asyncio.to_thread(_q)

@router.get("/kinds")
async def get_kinds():
    """Ce que contient le carnet, par nature : de quoi construire des compteurs honnêtes."""
    def _q():
        conn = get_sync_conn()
        rows = conn.execute(
            "SELECT COALESCE(kind,'mot') AS kind, COUNT(*) AS n FROM words GROUP BY 1").fetchall()
        sources = conn.execute(
            "SELECT COALESCE(source,'app') AS source, COUNT(*) AS n FROM words GROUP BY 1 ORDER BY 2 DESC"
        ).fetchall()
        conn.close()
        return {"kinds": {r["kind"]: r["n"] for r in rows},
                "sources": {r["source"]: r["n"] for r in sources}}
    return await asyncio.to_thread(_q)


@router.get("/words/{word_id}")
async def get_word(word_id: int):
    def _q():
        conn = get_sync_conn()
        row = conn.execute("SELECT w.*, c.name as cat_name, c.emoji as cat_emoji FROM words w LEFT JOIN categories c ON c.id = w.category_id WHERE w.id = ?", (word_id,)).fetchone()
        if not row:
            conn.close()
            raise HTTPException(404, "Mot non trouvé")
        trans_rows = conn.execute("SELECT * FROM translations WHERE word_id = ?", (word_id,)).fetchall()
        conn.close()
        translations = {}
        for t in trans_rows:
            translations[t["language"]] = {"translation": t["translation"], "phonetic": t["phonetic"] or "", "example_fr": t["example_fr"] or "", "example_target": t["example_target"] or "", "notes": t["notes"] or ""}
        return {"id": row["id"], "french": row["french"], "category": row["cat_name"], "category_emoji": row["cat_emoji"] or "", "subcategory": row["subcategory"] or "", "translations": translations}
    return await asyncio.to_thread(_q)

@router.post("/words")
async def create_word(data: WordCreate):
    def _q():
        conn = get_sync_conn()
        french = _normalize_french(data.french)
        if not french:
            conn.close()
            raise HTTPException(400, "Le mot français ne peut pas être vide")

        cat_id = None
        if data.category:
            r = conn.execute("SELECT id FROM categories WHERE name = ?", (data.category,)).fetchone()
            cat_id = r[0] if r else None

        cur = conn.execute(
            "INSERT INTO words (french, category_id, created_at, updated_at) "
            "VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)", (french, cat_id))
        wid = cur.lastrowid

        for lang, t in data.translations.items():
            conn.execute(
                "INSERT INTO translations (word_id, language, translation, phonetic, example_fr, example_target, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (wid, lang, t.translation, t.phonetic, t.example_fr, t.example_target, t.notes),
            )

        conn.commit()
        conn.close()
        return {"id": wid, "french": french}
    return await asyncio.to_thread(_q)

@router.put("/words/{word_id}")
async def update_word(word_id: int, data: WordUpdate):
    def _q():
        conn = get_sync_conn()
        row = conn.execute("SELECT id FROM words WHERE id = ?", (word_id,)).fetchone()
        if not row:
            conn.close()
            raise HTTPException(404, "Mot non trouvé")

        if data.french is not None:
            french = _normalize_french(data.french)
            conn.execute("UPDATE words SET french = ? WHERE id = ?", (french, word_id))
        conn.execute("UPDATE words SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (word_id,))

        if data.category is not None:
            cat_id = None
            if data.category:
                r = conn.execute("SELECT id FROM categories WHERE name = ?", (data.category,)).fetchone()
                cat_id = r[0] if r else None
            conn.execute("UPDATE words SET category_id = ? WHERE id = ?", (cat_id, word_id))

        if data.translations is not None:
            for lang, t in data.translations.items():
                existing = conn.execute("SELECT id FROM translations WHERE word_id = ? AND language = ?", (word_id, lang)).fetchone()
                if existing:
                    conn.execute(
                        "UPDATE translations SET translation=?, phonetic=?, example_fr=?, example_target=?, notes=? WHERE word_id=? AND language=?",
                        (t.translation, t.phonetic, t.example_fr, t.example_target, t.notes, word_id, lang),
                    )
                else:
                    conn.execute(
                        "INSERT INTO translations (word_id, language, translation, phonetic, example_fr, example_target, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (word_id, lang, t.translation, t.phonetic, t.example_fr, t.example_target, t.notes),
                    )

        conn.commit()
        conn.close()
        return {"status": "ok", "id": word_id}
    return await asyncio.to_thread(_q)

@router.delete("/words/{word_id}")
async def delete_word(word_id: int):
    def _q():
        conn = get_sync_conn()
        row = conn.execute("SELECT id, french FROM words WHERE id = ?", (word_id,)).fetchone()
        if not row:
            conn.close()
            raise HTTPException(404, "Mot non trouvé")
        french = row["french"]

        conn.execute("DELETE FROM word_collections WHERE word_id = ?", (word_id,))
        conn.execute("DELETE FROM user_progress WHERE word_id = ?", (word_id,))
        conn.execute("DELETE FROM mistakes WHERE word_id = ?", (word_id,))
        conn.execute("DELETE FROM quiz_questions WHERE word_id = ?", (word_id,))
        conn.execute("DELETE FROM translations WHERE word_id = ?", (word_id,))
        conn.execute("DELETE FROM words WHERE id = ?", (word_id,))

        conn.commit()
        conn.close()
        return {"status": "ok", "deleted": french}
    return await asyncio.to_thread(_q)

@router.post("/words/{word_id}/favorite")
async def set_favorite(word_id: int, value: int = None):
    """Marque une entrée comme « important à connaître ». Sans `value`, bascule l'état."""
    def _q():
        conn = get_sync_conn()
        row = conn.execute("SELECT COALESCE(favorite,0) FROM words WHERE id = ?", (word_id,)).fetchone()
        if not row:
            conn.close()
            raise HTTPException(404, "Entrée non trouvée")
        nouveau = (0 if row[0] else 1) if value is None else (1 if value else 0)
        conn.execute("UPDATE words SET favorite = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                     (nouveau, word_id))
        conn.commit()
        conn.close()
        return {"id": word_id, "favorite": nouveau}
    return await asyncio.to_thread(_q)


@router.get("/collections")
async def get_collections():
    """Les paquets nommés, avec leur nombre d'entrées."""
    def _q():
        conn = get_sync_conn()
        rows = conn.execute("""SELECT c.id, c.name, c.emoji, COUNT(wc.word_id) AS n
                               FROM collections c
                               LEFT JOIN word_collections wc ON wc.collection_id = c.id
                               GROUP BY c.id ORDER BY c.name COLLATE NOCASE""").fetchall()
        conn.close()
        return [{"id": r["id"], "name": r["name"], "emoji": r["emoji"] or "", "count": r["n"]} for r in rows]
    return await asyncio.to_thread(_q)


@router.post("/collections")
async def create_collection(name: str, emoji: str = ""):
    def _q():
        conn = get_sync_conn()
        propre = name.strip()
        if not propre:
            conn.close()
            raise HTTPException(400, "Le nom de la collection est requis")
        row = conn.execute("SELECT id FROM collections WHERE name = ? COLLATE NOCASE", (propre,)).fetchone()
        if row:
            conn.close()
            return {"id": row["id"], "name": propre, "existant": True}
        cur = conn.execute("INSERT INTO collections (name, emoji) VALUES (?, ?)", (propre, emoji))
        conn.commit()
        cid = cur.lastrowid
        conn.close()
        return {"id": cid, "name": propre, "existant": False}
    return await asyncio.to_thread(_q)


@router.delete("/collections/{collection_id}")
async def delete_collection(collection_id: int):
    def _q():
        conn = get_sync_conn()
        row = conn.execute("SELECT name FROM collections WHERE id = ?", (collection_id,)).fetchone()
        if not row:
            conn.close()
            raise HTTPException(404, "Collection non trouvée")
        conn.execute("DELETE FROM word_collections WHERE collection_id = ?", (collection_id,))
        conn.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        conn.commit()
        conn.close()
        return {"status": "ok", "supprimee": row["name"]}
    return await asyncio.to_thread(_q)


@router.post("/collections/{collection_id}/words/{word_id}")
async def add_to_collection(collection_id: int, word_id: int):
    def _q():
        conn = get_sync_conn()
        if not conn.execute("SELECT 1 FROM collections WHERE id = ?", (collection_id,)).fetchone():
            conn.close()
            raise HTTPException(404, "Collection non trouvée")
        if not conn.execute("SELECT 1 FROM words WHERE id = ?", (word_id,)).fetchone():
            conn.close()
            raise HTTPException(404, "Entrée non trouvée")
        conn.execute("INSERT OR IGNORE INTO word_collections (word_id, collection_id) VALUES (?, ?)",
                     (word_id, collection_id))
        conn.execute("UPDATE words SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (word_id,))
        conn.commit()
        conn.close()
        return {"status": "ok", "collection_id": collection_id, "word_id": word_id}
    return await asyncio.to_thread(_q)


@router.delete("/collections/{collection_id}/words/{word_id}")
async def remove_from_collection(collection_id: int, word_id: int):
    def _q():
        conn = get_sync_conn()
        conn.execute("DELETE FROM word_collections WHERE collection_id = ? AND word_id = ?",
                     (collection_id, word_id))
        conn.commit()
        conn.close()
        return {"status": "ok"}
    return await asyncio.to_thread(_q)


@router.post("/words/{word_id}/translations")
async def add_translation(word_id: int, language: str, data: TranslationData):
    def _q():
        conn = get_sync_conn()
        row = conn.execute("SELECT id FROM words WHERE id = ?", (word_id,)).fetchone()
        if not row:
            conn.close()
            raise HTTPException(404, "Mot non trouvé")
        existing = conn.execute("SELECT id FROM translations WHERE word_id = ? AND language = ?", (word_id, language)).fetchone()
        if existing:
            conn.close()
            raise HTTPException(400, f"Traduction déjà existante pour {language}")
        conn.execute(
            "INSERT INTO translations (word_id, language, translation, phonetic, example_fr, example_target, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (word_id, language, data.translation, data.phonetic, data.example_fr, data.example_target, data.notes),
        )
        conn.commit()
        conn.close()
        return {"status": "ok"}
    return await asyncio.to_thread(_q)

@router.delete("/words/{word_id}/translations/{language}")
async def delete_translation(word_id: int, language: str):
    def _q():
        conn = get_sync_conn()
        conn.execute("DELETE FROM translations WHERE word_id = ? AND language = ?", (word_id, language))
        conn.commit()
        conn.close()
        return {"status": "ok"}
    return await asyncio.to_thread(_q)
