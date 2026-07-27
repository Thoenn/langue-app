const API_PATH = '/langue/api';
function apiUrl(path) {
  return `${API_PATH}${path}`;
}
let currentPage = 'dashboard';
let searchTimeout = null;

// ======== NAVIGATION ========
function toggleMenu() {
  document.getElementById('mainNav').classList.toggle('open');
}

function navigate(page) {
  currentPage = page;
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(`page-${page}`).classList.add('active');
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`.nav-btn[data-page="${page}"]`).classList.add('active');
  document.getElementById('mainNav').classList.remove('open');

  switch(page) {
    case 'dashboard': loadDashboard(); break;
    case 'vocabulary': loadLanguages('vocabLang'); loadCategories('vocabCategory'); loadVocabulary(); break;
    case 'quiz': loadLanguages('quizLang'); loadCategories('quizCategory'); break;
    case 'progress': loadLanguages('progressLang'); loadProgress(); loadMistakes(); break;
    case 'stats': loadStats(); break;
    case 'ai': loadLanguages('aiLang'); break;
  }
}

// ======== API CALL ========
async function api(url, options = {}) {
  try {
    const res = await fetch(apiUrl(url), {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('API Error:', err);
    return { error: err.message };
  }
}

// ======== LANGUAGES ========
const LANG_NAMES = {
  en: 'English', la: 'Latin', es: 'Español', de: 'Deutsch',
  it: 'Italiano', ru: 'Русский', zh: '中文', ja: '日本語',
  kr: '한국어', km: 'ភាសាខ្មែរ',
};

function loadLanguages(selectId) {
  const sel = document.getElementById(selectId);
  sel.innerHTML = '';
  Object.entries(LANG_NAMES).forEach(([code, name]) => {
    sel.innerHTML += `<option value="${code}">${name}</option>`;
  });
}

async function loadCategories(selectId) {
  const sel = document.getElementById(selectId);
  const data = await api('/vocabulary/categories');
  if (data && !data.error) {
    sel.innerHTML = '<option value="">Toutes</option>';
    data.forEach(c => {
      sel.innerHTML += `<option value="${c.name}">${c.emoji} ${c.name}</option>`;
    });
  }
}

// ======== TTS ========
function speak(text, lang = 'fr') {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === 'fr' ? 'fr-FR' :
    lang === 'en' ? 'en-US' :
    lang === 'es' ? 'es-ES' :
    lang === 'de' ? 'de-DE' :
    lang === 'it' ? 'it-IT' :
    lang === 'ru' ? 'ru-RU' :
    lang === 'zh' ? 'zh-CN' :
    lang === 'ja' ? 'ja-JP' : 'fr-FR';
  utterance.rate = 0.9;
  speechSynthesis.speak(utterance);
}

// ======== DASHBOARD ========
async function loadDashboard() {
  const el = document.getElementById('dashboardContent');
  el.innerHTML = '<div class="spinner"></div>';
  const data = await api('/stats/dashboard');

  if (data.error) {
    el.innerHTML = `<div class="card">Erreur: ${data.error}</div>`;
    return;
  }

  el.innerHTML = `
    <div class="grid-4">
      <div class="card"><div class="card-value">${data.word_count || 0}</div><div class="card-label">Mots</div></div>
      <div class="card"><div class="card-value">${data.translation_count || 0}</div><div class="card-label">Traductions</div></div>
      <div class="card"><div class="card-value">${data.quiz_attempts || 0}</div><div class="card-label">Quiz tentés</div></div>
      <div class="card"><div class="card-value" style="color:${(data.recent_activity?.accuracy || 0) >= 70 ? 'var(--success)' : 'var(--danger)'}">${data.recent_activity?.accuracy || 0}%</div><div class="card-label">Précision (7j)</div></div>
    </div>
    <div class="card">
      <div class="card-title">📚 Progression par langue</div>
      <div class="grid-2" id="langProgressGrid">
        ${Object.entries(data.lang_progress || {}).map(([lang, p]) => `
          <div style="padding:8px 0;border-bottom:1px solid var(--bg3);display:flex;justify-content:space-between;align-items:center;">
            <div>
              <strong>${LANG_NAMES[lang] || lang}</strong>
              <div style="font-size:0.8rem;color:var(--text2);">${p.mastered}/${p.total} maîtrisés</div>
            </div>
            <div style="text-align:right;">
              <div class="progress-bar" style="width:100px;"><div class="progress-fill ${p.avg_mastery >= 0.7 ? 'success' : p.avg_mastery >= 0.4 ? 'warning' : 'danger'}" style="width:${p.avg_mastery*100}%;"></div></div>
              <div style="font-size:0.75rem;color:var(--text2);">${Math.round(p.avg_mastery*100)}%</div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
    <div class="card">
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <a class="btn btn-primary" href="#" onclick="navigate('quiz');return false;">🎯 Faire un quiz</a>
        <a class="btn btn-secondary" href="#" onclick="navigate('vocabulary');return false;">📖 Réviser le vocabulaire</a>
      </div>
    </div>
  `;
}

// ======== VOCABULARY ========
async function loadVocabulary() {
  const lang = document.getElementById('vocabLang').value;
  const category = document.getElementById('vocabCategory').value;
  const search = document.getElementById('vocabSearch').value;
  const el = document.getElementById('vocabList');
  el.innerHTML = '<div class="spinner"></div>';

  const params = new URLSearchParams({ language: lang, page: '1', per_page: '200' });
  if (category) params.set('category', category);
  if (search) params.set('search', search);

  const data = await api(`/vocabulary/words?${params}`);
  if (data.error) { el.innerHTML = `<div class="card">Erreur: ${data.error}</div>`; return; }

  if (!data.items?.length) {
    el.innerHTML = '<div class="card">Aucun mot trouvé pour cette langue.</div>';
    return;
  }

  el.innerHTML = `<div style="font-size:0.85rem;color:var(--text2);margin-bottom:8px;">${data.total} mots</div>
    <div class="card" style="padding:0;">${data.items.map(w => `
      <div class="vocab-item" onclick="showWordDetail(${w.id})">
        <div>
          <div class="vocab-fr">${w.french}</div>
          <div class="vocab-trans">${w.translation}</div>
          ${w.phonetic ? `<div class="vocab-phonetic">${w.phonetic}</div>` : ''}
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          ${w.category_emoji ? `<span>${w.category_emoji}</span>` : ''}
          <button class="speak-btn" onclick="event.stopPropagation();speak('${w.french.replace(/'/g, "\\'")}','fr')">🔊</button>
          ${w.translation ? `<button class="speak-btn" onclick="event.stopPropagation();speak('${w.translation.replace(/'/g, "\\'")}','${lang}')">🌍</button>` : ''}
        </div>
      </div>
    `).join('')}</div>`;
}

function debounceSearch() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(loadVocabulary, 300);
}

// ======== ADMIN: ADD / EDIT / DELETE ========
let editingWordId = null;

async function showWordDetail(wordId) {
  const data = await api(`/vocabulary/words/${wordId}`);
  if (data.error) return;

  document.getElementById('modalWord').textContent = data.french;
  const transEl = document.getElementById('modalTranslations');
  transEl.innerHTML = '';

  const langs = ['en','la','es','de','it','ru','zh','ja','kr','km'];
  langs.forEach(lang => {
    const t = data.translations?.[lang];
    if (!t) return;
    transEl.innerHTML += `
      <div class="translation-row">
        <span class="lang-code">${lang.toUpperCase()}</span>
        <span class="lang-trans"><strong>${t.translation}</strong>
          ${t.phonetic ? `<span class="lang-phonetic"> [${t.phonetic}]</span>` : ''}
        </span>
        <button class="speak-btn" onclick="speak('${t.translation.replace(/'/g, "\\'")}','${lang}')">🔊</button>
      </div>`;
  });

  const exEl = document.getElementById('modalExamples');
  const firstTrans = data.translations?.['en'];
  if (firstTrans?.example_fr) {
    exEl.innerHTML = `<div class="card" style="background:var(--bg);">
      <div style="font-size:0.85rem;color:var(--text2);">Exemple:</div>
      <div>${firstTrans.example_fr}</div>
      ${firstTrans.example_target ? `<div style="color:var(--accent2);margin-top:4px;">→ ${firstTrans.example_target}</div>` : ''}
    </div>`;
  } else {
    exEl.innerHTML = '';
  }

  document.getElementById('modalEditBtn').dataset.id = wordId;
  document.getElementById('wordModal').classList.add('open');
}

function closeModal() {
  document.getElementById('wordModal').classList.remove('open');
}

async function deleteWord(wordId, french) {
  if (!confirm(`Supprimer définitivement « ${french} » ?\nToutes les traductions et progressions seront supprimées.`)) return;
  await api(`/vocabulary/words/${wordId}`, { method: 'DELETE' });
  closeModal();
  loadVocabulary();
}

async function showEditWord(wordId) {
  const data = await api(`/vocabulary/words/${wordId}`);
  if (data.error) return;
  editingWordId = wordId;

  const cats = await api('/vocabulary/categories');
  const catOpts = cats.map(c => `<option value="${c.name}" ${c.name === data.category ? 'selected' : ''}>${c.emoji} ${c.name}</option>`).join('');

  let transHtml = '';
  const allLangs = { en:'English',la:'Latin',es:'Español',de:'Deutsch',it:'Italiano',ru:'Русский',zh:'中文',ja:'日本語',kr:'한국어',km:'ភាសាខ្មែរ' };
  for (const [code, name] of Object.entries(allLangs)) {
    const t = data.translations?.[code];
    transHtml += `<div class="form-row" style="margin-bottom:4px;">
      <div style="flex:0 0 40px;font-weight:700;color:var(--accent);padding-top:10px;">${code}</div>
      <div style="flex:3;"><input type="text" id="editTrans_${code}" value="${(t?.translation || '').replace(/"/g,'&quot;')}" placeholder="Traduction"></div>
      <div style="flex:2;"><input type="text" id="editPhon_${code}" value="${(t?.phonetic || '').replace(/"/g,'&quot;')}" placeholder="Phonétique"></div>
    </div>`;
  }

  document.getElementById('editModal').innerHTML = `
    <div class="modal">
      <button class="modal-close" onclick="closeEdit()">&times;</button>
      <h2>✏️ Modifier le mot</h2>
      <div class="form-group"><label>Mot français</label><input type="text" id="editFrench" value="${data.french.replace(/"/g,'&quot;')}"></div>
      <div class="form-group"><label>Catégorie</label><select id="editCategory">${catOpts}</select></div>
      <h3 style="margin-top:12px;margin-bottom:8px;">Traductions</h3>
      ${transHtml}
      <div style="display:flex;gap:8px;margin-top:16px;">
        <button class="btn btn-primary" onclick="saveEditWord()">💾 Enregistrer</button>
        <button class="btn btn-danger" onclick="deleteWord(${wordId}, '${data.french.replace(/'/g, "\\'")}')">🗑️ Supprimer</button>
        <button class="btn btn-secondary" onclick="closeEdit()">Annuler</button>
      </div>
    </div>`;
  document.getElementById('editModal').classList.add('open');
}

function closeEdit() {
  document.getElementById('editModal').classList.remove('open');
  editingWordId = null;
}

async function saveEditWord() {
  const french = document.getElementById('editFrench').value.trim();
  if (!french) return alert('Le mot français est requis');
  const category = document.getElementById('editCategory').value;

  const translations = {};
  const allLangs = ['en','la','es','de','it','ru','zh','ja','kr','km'];
  for (const code of allLangs) {
    const trans = document.getElementById(`editTrans_${code}`)?.value?.trim();
    const phon = document.getElementById(`editPhon_${code}`)?.value?.trim();
    if (trans) {
      translations[code] = { translation: trans, phonetic: phon || '', example_fr: '', example_target: '', notes: '' };
    }
  }

  if (editingWordId) {
    await api(`/vocabulary/words/${editingWordId}`, {
      method: 'PUT',
      body: JSON.stringify({ french, category, translations }),
    });
    closeEdit();
    loadVocabulary();
  } else {
    const r = await api('/vocabulary/words', {
      method: 'POST',
      body: JSON.stringify({ french, category, translations }),
    });
    if (r.id) { closeEdit(); loadVocabulary(); }
  }
}

async function showAddWord() {
  editingWordId = null;
  const cats = await api('/vocabulary/categories');
  const catOpts = cats.map(c => `<option value="${c.name}">${c.emoji} ${c.name}</option>`).join('');

  let transHtml = '';
  const allLangs = { en:'English',la:'Latin',es:'Español',de:'Deutsch',it:'Italiano',ru:'Русский',zh:'中文',ja:'日本語',kr:'한국어',km:'ភាសាខ្មែរ' };
  for (const [code, name] of Object.entries(allLangs)) {
    transHtml += `<div class="form-row" style="margin-bottom:4px;">
      <div style="flex:0 0 40px;font-weight:700;color:var(--accent);padding-top:10px;">${code}</div>
      <div style="flex:3;"><input type="text" id="editTrans_${code}" placeholder="${name}"></div>
      <div style="flex:2;"><input type="text" id="editPhon_${code}" placeholder="Phonétique"></div>
    </div>`;
  }

  document.getElementById('editModal').innerHTML = `
    <div class="modal">
      <button class="modal-close" onclick="closeEdit()">&times;</button>
      <h2>➕ Nouveau mot</h2>
      <div class="form-group"><label>Mot français</label><input type="text" id="editFrench" placeholder="Entrez le mot en français"></div>
      <div class="form-group"><label>Catégorie</label><select id="editCategory">${catOpts}</select></div>
      <h3 style="margin-top:12px;margin-bottom:8px;">Traductions (optionnel)</h3>
      ${transHtml}
      <div style="display:flex;gap:8px;margin-top:16px;">
        <button class="btn btn-success" onclick="saveEditWord()">➕ Ajouter</button>
        <button class="btn btn-secondary" onclick="closeEdit()">Annuler</button>
      </div>
    </div>`;
  document.getElementById('editModal').classList.add('open');
}

document.getElementById('editModal')?.addEventListener('click', function(e) {
  if (e.target === this) closeEdit();
});
document.getElementById('wordModal').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

// ======== QUIZ ========
let quizState = { questions: [], current: 0, answers: [], score: 0 };

function loadQuizConfig() {
  const lang = document.getElementById('quizLang').value;
  loadCategories('quizCategory');
}

async function startQuiz() {
  const lang = document.getElementById('quizLang').value;
  const category = document.getElementById('quizCategory').value;
  const count = parseInt(document.getElementById('quizCount').value);

  document.getElementById('quizConfig').style.display = 'none';
  const el = document.getElementById('quizContent');
  el.innerHTML = '<div class="spinner"></div>';

  const params = new URLSearchParams({ language: lang, count: count.toString() });
  if (category) params.set('category', category);

  const data = await api(`/quiz/generate?${params}`);
  if (data.error || !data.questions?.length) {
    el.innerHTML = `<div class="card">Pas assez de mots pour générer un quiz. ${data.error || ''}
      <button class="btn btn-primary btn-block" style="margin-top:8px;" onclick="resetQuiz()">Retour</button></div>`;
    return;
  }

  quizState = { questions: data.questions, current: 0, answers: [], score: 0 };
  showQuestion();
}

function showQuestion() {
  const el = document.getElementById('quizContent');
  const q = quizState.questions[quizState.current];
  if (!q) return showQuizResult();

  const total = quizState.questions.length;
  const num = quizState.current + 1;

  el.innerHTML = `
    <div class="card">
      <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
        <span style="color:var(--text2);font-size:0.85rem;">Question ${num}/${total}</span>
        <span style="color:var(--text2);font-size:0.85rem;">✅ ${quizState.score}</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" style="width:${(quizState.current/total)*100}%;"></div></div>
      <h3 style="margin:16px 0;font-size:1.1rem;">${q.question_text}</h3>
      <div id="quizOptions">
        ${q.options.map(opt => `
          <button class="quiz-option" onclick="answerQuiz('${opt.replace(/'/g, "\\'")}')">${opt}</button>
        `).join('')}
      </div>
    </div>`;
}

async function answerQuiz(answer) {
  const q = quizState.questions[quizState.current];
  const opts = document.querySelectorAll('.quiz-option');
  opts.forEach(b => b.disabled = true);

  const correct = answer === q.correct_answer;
  opts.forEach(b => {
    if (b.textContent === q.correct_answer) b.classList.add('correct');
    if (b.textContent === answer && !correct) b.classList.add('wrong');
    if (b.textContent === answer && correct) b.classList.add('selected');
  });

  await api('/quiz/answer', {
    method: 'POST',
    body: JSON.stringify({ question_id: q.id, answer, time_spent: 5 }),
  });

  if (correct) quizState.score++;

  setTimeout(() => {
    quizState.current++;
    if (quizState.current >= quizState.questions.length) {
      showQuizResult();
    } else {
      showQuestion();
    }
  }, 1000);
}

function showQuizResult() {
  const total = quizState.questions.length;
  const score = quizState.score;
  const pct = Math.round((score / total) * 100);
  const el = document.getElementById('quizContent');

  el.innerHTML = `
    <div class="card quiz-result">
      <div class="quiz-score">${score}/${total}</div>
      <div class="quiz-feedback">${pct >= 80 ? '🌟 Excellent !' : pct >= 60 ? '👏 Bien !' : pct >= 40 ? '💪 Continue !' : '📚 Révision nécessaire !'}</div>
      <div class="progress-bar" style="max-width:300px;margin:12px auto;">
        <div class="progress-fill ${pct >= 70 ? 'success' : pct >= 40 ? 'warning' : 'danger'}" style="width:${pct}%;"></div>
      </div>
      <div style="margin-top:16px;display:flex;gap:8px;justify-content:center;flex-wrap:wrap;">
        <button class="btn btn-primary" onclick="startQuiz()">🔄 Refaire</button>
        <button class="btn btn-secondary" onclick="resetQuiz()">🏠 Menu quiz</button>
      </div>
    </div>`;
}

function resetQuiz() {
  document.getElementById('quizConfig').style.display = 'block';
  document.getElementById('quizContent').innerHTML = '';
  quizState = { questions: [], current: 0, answers: [], score: 0 };
}

// ======== PROGRESS ========
async function loadProgress(status = 'all') {
  const lang = document.getElementById('progressLang').value;
  const overviewEl = document.getElementById('progressOverview');
  const listEl = document.getElementById('progressList');

  document.querySelectorAll('[data-status]').forEach(b => {
    b.style.background = b.dataset.status === status ? 'var(--accent)' : '';
    b.style.color = b.dataset.status === status ? '#fff' : '';
  });

  overviewEl.innerHTML = '<div class="spinner"></div>';

  const overview = await api(`/progress/overview?language=${lang}`);
  if (overview.error) { overviewEl.innerHTML = `<div class="card">${overview.error}</div>`; return; }

  overviewEl.innerHTML = `
    <div class="grid-4">
      <div class="card"><div class="card-value">${overview.total_words}</div><div class="card-label">Mots étudiés</div></div>
      <div class="card"><div class="card-value" style="color:var(--success)">${overview.mastered}</div><div class="card-label">Maîtrisés</div></div>
      <div class="card"><div class="card-value" style="color:var(--warning)">${overview.learning}</div><div class="card-label">En cours</div></div>
      <div class="card"><div class="card-value" style="color:var(--danger)">${overview.to_review}</div><div class="card-label">À réviser</div></div>
    </div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span>Précision globale</span>
        <span style="font-weight:700;color:${overview.accuracy >= 70 ? 'var(--success)' : 'var(--danger)'}">${overview.accuracy}%</span>
      </div>
      <div class="progress-bar"><div class="progress-fill ${overview.accuracy >= 70 ? 'success' : 'danger'}" style="width:${overview.accuracy}%;"></div></div>
      <div style="font-size:0.8rem;color:var(--text2);margin-top:4px;">${overview.total_answers} réponses</div>
    </div>`;

  const params = new URLSearchParams({ language: lang });
  if (status !== 'all') params.set('status', status);
  const words = await api(`/progress/words?${params}`);

  if (words.items?.length) {
    listEl.innerHTML = `<div class="card" style="padding:0;">
      ${words.items.map(w => `
        <div class="vocab-item">
          <div>
            <div class="vocab-fr">${w.french}</div>
            <div class="vocab-trans">${w.translation}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-weight:700;">${Math.round(w.mastery_level * 100)}%</div>
            <div class="progress-bar" style="width:80px;"><div class="progress-fill ${w.mastery_level >= 0.8 ? 'success' : w.mastery_level >= 0.4 ? 'warning' : 'danger'}" style="width:${w.mastery_level * 100}%;"></div></div>
            <div style="font-size:0.75rem;color:var(--text2);">${w.review_count} relectures</div>
          </div>
        </div>
      `).join('')}</div>`;
  } else {
    listEl.innerHTML = '<div class="card" style="color:var(--text2);text-align:center;">Aucun mot dans cette catégorie</div>';
  }
}

async function loadMistakes() {
  const el = document.getElementById('mistakesList');
  const lang = document.getElementById('progressLang').value;
  const data = await api(`/progress/mistakes?language=${lang}&reviewed=false`);

  if (!data?.length) {
    el.innerHTML = '<div class="card" style="color:var(--text2);text-align:center;">Aucune erreur enregistrée 🎉</div>';
    return;
  }

  el.innerHTML = `<div class="card" style="padding:0;">${data.map(m => `
    <div class="mistake-item">
      <div style="flex:1;">
        <div style="font-size:0.85rem;color:var(--text2);margin-bottom:4px;">${m.context || 'Quiz'}</div>
        <div>Tu as répondu: <span class="mistake-wrong">${m.user_answer}</span></div>
        <div>Réponse correcte: <span class="mistake-correct">${m.correct_answer}</span></div>
      </div>
      <button class="btn btn-sm btn-success" onclick="reviewMistake(${m.id})">✅ Vue</button>
    </div>
  `).join('')}</div>`;
}

async function reviewMistake(id) {
  await api(`/progress/mistakes/${id}/review`, { method: 'POST' });
  loadMistakes();
  loadProgress();
}

// ======== STATS ========
async function loadStats() {
  const dashEl = document.getElementById('statsDashboard');
  const weeklyEl = document.getElementById('statsWeekly');
  const weakEl = document.getElementById('weaknesses');

  const [dashboard, weekly, weaknesses] = await Promise.all([
    api('/stats/dashboard'),
    api('/stats/weekly'),
    api('/stats/weaknesses?language=en'),
  ]);

  dashEl.innerHTML = `
    <div class="card">
      <div class="card-title">📊 Vue d'ensemble</div>
      <div class="grid-2">
        <div class="stat-box"><div class="stat-value">${dashboard.word_count}</div><div class="stat-label">Mots</div></div>
        <div class="stat-box"><div class="stat-value">${dashboard.translation_count}</div><div class="stat-label">Traductions</div></div>
        <div class="stat-box"><div class="stat-value">${dashboard.quiz_attempts}</div><div class="stat-label">Quiz tentés</div></div>
        <div class="stat-box"><div class="stat-value">${dashboard.mistake_count}</div><div class="stat-label">Erreurs</div></div>
      </div>
    </div>`;

  if (weekly.days?.length) {
    weeklyEl.innerHTML = `<div class="card">
      <div class="card-title">📅 Activité des 7 derniers jours</div>
      <div style="display:flex;gap:8px;overflow-x:auto;padding:8px 0;">
        ${weekly.days.map(d => `
          <div style="flex:1;min-width:60px;text-align:center;">
            <div style="font-size:0.7rem;color:var(--text2);">${new Date(d.date).toLocaleDateString('fr', { weekday: 'short' })}</div>
            <div style="height:60px;display:flex;align-items:flex-end;justify-content:center;gap:2px;">
              <div style="width:12px;background:var(--success);border-radius:3px;height:${d.total ? (d.correct/d.total)*50 : 0}px;"></div>
              <div style="width:12px;background:var(--danger);border-radius:3px;height:${d.total ? (d.mistakes/d.total)*50 : 0}px;"></div>
            </div>
            <div style="font-size:0.75rem;font-weight:600;">${d.total}</div>
          </div>
        `).join('')}
      </div>
    </div>`;
  }

  if (weaknesses.weaknesses?.length) {
    weakEl.innerHTML = `<div class="card">
      <div class="card-title">⚠️ Points faibles (erreurs non corrigées)</div>
      ${weaknesses.weaknesses.slice(0, 10).map(w => `
        <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--bg3);">
          <span style="color:var(--danger);">❌ ${w.word}</span>
          <span style="color:var(--text2);font-size:0.85rem;">${w.count} erreurs</span>
        </div>
      `).join('')}
    </div>`;
  }
}

