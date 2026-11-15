// Enhance Vintage MILF - ekran aplikacji: odpytuje /api/stan i wysyla akcje do aplikacja.py
(() => {
const R = document.getElementById('a3App'), $ = s => R.querySelector(s), $$ = s => [...R.querySelectorAll(s)];
let ac;
const klik = (f = 520, d = .05) => { try { ac = ac || new AudioContext(); const o = ac.createOscillator(), g = ac.createGain(); o.type = 'triangle'; o.frequency.value = f; g.gain.setValueAtTime(.08, ac.currentTime); g.gain.exponentialRampToValueAtTime(.0001, ac.currentTime + d); o.connect(g).connect(ac.destination); o.start(); o.stop(ac.currentTime + d) } catch (e) {} };
// akcja na serwerze; przy bledzie toast i { blad }, zeby wolajacy mogl cofnac zmiane w oknie
const api = (n, d = {}) => fetch('/api/' + n, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(d) })
  .then(r => r.ok ? r.json() : r.json().catch(() => ({})).then(j => { throw new Error(j.blad || 'kod ' + r.status) }))
  .catch(e => { toast('Nie udało się: ' + e.message); return { blad: e.message } }).finally(odswiez);
// przycisk zablokowany na czas zadania, z tymczasowym napisem
const zajety = (btn, napis, obietnica) => { const t = btn.innerHTML; btn.disabled = true; btn.innerHTML = napis; return obietnica.finally(() => { btn.innerHTML = t; btn.disabled = false }) };
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const zegar = s => { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0') };
const sek = s => s >= 60 ? Math.floor(s / 60) + ' min ' + Math.round(s % 60) + ' s' : Math.round(s) + ' s';
const mb = b => (b / 1048576).toLocaleString('pl-PL', { maximumFractionDigits: 1 }) + ' MB';
const liczba = x => (+x).toLocaleString('pl-PL', { maximumFractionDigits: 2 });
const nazwaPliku = p => String(p || '').split(/[\\/]/).pop();

function toast(t) { const el = $('#a3Toast'); el.textContent = t; el.classList.add('on'); clearTimeout(toast.t); toast.t = setTimeout(() => el.classList.remove('on'), 5000) }

// os klatek: dekoracyjne miniatury, zapalaja sie wraz z postepem
const OS = ['supermarket', 'silownia', 'wrotki', 'kregle', 'frisbee', 'supermarket', 'silownia', 'wrotki'];
$('#a3Os').innerHTML = OS.map(n => `<img src="grafiki/${n}.jpg" alt="" onerror="this.style.visibility='hidden'">`).join('');
R.querySelectorAll('img').forEach(i => { i.addEventListener('error', () => { i.style.visibility = 'hidden' }); i.addEventListener('load', () => { i.style.visibility = '' }) });

// pozy postaci w kazdym stanie
const POZY = { pusty: ['kobieta_szpula', '../facet'], plik: ['kobieta_szpula', 'facet_szpula'], trwa: ['kobieta_szpula', 'facet_zegarek'], gotowe: ['kobieta_kciuk', 'facet_skok'], blad: ['kobieta_zdziwiona', 'facet_oszolomiony'] };
const pozy = s => { const [k, f] = POZY[s]; $('#a3KobPlyn').src = 'grafiki/wyciete/pozy/' + k + '.png'; $('#a3FacetImg').src = 'grafiki/wyciete/pozy/' + f + '.png' };
const skokFaceta = () => { const f = $('#a3Facet'); f.classList.remove('skok'); void f.offsetWidth; f.classList.add('skok'); klik(760, .08) };
const przel = (el, on) => { el.classList.toggle('on', !!on); el.setAttribute('aria-pressed', !!on) };

const POCZ = [0, 60, 70, 90], SZER = [60, 10, 20, 10];
let ost = { stan: '', krok: 0, kadr: '', wynik: '', kolejka: '', hist: '', log: '' };

function render(s) {
  const st = s.stan, p = s.plik;
  if (st !== ost.stan) {
    if (st === 'gotowe' && ost.stan === 'trwa') klik(880, .2);
    R.dataset.stan = st; pozy(st); $('#a3AnBox').classList.remove('pyta'); ost.stan = st;
  }
  // plik
  if (p) {
    const k = p.sciezka + '|' + p.rozmiar;
    if (k !== ost.kadr) {
      $('#a3Nazwa').textContent = p.nazwa;
      $('#a3Info').innerHTML = [`${p.w}×${p.h}`, `${liczba(p.fps)} kl./s`, sek(p.dlugosc), mb(p.rozmiar)].map(t => `<span class="tag">${esc(t)}</span>`).join('') + `<span class="tag zl">po poprawie ${p.w * 4}×${p.h * 4}</span>`;
      ost.kadr = k; const u = '/api/kadr?co=src&k=' + encodeURIComponent(k); $('#a3Mini').style.backgroundImage = `url("${u}")`; $('#a3PrzedImg').src = u; $('#a3PoImg').src = u; ost.wynik = '' }
    const m = Math.max(1, Math.round(s.kl_s / p.fps));
    $('#a3Wyl').innerHTML = `${liczba(p.fps)} → <b>${Math.round(p.fps * m)} kl./s</b> (×${m}) · około ${Math.max(1, Math.round(s.szacunek / 60))} min`;
    $('#a3TrwaTyt').textContent = 'Poprawiam ' + p.nazwa;
  } else { $('#a3Wyl').textContent = 'Wybierz film, a policzę, ile to potrwa.'; ost.kadr = '' }
  $$('#a3Kls .kl').forEach(b => b.classList.toggle('on', +b.dataset.k === s.kl_s));
  $('#a3OpRife').textContent = `RIFE do ${s.kl_s} kl./s`;
  const biel = $('#a3Biel');
  if (document.activeElement !== biel) { biel.value = s.sila; $('#a3BielW').textContent = (+s.sila).toFixed(2).replace('.', ',') }
  przel($('#a3PrzPor'), s.porownanie); przel($('#a3PrzFol'), s.otworz_folder);
  $('#a3Start').disabled = !p || st === 'trwa';
  $('#a3Zmien').hidden = st === 'trwa';
  $$('#a3Kroki .krok .op')[3].textContent = s.porownanie ? 'Film porównawczy' : 'Porównanie pominięte';

  // postep
  const pr = s.postep;
  $('#a3Wyp').style.transform = `scaleX(${pr / 100})`;
  $('#a3Proc').innerHTML = Math.floor(pr) + '<span>%</span>';
  $('#a3Min').textContent = zegar(s.minelo);
  $('#a3Zost').textContent = st === 'trwa' ? zegar(s.zostalo) : '0:00';
  $$('#a3Kroki .krok').forEach((k, i) => {
    const czesc = Math.min(1, Math.max(0, (pr - POCZ[i]) / SZER[i]));
    k.classList.toggle('zrob', czesc >= 1 || st === 'gotowe');
    k.classList.toggle('akt', (st === 'trwa' || st === 'blad') && i === Math.max(1, s.krok) - 1 && czesc < 1);
    k.querySelector('.pas i').style.transform = `scaleX(${czesc})`;
  });
  if (st === 'trwa' && s.krok > ost.krok && ost.krok > 0) skokFaceta();
  ost.krok = s.krok;
  const os = $$('#a3Os img'); os.forEach((im, i) => im.classList.toggle('zr', i < Math.round(pr / 100 * os.length)));
  const lk = s.log.join('\n');
  if (lk !== ost.log) {  // tylko przy nowych liniach, zeby dalo sie zaznaczac i kopiowac log
    ost.log = lk;
    const log = $('#a3Log'), naDole = log.scrollHeight - log.scrollTop - log.clientHeight < 30;
    log.innerHTML = esc(lk) + '\n<span class="kursor">▌</span>';
    if (naDole) log.scrollTop = log.scrollHeight;
  }

  // gotowe i blad
  if (st === 'gotowe') {
    $('#a3GotTyt').textContent = `Gotowe w ${(s.minelo / 60).toFixed(1).replace('.', ',')} min!`;
    $('#a3Sciezki').innerHTML = [s.wynik, s.wynik_por].filter(Boolean).map(x => esc(nazwaPliku(x))).join('<br>');
    if (s.wynik && ost.wynik !== s.wynik) { ost.wynik = s.wynik; $('#a3PoImg').src = '/api/kadr?co=wynik&k=' + encodeURIComponent(s.wynik) }
  }
  if (st === 'blad') { $('#a3BladTxt').textContent = s.blad || ''; $('#a3BladKod').textContent = s.log.slice(-3).join('\n') }

  // karta graficzna
  const g = s.gpu, gb = mbs => (mbs / 1024).toFixed(1).replace('.', ',');
  $('#a3GpuNazwa').textContent = g.nazwa ? `${g.nazwa} · ${Math.round(g.razem / 1024)} GB` : 'Karta graficzna';
  $('#a3GpuTxt').textContent = g.comfyui ? `działa ComfyUI · zajęte ${gb(g.uzyte)} GB` : g.razem ? `zajęte ${gb(g.uzyte)} z ${Math.round(g.razem / 1024)} GB` : 'nie widzę karty NVIDIA';
  $('#a3Gpu').classList.toggle('zajeta', !!g.comfyui);

  // kolejka i historia (przebudowa tylko po zmianie, zeby nie gubic potwierdzenia pod mysza)
  const kk = JSON.stringify(s.kolejka.map(f => f.sciezka));
  if (kk !== ost.kolejka) {
    ost.kolejka = kk;
    $('#a3Kolejka').innerHTML = s.kolejka.map((f, i) => `<li data-i="${i}"><span>🎬</span><span class="n" title="${esc(f.sciezka)}">${esc(f.nazwa)}</span><span class="st">${esc(sek(f.dlugosc))}</span><div class="akcje"><span class="zwykle"><button class="ik" data-co="gora" title="W górę" aria-label="Przesuń w górę">↑</button><button class="ik" data-co="dol" title="W dół" aria-label="Przesuń w dół">↓</button><button class="ik usun" title="Usuń z kolejki" aria-label="Usuń z kolejki">🗑</button></span><span class="potw">Usunąć? <button class="tak">Usuń</button><button class="nie">Nie</button></span></div></li>`).join('');
  }
  const hk = JSON.stringify(s.historia);
  if (hk !== ost.hist) {
    ost.hist = hk;
    $('#a3Hist').innerHTML = s.historia.length ? s.historia.map(h => `<li><span>✔</span><span class="n" title="${esc(h.sciezka)}">${esc(h.zrodlo || h.nazwa)}</span><span class="st">${esc(h.data.slice(5, 10).split('-').reverse().join('.'))}</span><div class="akcje"><span class="zwykle"><button class="ik" data-folder="${esc(h.sciezka)}" title="Pokaż w folderze" aria-label="Pokaż w folderze">📁</button></span></div></li>`).join('')
      : '<li><span>·</span><span class="n">Jeszcze nic nie poprawiono</span></li>';
  }
}

let czekaj;
async function odswiez() {
  clearTimeout(czekaj);
  try { const s = await fetch('/api/stan', { cache: 'no-store' }).then(r => r.json()); render(s); czekaj = setTimeout(odswiez, s.stan === 'trwa' ? 700 : 1500) }
  catch (e) { toast('Program w tle nie odpowiada. Zamknij to okno i uruchom program ponownie.'); czekaj = setTimeout(odswiez, 3000) }
}

// wybor plikow (okno Windows otwiera serwer)
let wybieram = false;  // jedno okno wyboru naraz
const wybierz = przycisk => {
  if (wybieram) return; wybieram = true; klik();
  const z = api('wybierz').then(r => r.bledy?.length && toast('Nie da się otworzyć: ' + r.bledy.join('; '))).finally(() => { wybieram = false });
  if (przycisk) zajety(przycisk, 'Otwieram…', z);
};
const strefa = $('#a3Strefa');
strefa.addEventListener('click', () => wybierz($('#a3Wybierz')));
strefa.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); wybierz($('#a3Wybierz')) } });
// okno przegladarki nie zna sciezki upuszczonego pliku: zamiast otwierac film w oknie, podpowiedz skrot
document.addEventListener('dragover', e => e.preventDefault());
document.addEventListener('drop', e => { e.preventDefault(); klik(300); toast('Upuść film na ikonę programu na pulpicie (trafi do kolejki) albo kliknij „Wybierz film”.') });
$('#a3Dodaj').addEventListener('click', e => wybierz(e.currentTarget));
$('#a3Zmien').addEventListener('click', () => { klik(); api('zmien') });
$('#a3Kolejny').addEventListener('click', () => { klik(); api('zmien') });

