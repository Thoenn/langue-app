#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Importe les récapitulatifs d'apprentissage dans Langue App.

Source : cinq fichiers Markdown fournis par Michel (sessions Magistrats, IT, DEV,
multilingue). Le contenu est reproduit ici pour que l'import soit rejouable et
vérifiable — les fichiers d'origine restent la référence, mais un import qui dépend
d'un chemin dans /home/debian/.hermes/cache ne survit pas à un nettoyage.

Trois natures d'entrées, distinguées par words.kind :
  mot        — un terme à connaître (lexique pro, vocabulaire juridique)
  phrase     — une phrase complète, français -> langue cible, avec sa nuance
  correction — une phrase réellement écrite par Michel, et sa version naturelle

Idempotent : la clé est (kind, source, french). Rejouer le script ne duplique rien.
"""
import os
import re
import sqlite3
import sys

DB = os.environ.get("LANGUE_DB", "/app/data/langue.db")

CATEGORIES = {
    "phrases-pro": ("Anglais pro — phrases", "🗣️"),
    "corrections": ("Mes erreurs corrigées", "✏️"),
    "lexique-tech": ("Lexique tech & métier", "💻"),
    "grammaire": ("Points de grammaire", "📐"),
    "multilingue": ("Multilingue pro", "🌍"),
}

# (kind, source, categorie, sous-categorie, français, langue, traduction, note, exemple_fr, exemple_cible)
ENTREES = [
    # ── Phrases professionnelles (session IT) ──────────────────────────────────
    ("phrase", "recap-it", "phrases-pro", "déploiement",
     "Avons-nous des retours d'utilisateurs sur le dernier déploiement en production ?", "en",
     "Do we have user feedback on the latest production deployment?",
     "latest = le plus récent (versions, mises à jour) ; last = le dernier d'une série finie. "
     "feedback est indénombrable : jamais de « s ».", "", ""),
    ("phrase", "recap-it", "phrases-pro", "performance",
     "Je rencontre des problèmes de performance avec la base de données depuis la dernière mise à jour.", "en",
     "I'm encountering performance issues with the database since the last update.",
     "encountering est plus professionnel que having ; issues est plus courant que problems en IT ; "
     "on dit issues WITH the database, jamais on.", "", ""),
    ("phrase", "recap-it", "phrases-pro", "sécurité",
     "Est-ce que tu peux me transférer la clé API pour l'environnement de production ?", "en",
     "Can you forward the API key for the production environment?",
     "forward = transférer un élément reçu (mail, message, clé) ; transfer est réservé aux "
     "transferts formels. À l'oral, prod environnement se dit couramment.", "", ""),
    ("phrase", "recap-it", "phrases-pro", "migration",
     "Nous devons migrer vers la nouvelle version d'Angular d'ici la fin du mois prochain.", "en",
     "We need to upgrade to the latest Angular version by the end of next month.",
     "upgrade to pour une mise à niveau logicielle ; by the end of + période = d'ici la fin de.", "", ""),
    ("phrase", "recap-it", "phrases-pro", "configuration",
     "J'ai configuré la connexion à la base de données PostgreSQL dans le fichier application.properties.", "en",
     "I configured the connection to the PostgreSQL database in the application.properties file.",
     "Variante très courante à l'oral : « I've set up the PostgreSQL database connection in the "
     "application.properties file. » — set up = installer/mettre en place.", "", ""),

    # ── Phrases du domaine Magistrats ─────────────────────────────────────────
    ("phrase", "recap-magistrats", "phrases-pro", "magistrats",
     "Il y a une fonctionnalité qui permet aux magistrats de rechercher la nature des infractions "
     "en utilisant la qualification simplifiée.", "en",
     "There is a feature that allows magistrates to search for the nature of infractions by using "
     "simplified qualification.",
     "allow someone TO + verbe ; on cherche quelque chose : search FOR. by using = au moyen de.", "", ""),
    ("phrase", "recap-magistrats", "phrases-pro", "magistrats",
     "Cette fonctionnalité permet aux magistrats de rechercher la nature des infractions via la "
     "qualification simplifiée.", "en",
     "That feature allows magistrates to search for the nature of infractions using simplified qualification.",
     "Version concise de la même idée. Attention : that feature est singulier, donc allows avec un s.", "", ""),
    ("phrase", "recap-magistrats", "phrases-pro", "magistrats",
     "Lorsque les magistrats effectuent la recherche, les résultats affichent une liste d'infractions.", "en",
     "When magistrates perform the search, the results display a list of infractions.",
     "to perform a search est plus professionnel que to do a search. to display = afficher.", "", ""),
    ("phrase", "recap-magistrats", "phrases-pro", "magistrats",
     "Lorsque les magistrats effectuent la recherche, les résultats affichent une liste de types "
     "d'infractions.", "en",
     "When magistrates perform the search, the results display a list of infraction types.",
     "infraction types est plus naturel en anglais que la tournure calquée nature of infractions.", "", ""),

    # ── Corrections : ses propres phrases (session DEV) ────────────────────────
    ("correction", "recap-dev", "corrections", "recherche",
     "I need to add this new field in the result of all research.", "en",
     "I need to add this new field to all search results.",
     "En informatique on dit search (recherche dans une application), research c'est la recherche "
     "scientifique. Et on ajoute quelque chose TO a list, pas in.", "", ""),
    ("correction", "recap-dev", "corrections", "frontend",
     "Yes, I also need to update the code on the front end in order to add a new field in the details "
     "of nature of infraction.", "en",
     "Yes, I also need to update the code on the frontend to add a new field in the details of the "
     "nature of the infraction.",
     "« in order to » est correct mais « to » suffit à l'oral. Penser à l'article the devant les noms "
     "spécifiques : the details of THE nature of THE infraction.", "", ""),
    ("correction", "recap-dev", "corrections", "frontend",
     "The front end doesn't need a lot of change because the structure of nature of infraction is "
     "already good, so I only need to add a single field above the table.", "en",
     "The frontend doesn't need a lot of change because the structure of the nature of the infraction "
     "is already good, so I only need to add a single field above the table.",
     "Structure de phrase déjà claire et directe — il ne manquait que les articles.", "", ""),
    ("correction", "recap-dev", "corrections", "batch",
     "Firstly, I need to execute the batch of importation of data.", "en",
     "First, I need to execute the data import batch.",
     "À l'oral on dit First. Et l'anglais empile les noms dans l'ordre inverse du français : "
     "« batch of importation of data » devient data import batch.", "", ""),
    ("correction", "recap-dev", "corrections", "vérification",
     "Then I need to check if the new field is added to the nature of infraction table, then if the "
     "new table of nature of business is also added created.", "en",
     "Then, I need to check if the new field is added to the nature of the infraction table, and that "
     "the new nature of business table is also created.",
     "Éviter de répéter « then if » : on enchaîne avec and that. Et un objet est created, pas added created.", "", ""),
    ("correction", "recap-dev", "corrections", "vérification",
     "Then I need to check if the data is successfully added on this new field and this new table "
     "from the repository. The repository is the XML files.", "en",
     "Then, I need to check if the data is successfully added to the new field and new table from the "
     "repository, as the repository consists of XML files.",
     "On ajoute des données TO a field/table, jamais on. to consist of = se composer de, très "
     "professionnel pour décrire un dépôt.", "", ""),

    # ── Points de grammaire ───────────────────────────────────────────────────
    ("mot", "recap-magistrats", "grammaire", "verbes",
     "Effectuer une recherche (informatique) / faire de la recherche (scientifique)", "en",
     "to perform a search / to do a search (vs to do research)",
     "search = chercher dans une application ; research = recherche académique. Faux ami classique.", "", ""),
    ("mot", "recap-magistrats", "grammaire", "prépositions",
     "Chercher quelque chose de précis", "en",
     "to search FOR something",
     "On utilise toujours search for quand on cherche quelque chose de précis : "
     "search for the nature of infractions.", "", ""),
    ("mot", "recap-magistrats", "grammaire", "conjugaison",
     "Cette fonctionnalité permet à…", "en",
     "That feature allows…",
     "Sujet singulier = -s au présent simple. L'erreur à ne plus faire : that feature allow.", "", ""),
    ("mot", "recap-magistrats", "grammaire", "moyen",
     "En utilisant / au moyen de", "en",
     "by using… / using…",
     "by using + nom, ou simplement using + nom, pour exprimer le moyen.", "", ""),

    # ── Lexique IT ────────────────────────────────────────────────────────────
    ("mot", "recap-it", "lexique-tech", "déploiement", "Retours d'utilisateurs", "en", "user feedback",
     "Indénombrable : jamais « feedbacks ».", "", ""),
    ("mot", "recap-it", "lexique-tech", "déploiement", "Déploiement en production", "en", "production deployment",
     "deployment = l'action de mettre en production ; deployment pipeline = chaîne de déploiement.", "", ""),
    ("mot", "recap-it", "lexique-tech", "versions", "Le plus récent (d'une version)", "en", "latest",
     "À privilégier pour les versions : the latest version, the latest update.", "", ""),
    ("mot", "recap-it", "lexique-tech", "performance", "Problèmes de performance", "en", "performance issues",
     "issues est plus courant et plus professionnel que problems en contexte technique.", "", ""),
    ("mot", "recap-it", "lexique-tech", "performance", "Rencontrer (un problème, un bug)", "en", "to encounter",
     "to encounter an issue / an error — plus soutenu que to have.", "", ""),
    ("mot", "recap-it", "lexique-tech", "versions", "Mise à jour", "en", "update",
     "Logicielle ou applicative. À ne pas confondre avec upgrade (changement de version majeure).", "", ""),
    ("mot", "recap-it", "lexique-tech", "communication", "Transférer (un message, une clé)", "en", "to forward",
     "Pour un élément reçu par mail ou messagerie.", "", ""),
    ("mot", "recap-it", "lexique-tech", "sécurité", "Clé API", "en", "API key",
     "Identifiant d'authentification pour une API.", "", ""),
    ("mot", "recap-it", "lexique-tech", "environnements", "Environnement de production", "en",
     "production environment",
     "Abrégé prod à l'oral : the prod environment.", "", ""),
    ("mot", "recap-it", "lexique-tech", "versions", "Mettre à niveau vers", "en", "to upgrade (to)",
     "Passage à une version supérieure d'un outil ou d'un framework.", "", ""),
    ("mot", "recap-it", "lexique-tech", "échéances", "D'ici la fin de [période]", "en", "by the end of [period]",
     "by the end of next month, by the end of the week.", "", ""),

    # ── Lexique DEV ───────────────────────────────────────────────────────────
    ("mot", "recap-dev", "lexique-tech", "recherche", "Résultats de recherche", "en", "search results",
     "À préférer à research results en informatique.", "", ""),
    ("mot", "recap-dev", "lexique-tech", "frontend", "Interface utilisateur / code côté client", "en",
     "frontend (ou front-end)", "Le code qui tourne chez l'utilisateur, par opposition au backend.", "", ""),
    ("mot", "recap-dev", "lexique-tech", "base de données", "Champ", "en", "field",
     "Un champ dans un formulaire ou une table.", "", ""),
    ("mot", "recap-dev", "lexique-tech", "base de données", "Table", "en", "table",
     "Base de données comme affichage.", "", ""),
    ("mot", "recap-dev", "lexique-tech", "interface", "Au-dessus du tableau", "en", "above the table",
     "Préposition de lieu très utile pour décrire une interface.", "", ""),
    ("mot", "recap-dev", "lexique-tech", "batch", "Batch d'importation de données", "en",
     "data import batch", "Traitement par lots pour importer des données.", "", ""),
    ("mot", "recap-dev", "lexique-tech", "architecture", "Dépôt / référentiel", "en", "repository",
     "L'endroit où sont stockés les fichiers (dépôt Git, fichiers XML…).", "", ""),
    ("mot", "recap-dev", "lexique-tech", "architecture", "Se composer de / consister en", "en",
     "to consist of", "Idéal pour décrire le contenu d'un fichier ou d'un dossier.", "", ""),
    ("mot", "recap-dev", "lexique-tech", "tests", "Ajouté avec succès", "en", "successfully added",
     "Expression standard pour valider un test.", "", ""),

    # ── Lexique Magistrats ────────────────────────────────────────────────────
    ("mot", "recap-magistrats", "lexique-tech", "métier", "Une fonctionnalité", "en", "a feature",
     "Terme standard en informatique pour une capacité du logiciel.", "", ""),
    ("mot", "recap-magistrats", "lexique-tech", "métier", "Permettre à quelqu'un de faire", "en",
     "to allow someone to + verbe", "Allows magistrates to search…", "", ""),
    ("mot", "recap-magistrats", "lexique-tech", "juridique", "Un magistrat", "en", "a magistrate",
     "Terme générique ; judge pour le juge d'instance, prosecutor pour le procureur.", "", ""),
    ("mot", "recap-magistrats", "lexique-tech", "juridique", "Nature d'infraction", "en",
     "nature of infraction(s)", "Souvent au pluriel en emploi général : nature of infractions.", "", ""),
    ("mot", "recap-magistrats", "lexique-tech", "juridique", "Types d'infractions", "en", "infraction types",
     "Plus naturel en anglais que nature of infractions.", "", ""),
    ("mot", "recap-magistrats", "lexique-tech", "juridique", "Qualification simplifiée", "en",
     "simplified qualification", "Terme métier du domaine juridique.", "", ""),

    # ── Multilingue ───────────────────────────────────────────────────────────
    ("phrase", "recap-multilingue", "multilingue", "espagnol",
     "Je suis développeur de logiciels.", "es", "Soy desarrollador de software",
     "ser (soy) pour l'état durable et la profession ; estar pour l'état passager.", "", ""),
    ("phrase", "recap-multilingue", "multilingue", "espagnol",
     "Je travaille sur ce projet.", "es", "Trabajo en este proyecto",
     "trabajar en = travailler sur/dans. este = ce (démonstratif masculin).", "", ""),
    ("phrase", "recap-multilingue", "multilingue", "italien",
     "Je travaille sur ce projet.", "it", "Lavoro a questo progetto",
     "lavorare a = travailler à/sur ; questo = ce.", "", ""),
    ("phrase", "recap-multilingue", "multilingue", "khmer",
     "Bonjour, je m'appelle Michel.", "km", "Chriab-suor, khnhom chhmoh Michel",
     "Prononciation : tchriab-suo, khnom tchmoh. Chriab-suor = bonjour (salutation polie), "
     "khnhom chhmoh = je m'appelle.", "Bonjour, je m'appelle Michel.", ""),
    ("phrase", "recap-multilingue", "multilingue", "khmer",
     "Je travaille sur le projet.", "km", "Knhom thveu-kar leu koumroung nis",
     "thveu-kar = travailler (littéralement faire le travail) ; leu = sur ; koumroung = projet.", "", ""),
]


def normalise(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").strip().lower())


def main() -> int:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # 1. colonnes nouvelles (migration douce)
    colonnes = {r["name"] for r in conn.execute("PRAGMA table_info(words)")}
    for nom, ddl in (("kind", "TEXT DEFAULT 'mot'"), ("source", "TEXT DEFAULT 'app'")):
        if nom not in colonnes:
            conn.execute(f"ALTER TABLE words ADD COLUMN {nom} {ddl}")
            print(f"colonne ajoutée : words.{nom}")

    # 2. catégories
    ids = {}
    for cle, (nom, emoji) in CATEGORIES.items():
        row = conn.execute("SELECT id FROM categories WHERE name = ?", (nom,)).fetchone()
        if row:
            ids[cle] = row["id"]
        else:
            ordre = conn.execute("SELECT COALESCE(MAX(order_index),0)+1 FROM categories").fetchone()[0]
            cur = conn.execute("INSERT INTO categories (name, emoji, order_index) VALUES (?,?,?)",
                               (nom, emoji, ordre))
            ids[cle] = cur.lastrowid
            print(f"catégorie créée : {nom}")

    # 3. entrées
    ajouts = maj = 0
    for (kind, source, cat, sous, fr, langue, trad, note, ex_fr, ex_cible) in ENTREES:
        existant = conn.execute(
            "SELECT id FROM words WHERE kind = ? AND source = ? AND lower(french) = ?",
            (kind, source, normalise(fr))).fetchone()
        if existant:
            word_id = existant["id"]
            conn.execute("UPDATE words SET category_id = ?, subcategory = ? WHERE id = ?",
                         (ids[cat], sous, word_id))
            maj += 1
        else:
            cur = conn.execute(
                "INSERT INTO words (french, category_id, subcategory, kind, source) VALUES (?,?,?,?,?)",
                (fr, ids[cat], sous, kind, source))
            word_id = cur.lastrowid
            ajouts += 1
        tr = conn.execute(
            "SELECT id FROM translations WHERE word_id = ? AND language = ?", (word_id, langue)).fetchone()
        if tr:
            conn.execute(
                "UPDATE translations SET translation = ?, notes = ?, example_fr = ?, example_target = ? "
                "WHERE id = ?", (trad, note, ex_fr, ex_cible, tr["id"]))
        else:
            conn.execute(
                "INSERT INTO translations (word_id, language, translation, phonetic, example_fr, "
                "example_target, notes) VALUES (?,?,?,'',?,?,?)",
                (word_id, langue, trad, ex_fr, ex_cible, note))
    conn.execute("CREATE INDEX IF NOT EXISTS idx_words_kind ON words(kind)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_words_source ON words(source)")
    conn.commit()

    print(f"\n{ajouts} entrées ajoutées, {maj} mises à jour")
    for kind in ("mot", "phrase", "correction"):
        n = conn.execute("SELECT COUNT(*) FROM words WHERE kind = ?", (kind,)).fetchone()[0]
        print(f"  {kind:11} : {n} au total")
    print("\npar catégorie :")
    for r in conn.execute("""SELECT c.name, COUNT(*) n FROM words w
                             JOIN categories c ON c.id = w.category_id
                             WHERE w.source LIKE 'recap-%' GROUP BY c.name ORDER BY n DESC"""):
        print(f"  {r['name']:28} {r['n']}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
