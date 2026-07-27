from fastapi import APIRouter

router = APIRouter(prefix="/api/languages", tags=["languages"])

ALPHABETS = {
    "ru": {
        "name": "Alphabet cyrillique russe",
        "note": "Le russe utilise l'alphabet cyrillique (33 lettres). Chaque lettre a un son unique. Une fois l'alphabet maîtrisé, tu peux lire n'importe quel mot russe.",
        "letters": [
            {"letter": "А а", "sound": "a", "example": "арбуз (arbuz) — pastèque"},
            {"letter": "Б б", "sound": "b", "example": "банан (banan) — banane"},
            {"letter": "В в", "sound": "v", "example": "вода (voda) — eau"},
            {"letter": "Г г", "sound": "g", "example": "город (gorod) — ville"},
            {"letter": "Д д", "sound": "d", "example": "дом (dom) — maison"},
            {"letter": "Е е", "sound": "yé", "example": "еда (yeda) — nourriture"},
            {"letter": "Ё ё", "sound": "yo", "example": "ёж (yozh) — hérisson"},
            {"letter": "Ж ж", "sound": "j (comme 'je' français)", "example": "жизнь (jizn') — vie"},
            {"letter": "З з", "sound": "z", "example": "звезда (zvezda) — étoile"},
            {"letter": "И и", "sound": "i", "example": "игра (igra) — jeu"},
            {"letter": "Й й", "sound": "y court", "example": "йога (yoga) — yoga"},
            {"letter": "К к", "sound": "k", "example": "книга (kniga) — livre"},
            {"letter": "Л л", "sound": "l", "example": "луна (luna) — lune"},
            {"letter": "М м", "sound": "m", "example": "молоко (moloko) — lait"},
            {"letter": "Н н", "sound": "n", "example": "ночь (noch') — nuit"},
            {"letter": "О о", "sound": "o", "example": "окно (okno) — fenêtre"},
            {"letter": "П п", "sound": "p", "example": "папа (papa) — papa"},
            {"letter": "Р р", "sound": "r roulé", "example": "рыба (ryba) — poisson"},
            {"letter": "С с", "sound": "s", "example": "сыр (syr) — fromage"},
            {"letter": "Т т", "sound": "t", "example": "телефон (telefon) — téléphone"},
            {"letter": "У у", "sound": "ou", "example": "утро (utro) — matin"},
            {"letter": "Ф ф", "sound": "f", "example": "фрукты (frukty) — fruits"},
            {"letter": "Х х", "sound": "kh (jota espagnole)", "example": "хлеб (khleb) — pain"},
            {"letter": "Ц ц", "sound": "ts", "example": "цветок (tsvetok) — fleur"},
            {"letter": "Ч ч", "sound": "tch", "example": "чай (chay) — thé"},
            {"letter": "Ш ш", "sound": "ch (dur)", "example": "школа (shkola) — école"},
            {"letter": "Щ щ", "sound": "chtch (doux)", "example": "щи (shchi) — soupe aux choux"},
            {"letter": "Ъ ъ", "sound": "signe dur (sépare)", "example": "объект (obyekt) — objet"},
            {"letter": "Ы ы", "sound": "i guttural", "example": "мы (my) — nous"},
            {"letter": "Ь ь", "sound": "signe mou (adoucit)", "example": "день (den') — jour"},
            {"letter": "Э э", "sound": "è", "example": "это (eto) — ceci"},
            {"letter": "Ю ю", "sound": "you", "example": "юг (youg) — sud"},
            {"letter": "Я я", "sound": "ya", "example": "яблоко (yabloko) — pomme"},
        ]
    },
    "zh": {
        "name": "Pinyin & Tons (chinois mandarin)",
        "note": "4 tons essentiels : le même son peut avoir 4 sens différents. Le pinyin est la transcription en alphabet latin.",
        "letters": [
            {"letter": "b p m f", "sound": "comme en français (non aspiré)", "example": "爸 bà (papa), 怕 pà (peur)"},
            {"letter": "d t n l", "sound": "dental, t aspiré", "example": "大 dà (grand), 他 tā (il)"},
            {"letter": "g k h", "sound": "g dur, k aspiré, h guttural", "example": "歌 gē (chanson)"},
            {"letter": "j q x", "sound": "dj, tchi, si (palatal)", "example": "家 jiā (maison), 七 qī (sept)"},
            {"letter": "zh ch sh r", "sound": "dj, tch, ch, j rétroflexe", "example": "中 zhōng (milieu)"},
            {"letter": "z c s", "sound": "dz, ts, s dental", "example": "在 zài (être à)"},
        ],
        "tones": [
            {"tone": "1er ton (¯)", "sound": "haut et plat", "example": "mā (maman)"},
            {"tone": "2e ton (´)", "sound": "montant (question)", "example": "má (chanvre)"},
            {"tone": "3e ton (ˇ)", "sound": "descend puis monte", "example": "mǎ (cheval)"},
            {"tone": "4e ton (ˋ)", "sound": "descendant brusque", "example": "mà (insulter)"},
        ]
    },
    "ja": {
        "name": "Hiragana & Katakana (japonais)",
        "note": "2 syllabaires de 46 lettres chacun. Hiragana = mots japonais. Katakana = mots étrangers. Chaque signe = une syllabe.",
        "letters": [
            {"letter": "あ ア", "sound": "a", "example": "あめ (ame) — pluie"},
            {"letter": "い イ", "sound": "i", "example": "いぬ (inu) — chien"},
            {"letter": "う ウ", "sound": "ou", "example": "うみ (umi) — mer"},
            {"letter": "え エ", "sound": "é", "example": "えき (eki) — gare"},
            {"letter": "お オ", "sound": "o", "example": "おと (oto) — son"},
            {"letter": "か カ", "sound": "ka", "example": "かさ (kasa) — parapluie"},
            {"letter": "き キ", "sound": "ki", "example": "き (ki) — arbre"},
            {"letter": "く ク", "sound": "kou", "example": "くも (kumo) — nuage"},
            {"letter": "け ケ", "sound": "ké", "example": "けさ (kesa) — ce matin"},
            {"letter": "こ コ", "sound": "ko", "example": "こえ (koe) — voix"},
            {"letter": "さ サ", "sound": "sa", "example": "さくら (sakura) — cerisier"},
            {"letter": "し シ", "sound": "chi", "example": "しごと (shigoto) — travail"},
            {"letter": "す ス", "sound": "sou", "example": "すし (sushi) — sushi"},
            {"letter": "せ セ", "sound": "sé", "example": "せんせい (sensei) — professeur"},
            {"letter": "そ ソ", "sound": "so", "example": "そら (sora) — ciel"},
            {"letter": "た タ", "sound": "ta", "example": "たまご (tamago) — œuf"},
            {"letter": "ち チ", "sound": "tchi", "example": "ちず (chizu) — carte"},
            {"letter": "つ ツ", "sound": "tsou", "example": "つき (tsuki) — lune"},
            {"letter": "て テ", "sound": "té", "example": "て (te) — main"},
            {"letter": "と ト", "sound": "to", "example": "とけい (tokei) — montre"},
            {"letter": "な ナ", "sound": "na", "example": "なつ (natsu) — été"},
            {"letter": "に ニ", "sound": "ni", "example": "にほん (nihon) — Japon"},
            {"letter": "ぬ ヌ", "sound": "nou", "example": "ぬま (numa) — marais"},
            {"letter": "ね ネ", "sound": "né", "example": "ねこ (neko) — chat"},
            {"letter": "の ノ", "sound": "no", "example": "のり (nori) — algue"},
            {"letter": "は ハ", "sound": "ha", "example": "はな (hana) — fleur"},
            {"letter": "ひ ヒ", "sound": "hi", "example": "ひと (hito) — personne"},
            {"letter": "ふ フ", "sound": "fou", "example": "ふね (fune) — bateau"},
            {"letter": "へ ヘ", "sound": "hé", "example": "へや (heya) — chambre"},
            {"letter": "ほ ホ", "sound": "ho", "example": "ほし (hoshi) — étoile"},
            {"letter": "ま マ", "sound": "ma", "example": "まち (machi) — ville"},
            {"letter": "み ミ", "sound": "mi", "example": "みず (mizu) — eau"},
            {"letter": "む ム", "sound": "mou", "example": "むし (mushi) — insecte"},
            {"letter": "め メ", "sound": "mé", "example": "め (me) — œil"},
            {"letter": "も モ", "sound": "mo", "example": "もり (mori) — forêt"},
            {"letter": "や ヤ", "sound": "ya", "example": "やま (yama) — montagne"},
            {"letter": "ゆ ユ", "sound": "you", "example": "ゆき (yuki) — neige"},
            {"letter": "よ ヨ", "sound": "yo", "example": "よる (yoru) — nuit"},
            {"letter": "ら ラ", "sound": "ra", "example": "りんご (ringo) — pomme"},
            {"letter": "わ ワ", "sound": "wa", "example": "わたし (watashi) — je"},
            {"letter": "を ヲ", "sound": "o", "example": "本を読む (hon o yomu) — lire"},
            {"letter": "ん ン", "sound": "n", "example": "にほん (nihon) — Japon"},
        ]
    },
    "kr": {
        "name": "Hangeul (coréen)",
        "note": "Alphabet créé au XVe siècle. 24 lettres de base. Chaque lettre imite la forme de la bouche. S'apprend en 2 heures.",
        "letters": [
            {"letter": "ㄱ", "sound": "g/k", "example": "가구 (gagu) — meuble"},
            {"letter": "ㄴ", "sound": "n", "example": "나 (na) — moi"},
            {"letter": "ㄷ", "sound": "d/t", "example": "도시 (dosi) — ville"},
            {"letter": "ㄹ", "sound": "r/l", "example": "라면 (ramyeon) — nouilles"},
            {"letter": "ㅁ", "sound": "m", "example": "마음 (maeum) — cœur"},
            {"letter": "ㅂ", "sound": "b/p", "example": "바다 (bada) — mer"},
            {"letter": "ㅅ", "sound": "s", "example": "사랑 (sarang) — amour"},
            {"letter": "ㅇ", "sound": "ng (muet en début)", "example": "아이 (ai) — enfant"},
            {"letter": "ㅈ", "sound": "j", "example": "주스 (juseu) — jus"},
            {"letter": "ㅊ", "sound": "tch", "example": "친구 (chingu) — ami"},
            {"letter": "ㅋ", "sound": "k", "example": "커피 (keopi) — café"},
            {"letter": "ㅌ", "sound": "t", "example": "토마토 (tomato) — tomate"},
            {"letter": "ㅍ", "sound": "p", "example": "피자 (pija) — pizza"},
            {"letter": "ㅎ", "sound": "h", "example": "하늘 (haneul) — ciel"},
            {"letter": "ㅏ", "sound": "a", "example": "사랑 (sarang) — amour"},
            {"letter": "ㅑ", "sound": "ya", "example": "야구 (yagu) — baseball"},
            {"letter": "ㅓ", "sound": "eo (entre o et eu)", "example": "서울 (Seoul)"},
            {"letter": "ㅕ", "sound": "yeo", "example": "여자 (yeoja) — femme"},
            {"letter": "ㅗ", "sound": "o", "example": "오이 (oi) — concombre"},
            {"letter": "ㅛ", "sound": "yo", "example": "요리 (yori) — cuisine"},
            {"letter": "ㅜ", "sound": "ou", "example": "우유 (uyu) — lait"},
            {"letter": "ㅠ", "sound": "you", "example": "유리 (yuri) — verre"},
            {"letter": "ㅡ", "sound": "eu", "example": "음악 (eumak) — musique"},
            {"letter": "ㅣ", "sound": "i", "example": "이 (i) — dent"},
        ]
    },
    "km": {
        "name": "Alphabet khmer (cambodgien)",
        "note": "74 lettres — l'alphabet le plus long du monde. Écriture abugida : chaque consonne a une voyelle inhérente.",
        "letters": [
            {"letter": "ក", "sound": "k", "example": "កាហ្វេ (kaafé) — café"},
            {"letter": "ខ", "sound": "kh", "example": "ខ្មែរ (khmae) — khmer"},
            {"letter": "គ", "sound": "k (sonore)", "example": "គ្រូ (kru) — prof"},
            {"letter": "ង", "sound": "ng", "example": "ងងឹត (ngongyt) — sombre"},
            {"letter": "ច", "sound": "ch", "example": "ចាន (chan) — assiette"},
            {"letter": "ជ", "sound": "ch (sonore)", "example": "ជាតិ (cheat) — nation"},
            {"letter": "ញ", "sound": "ny (gn)", "example": "ញញឹម (nyonyum) — sourire"},
            {"letter": "ដ", "sound": "d", "example": "ដើម (daem) — arbre"},
            {"letter": "ត", "sound": "t", "example": "ត្រី (trey) — poisson"},
            {"letter": "ទ", "sound": "t (sonore)", "example": "ទឹក (teuk) — eau"},
            {"letter": "ន", "sound": "n", "example": "នំ (num) — gâteau"},
            {"letter": "ប", "sound": "b/p", "example": "បាយ (bay) — riz"},
            {"letter": "ព", "sound": "p (sonore)", "example": "ពស់ (pous) — serpent"},
            {"letter": "ម", "sound": "m", "example": "មាន (mean) — avoir"},
            {"letter": "យ", "sound": "y", "example": "យប់ (yup) — nuit"},
            {"letter": "រ", "sound": "r", "example": "រៀន (rian) — apprendre"},
            {"letter": "ល", "sound": "l", "example": "លុយ (luy) — argent"},
            {"letter": "វ", "sound": "v", "example": "វិល (vil) — tourner"},
            {"letter": "ស", "sound": "s", "example": "សាលា (sala) — école"},
            {"letter": "ហ", "sound": "h", "example": "ហត់ (hat) — fatigué"},
            {"letter": "អ", "sound": "' (coup de glotte)", "example": "អណ្តើក (andaeuk) — tortue"},
        ]
    }
}

