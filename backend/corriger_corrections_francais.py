#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remet le français en premier dans les six corrections de phrases.

Le problème : pour une correction, la colonne « français » contenait la phrase
anglaise fautive de Michel et la traduction la phrase corrigée — donc deux lignes
d'anglais l'une sous l'autre, sans français. Or l'appli affiche toujours
`words.french` d'abord : le français doit y être.

Nouvelle disposition :
  words.french                     -> le sens français de la phrase
  translations.en.translation      -> la version anglaise naturelle
  translations.en.example_target   -> ce que Michel avait écrit (l'erreur d'origine)
  translations.en.notes            -> l'explication, inchangée

Idempotent : si le français est déjà en français, on ne retouche rien.
"""
import os
import sqlite3
import sys

DB = os.environ.get("LANGUE_DB", "/app/data/langue.db")

# clé = début de la phrase anglaise d'origine, valeur = (sens français, phrase fautive)
CORRECTIONS = {
    "I need to add this new field in the result of all research.": (
        "Je dois ajouter ce nouveau champ à tous les résultats de recherche.",
        "I need to add this new field in the result of all research.",
    ),
    "Yes, I also need to update the code on the front end": (
        "Oui, je dois aussi mettre à jour le code du frontend pour ajouter un nouveau "
        "champ dans le détail de la nature d'infraction.",
        "Yes, I also need to update the code on the front end in order to add a new field "
        "in the details of nature of infraction.",
    ),
    "The front end doesn't need a lot of change": (
        "Le frontend n'a pas besoin de beaucoup de changements, car la structure de la nature "
        "d'infraction est déjà bonne ; je n'ai donc qu'un seul champ à ajouter au-dessus du tableau.",
        "The front end doesn't need a lot of change because the structure of nature of infraction "
        "is already good, so I only need to add a single field above the table.",
    ),
    "Firstly, I need to execute the batch of importation of data.": (
        "D'abord, je dois lancer le batch d'importation des données.",
        "Firstly, I need to execute the batch of importation of data.",
    ),
    "Then I need to check if the new field is added to the nature": (
        "Ensuite, je dois vérifier que le nouveau champ est bien ajouté à la table nature "
        "d'infraction, et que la nouvelle table nature d'activité est bien créée.",
        "Then I need to check if the new field is added to the nature of infraction table, "
        "then if the new table of nature of business is also added created.",
    ),
    "Then I need to check if the data is successfully added on this": (
        "Ensuite, je dois vérifier que les données sont bien ajoutées au nouveau champ et à la "
        "nouvelle table depuis le dépôt — le dépôt étant constitué de fichiers XML.",
        "Then I need to check if the data is successfully added on this new field and this new "
        "table from the repository. The repository is the XML files.",
    ),
}


def main() -> int:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    faits = 0
    for prefixe, (francais, fautive) in CORRECTIONS.items():
        rows = conn.execute(
            "SELECT id, french FROM words WHERE kind = 'correction' AND french LIKE ?",
            (prefixe + "%",)).fetchall()
        for r in rows:
            if r["french"] == francais:
                continue  # déjà traité
            conn.execute("UPDATE words SET french = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                         (francais, r["id"]))
            # la phrase fautive part dans example_target : elle ne se perd pas, elle change de place
            maj = conn.execute(
                "UPDATE translations SET example_target = ? WHERE word_id = ? AND language = 'en'",
                (fautive, r["id"]))
            if maj.rowcount == 0:
                conn.execute(
                    "INSERT INTO translations (word_id, language, translation, example_target) "
                    "VALUES (?, 'en', '', ?)", (r["id"], fautive))
            faits += 1
    conn.commit()

    print(f"{faits} correction(s) remises en français d'abord\n")
    print("contrôle :")
    for r in conn.execute(
            "SELECT w.french, t.translation, t.example_target FROM words w "
            "JOIN translations t ON t.word_id = w.id AND t.language = 'en' "
            "WHERE w.kind = 'correction' ORDER BY w.id"):
        fr = r["french"]
        anglais_fr = fr.strip().lower().startswith(("i ", "the ", "yes", "then", "firstly"))
        print(f"  {'ANGLais!' if anglais_fr else 'fr  '} {fr[:62]}")
        print(f"        -> {r['translation'][:62]}")
        print(f"        écrit avant : {(r['example_target'] or '')[:58]}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
