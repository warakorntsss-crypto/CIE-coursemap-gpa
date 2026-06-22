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

  // extras = {starred, note, elec_code, elec_name}; upserts one row in the `extras` tab
  setExtra(student_id, course_key, data) {
    return apiPost({ action: "setExtra", student_id, course_key, data });
  },

  // data = {name, advisor_comment}; updates the student's `students` row
  setProfile(student_id, data) {
    return apiPost({ action: "setProfile", student_id, data });
  }
};