// ustawienia
$$('#a3Kls .kl').forEach(b => b.addEventListener('click', () => { klik(640); api('ustaw', { kl_s: +b.dataset.k }) }));
const biel = $('#a3Biel');
biel.addEventListener('input', () => $('#a3BielW').textContent = (+biel.value).toFixed(2).replace('.', ','));
biel.addEventListener('change', () => { klik(580, .04); api('ustaw', { sila: +biel.value }) });
[['#a3PrzPor', 'porownanie'], ['#a3PrzFol', 'otworz_folder']].forEach(([sel, klucz]) => $(sel).addEventListener('click', e => {
  const el = e.currentTarget, on = !el.classList.contains('on'); klik(on ? 560 : 380); przel(el, on);
  api('ustaw', { [klucz]: on }).then(r => r.blad && przel(el, !on));
}));

// start, anulowanie, wynik
const uruchom = e => { klik(780, .12); zajety(e.currentTarget, 'Uruchamiam…', api('start')) };
$('#a3Start').addEventListener('click', uruchom);
$('#a3Ponow').addEventListener('click', uruchom);
$('#a3Anuluj').addEventListener('click', () => { klik(360); $('#a3AnBox').classList.add('pyta') });
$('#a3AnNie').addEventListener('click', () => { klik(); $('#a3AnBox').classList.remove('pyta') });
$('#a3AnTak').addEventListener('click', () => { klik(260, .15); $('#a3AnBox').classList.remove('pyta'); api('anuluj') });
$('#a3Folder').addEventListener('click', () => { klik(700); api('folder').then(r => r.ok === false && toast('Nie znalazłem pliku z wynikiem.')) });
$('details.log summary').addEventListener('click', () => klik(620, .04));

