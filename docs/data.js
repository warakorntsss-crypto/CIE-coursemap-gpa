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

async function apiPost(payload) {
  if (!CONFIGURED) throw new Error("Set your Apps Script /exec URL in data.js (GSHEET_API)");
  const r = await fetch(GSHEET_API, { method: "POST", body: JSON.stringify(payload) });
  if (!r.ok) throw new Error("POST " + r.status);
  const out = await r.json();
  if (out && out.error) throw new Error(out.error);
  return out;
}

window.API = {
  configured: CONFIGURED,

  // Wake the Apps Script (cold-start is the main login delay). Fire-and-forget GET
  // on page load so the script is warm by the time the student submits.
  warmup() {
    if (!CONFIGURED) return;
    try { fetch(GSHEET_API + "?action=ping", { cache: "no-store" }).catch(() => {}); } catch (e) {}
  },

  // -> {ok:true, profile, grades:{key:grade}, extras:[...]} | {ok:false}
  login(student_id, password) {
    return apiPost({ action: "login", student_id, password });
  },

  // -> {ok:true, profile} | {ok:false, error}
  register({ student_id, name, password, advisor }) {
    return apiPost({ action: "register", student_id, name, password, advisor });
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
    const r = await fetch(GSHEET_API + "?sheet=" + encodeURIComponent(name), { cache: "no-store" });
    if (!r.ok) throw new Error("GET " + name + " " + r.status);
    const out = await r.json();
    if (out && out.error) {
      if (/no sheet named/i.test(out.error)) return [];
      throw new Error(out.error);
    }
    return Array.isArray(out) ? out : [];
  }
};