COURSES = {
    "la": {
        "title": "Latin — Cours accéléré",
        "sections": [
            {"title": "🔤 Prononciation",
             "content": "Alphabet latin classique (23 lettres, pas de J, U, W). C = k (toujours dur), V = w (ou), AE = aï, OE = eu."},
            {"title": "📚 Les 5 déclinaisons",
             "content": "Le latin fonctionne par CAS (nominatif, vocatif, accusatif, génitif, datif, ablatif). Chaque nom change sa terminaison. 5 déclinaisons. La 1ère (rosa, -ae) = féminin, la 2nde (dominus, -i) = masculin/neutre."},
            {"title": "🎯 Ordre SOV",
             "content": "Ordre Sujet-Objet-Verbe. 'Marcus pomam edit' = 'Marc mange une pomme' (litt. Marc pomme mange)."},
            {"title": "💡 Pour un Français",
             "content": "80% du vocabulaire français vient du latin. 'Pater' → père, 'Mater' → mère, 'Frater' → frère. Grammaire plus complexe (cas) mais reconnaissance de mots immédiate."},
        ]
    },
    "es": {
        "title": "Español — Curso rápido",
        "sections": [
            {"title": "🔤 Prononciation",
             "content": "LL = y (llamar = yamar), Ñ = gn (español), J = jota, H = muet. Accent tonique régulier."},
            {"title": "📚 Verbes",
             "content": "3 groupes : -AR, -ER, -IR. Présent : hablar → hablo, hablas, habla, hablamos, habláis, hablan. Deux 'être' : SER (essence) et ESTAR (état)."},
            {"title": "🎯 Faux amis",
             "content": "Embarazada ≠ embarrassée = enceinte. Éxito ≠ exit = succès. Constipado ≠ constipé = enrhumé. Asistir ≠ assister = être présent."},
            {"title": "💡 Pour un Français",
             "content": "Langue la plus proche du français. Grammaire très similaire. Subjonctif très utilisé."},
        ]
    },
    "de": {
        "title": "Deutsch — Schnellkurs",
        "sections": [
            {"title": "🔤 Prononciation",
             "content": "W = v, V = f, CH = r (ich) ou kh (ach), ß = ss, Ö = eu, Ü = u. Accent sur la première syllabe."},
            {"title": "📚 Genres & Cas",
             "content": "3 genres (masc, fém, neutre) et 4 cas (nom, acc, dat, gén). Articles changent : der (nom.m.), den (acc.m.), dem (dat.m.), des (gén.m.)."},
            {"title": "🎯 Verbe en 2e position",
             "content": "Le verbe conjugué est TOUJOURS en 2e position. En subordonnée, le verbe va à la fin : '…weil ich heute ins Kino gehe'."},
            {"title": "💡 Pour un Français",
             "content": "Langue très logique et construite. Mots composés comme des Lego : 'Fernsehgerät' = télé-vision-appareil."},
        ]
    },
    "it": {
        "title": "Italiano — Corso rapido",
        "sections": [
            {"title": "🔤 Prononciation",
             "content": "C = k (casa) ou tch (ciao). G = g (gatto) ou dj (gelato). CH = k, GLI = lli, GN = gn. Doubles consonnes à tenir !"},
            {"title": "📚 Verbes",
             "content": "3 groupes : -ARE, -ERE, -IRE. Présent : parlare → parlo, parli, parla, parliamo, parlate, parlano."},
            {"title": "🎯 Articles",
             "content": "il (masc.), lo (devant s+cons/z), la (fém.), i, gli, le. Articulés : al (a+il), dal (da+il), nel (in+il)."},
            {"title": "💡 Pour un Français",
             "content": "80% du vocabulaire similaire. Conjugaisons proches. Attention aux doubles consonnes (nonna ≠ nóna)."},
        ]
    },
    "ru": {
        "title": "Русский — Курс",
        "sections": [
            {"title": "🔤 Alphabet",
             "content": "33 lettres. Faux amis visuels : В = V, Н = N, Р = R, С = S, У = OU, Х = KH. Une fois appris, tu lis tout."},
            {"title": "📚 Les 6 cas",
             "content": "Nominatif, génitif, datif, accusatif, instrumental, prépositionnel. Les noms, adjectifs et pronoms changent selon leur fonction."},
            {"title": "🎯 Verbes de mouvement",
             "content": "Deux verbes pour 'aller' : идти (à pied, une fois) / ходить (régulièrement), ехать (transport) / ездить (régulièrement)."},
            {"title": "💡 Pour un Français",
             "content": "Sons inconnus (ы, щ, ж, ц). Accent mobile imprévisible. Pas d'article. Grammaire complexe mais régulière."},
        ]
    },
    "zh": {
        "title": "中文 — 入门课程",
        "sections": [
            {"title": "🔤 Pinyin & Tons",
             "content": "4 tons + neutre. 'ma' = maman (mā), chanvre (má), cheval (mǎ), insulter (mà). Sans les tons, tu n'es pas compris."},
            {"title": "📚 Caractères",
             "content": "Chaque caractère = une syllabe + un sens. ~3500 pour lire un journal. Radicaux de base : 人 (personne), 大 (grand), 小 (petit)."},
            {"title": "🎯 Grammaire simple",
             "content": "Pas de conjugaison, pas de genre, pas de cas. Ordre SVO. Temps indiqués par 昨天 (hier), 今天 (aujourd'hui), 明天 (demain)."},
            {"title": "💡 Pour un Français",
             "content": "Grammaire très simple. Défi = caractères + tons. Commence par 100 caractères de base."},
        ]
    },
    "ja": {
        "title": "日本語 — 入門コース",
        "sections": [
            {"title": "🔤 3 écritures",
             "content": "Hiragana (mots japonais), Katakana (mots étrangers), Kanji (chinois). Apprends d'abord les hiragana !"},
            {"title": "📚 Grammaire SOV",
             "content": "Sujet-Objet-Verbe. 'Watashi wa sushi o taberu' = Je sushi mange. Particules : は (sujet), を (objet), に (destination)."},
            {"title": "🎯 Politesse",
             "content": "3 niveaux : informel, poli (-masu), honorifique. Utilise -masu en toutes situations sauf amis proches."},
            {"title": "💡 Pour un Français",
             "content": "Pas de genre, pas d'article. Prononciation facile (5 voyelles comme l'italien). Le plus dur : kanji + politesse."},
        ]
    },
    "kr": {
        "title": "한국어 — 초급 코스",
        "sections": [
            {"title": "🔤 Hangeul",
             "content": "24 lettres. S'apprend en 2h. Chaque lettre imite la bouche : ㅁ (m) = lèvres, ㅗ (o) = arrondi."},
            {"title": "📚 Grammaire SOV",
             "content": "SOV + particules. 은/는 (sujet), 을/를 (objet), 에 (lieu). '저는 커피를 좋아해요' = je café aime."},
            {"title": "🎯 Politesse",
             "content": "3 niveaux : 해요체 (poli), 해체 (informel), 하십시오체 (formel). Les verbes changent de terminaison."},
            {"title": "💡 Pour un Français",
             "content": "Alphabet le plus facile au monde. Prononciation délicate (tension, aspiration). Pas de genre ni d'article."},
        ]
    },
    "km": {
        "title": "ភាសាខ្មែរ — វគ្គសិក្សា",
        "sections": [
            {"title": "🔤 Alphabet",
             "content": "74 lettres. Abugida : chaque consonne a une voyelle inhérente 'a'. 2 séries de consonnes qui changent la voyelle."},
            {"title": "📚 Prononciation",
             "content": "Sons inconnus en français : ង (ng), ញ (ny), អ (coup de glotte). 32 voyelles écrites."},
            {"title": "🎯 Grammaire",
             "content": "Pas de conjugaison, pas de genre. Ordre SVO. Temps : កំពុង (en train de), បាន (passé), នឹង (futur)."},
            {"title": "💡 Pour un Français",
             "content": "Grammaire simple (comme le chinois). Défi = écriture + prononciation. 33 consonnes puis 23 voyelles."},
        ]
    },
    "en": {
        "title": "English — Quick Course",
        "sections": [
            {"title": "🔤 Prononciation",
             "content": "L'anglais n'est PAS phonétique ! 'ough' = though (δóu), through (θρού), tough (taf), cough (kof). TH = langue entre les dents."},
            {"title": "📚 Conjugaison",
             "content": "To be : I am, you are, he/she/it is. Pour les autres verbes, seul le -s à la 3e personne change (he eats)."},
            {"title": "🎯 Les temps",
             "content": "Plus de temps qu'en français : Present Simple (I eat), Continuous (I am eating), Perfect (I have eaten), Past (I ate)… Chacun a un usage spécifique."},
            {"title": "💡 Pour un Français",
             "content": "Plus dur = prononciation. Plus facile = pas de genre, conjugaison simple. Faux amis : Actually ≠ Actuellement."},
        ]
    }
}

@router.get("/{code}/alphabet")
async def get_alphabet(code: str):
    if code in ALPHABETS:
        return ALPHABETS[code]
    return {"note": "Alphabet latin standard (identique au français)", "letters": []}

@router.get("/{code}/course")
async def get_course(code: str):
    if code in COURSES:
        return COURSES[code]
    return {"title": f"Cours de {code}", "sections": [
        {"title": "📖 Introduction", "content": "Cours en préparation."}
    ]}