// ======== AI ========
async function callAI() {
  const action = document.getElementById('aiAction').value;
  const lang = document.getElementById('aiLang').value;
  const word = document.getElementById('aiWord').value.trim();
  const el = document.getElementById('aiResult');

  if (!word) { el.innerHTML = '<div style="color:var(--danger);">Veuillez entrer un mot ou une expression.</div>'; return; }

  el.innerHTML = '<div class="spinner"></div>';

  let endpoint = '';
  let body = { word, language: lang };

  switch(action) {
    case 'explain': endpoint = '/ai/explain'; break;
    case 'sentences': endpoint = '/ai/sentences'; break;
    case 'phonetics': endpoint = '/ai/phonetics'; break;
    case 'translate': endpoint = '/ai/translate'; break;
    case 'generate_quiz':
      const params = new URLSearchParams({ language: lang, count: '3' });
      endpoint = `/ai/generate-quiz?${params}`;
      body = {};
      break;
  }

  const data = await api(endpoint, {
    method: 'POST',
    body: JSON.stringify(body),
  });

  if (data.error) {
    el.innerHTML = `<div class="card" style="color:var(--danger);">${data.error}</div>`;
    return;
  }

  el.innerHTML = formatAIResponse(action, data);
}

function formatAIResponse(action, data) {
  if (data.explanation) {
    return `<div class="card" style="background:var(--bg);">
      <div style="white-space:pre-wrap;">${data.explanation}</div>
      ${data.examples?.map(e => `
        <div style="margin-top:8px;padding:8px;background:var(--bg3);border-radius:8px;">
          <div>${e.fr}</div>
          <div style="color:var(--accent2);">→ ${e.target}</div>
        </div>
      `).join('')}
      ${data.tips?.length ? `<div style="margin-top:8px;"><strong>💡 Astuces:</strong><ul>${data.tips.map(t => `<li>${t}</li>`).join('')}</ul></div>` : ''}
    </div>`;
  }
  if (data.sentences) {
    return `<div class="card" style="background:var(--bg);">
      ${data.sentences.map(s => `
        <div style="padding:8px;margin-bottom:8px;background:var(--bg3);border-radius:8px;">
          <div>${s.fr}</div>
          <div style="color:var(--accent2);">→ ${s.target}</div>
          <button class="speak-btn" onclick="speak('${(s.target || '').replace(/'/g, "\\'")}','en')">🔊</button>
        </div>
      `).join('')}
    </div>`;
  }
  if (data.phonetic_simple || data.phonetic_ipa) {
    return `<div class="card" style="background:var(--bg);">
      ${data.phonetic_simple ? `<div><strong>Simplifié:</strong> ${data.phonetic_simple}</div>` : ''}
      ${data.phonetic_ipa ? `<div><strong>IPA:</strong> ${data.phonetic_ipa}</div>` : ''}
      ${data.pronunciation_tips ? `<div style="margin-top:8px;">💡 ${data.pronunciation_tips}</div>` : ''}
    </div>`;
  }
  if (data.translation) {
    return `<div class="card" style="background:var(--bg);">
      <div><strong>Traduction:</strong> ${data.translation}</div>
      ${data.alternative_translations?.length ? `<div style="margin-top:8px;"><strong>Alternatives:</strong> ${data.alternative_translations.join(', ')}</div>` : ''}
      ${data.usage_context ? `<div style="margin-top:8px;color:var(--text2);">📝 ${data.usage_context}</div>` : ''}
      ${data.register ? `<div style="margin-top:4px;"><span style="padding:2px 8px;border-radius:4px;background:var(--bg3);font-size:0.8rem;">${data.register}</span></div>` : ''}
      ${data.common_mistakes ? `<div style="margin-top:8px;color:var(--danger);">⚠️ ${data.common_mistakes}</div>` : ''}
    </div>`;
  }
  if (data.questions) {
    return `<div class="card" style="background:var(--bg);">
      <div class="card-title">📝 QCM généré par l'IA</div>
      ${data.questions.map((q, i) => `
        <div style="padding:8px;margin-bottom:8px;background:var(--bg3);border-radius:8px;">
          <div style="font-weight:600;">${i+1}. ${q.question_text}</div>
          <div style="margin-top:4px;color:var(--success);">✅ ${q.correct_answer}</div>
          ${q.explanation ? `<div style="margin-top:4px;font-size:0.85rem;color:var(--text2);">${q.explanation}</div>` : ''}
        </div>
      `).join('')}
    </div>`;
  }
  return `<div class="card" style="background:var(--bg);"><pre style="white-space:pre-wrap;">${JSON.stringify(data, null, 2)}</pre></div>`;
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const msg = input.value.trim();
  if (!msg) return;

  const messagesEl = document.getElementById('chatMessages');
  messagesEl.innerHTML += `<div class="chat-msg user">${msg}</div>`;
  input.value = '';
  messagesEl.scrollTop = messagesEl.scrollHeight;
  messagesEl.innerHTML += `<div class="chat-msg ai"><div class="spinner" style="margin:4px auto;"></div></div>`;

  const data = await api('/ai/chat', {
    method: 'POST',
    body: JSON.stringify({ messages: [{ role: 'user', content: msg }] }),
  });

  messagesEl.querySelector('.chat-msg:last-child').remove();

  const response = data.response?.explanation || data.response?.raw || JSON.stringify(data.response || data, null, 2);
  messagesEl.innerHTML += `<div class="chat-msg ai">${response}</div>`;
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ======== INIT ========
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
});
