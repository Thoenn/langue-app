#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ajoute le tri par date, les favoris et les collections à Langue App.

Idempotent : rejouable sans dommage.

- words.created_at / updated_at : pour trier par « récemment ajouté » et voir ce qui
  vient de bouger. Les entrées déjà présentes reçoivent la date de création de la base,
  ce qui les place naturellement derrière les ajouts récents.
- words.favorite : ce qu'il faut absolument savoir, indépendamment du niveau atteint.
- collections + word_collections : des paquets nommés par Michel (par exemple
  « session magistrats », « entretien », « à revoir avant vendredi »). Une entrée peut
  appartenir à plusieurs collections.
"""
import os
import sqlite3
import sys

DB = os.environ.get("LANGUE_DB", "/app/data/langue.db")


def main() -> int:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    colonnes = {r["name"] for r in conn.execute("PRAGMA table_info(words)")}
    if "created_at" not in colonnes:
        conn.execute("ALTER TABLE words ADD COLUMN created_at TEXT")
        print("colonne ajoutée : words.created_at")
    if "updated_at" not in colonnes:
        conn.execute("ALTER TABLE words ADD COLUMN updated_at TEXT")
        print("colonne ajoutée : words.updated_at")
    if "favorite" not in colonnes:
        conn.execute("ALTER TABLE words ADD COLUMN favorite INTEGER DEFAULT 0")
        print("colonne ajoutée : words.favorite")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(120) NOT NULL UNIQUE,
            emoji VARCHAR(10) DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS word_collections (
            word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
            collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (word_id, collection_id)
        );
        CREATE INDEX IF NOT EXISTS idx_words_created ON words(created_at);
        CREATE INDEX IF NOT EXISTS idx_words_favorite ON words(favorite);
        CREATE INDEX IF NOT EXISTS idx_wc_collection ON word_collections(collection_id);
    """)

    # Rattrapage : tout ce qui existe déjà reçoit une date, sinon le tri par récence
    # mettrait les 800 entrées anciennes avant les nouvelles (NULL se trie bizarrement).
    n = conn.execute("SELECT COUNT(*) FROM words WHERE created_at IS NULL").fetchone()[0]
    if n:
        conn.execute("UPDATE words SET created_at = '2026-07-27 00:00:00', updated_at = '2026-07-27 00:00:00' "
                     "WHERE created_at IS NULL")
        print(f"{n} entrées existantes datées (2026-07-27, création de la base)")

    conn.commit()

    print("\nétat :")
    print("  entrées       :", conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    print("  favorites     :", conn.execute("SELECT COUNT(*) FROM words WHERE favorite = 1").fetchone()[0])
    print("  collections   :", conn.execute("SELECT COUNT(*) FROM collections").fetchone()[0])
    print("  colonnes      :", ", ".join(r["name"] for r in conn.execute("PRAGMA table_info(words)")))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