// kolejka: akcje po najechaniu, usuwanie z potwierdzeniem w miejscu
const kol = $('#a3Kolejka');
kol.addEventListener('click', e => {
  const a = e.target.closest('.akcje'); if (!a) return; const li = a.closest('li'), i = +li.dataset.i;
  if (e.target.closest('.usun')) { klik(360); a.classList.add('pyta') }
  else if (e.target.closest('.nie')) { klik(); a.classList.remove('pyta') }
  else if (e.target.closest('.tak')) { klik(260, .15); li.classList.add('znika'); setTimeout(() => api('kolejka', { i, co: 'usun' }).then(r => { if (r.blad) { li.classList.remove('znika'); a.classList.remove('pyta') } }), 280) }
  else if (e.target.closest('[data-co]')) { klik(600); api('kolejka', { i, co: e.target.closest('[data-co]').dataset.co }) }
});
// potwierdzenie znika, gdy mysz opusci swoj wiersz
kol.addEventListener('mouseout', e => { const li = e.target.closest('li'); if (li && !li.contains(e.relatedTarget)) li.querySelector('.akcje')?.classList.remove('pyta') });
$('#a3Hist').addEventListener('click', e => { const b = e.target.closest('[data-folder]'); if (b) { klik(700); api('folder', { sciezka: b.dataset.folder }).then(r => r.ok === false && toast('Tego pliku już nie ma na dysku.')) } });

// przed / po
const por = $('#a3Por'), przed = por.querySelector('.przed'), lin = por.querySelector('.linia'); let ciag = false;
const ruch = x => { const r = por.getBoundingClientRect(), p = Math.min(100, Math.max(0, (x - r.left) / r.width * 100)); przed.style.clipPath = `inset(0 ${100 - p}% 0 0)`; lin.style.left = p + '%' };
por.addEventListener('pointerdown', e => { ciag = true; klik(500, .03); por.setPointerCapture(e.pointerId); ruch(e.clientX) });
por.addEventListener('pointermove', e => ciag && ruch(e.clientX));
por.addEventListener('pointerup', () => ciag = false);

pozy('pusty');
odswiez();
})();
