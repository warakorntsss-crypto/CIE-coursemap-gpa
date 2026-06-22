// ============================================================================
//  DATA LAYER  —  the ONLY file that knows where the database lives.
//
//  CourseMaps CIE — multi-student course map backed by a Google Sheet.
//
//  >>> SWAP POINT <<<  flip ONE line: MODE.
//    MODE = "local"   -> serve.py + a local .xlsx   (offline dev; not used here)
//    MODE = "gsheet"  -> Google Apps Script web app  (live Google Sheet)
//
//  For "gsheet": deploy APPS_SCRIPT.md (see that file), then paste the /exec URL
//  into GSHEET_API below. index.html never changes — both backends expose the
//  same DB interface: DB.students / DB.progress (+ DB.table(name)),
//  each with getAll / create / update / remove.
// ============================================================================
const MODE = "gsheet";                                       // "local" | "gsheet"
const LOCAL_API  = "/api/rows";                              // serve.py + .xlsx (local mode)
const GSHEET_API = "https://script.google.com/macros/s/AKfycbwJDFwpp8reVdDEDAv4sfVtwBPe-CdZG8zoWBGXUeHvtNc9ioGe_N64TgI1-UXc-NJH/exec";  // <-- your Apps Script /exec URL

// ---------------------------------------------------------------------------
const JSON_H = { "Content-Type": "application/json" };

function withSheet(url, sheet) {
  return url + (url.includes("?") ? "&" : "?") + "sheet=" + encodeURIComponent(sheet);
}

// ----- LOCAL backend (serve.py): SheetDB-shaped REST ----------------------
const localBackend = {
  async getAll(sheet) {
    const r = await fetch(withSheet(LOCAL_API, sheet));
    if (!r.ok) throw new Error("GET " + r.status);
    return r.json();
  },
  async create(sheet, row) {
    const r = await fetch(withSheet(LOCAL_API, sheet), {
      method: "POST", headers: JSON_H, body: JSON.stringify({ data: row })
    });
    if (!r.ok) throw new Error("POST " + r.status);
    return r.json();
  },
  async update(sheet, id, fields) {
    const r = await fetch(withSheet(`${LOCAL_API}/id/${encodeURIComponent(id)}`, sheet), {
      method: "PATCH", headers: JSON_H, body: JSON.stringify({ data: fields })
    });
    if (!r.ok) throw new Error("PATCH " + r.status);
    return r.json();
  },
  async remove(sheet, id) {
    const r = await fetch(withSheet(`${LOCAL_API}/id/${encodeURIComponent(id)}`, sheet), {
      method: "DELETE"
    });
    if (!r.ok) throw new Error("DELETE " + r.status);
    return r.json();
  }
};

// ----- GSHEET backend (Apps Script web app) -------------------------------
// Apps Script only has doGet/doPost (no PATCH/DELETE) and cannot answer a CORS
// preflight. So: reads = GET ?sheet=, writes = POST with an {action} body sent as
// a PLAIN string (no JSON Content-Type) so it stays a preflight-free simple request.
function gsheetReady() {
  if (GSHEET_API.includes("PASTE")) {
    throw new Error("Set your Apps Script /exec URL in data.js (GSHEET_API)");
  }
}
async function gsheetPost(payload) {
  gsheetReady();
  const r = await fetch(GSHEET_API, { method: "POST", body: JSON.stringify(payload) });
  if (!r.ok) throw new Error("POST " + r.status);
  const out = await r.json();
  if (out && out.error) throw new Error(out.error);
  return out;
}
const gsheetBackend = {
  async getAll(sheet) {
    gsheetReady();
    const r = await fetch(withSheet(GSHEET_API, sheet));
    if (!r.ok) throw new Error("GET " + r.status);
    const out = await r.json();
    if (out && out.error) throw new Error(out.error);
    return out;
  },
  create(sheet, row)        { return gsheetPost({ action: "create", sheet, data: row }); },
  update(sheet, id, fields) { return gsheetPost({ action: "update", sheet, id, data: fields }); },
  remove(sheet, id)         { return gsheetPost({ action: "delete", sheet, id }); }
};

// ---------------------------------------------------------------------------
const backend = MODE === "gsheet" ? gsheetBackend : localBackend;

// A table = the CRUD client bound to one sheet (students | progress).
function makeTable(sheet) {
  return {
    getAll: ()           => backend.getAll(sheet),
    create: (row)        => backend.create(sheet, row),
    update: (id, fields) => backend.update(sheet, id, fields),
    remove: (id)         => backend.remove(sheet, id),
  };
}

window.DB = {
  table: makeTable,
  mode: MODE,
  configured: !(MODE === "gsheet" && GSHEET_API.includes("PASTE")),
  students: makeTable("students"),
  progress: makeTable("progress"),
};
