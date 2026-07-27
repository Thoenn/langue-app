from fastapi import APIRouter
from database import get_sync_conn
import asyncio
from datetime import datetime, timezone

router = APIRouter(prefix="/api/progress", tags=["progress"])

@router.get("/overview")
async def get_progress_overview(language: str = "en"):
    def _q():
        conn = get_sync_conn()
        rows = conn.execute("SELECT * FROM user_progress WHERE language = ?", (language,)).fetchall()
        conn.close()
        total = len(rows)
        if total == 0:
            return {"total_words": 0, "mastered": 0, "learning": 0, "to_review": 0, "due_for_review": 0, "accuracy": 0, "total_answers": 0}
        mastered = sum(1 for r in rows if r["mastery_level"] >= 0.8)
        learning = sum(1 for r in rows if 0.3 <= r["mastery_level"] < 0.8)
        to_review = sum(1 for r in rows if r["mastery_level"] < 0.3)
        total_answers = sum(r["correct_count"] + r["wrong_count"] for r in rows)
        correct = sum(r["correct_count"] for r in rows)
        accuracy = round((correct / total_answers * 100), 1) if total_answers else 0
        now = datetime.now(timezone.utc).isoformat()
        due = sum(1 for r in rows if r["next_review"] and r["next_review"] <= now)
        return {"total_words": total, "mastered": mastered, "learning": learning, "to_review": to_review, "due_for_review": due, "accuracy": accuracy, "total_answers": total_answers}
    return await asyncio.to_thread(_q)

@router.get("/words")
async def get_progress_words(language: str = "en", status: str = None):
    def _q():
        conn = get_sync_conn()
        where = "p.language = ?"
        params = [language]
        if status == "mastered":
            where += " AND p.mastery_level >= 0.8"
        elif status == "learning":
            where += " AND p.mastery_level >= 0.3 AND p.mastery_level < 0.8"
        elif status == "to_review":
            where += " AND p.mastery_level < 0.3"
        rows = conn.execute(
            f"SELECT p.*, w.french FROM user_progress p JOIN words w ON w.id = p.word_id WHERE {where} ORDER BY p.mastery_level",
            params,
        ).fetchall()
        items = []
        for r in rows:
            t = conn.execute("SELECT translation FROM translations WHERE word_id = ? AND language = ?", (r["word_id"], language)).fetchone()
            items.append({
                "id": r["id"], "word_id": r["word_id"], "french": r["french"],
                "translation": t["translation"] if t else "",
                "review_count": r["review_count"], "correct_count": r["correct_count"],
                "wrong_count": r["wrong_count"], "mastery_level": round(r["mastery_level"], 2),
                "last_reviewed": r["last_reviewed"], "next_review": r["next_review"],
            })
        conn.close()
        return {"items": items}
    return await asyncio.to_thread(_q)

@router.get("/mistakes")
async def get_mistakes(language: str = None, reviewed: bool = None):
    def _q():
        conn = get_sync_conn()
        params = []
        where = []
        if language:
            where.append("language = ?"); params.append(language)
        if reviewed is not None:
            where.append("reviewed = ?"); params.append(1 if reviewed else 0)
        w = " WHERE " + " AND ".join(where) if where else ""
        rows = conn.execute(f"SELECT * FROM mistakes{w} ORDER BY timestamp DESC LIMIT 100", params).fetchall()
        conn.close()
        return [{"id": r["id"], "language": r["language"], "word_id": r["word_id"], "mistake_type": r["mistake_type"], "user_answer": r["user_answer"], "correct_answer": r["correct_answer"], "context": r["context"], "timestamp": r["timestamp"], "reviewed": bool(r["reviewed"])} for r in rows]
    return await asyncio.to_thread(_q)

@router.post("/mistakes/{mistake_id}/review")
async def review_mistake(mistake_id: int):
    def _q():
        conn = get_sync_conn()
        conn.execute("UPDATE mistakes SET reviewed = 1, reviewed_at = ? WHERE id = ?", (datetime.now(timezone.utc).isoformat(), mistake_id))
        conn.commit()
        conn.close()
        return {"status": "ok"}
    return await asyncio.to_thread(_q)

@router.get("/due")
async def get_due_words(language: str = "en"):
    def _q():
        conn = get_sync_conn()
        now = datetime.now(timezone.utc).isoformat()
        rows = conn.execute(
            "SELECT p.*, w.french FROM user_progress p JOIN words w ON w.id = p.word_id WHERE p.language = ? AND p.next_review <= ? ORDER BY p.next_review LIMIT 20",
            (language, now),
        ).fetchall()
        items = []
        for r in rows:
            t = conn.execute("SELECT translation FROM translations WHERE word_id = ? AND language = ?", (r["word_id"], language)).fetchone()
            items.append({"id": r["id"], "word_id": r["word_id"], "french": r["french"], "translation": t["translation"] if t else "", "mastery_level": round(r["mastery_level"], 2)})
        conn.close()
        return {"items": items}
    return await asyncio.to_thread(_q)
