from fastapi import APIRouter
from database import get_sync_conn
import asyncio
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/stats", tags=["stats"])

LANG_NAMES = {"en":"English","la":"Latin","es":"Español","de":"Deutsch","it":"Italiano","ru":"Русский","zh":"中文","ja":"日本語","kr":"한국어","km":"ភាសាខ្មែរ"}

@router.get("/dashboard")
async def get_dashboard():
    def _q():
        conn = get_sync_conn()
        word_count = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        trans_count = conn.execute("SELECT COUNT(*) FROM translations").fetchone()[0]
        quiz_count = conn.execute("SELECT COUNT(*) FROM quiz_attempts").fetchone()[0]
        mistake_count = conn.execute("SELECT COUNT(*) FROM mistakes").fetchone()[0]

        lang_progress = {}
        for lang in LANG_NAMES:
            rows = conn.execute("SELECT * FROM user_progress WHERE language = ?", (lang,)).fetchall()
            if rows:
                total = len(rows)
                mastered = sum(1 for r in rows if r["mastery_level"] >= 0.8)
                avg_mastery = sum(r["mastery_level"] for r in rows) / total if total else 0
                lang_progress[lang] = {"total": total, "mastered": mastered, "avg_mastery": round(avg_mastery, 2)}

        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recent = conn.execute("SELECT * FROM quiz_attempts WHERE timestamp >= ?", (week_ago,)).fetchall()
        recent_total = len(recent)
        recent_correct = sum(1 for r in recent if r["correct"])

        conn.close()
        return {
            "word_count": word_count, "translation_count": trans_count,
            "quiz_attempts": quiz_count, "mistake_count": mistake_count,
            "lang_progress": lang_progress,
            "recent_activity": {"total": recent_total, "correct": recent_correct, "accuracy": round((recent_correct / recent_total * 100), 1) if recent_total else 0},
        }
    return await asyncio.to_thread(_q)

@router.get("/weekly")
async def get_weekly_stats():
    def _q():
        conn = get_sync_conn()
        days = []
        for i in range(6, -1, -1):
            day = datetime.now(timezone.utc) - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            day_end = (day.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat()
            attempts = conn.execute("SELECT * FROM quiz_attempts WHERE timestamp >= ? AND timestamp < ?", (day_start, day_end)).fetchall()
            total = len(attempts)
            correct = sum(1 for a in attempts if a["correct"])
            mistakes = total - correct
            days.append({"date": day_start, "total": total, "correct": correct, "mistakes": mistakes, "accuracy": round((correct / total * 100), 1) if total else 0})
        conn.close()
        return {"days": days}
    return await asyncio.to_thread(_q)

@router.get("/weaknesses")
async def get_weaknesses(language: str = "en"):
    def _q():
        conn = get_sync_conn()
        rows = conn.execute("SELECT * FROM mistakes WHERE language = ? AND reviewed = 0", (language,)).fetchall()
        conn.close()
        words_map = {}
        for r in rows:
            key = r["correct_answer"].lower()
            if key not in words_map:
                words_map[key] = {"word": r["correct_answer"], "count": 0, "user_answers": []}
            words_map[key]["count"] += 1
            words_map[key]["user_answers"].append(r["user_answer"])
        top = sorted(words_map.values(), key=lambda x: x["count"], reverse=True)[:20]
        return {"weaknesses": top}
    return await asyncio.to_thread(_q)
