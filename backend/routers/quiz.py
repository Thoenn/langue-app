from fastapi import APIRouter, HTTPException
from database import get_sync_conn
from pydantic import BaseModel
import random, json, asyncio
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

class QuizAnswer(BaseModel):
    question_id: int
    answer: str
    time_spent: float = 0.0

@router.get("/generate")
async def generate_quiz(language: str = "en", category: str = None, count: int = 10):
    def _q():
        conn = get_sync_conn()
        if category:
            words = conn.execute(
                "SELECT w.id, w.french FROM words w JOIN categories c ON c.id = w.category_id JOIN translations t ON t.word_id = w.id WHERE t.language = ? AND c.name = ? ORDER BY RANDOM() LIMIT ?",
                (language, category, count),
            ).fetchall()
        else:
            words = conn.execute(
                "SELECT DISTINCT w.id, w.french FROM words w JOIN translations t ON t.word_id = w.id WHERE t.language = ? ORDER BY RANDOM() LIMIT ?",
                (language, count),
            ).fetchall()

        if not words:
            conn.close()
            return {"questions": [], "error": "No words found"}

        all_words = conn.execute("SELECT id, french FROM words ORDER BY RANDOM()").fetchall()
        questions = []
        for w in words:
            t_row = conn.execute("SELECT translation FROM translations WHERE word_id = ? AND language = ?", (w["id"], language)).fetchone()
            if not t_row:
                continue
            translation = t_row["translation"]

            qtype = random.choice(["fr_to_target", "target_to_fr"])
            if qtype == "fr_to_target":
                question_text = f"Quelle est la traduction en {language} de « {w['french']} » ?"
                correct = translation
            else:
                question_text = f"Que signifie « {translation} » en français ?"
                correct = w["french"]

            wrongs = []
            for w2 in all_words:
                if w2["id"] != w["id"] and len(wrongs) < 3:
                    t2 = conn.execute("SELECT translation FROM translations WHERE word_id = ? AND language = ?", (w2["id"], language)).fetchone()
                    if t2 and t2["translation"]:
                        wrongs.append(t2["translation"] if qtype == "fr_to_target" else w2["french"])
            while len(wrongs) < 3:
                wrongs.append("(pas de réponse)")

            cur = conn.execute(
                "INSERT INTO quiz_questions (word_id, language, question_type, question_text, correct_answer, wrong_answers) VALUES (?, ?, ?, ?, ?, ?)",
                (w["id"], language, qtype, question_text, correct, json.dumps(wrongs)),
            )
            qid = cur.lastrowid

            options = [correct] + wrongs
            random.shuffle(options)

            questions.append({
                "id": qid, "word_id": w["id"],
                "question_text": question_text, "correct_answer": correct,
                "wrong_answers": wrongs, "options": options,
            })

        conn.commit()
        conn.close()
        return {"questions": questions}
    return await asyncio.to_thread(_q)

@router.post("/answer")
async def submit_answer(data: QuizAnswer):
    def _q():
        conn = get_sync_conn()
        row = conn.execute("SELECT * FROM quiz_questions WHERE id = ?", (data.question_id,)).fetchone()
        if not row:
            conn.close()
            raise HTTPException(404, "Question not found")

        correct = data.answer.strip().lower() == row["correct_answer"].strip().lower()

        conn.execute(
            "INSERT INTO quiz_attempts (question_id, language, user_answer, correct, time_spent) VALUES (?, ?, ?, ?, ?)",
            (data.question_id, row["language"], data.answer, 1 if correct else 0, data.time_spent),
        )

        if row["word_id"]:
            prog = conn.execute("SELECT * FROM user_progress WHERE word_id = ? AND language = ?", (row["word_id"], row["language"])).fetchone()
            if prog:
                mastery = prog["mastery_level"]
                if correct:
                    mastery = min(1.0, mastery + 0.1)
                else:
                    mastery = max(0.0, mastery - 0.1)

                if mastery < 0.3:
                    next_review = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                elif mastery < 0.6:
                    next_review = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
                elif mastery < 0.8:
                    next_review = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
                else:
                    next_review = (datetime.now(timezone.utc) + timedelta(weeks=1)).isoformat()

                conn.execute(
                    "UPDATE user_progress SET review_count = review_count + 1, correct_count = correct_count + ?, wrong_count = wrong_count + ?, mastery_level = ?, last_reviewed = ?, next_review = ? WHERE id = ?",
                    (1 if correct else 0, 0 if correct else 1, mastery, datetime.now(timezone.utc).isoformat(), next_review, prog["id"]),
                )
            else:
                mastery = 0.1 if correct else 0.0
                next_review = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                conn.execute(
                    "INSERT INTO user_progress (word_id, language, review_count, correct_count, wrong_count, mastery_level, last_reviewed, next_review) VALUES (?, ?, 1, ?, ?, ?, ?, ?)",
                    (row["word_id"], row["language"], 1 if correct else 0, 0 if correct else 1, mastery, datetime.now(timezone.utc).isoformat(), next_review),
                )

            if not correct:
                conn.execute(
                    "INSERT INTO mistakes (word_id, language, mistake_type, user_answer, correct_answer, context) VALUES (?, ?, 'quiz', ?, ?, ?)",
                    (row["word_id"], row["language"], data.answer, row["correct_answer"], row["question_text"]),
                )

        conn.commit()
        conn.close()
        return {"correct": correct, "correct_answer": row["correct_answer"]}
    return await asyncio.to_thread(_q)

@router.get("/history")
async def get_quiz_history(language: str = None, limit: int = 50):
    def _q():
        conn = get_sync_conn()
        if language:
            rows = conn.execute("SELECT * FROM quiz_attempts WHERE language = ? ORDER BY timestamp DESC LIMIT ?", (language, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM quiz_attempts ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [{"id": r["id"], "language": r["language"], "user_answer": r["user_answer"], "correct": bool(r["correct"]), "timestamp": r["timestamp"], "time_spent": r["time_spent"]} for r in rows]
    return await asyncio.to_thread(_q)
