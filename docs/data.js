// ============================================================================
//  DATA LAYER (v2)  —  the ONLY file that knows where the backend lives.
//
//  Backend = a Google Apps Script web app exposing named actions:
//    login / register / setGrade / setExtra / setProfile  (POST)
//  Deploy APPS_SCRIPT.md, then paste the /exec URL into GSHEET_API below.
//  index.html talks only to window.API.
//
//  POST bodies are sent as a PLAIN string (no JSON Content-Type) so they stay
//  preflight-free simple requests — Apps Script can't answer a CORS preflight.
// ============================================================================
const GSHEET_API = "https://script.google.com/macros/s/AKfycbwJDFwpp8reVdDEDAv4sfVtwBPe-CdZG8zoWBGXUeHvtNc9ioGe_N64TgI1-UXc-NJH/exec";  // <-- your Apps Script /exec URL

const CONFIGURED = !!GSHEET_API && !GSHEET_API.includes("PASTE");

// Apps Script's /exec 302-redirects to script.googleusercontent.com, and THAT endpoint drops a
// request often enough to matter -- the admin dashboard already had to grow sheetRetry() around
// exactly this (see the note above fetchCohort in index.html). The student login/write path had
// no retry at all, so a single transient 404 either lost an edit outright or, at login, latched
// the whole session into offline mode. Every action below except register() is a read or an
// upsert-by-key, so replaying one is a no-op; register is the one non-idempotent call and opts
// out with {retry:false}.
const POST_TRIES = 3, POST_TIMEOUT_MS = 25000, GET_TIMEOUT_MS = 20000;
// NOTE: named apiSleep, not sleepMs -- data.js and the inline script in index.html are both
// classic top-level scripts sharing ONE lexical scope, and index.html already declares a
// top-level "const sleepMs" for sheetRetry(). A duplicate const there is a SyntaxError that
// takes the whole page down, not a shadowed variable.
const apiSleep = (ms) => new Promise((r) => setTimeout(r, ms));

// fetch with a deadline. Apps Script can stall behind its own script lock, and a hung POST used
// to leave the login button reading "Signing in..." for ever -- no error, no offline fallback,
// nothing to retry. AbortController turns that into an ordinary failure the caller can handle.
function fetchDeadline(url, init, ms) {
  if (typeof AbortController === "undefined") return fetch(url, init);
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), ms);
  return fetch(url, Object.assign({}, init, { signal: ctl.signal }))
    .finally(() => clearTimeout(t));
}

async function apiPost(payload, opts) {
  if (!CONFIGURED) throw new Error("Set your Apps Script /exec URL in data.js (GSHEET_API)");
  const tries = (opts && opts.retry === false) ? 1 : POST_TRIES;
  let last = null;
  for (let i = 0; i < tries; i++) {
    try {
      const r = await fetchDeadline(GSHEET_API, { method: "POST", body: JSON.stringify(payload) }, POST_TIMEOUT_MS);
      if (!r.ok) throw new Error("POST " + r.status);
      const out = await r.json();
      // A well-formed reply carrying .error is the BACKEND's verdict ("unknown action",
      // "ID already taken"), not a transport failure. Replaying it would change nothing, so it
      // is raised at once and flagged, and the retry loop lets a flagged error straight through.
      if (out && out.error) { const e = new Error(out.error); e.fromBackend = true; throw e; }
      return out;
    } catch (err) {
      if (err && err.fromBackend) throw err;
      last = err;
      if (i < tries - 1) await apiSleep(400 * (i + 1));
    }
  }
  throw last;
}

window.API = {
  configured: CONFIGURED,

  // Wake the Apps Script (cold-start is the main login delay). Fire-and-forget GET
  // on page load so the script is warm by the time the student submits.
  warmup() {
    if (!CONFIGURED) return;
    try { fetch(GSHEET_API + "?action=ping", { cache: "no-store" }).catch(() => {}); } catch (e) {}
  },

  // Cheap liveness check driving the reconnect probe in index.html. Resolves true/false and
  // never rejects, so a caller can poll it on a timer without a catch on every tick.
  ping() {
    if (!CONFIGURED) return Promise.resolve(false);
    return fetchDeadline(GSHEET_API + "?action=ping", { cache: "no-store" }, GET_TIMEOUT_MS)
      .then((r) => r.ok).catch(() => false);
  },

  // -> {ok:true, profile, grades:{key:grade}, extras:[...]} | {ok:false}
  login(student_id, password) {
    return apiPost({ action: "login", student_id, password });
  },

  // -> {ok:true, profile} | {ok:false, error}
  register({ student_id, name, password, advisor }) {
    // NOT retried: the row append is not idempotent, so a replay after a lost response comes
    // back "ID already taken" for an account that was in fact just created.
    return apiPost({ action: "register", student_id, name, password, advisor }, { retry: false });
  },

  // grade lives in the per-semester tab `sem` (e.g. "Y1S1"); "" clears it
  setGrade(student_id, sem, course_key, grade) {
    return apiPost({ action: "setGrade", student_id, sem, course_key, grade });
  },

  // extras = {starred, note, elec_code, elec_name, moved_col}; upserts one row in `extras`.
  // moved_col is the semester column the student actually took the course in ("" = follows the plan).
  setExtra(student_id, course_key, data) {
    return apiPost({ action: "setExtra", student_id, course_key, data });
  },

  // Bulk setExtra: items = [{course_key, data}, ...]. The auto-shift cascade moves a dozen
  // courses at once, and a dozen separate POSTs all queue behind the backend's script lock
  // until the last ones time out. One request, one lock, one write.
  // Throws "unknown action: setExtras" against a backend that has not been redeployed yet —
  // index.html catches that and falls back to per-key setExtra.
  setExtras(student_id, items) {
    return apiPost({ action: "setExtras", student_id, items });
  },

  // removes the extras row entirely. Used when a student-added course is deleted: upserting a
  // blank row instead (the only option before) left an empty row behind permanently.
  delExtra(student_id, course_key) {
    return apiPost({ action: "setExtra", student_id, course_key, remove: true });
  },

  // data = {name, advisor_comment, track}; updates the student's `students` row
  setProfile(student_id, data) {
    return apiPost({ action: "setProfile", student_id, data });
  },

  // a student-added course that is not in the curriculum. Definition only — its grade goes
  // through setGrade into its home semester tab, like every other course.
  // data = {code, name, cr, cat, col, major_gpa}; upserts one row in the `custom` tab.
  setCustom(student_id, course_key, data) {
    return apiPost({ action: "setCustom", student_id, course_key, data });
  },

  // removes a student-added course
  delCustom(student_id, course_key) {
    return apiPost({ action: "setCustom", student_id, course_key, remove: true });
  },

  // ADMIN DASHBOARD — read one whole tab. The backend already exposes this (doGet ?sheet=),
  // strips the password column from `students`, and needs no new action, so the dashboard is
  // built entirely out of reads. Resolves to [] rather than throwing when the tab does not
  // exist yet: the Y5+ semester tabs are created on demand and are legitimately absent.
  async sheet(name) {
    if (!CONFIGURED) throw new Error("Set your Apps Script /exec URL in data.js (GSHEET_API)");
    const r = await fetchDeadline(GSHEET_API + "?sheet=" + encodeURIComponent(name), { cache: "no-store" }, GET_TIMEOUT_MS);
    if (!r.ok) throw new Error("GET " + name + " " + r.status);
    const out = await r.json();
    if (out && out.error) {
      if (/no sheet named/i.test(out.error)) return [];
      throw new Error(out.error);
    }
    return Array.isArray(out) ? out : [];
  }
};
