#!/usr/bin/env python3
"""
Build an interactive single-file HTML study course map (index.html) for the
B.Eng. Civil Engineering (International Program) curriculum (CIE 2568).

Features:
  - hover (desktop) or tap (mobile) a course -> it + all transitive
    prerequisites AND all courses it unlocks glow, with connecting lines.
  - star a course (persists in browser localStorage).
  - filter: by category (click legend chips) and "starred only".
  - zoom: fit-to-screen (one click = whole picture), +, -, 1:1.
  - click a course -> side panel: description, prereqs, unlocks, notes (autosaved).
  - boxes auto-ordered vertically (barycenter) to cut crossings; wires routed
    orthogonally through gutters/gap-bands so they never cross a box; adjacent
    edges use clean single-bend elbows (straight, not wavy).
  - semester header row stays pinned while scrolling; header height measured so
    it never overlaps the map.
  - responsive: works and stays fully usable on phones.

Aesthetic: engineering blueprint (dark drafting grid, cyan glow, amber stars).
Data: shared curriculum_data.py (NotebookLM `cie_curriculum`).

Re-run after editing curriculum_data.py:
    python build-interactive.py
"""

import os
import json

from curriculum_data import CAT, CAT_LABEL, SEMS, COURSES, PREREQS, DESC

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

nodes = [
    {"key": k, "col": v[0], "short": v[1], "name": v[2], "cr": v[3],
     "cat": v[4], "desc": DESC.get(k, "")}
    for k, v in COURSES.items()
]
edges = [{"s": s, "t": t, "co": co} for (s, t, co) in PREREQS]
cats = {k: {"fill": f, "stroke": s, "label": CAT_LABEL[k]}
        for k, (f, s) in CAT.items()}
sems = [{"label": l, "cr": c} for (l, c) in SEMS]

DATA = json.dumps(
    {"nodes": nodes, "edges": edges, "cats": cats, "sems": sems},
    ensure_ascii=False,
)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5"/>
<title>CIE Civil Engineering — Interactive Course Map</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0a1626; --grid:rgba(94,164,214,.10); --grid2:rgba(94,164,214,.05);
  --ink:#cfe6f5; --ink-dim:#7f9bb3; --line:rgba(120,180,220,.20);
  --cyan:#37c5ff; --amber:#ffb648; --panel-line:rgba(120,180,220,.25); --bar:60px;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{
  background:var(--bg); color:var(--ink); font-family:"IBM Plex Sans",sans-serif; overflow:hidden;
  background-image:
    linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px),
    linear-gradient(var(--grid2) 1px,transparent 1px),linear-gradient(90deg,var(--grid2) 1px,transparent 1px);
  background-size:120px 120px,120px 120px,24px 24px,24px 24px;
  -webkit-text-size-adjust:100%;
}
/* ---- top bar ---- */
header{
  position:fixed; top:0; left:0; right:0; z-index:30;
  display:flex; align-items:center; gap:14px 18px; flex-wrap:wrap;
  padding:10px 18px; background:linear-gradient(180deg,rgba(8,18,32,.98),rgba(8,18,32,.9));
  border-bottom:1px solid var(--panel-line); backdrop-filter:blur(4px);
}
.brand{display:flex; flex-direction:column; line-height:1.05}
.brand b{font-family:"Saira Condensed",sans-serif; font-weight:700; font-size:20px; letter-spacing:.5px; text-transform:uppercase; color:#eaf6ff}
.brand small{font-family:"IBM Plex Mono",monospace; font-size:10px; color:var(--ink-dim); letter-spacing:1px}
.legend{display:flex; gap:8px; flex-wrap:wrap; align-items:center}
.lg{display:flex; align-items:center; gap:6px; font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-dim);
  cursor:pointer; user-select:none; border:1px solid transparent; border-radius:20px; padding:4px 9px; transition:.15s}
.lg:hover{border-color:var(--panel-line)}
.lg.off{opacity:.34; text-decoration:line-through}
.lg i{width:11px; height:11px; border-radius:3px; display:inline-block; border:1px solid rgba(255,255,255,.25)}
.tools{display:flex; align-items:center; gap:9px; margin-left:auto; flex-wrap:wrap}
.tools input[type=search]{background:#08121f; border:1px solid var(--panel-line); color:var(--ink); font-family:"IBM Plex Mono",monospace; font-size:12px; padding:8px 10px; border-radius:6px; width:150px}
.tools input::placeholder{color:#5b7a93}
.btn{font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.5px; background:#08121f; color:var(--ink-dim); border:1px solid var(--panel-line); padding:8px 11px; border-radius:6px; cursor:pointer; user-select:none; white-space:nowrap}
.btn:hover{color:var(--ink); border-color:var(--cyan)}
.btn.on{color:#08121f; background:var(--amber); border-color:var(--amber); font-weight:600}
.counts{font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-dim); white-space:nowrap}
.counts b{color:var(--amber)}
/* ---- scroll + map ---- */
#scroll{position:absolute; left:0; right:0; bottom:0; top:var(--bar); overflow:auto; -webkit-overflow-scrolling:touch}
#cols{position:sticky; top:0; height:56px; z-index:12; pointer-events:none}
#cols .colhdr{
  position:absolute; top:8px; height:42px; display:flex; flex-direction:column; align-items:center; justify-content:center;
  border:1px solid var(--panel-line); border-radius:7px;
  background:linear-gradient(180deg,rgba(11,28,48,.98),rgba(9,22,40,.98)); box-shadow:0 8px 18px rgba(0,0,0,.5);
  font-family:"Saira Condensed",sans-serif;
}
#cols .colhdr b{font-size:16px; font-weight:700; letter-spacing:1px; color:#eaf6ff; text-transform:uppercase}
#cols .colhdr span{font-family:"IBM Plex Mono",monospace; font-size:10px; color:var(--cyan)}
#map{position:relative}
#wires{position:absolute; left:0; top:0; pointer-events:none; overflow:visible}
.node{
  position:absolute; border-radius:8px; cursor:pointer;
  background:linear-gradient(180deg,rgba(14,34,54,.94),rgba(10,24,40,.94));
  border:1px solid var(--line); border-left-width:4px; padding:8px 10px 8px 12px; overflow:hidden;
  transition:box-shadow .18s,border-color .18s,opacity .18s,transform .12s;
}
.node:hover{transform:translateY(-1px)}
.node .code{font-family:"IBM Plex Mono",monospace; font-weight:600; font-size:12px; color:#eaf6ff; letter-spacing:.5px}
.node .ecode{width:118px; font-family:"IBM Plex Mono",monospace; font-weight:600; font-size:12px; color:#eaf6ff; letter-spacing:.5px;
  background:rgba(120,180,220,.10); border:1px dashed var(--panel-line); border-radius:4px; padding:1px 5px}
.node .ecode:hover{border-color:var(--cyan)}
.node .ecode:focus{outline:none; border-style:solid; border-color:var(--cyan); background:#08131f}
.node .nm{font-size:11px; line-height:1.2; color:var(--ink-dim); margin-top:3px; height:26px; overflow:hidden}
.node.elec .nm{height:13px; font-size:9.5px; opacity:.65; margin-top:2px}
.node .ename{display:block; width:calc(100% - 4px); margin-top:3px; font-family:"IBM Plex Sans",sans-serif; font-size:10px; color:var(--ink);
  background:#08131f; border:1px dashed var(--panel-line); border-radius:4px; padding:3px 5px}
.node .ename::placeholder{color:#5b7a93; font-style:italic}
.node .ename:hover{border-color:var(--cyan)}
.node .ename:focus{outline:none; border-style:solid; border-color:var(--cyan)}
.node .cr{position:absolute; left:16px; bottom:11px; font-family:"IBM Plex Mono",monospace; font-size:10px; color:var(--ink-dim)}
.node .grade{position:absolute; right:7px; bottom:7px; width:60px; height:24px; padding:0 4px; cursor:pointer;
  background:#08131f; color:var(--ink); border:1px solid var(--panel-line); border-radius:5px;
  font-family:"IBM Plex Mono",monospace; font-size:12px; font-weight:600; text-align:center; text-align-last:center; appearance:none; -webkit-appearance:none}
.node .grade:hover{border-color:var(--cyan)}
.node .grade:focus{outline:none; border-color:var(--cyan); box-shadow:0 0 0 1px var(--cyan)}
.node.graded .grade{color:#bdf0c4; border-color:#82B366}
.node.failed .grade{color:#ff9a9a; border-color:#c96b6b}
.node.withdrawn .grade{color:#9fb4c6; border-color:#5a7a93}
.node.graded{box-shadow:inset 0 0 0 1px rgba(130,190,120,.30)}
.node.failed{box-shadow:inset 0 0 0 1px rgba(220,110,110,.35)}
.node .star{position:absolute; right:4px; top:3px; font-size:15px; line-height:1; color:#3a5470; cursor:pointer; transition:color .15s,transform .15s; padding:5px}
.node .star:hover{transform:scale(1.2)}
.node.starred .star{color:var(--amber); text-shadow:0 0 8px rgba(255,182,72,.7)}
.node .dot{position:absolute; left:6px; bottom:6px; width:6px; height:6px; border-radius:50%; background:var(--cyan); opacity:0; box-shadow:0 0 6px var(--cyan)}
.node.hasnote .dot{opacity:.9}
#map.dimmed .node{opacity:.16}
.node.glow{opacity:1 !important; border-color:var(--cyan); box-shadow:0 0 0 1px var(--cyan),0 0 22px rgba(55,197,255,.55)}
.node.glow.up{border-color:#8fe0ff}
.node.glow.down{border-color:#ffd27a; box-shadow:0 0 0 1px #ffd27a,0 0 22px rgba(255,182,72,.45)}
.node.glow.root{box-shadow:0 0 0 2px var(--cyan),0 0 32px rgba(55,197,255,.9)}
.node.selected{border-color:var(--amber); box-shadow:0 0 0 1px var(--amber),0 0 16px rgba(255,182,72,.5)}
.node.hidden{display:none}
.node.faded{opacity:.08 !important}
/* code-only overview (very low zoom): hide everything but the course code, centered + enlarged */
#map.codeonly .node{display:flex; align-items:center; justify-content:center; padding:4px}
#map.codeonly .node>.nm,#map.codeonly .node>.cr,#map.codeonly .node>.grade,
#map.codeonly .node>.star,#map.codeonly .node>.dot,#map.codeonly .node>.ename{display:none}
#map.codeonly .node>.code{font-size:10.5px; font-weight:700}
#map.codeonly .node>.ecode{font-size:10.5px; width:auto; max-width:100%; text-align:center; border-color:transparent; background:transparent}
/* FIT view: abbreviate the year-box credit ("21 Credit" -> "21 CR") */
#cols .colhdr .u-short{display:none}
#cols.codeonly .colhdr .u-long{display:none}
#cols.codeonly .colhdr .u-short{display:inline}
/* wires */
.wire{fill:none; stroke:rgba(130,190,230,.34); stroke-width:1.4}
.wire.co{stroke-dasharray:5 5}
.wire.glow{stroke:var(--cyan); stroke-width:2.1; filter:url(#glow); opacity:1}
.wire.glow.down{stroke:var(--amber)}
#map.dimmed .wire:not(.glow){opacity:.05}
/* ---- zoom controls ---- */
#zoom{position:fixed; right:14px; bottom:14px; z-index:25; display:flex; flex-direction:column; gap:6px; align-items:stretch}
#zoom button{width:40px; height:40px; font-size:16px; font-family:"IBM Plex Mono",monospace; background:rgba(8,18,32,.92);
  color:var(--ink); border:1px solid var(--panel-line); border-radius:8px; cursor:pointer; display:flex; align-items:center; justify-content:center}
#zoom button:hover{border-color:var(--cyan); color:#eaf6ff}
#zoom .fit{font-size:11px; letter-spacing:.5px}
#zlevel{font-family:"IBM Plex Mono",monospace; font-size:10px; color:var(--ink-dim); text-align:center}
/* ---- side panel ---- */
#panel{position:fixed; top:0; right:0; height:100%; width:370px; max-width:92vw; z-index:40;
  background:linear-gradient(180deg,#0e2236,#0a1828); border-left:1px solid var(--panel-line);
  box-shadow:-18px 0 50px rgba(0,0,0,.5); transform:translateX(102%);
  transition:transform .28s cubic-bezier(.4,0,.2,1); display:flex; flex-direction:column}
#panel.open{transform:translateX(0)}
.ph{padding:18px 20px 14px; border-bottom:1px solid var(--panel-line); position:relative}
.ph .tag{font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:1.5px; text-transform:uppercase; color:var(--cyan)}
.ph h2{margin:6px 0 2px; font-family:"IBM Plex Mono",monospace; font-size:20px; color:#eaf6ff}
.ph p{margin:2px 0 0; font-size:13px; color:var(--ink-dim)}
.ph .x{position:absolute; top:12px; right:14px; cursor:pointer; color:var(--ink-dim); font-size:22px; line-height:1; padding:4px}
.ph .x:hover{color:var(--ink)}
.pbody{padding:16px 20px; overflow:auto; flex:1; -webkit-overflow-scrolling:touch}
.meta{display:flex; gap:8px; flex-wrap:wrap; margin-bottom:6px}
.chip{font-family:"IBM Plex Mono",monospace; font-size:11px; padding:4px 9px; border-radius:20px; border:1px solid var(--panel-line); color:var(--ink)}
.sect{font-family:"Saira Condensed",sans-serif; font-weight:600; text-transform:uppercase; letter-spacing:1px; font-size:13px; color:var(--cyan); margin:16px 0 8px}
.desc{font-size:13px; line-height:1.55; color:var(--ink); background:rgba(55,197,255,.06); border:1px solid var(--panel-line); border-left:3px solid var(--cyan); border-radius:6px; padding:10px 12px}
.prereq-list{display:flex; flex-direction:column; gap:6px}
.prereq-list a{font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--ink); text-decoration:none; border:1px solid var(--panel-line); border-radius:6px; padding:8px 10px; cursor:pointer; transition:.15s}
.prereq-list a:hover{border-color:var(--cyan); color:#eaf6ff; background:rgba(55,197,255,.07)}
.prereq-list a span{color:var(--ink-dim)}
.none{font-size:12px; color:var(--ink-dim); font-style:italic}
.starbtn{display:inline-flex; align-items:center; gap:7px; cursor:pointer; margin-bottom:6px; font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--ink-dim); border:1px solid var(--panel-line); border-radius:6px; padding:9px 12px; user-select:none}
.starbtn:hover{border-color:var(--amber); color:var(--ink)}
.starbtn.on{color:var(--amber); border-color:var(--amber)}
.starbtn b{font-size:15px}
textarea{width:100%; min-height:140px; resize:vertical; margin-top:4px; background:#08131f; border:1px solid var(--panel-line); border-radius:8px; color:var(--ink); font-family:"IBM Plex Sans",sans-serif; font-size:13px; line-height:1.5; padding:11px 12px}
textarea:focus{outline:none; border-color:var(--cyan); box-shadow:0 0 0 1px var(--cyan)}
.saved{font-family:"IBM Plex Mono",monospace; font-size:10px; color:var(--ink-dim); margin-top:6px; height:12px}
.hint{position:fixed; bottom:14px; left:18px; z-index:20; font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-dim); background:rgba(8,18,32,.7); padding:5px 9px; border-radius:6px; max-width:50vw}
.hint b{color:var(--cyan)}
/* ---- summary / progress panel ---- */
#summary{position:fixed; left:14px; bottom:14px; z-index:35; width:300px; max-width:80vw;
  background:linear-gradient(180deg,#0e2236,#0a1828); border:1px solid var(--panel-line);
  border-radius:10px; box-shadow:0 18px 50px rgba(0,0,0,.55); padding:12px 14px 13px;
  transform:translateY(140%); opacity:0; transition:transform .26s cubic-bezier(.4,0,.2,1),opacity .26s; pointer-events:none}
#summary.open{transform:translateY(0); opacity:1; pointer-events:auto}
#summary .sh{display:flex; align-items:center; justify-content:space-between; margin-bottom:8px}
#summary .sh b{font-family:"Saira Condensed",sans-serif; font-weight:700; text-transform:uppercase; letter-spacing:1px; font-size:15px; color:#eaf6ff}
#summary .sx{cursor:pointer; color:var(--ink-dim); font-size:16px; line-height:1; padding:2px 4px}
#summary .sx:hover{color:var(--ink)}
.sbig{font-family:"IBM Plex Mono",monospace; font-size:24px; font-weight:600; color:var(--amber); margin:2px 0 10px}
.sbig small{font-size:11px; color:var(--ink-dim); font-weight:400}
.srow{display:flex; align-items:baseline; gap:8px; padding:4px 0; border-top:1px solid rgba(120,180,220,.12); font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--ink-dim)}
.srow span{flex:1; white-space:nowrap}
.srow b{color:#eaf6ff; font-size:14px; min-width:42px; text-align:right}
.srow i{font-style:normal; color:var(--ink-dim); font-size:10px; min-width:42px; text-align:right}
.srow.total{margin-top:3px; border-top:1px solid var(--panel-line)}
.srow.total span{color:var(--cyan); font-weight:600}
.srow.total b{color:var(--amber)}
#summary #sumBody{max-height:54vh; overflow:auto}
/* ---- formal PDF document view ---- */
#docview{position:fixed; inset:0; z-index:60; background:#3a4763; overflow:auto; display:none; padding:30px 0}
#docview.open{display:block}
.doctools{position:fixed; top:14px; right:20px; z-index:61; display:flex; gap:8px}
.doctools button{font-family:"IBM Plex Mono",monospace; font-size:12px; padding:9px 13px; border-radius:7px; cursor:pointer; border:1px solid #2a3850; background:#0e2236; color:#eaf6ff}
.doctools button:hover{border-color:var(--cyan)}
.docpaper{background:#fff; color:#16202b; width:820px; max-width:96vw; margin:0 auto; padding:46px 52px 40px;
  box-shadow:0 12px 48px rgba(0,0,0,.5); font-family:"IBM Plex Sans",Arial,sans-serif; font-size:13px; line-height:1.45}
.doc-head{text-align:center; border-bottom:2px solid #16202b; padding-bottom:12px; margin-bottom:14px}
.doc-title{font-family:"Saira Condensed",sans-serif; font-weight:700; font-size:22px; letter-spacing:.3px; text-transform:uppercase}
.doc-sub{font-size:11px; color:#5a6675; margin-top:4px; letter-spacing:.4px}
.doc-meta{display:flex; flex-wrap:wrap; gap:6px 26px; font-size:12px; margin:0 0 18px}
.doc-meta label{color:#5a6675; margin-right:6px}
.doc-meta input{border:none; border-bottom:1px solid #9aa6b4; font:inherit; font-size:12px; padding:2px 4px; min-width:160px; background:transparent; color:#16202b}
.doc-meta input:focus{outline:none; border-bottom-color:var(--cyan)}
.docsem{width:100%; border-collapse:collapse; margin:0 0 12px; break-inside:avoid}
.docsem caption{caption-side:top; text-align:left; font-weight:700; font-size:13px; background:#eef2f7; border:1px solid #c7d0db; border-bottom:none; padding:6px 9px; letter-spacing:.3px}
.docsem th,.docsem td{border:1px solid #c7d0db; padding:5px 9px; font-size:12px}
.docsem th{background:#f6f8fb; text-align:left; font-weight:600; color:#384655}
.docsem td.c,.docsem th.c{text-align:center; width:62px}
.docsem td.r{text-align:right; font-weight:600}
.docsem tfoot td{background:#f6f8fb; font-weight:700}
.docsummary{border:2px solid #16202b; border-radius:6px; padding:12px 16px; margin:18px 0 14px; break-inside:avoid}
.docsummary h3{margin:0 0 8px; font-family:"Saira Condensed",sans-serif; text-transform:uppercase; letter-spacing:.6px; font-size:15px}
.srow2{display:flex; justify-content:space-between; align-items:baseline; padding:4px 0; border-top:1px solid #e0e6ee; font-size:13px}
.srow2 b{font-size:15px}
.srow2.big b{font-size:17px; color:#1f3a8a}
.adv-comment{margin:14px 0 6px; break-inside:avoid}
.adv-comment .lbl{font-weight:700; font-size:12px; margin-bottom:5px}
.adv-comment textarea{width:100%; min-height:96px; border:1px solid #9aa6b4; border-radius:5px; padding:8px 10px; font:inherit; font-size:12px; resize:vertical; color:#16202b; background:#fff; box-shadow:none}
.adv-comment textarea:focus{outline:none; border-color:var(--cyan)}
.sigrow{display:flex; gap:40px; margin-top:30px; break-inside:avoid}
.sigbox{flex:1; text-align:center; font-size:12px}
.sigline{border-bottom:1px solid #16202b; height:46px; margin-bottom:6px}
.sigbox b{display:block; font-size:12.5px}
.sigbox span{color:#5a6675; font-size:11px}
.doctools .docmode{background:#16202b}
.doctools .docmode.on{background:var(--cyan); color:#06121d; border-color:var(--cyan); font-weight:600}
/* one-page compact layout */
.docsummary.compact{display:flex; justify-content:center; padding:8px 12px; margin:12px 0 10px; font-size:13px}
.docsummary.compact b{color:#1f3a8a}
.compactgrid{display:flex; gap:10px; align-items:flex-start; margin:6px 0 8px}
.cyear{flex:1; border:1px solid #c7d0db; border-radius:5px; overflow:hidden; font-size:10.5px}
.cytitle{background:#16202b; color:#fff; font-family:"Saira Condensed",sans-serif; font-weight:700; text-transform:uppercase; letter-spacing:.5px; font-size:13px; text-align:center; padding:4px}
.cyhdr{background:#eef2f7; color:#384655; font-weight:700; font-size:9.5px; letter-spacing:.3px; padding:2px 6px; border-top:1px solid #d4dce6}
.cyrow{display:flex; flex-wrap:nowrap; justify-content:space-between; gap:6px; padding:2px 6px; border-top:1px solid #eef2f7}
.cyrow span{font-family:"IBM Plex Mono",monospace; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; min-width:0}
.cyrow b{flex:0 0 auto; font-weight:700; min-width:18px; text-align:right}
.cygpa{padding:4px 6px; border-top:2px solid #16202b; background:#f6f8fb; font-weight:700; text-align:right; font-size:11px}
.cygpa b{color:#1f3a8a; margin-left:4px}
.compactpaper .sigrow{margin-top:18px}
.doc-warn{background:#fff4d6; border:1px solid #e0b34a; border-left:4px solid #e0a020; color:#5a4205;
  border-radius:6px; padding:9px 12px; margin:0 0 14px; font-size:12px; line-height:1.45}
.doc-warn b{color:#7a5800}
@media print{
  .doc-warn{display:none !important}
  @page{ size:A4; margin:13mm }
  html,body{height:auto; overflow:visible; background:#fff}
  header,#scroll,#zoom,#panel,#summary,.hint,.doctools{display:none !important}
  #docview{position:static; inset:auto; background:#fff; padding:0; overflow:visible; display:block !important}
  .docpaper{box-shadow:none; width:auto; max-width:none; margin:0; padding:0}
  .doc-meta input{border-bottom:1px solid #16202b}
  .compactpaper{font-size:10px}
  .compactgrid,.cyear,.sigrow,.docsummary,.compactpaper .doc-head{break-inside:avoid; page-break-inside:avoid}
}
::-webkit-scrollbar{width:11px;height:11px}
::-webkit-scrollbar-thumb{background:#1b3550;border-radius:6px}
::-webkit-scrollbar-track{background:transparent}
/* ---- mobile ---- */
/* phone, either orientation: tighter year header + header that scrolls away on scroll-down */
@media (max-width:720px),(max-height:520px){
  #cols{height:48px}
  #cols .colhdr{top:2px; height:42px; flex-direction:row; gap:7px}  /* slightly thicker; year + credit on one row */
  #cols .colhdr b{font-size:10.5px}     /* white year label, 25% smaller than before (14px) */
  #cols .colhdr span{font-size:9px}     /* blue credit now sits to the right of the year */
  header{position:static}   /* not fixed: top bar scrolls away with the content */
  #scroll{top:0}            /* header now lives at the top of the scroll flow; year box stays sticky */
}
@media (max-width:720px){
  header{gap:8px 12px; padding:8px 12px}
  .brand b{font-size:16px} .brand small{font-size:9px}
  .legend{order:3; width:100%; flex-wrap:nowrap; overflow-x:auto; padding-bottom:2px}
  .lg{flex:0 0 auto}
  .tools{margin-left:0; width:100%; justify-content:space-between}
  .tools input[type=search]{flex:1; min-width:0; width:auto}
  #panel{width:100%; max-width:100%}
  .hint{display:none}
  #zoom button{width:44px; height:44px}
  .node .star{padding:4px; font-size:14px; right:2px; top:2px}
  /* compact 1-page recap: fixed readable width on phone, modal scrolls sideways */
  .compactpaper{width:720px; max-width:none}
}
</style>
</head>
<body>
<div id="scroll">
  <header>
    <div class="brand">
      <b>Civil Engineering &middot; Course Map</b>
      <small>B.ENG INTERNATIONAL &nbsp;//&nbsp; CIE 2568 &nbsp;//&nbsp; 149 Credit</small>
    </div>
    <div class="legend" id="legend"></div>
    <div class="tools">
      <input type="search" id="search" placeholder="search…" autocomplete="off"/>
      <button class="btn" id="starsBtn">★ starred</button>
      <button class="btn" id="sumBtn">▣ progress</button>
      <button class="btn" id="pdfBtn">⭳ save pdf</button>
      <span class="counts" id="counts"></span>
    </div>
  </header>
  <div id="cols"></div>
  <div id="map">
    <svg id="wires">
      <defs>
        <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="3" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <marker id="arw" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse" markerUnits="userSpaceOnUse">
          <path d="M0,0 L10,5 L0,10 L2.5,5 z" fill="rgba(140,195,235,.55)"/>
        </marker>
        <marker id="arwC" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse" markerUnits="userSpaceOnUse">
          <path d="M0,0 L10,5 L0,10 L2.5,5 z" fill="#37c5ff"/>
        </marker>
        <marker id="arwD" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse" markerUnits="userSpaceOnUse">
          <path d="M0,0 L10,5 L0,10 L2.5,5 z" fill="#ffb648"/>
        </marker>
      </defs>
    </svg>
  </div>
</div>

<div id="zoom">
  <button class="fit" id="zfit" title="Fit whole map">FIT</button>
  <button id="zin" title="Zoom in">+</button>
  <button id="zout" title="Zoom out">&minus;</button>
  <button id="zone" title="Reset 1:1">1:1</button>
  <div id="zlevel">100%</div>
</div>

<div class="hint">Hover/tap a course → it, its <b>prerequisites</b> &amp; what it <b>unlocks</b> glow.</div>

<aside id="summary">
  <div class="sh"><b>Study Progress</b><span class="sx" id="sumClose">✕</span></div>
  <div id="sumBody"></div>
</aside>

<div id="docview">
  <div class="doctools">
    <button id="docFull" class="docmode on">Detailed</button>
    <button id="docCompact" class="docmode">1-Page</button>
    <button id="docPrint">🖨 Print / Save PDF</button>
    <button id="docClose">✕ Close</button>
  </div>
  <div class="docpaper" id="docPaper"></div>
</div>

<aside id="panel">
  <div class="ph">
    <span class="x" id="pclose">✕</span>
    <div class="tag" id="ptag"></div>
    <h2 id="pcode"></h2>
    <p id="pname"></p>
  </div>
  <div class="pbody">
    <div class="meta" id="pmeta"></div>
    <div class="starbtn" id="pstar"><b>☆</b><span id="pstartxt">Mark as interested</span></div>
    <div class="sect">Description</div>
    <div class="desc" id="pdesc"></div>
    <div class="sect">Prerequisites</div>
    <div class="prereq-list" id="pprereq"></div>
    <div class="sect">Unlocks</div>
    <div class="prereq-list" id="punlocks"></div>
    <div class="sect">My notes</div>
    <textarea id="pnotes" placeholder="Write notes about this subject…"></textarea>
    <div class="saved" id="psaved"></div>
  </div>
</aside>

<script>
const DATA = __DATA__;
const LS_STAR="cie_stars_v1", LS_NOTE="cie_notes_v1", LS_GRADE="cie_grades_v1";
const stars = JSON.parse(localStorage.getItem(LS_STAR)||"{}");
const notes = JSON.parse(localStorage.getItem(LS_NOTE)||"{}");
const grades = JSON.parse(localStorage.getItem(LS_GRADE)||"{}");
const saveStars=()=>localStorage.setItem(LS_STAR,JSON.stringify(stars));
const saveNotes=()=>localStorage.setItem(LS_NOTE,JSON.stringify(notes));
const saveGrades=()=>localStorage.setItem(LS_GRADE,JSON.stringify(grades));
// elective overrides: student-registered code + actual course name {key:{code,name}}
const LS_ELEC="cie_elec_v1";
const elec = JSON.parse(localStorage.getItem(LS_ELEC)||"{}");
const saveElec=()=>localStorage.setItem(LS_ELEC,JSON.stringify(elec));
const isElec=n=>n.cat==='elec';
const elecCode=n=>(elec[n.key]&&elec[n.key].code)||n.short;          // displayed/registered code
const elecName=n=>(elec[n.key]&&elec[n.key].name)||'';               // student-entered actual name

// ---- geometry ----
const COL_W=232, BOX_W=172, BOX_H=104, GAP=44, PAD=28, BODY_Y=14;
const ROW_H=BOX_H+GAP, GUT=COL_W-BOX_W;
const map=document.getElementById('map'), wires=document.getElementById('wires'), colsBar=document.getElementById('cols');
const scroll=document.getElementById('scroll'), header=document.querySelector('header');
const byKey={}; DATA.nodes.forEach(n=>byKey[n.key]=n);
const NCOL=DATA.sems.length;
const HOVER=window.matchMedia('(hover:hover)').matches;   // false on touch screens

// adjacency
const prereqsOf={}, unlocksOf={};
DATA.edges.forEach(e=>{ (prereqsOf[e.t]=prereqsOf[e.t]||[]).push(e.s); (unlocksOf[e.s]=unlocksOf[e.s]||[]).push(e.t); });
function closure(start, adj){
  const seen=new Set(), stack=[...(adj[start]||[])];
  while(stack.length){const x=stack.pop(); if(seen.has(x))continue; seen.add(x); (adj[x]||[]).forEach(p=>stack.push(p));}
  return seen;
}
const ancCache={}, descCache={};
const ancestors=k=>ancCache[k]||(ancCache[k]=closure(k,prereqsOf));
const descendants=k=>descCache[k]||(descCache[k]=closure(k,unlocksOf));

// ---- barycenter ordering (vertical moves to cut crossings) ----
const order=[]; for(let c=0;c<NCOL;c++) order[c]=[];
DATA.nodes.forEach(n=>order[n.col].push(n.key));
function posIndex(){const m={}; for(let c=0;c<NCOL;c++) order[c].forEach((k,i)=>m[k]=i); return m;}
function sweep(dir){
  const idx=posIndex(); const range=dir>0?[...Array(NCOL).keys()]:[...Array(NCOL).keys()].reverse();
  for(const c of range){
    const adjCol=c-dir; if(adjCol<0||adjCol>=NCOL) continue;
    const bary={};
    order[c].forEach((k,i)=>{
      const nbrs=[...(prereqsOf[k]||[]),...(unlocksOf[k]||[])].filter(x=>byKey[x]&&byKey[x].col===adjCol);
      bary[k]= nbrs.length? nbrs.reduce((s,x)=>s+idx[x],0)/nbrs.length : i;
    });
    order[c].sort((a,b)=>bary[a]-bary[b]);
  }
}
for(let s=0;s<6;s++){ sweep(1); sweep(-1); }

// ---- positions ----
const pos={}, rowOf={};
for(let c=0;c<NCOL;c++) order[c].forEach((k,i)=>{ rowOf[k]=i; pos[k]={x:PAD+c*COL_W, y:BODY_Y+i*ROW_H}; });
let maxRows=0; for(let c=0;c<NCOL;c++) maxRows=Math.max(maxRows,order[c].length);
const mapW=PAD*2+(NCOL-1)*COL_W+BOX_W, mapH=BODY_Y+maxRows*ROW_H+10;
map.style.width=mapW+"px"; map.style.height=mapH+"px"; colsBar.style.width=mapW+"px";
wires.setAttribute("width",mapW); wires.setAttribute("height",mapH); wires.setAttribute("viewBox","0 0 "+mapW+" "+mapH);

// ---- sticky column headers ----
DATA.sems.forEach((s,i)=>{
  const h=document.createElement('div'); h.className='colhdr';
  h.style.left=(PAD+i*COL_W)+"px"; h.style.width=BOX_W+"px";
  h.innerHTML="<b>"+s.label+"</b><span>"+s.cr+'<span class="u-long"> Credit</span><span class="u-short"> CR</span></span>'; colsBar.appendChild(h);
});

// ---- nodes ----
const GRADES=['A','B+','B','C+','C','D+','D','F','W'];
const GRADE_OPTS=GRADES.map(g=>'<option value="'+g+'">'+g+'</option>').join('');
const nodeEl={};
DATA.nodes.forEach(n=>{
  const c=DATA.cats[n.cat];
  const el=document.createElement('div'); el.className='node'; el.dataset.key=n.key;
  el.style.left=pos[n.key].x+"px"; el.style.top=pos[n.key].y+"px";
  el.style.width=BOX_W+"px"; el.style.height=BOX_H+"px"; el.style.borderLeftColor=c.stroke;
  const codeHtml = isElec(n)
    ? '<input class="ecode" title="edit registered course code" value="'+esc(elecCode(n))+'">'
    : '<div class="code">'+n.short+'</div>';
  const elecNameHtml = isElec(n)
    ? '<input class="ename" title="actual course name" placeholder="actual course name…" value="'+esc(elecName(n))+'">'
    : '';
  el.innerHTML=codeHtml+'<div class="nm">'+n.name+'</div>'+elecNameHtml+
    '<div class="cr">'+n.cr+' Credit</div>'+
    '<select class="grade" title="grade received"><option value="">-</option>'+GRADE_OPTS+'</select>'+
    '<div class="star" title="star">★</div><div class="dot"></div>';
  if(isElec(n)) el.classList.add('elec');
  if(stars[n.key]) el.classList.add('starred');
  if(notes[n.key] && notes[n.key].trim()) el.classList.add('hasnote');
  map.appendChild(el); nodeEl[n.key]=el;
  el.addEventListener('mouseenter',()=>{ if(HOVER && !pinned) highlight(n.key); });
  el.addEventListener('mouseleave',()=>{ if(HOVER && !pinned) clearHi(); });
  el.addEventListener('click',e=>{ const t=e.target;
    if(t.classList.contains('star')||t.classList.contains('grade')||t.classList.contains('ecode')||t.classList.contains('ename')) return;
    if(HOVER) selectNode(n.key); else tapNode(n.key);   // desktop: click=info; touch: two-step tap
  });
  el.querySelector('.star').addEventListener('click',e=>{e.stopPropagation(); toggleStar(n.key);});
  const sel=el.querySelector('.grade'); sel.value=grades[n.key]||''; applyGradeClass(n.key,sel.value);
  sel.addEventListener('mousedown',e=>e.stopPropagation());
  sel.addEventListener('click',e=>e.stopPropagation());
  sel.addEventListener('change',e=>{ e.stopPropagation(); setGrade(n.key,sel.value); });
  if(isElec(n)){
    const setElec=(f,v)=>{ elec[n.key]=elec[n.key]||{}; if(v) elec[n.key][f]=v; else delete elec[n.key][f]; if(!Object.keys(elec[n.key]).length) delete elec[n.key]; saveElec(); };
    el.querySelectorAll('.ecode,.ename').forEach(inp=>{ inp.addEventListener('mousedown',e=>e.stopPropagation()); inp.addEventListener('click',e=>e.stopPropagation()); });
    el.querySelector('.ecode').addEventListener('input',e=>setElec('code',e.target.value.trim()));
    el.querySelector('.ename').addEventListener('input',e=>setElec('name',e.target.value.trim()));
  }
});

// ---- edge attach ordering ----
const outE={}, inE={};
DATA.edges.forEach(e=>{ if(!byKey[e.s]||!byKey[e.t])return; (outE[e.s]=outE[e.s]||[]).push(e); (inE[e.t]=inE[e.t]||[]).push(e); });
const rk=k=>rowOf[k]+byKey[k].col*0.001;
for(const k in outE) outE[k].sort((a,b)=>rk(a.t)-rk(b.t));
for(const k in inE)  inE[k].sort((a,b)=>rk(a.s)-rk(b.s));

// ---- rounded orthogonal path ----
function roundPath(pts,r){
  if(pts.length<2) return "M"+pts[0][0]+","+pts[0][1];
  let d="M"+pts[0][0]+","+pts[0][1];
  for(let i=1;i<pts.length-1;i++){
    const p0=pts[i-1],p1=pts[i],p2=pts[i+1];
    const d1=Math.hypot(p1[0]-p0[0],p1[1]-p0[1]), d2=Math.hypot(p2[0]-p1[0],p2[1]-p1[1]);
    const rr=Math.max(2,Math.min(r,d1/2,d2/2));
    const u1=[(p0[0]-p1[0])/(d1||1),(p0[1]-p1[1])/(d1||1)], u2=[(p2[0]-p1[0])/(d2||1),(p2[1]-p1[1])/(d2||1)];
    d+=" L"+(p1[0]+u1[0]*rr)+","+(p1[1]+u1[1]*rr)+" Q"+p1[0]+","+p1[1]+" "+(p1[0]+u2[0]*rr)+","+(p1[1]+u2[1]*rr);
  }
  const L=pts[pts.length-1]; d+=" L"+L[0]+","+L[1]; return d;
}

// ---- deterministic no-cross orthogonal router ----
// Grid invariant: every column gutter (GUT wide) is clear full-height; every global
// row-gap (GAP tall, between two row bands) is clear full-width. So: verticals live only
// in gutters, horizontals live only in gutters or row-gaps -> zero box crossings.
const gutLeft = c => PAD + c*COL_W + BOX_W;          // left edge of gutter right of col c
function gapIndexNear(y){                             // nearest global row-gap below a box row
  let gi=Math.round((y-BODY_Y-BOX_H-GAP/2)/ROW_H);
  return Math.max(0, Math.min(Math.max(0,maxRows-2), gi));
}
// pass 1: compute attach points + which gutter(s)/lane each edge wants
const wireInfo=[]; const GUT_GROUP={}, LANE_GROUP={};
DATA.edges.forEach(e=>{
  if(!byKey[e.s]||!byKey[e.t]) return;
  const s=byKey[e.s], t=byKey[e.t], sp=pos[e.s], tp=pos[e.t];
  const ko=outE[e.s].length, io=outE[e.s].indexOf(e);
  const ki=inE[e.t].length,  ii=inE[e.t].indexOf(e);
  const ay=sp.y+BOX_H*(io+1)/(ko+1), by=tp.y+BOX_H*(ii+1)/(ki+1);
  const span=t.col-s.col;
  const inf={e,sp,tp,ay,by,span};
  if(span<=1){ inf.g1=s.col; }                       // single gutter (same col or adjacent)
  else { inf.g1=s.col; inf.g2=t.col-1; inf.gap=gapIndexNear((ay+by)/2); }
  wireInfo.push(inf);
  (GUT_GROUP[inf.g1]=GUT_GROUP[inf.g1]||[]).push({inf,side:1});
  if(inf.g2!=null) (GUT_GROUP[inf.g2]=GUT_GROUP[inf.g2]||[]).push({inf,side:2});
  if(inf.gap!=null) (LANE_GROUP[inf.gap]=LANE_GROUP[inf.gap]||[]).push(inf);
});
// pass 2: assign a distinct x-slot per gutter and y-slot per lane so wires never coincide
Object.keys(GUT_GROUP).forEach(g=>{
  const list=GUT_GROUP[g];
  list.sort((a,b)=>(a.side===1?a.inf.ay:a.inf.by)-(b.side===1?b.inf.ay:b.inf.by));
  const n=list.length, step=Math.min(11,(GUT-16)/Math.max(1,n-1));
  list.forEach((r,i)=>{ const x=gutLeft(+g)+8+i*step; if(r.side===1) r.inf.x1=x; else r.inf.x2=x; });
});
Object.keys(LANE_GROUP).forEach(gi=>{
  const list=LANE_GROUP[gi]; list.sort((a,b)=>a.ay-b.ay);
  const yTop=BODY_Y+(+gi)*ROW_H+BOX_H, n=list.length, step=Math.min(8,(GAP-12)/Math.max(1,n-1));
  list.forEach((inf,i)=>{ inf.laneY=yTop+6+i*step; });
});
// pass 3: draw
const wireMeta=[];
wireInfo.forEach(inf=>{
  const {e,sp,tp,ay,by,span}=inf;
  const sxR=sp.x+BOX_W, txL=tp.x, txR=tp.x+BOX_W;
  let pts;
  if(span===0){                                      // same column: short hop in right gutter
    pts=[[sxR,ay],[inf.x1,ay],[inf.x1,by],[txR,by]];
  }else if(span===1){                                // adjacent: one vertical in the gutter
    pts=[[sxR,ay],[inf.x1,ay],[inf.x1,by],[txL,by]];
  }else{                                             // span>=2: gutter -> row-gap lane -> gutter
    pts=[[sxR,ay],[inf.x1,ay],[inf.x1,inf.laneY],[inf.x2,inf.laneY],[inf.x2,by],[txL,by]];
  }
  const p=document.createElementNS("http://www.w3.org/2000/svg","path");
  p.setAttribute("d",roundPath(pts,6)); p.setAttribute("class","wire"+(e.co?" co":""));
  p.setAttribute("marker-end","url(#arw)");
  wires.appendChild(p); wireMeta.push({el:p,s:e.s,t:e.t});
});

// ---- highlight both ways ----
let pinned=null;
function highlight(key){
  const up=ancestors(key), down=descendants(key), set=new Set([key,...up,...down]);
  map.classList.add('dimmed');
  up.forEach(k=>nodeEl[k]&&nodeEl[k].classList.add('glow','up'));
  down.forEach(k=>nodeEl[k]&&nodeEl[k].classList.add('glow','down'));
  nodeEl[key].classList.add('glow','root');
  wireMeta.forEach(w=>{
    if(set.has(w.s)&&set.has(w.t)){
      w.el.classList.add('glow');
      const isDown=down.has(w.t)&&(w.s===key||down.has(w.s));
      if(isDown) w.el.classList.add('down');
      w.el.setAttribute('marker-end', isDown?'url(#arwD)':'url(#arwC)');  // recolor arrowhead
    }
  });
}
function clearHi(){
  map.classList.remove('dimmed');
  document.querySelectorAll('.node.glow').forEach(n=>n.classList.remove('glow','root','up','down'));
  wireMeta.forEach(w=>{ w.el.classList.remove('glow','down'); w.el.setAttribute('marker-end','url(#arw)'); });
}

// ---- stars ----
let starsOnly=false;
function toggleStar(key){
  if(stars[key]) delete stars[key]; else stars[key]=1;
  saveStars(); nodeEl[key].classList.toggle('starred',!!stars[key]);
  if(curPanel===key) syncPanelStar();
  if(starsOnly) applyFilters();
  updateCounts();
}
const starsBtn=document.getElementById('starsBtn');
starsBtn.addEventListener('click',()=>{ starsOnly=!starsOnly; starsBtn.classList.toggle('on',starsOnly); applyFilters(); });

// ---- category filter (legend chips) ----
const activeCats=new Set(Object.keys(DATA.cats));
const legend=document.getElementById('legend');
Object.keys(DATA.cats).forEach(k=>{
  const c=DATA.cats[k]; const d=document.createElement('div'); d.className='lg'; d.dataset.cat=k;
  d.innerHTML='<i style="background:'+c.stroke+'"></i>'+c.label;
  d.addEventListener('click',()=>{
    if(activeCats.has(k)) activeCats.delete(k); else activeCats.add(k);
    d.classList.toggle('off',!activeCats.has(k)); applyFilters();
  });
  legend.appendChild(d);
});
function applyFilters(){
  DATA.nodes.forEach(n=>{
    const off=!activeCats.has(n.cat) || (starsOnly && !stars[n.key]);
    nodeEl[n.key].classList.toggle('hidden',off);
  });
  wireMeta.forEach(w=>{
    const hide=nodeEl[w.s].classList.contains('hidden')||nodeEl[w.t].classList.contains('hidden');
    w.el.style.display=hide?'none':'';
  });
}

// ---- search ----
const search=document.getElementById('search');
search.addEventListener('input',()=>{
  const q=search.value.trim().toLowerCase();
  DATA.nodes.forEach(n=>{
    const hit=!q||n.short.toLowerCase().includes(q)||n.name.toLowerCase().includes(q)||n.key.toLowerCase().includes(q);
    nodeEl[n.key].classList.toggle('faded',!hit);
  });
});

// ---- counts ----
const counts=document.getElementById('counts');
function updateCounts(){
  const ks=Object.keys(stars); let cr=0; ks.forEach(k=>{if(byKey[k])cr+=byKey[k].cr;});
  counts.innerHTML='<b>'+ks.length+'</b>★ &middot; '+cr+'cr';
}

// ---- grades + GPA summary (CMU scale: A4 B+3.5 B3 C+2.5 C2 D+1.5 D1 F0; W excluded) ----
const GPOINTS={A:4,'B+':3.5,B:3,'C+':2.5,C:2,'D+':1.5,D:1,F:0};
const PASSING=new Set(['A','B+','B','C+','C','D+','D']);  // counts toward credits studied
const TOTAL_CR=DATA.sems.reduce((s,x)=>s+x.cr,0);
function semLabel(col){ const l=DATA.sems[col].label; if(/summer/i.test(l)) return 'Summer';
  const m=l.match(/Y(\d)\s*S(\d)/i); return m?('Year '+m[1]+' Semester '+m[2]):l; }
function applyGradeClass(key,g){
  const el=nodeEl[key]; if(!el) return;
  el.classList.toggle('graded', !!g && g!=='W' && g!=='F');
  el.classList.toggle('failed', g==='F');
  el.classList.toggle('withdrawn', g==='W');
}
function setGrade(key,g){
  if(g) grades[key]=g; else delete grades[key];
  saveGrades(); applyGradeClass(key,g); computeSummary();
}
// per-semester GPA data, shared by the on-screen panel and the PDF document
function gpaData(){
  const rows=[]; let tNum=0,tDen=0,cred=0;
  for(let c=0;c<DATA.sems.length;c++){
    let num=0,den=0;
    DATA.nodes.filter(n=>n.col===c).forEach(n=>{
      const g=grades[n.key]; if(!g||g==='W') return;     // W & blank: no points, no credit
      num+=GPOINTS[g]*n.cr; den+=n.cr;
      if(PASSING.has(g)) cred+=n.cr;                       // credits studied = A..D only
    });
    tNum+=num; tDen+=den;
    rows.push({col:c, label:semLabel(c), gpa:den?(num/den).toFixed(2):'—', den});
  }
  return {rows, total:tDen?(tNum/tDen).toFixed(2):'—', tDen, cred};
}
const summary=document.getElementById('summary');
document.getElementById('sumBtn').addEventListener('click',()=>{ summary.classList.toggle('open'); });
document.getElementById('sumClose').addEventListener('click',()=>summary.classList.remove('open'));
function computeSummary(){
  const d=gpaData();
  const rows=d.rows.map(r=>'<div class="srow"><span>'+r.label+'</span><b>'+r.gpa+'</b><i>'+r.den+' cr</i></div>').join('');
  document.getElementById('sumBody').innerHTML=
    '<div class="sbig">'+d.cred+'<small> / '+TOTAL_CR+' credits studied</small></div>'+rows+
    '<div class="srow total"><span>Total GPA</span><b>'+d.total+'</b><i>'+d.tDen+' cr</i></div>';
}

// ---- formal PDF document (course list + summary + advisor comment + signatures) ----
const LS_STU="cie_student_v1", LS_ADV="cie_advnote_v1";
const stu=JSON.parse(localStorage.getItem(LS_STU)||"{}");
const docview=document.getElementById('docview');
function esc(s){ return (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
// in-app webviews (LINE, Facebook, Instagram, etc.) usually can't run window.print() / save PDF
const INAPP=/\b(Line|FBAN|FBAV|FB_IAB|Instagram|MicroMessenger|Twitter|TikTok)\b/i.test(navigator.userAgent);
function warnHtml(){ return INAPP
  ? '<div class="doc-warn">⚠ You opened this from an in-app browser (e.g. <b>LINE</b>), which can’t save PDF. '+
    'Tap the <b>⋯</b> / share menu and choose <b>“Open in browser”</b> (Safari / Chrome), then press Save PDF.</div>'
  : ''; }
const codeFor=n=>isElec(n)?elecCode(n):n.short;                       // registered/displayed code
const titleFor=n=>isElec(n)?(elecName(n)||n.name):n.name;            // actual name if student filled it
function docHead(today){
  return '<div class="doc-head"><div class="doc-title">B.Eng. Civil Engineering (International Program)</div>'+
    '<div class="doc-sub">Curriculum CIE 2568 &middot; '+TOTAL_CR+' Credits &middot; Academic Progress Report</div></div>'+
    '<div class="doc-meta"><div><label>Student Name:</label><input id="docName" value="'+esc(stu.name)+'"></div>'+
    '<div><label>Student ID:</label><input id="docID" value="'+esc(stu.id)+'"></div>'+
    '<div><label>Date:</label> '+today+'</div></div>';
}
function sigRow(){
  return '<div class="sigrow">'+
    '<div class="sigbox"><div class="sigline"></div><b>Student</b><span>Signature / Date</span></div>'+
    '<div class="sigbox"><div class="sigline"></div><b>Academic Advisor</b><span>Signature / Date</span></div></div>';
}
// year-column helpers for the 1-page layout (Summer counts as Year 3)
function yearOfCol(c){ const l=DATA.sems[c].label; const m=l.match(/Y(\d)/i); return m?+m[1]:(/summer/i.test(l)?3:0); }
function buildFull(today){
  const d=gpaData();
  let sems='';
  for(let c=0;c<DATA.sems.length;c++){
    const rowsHtml=DATA.nodes.filter(n=>n.col===c).map(n=>{
      const g=grades[n.key]||'-';
      return '<tr><td>'+esc(codeFor(n))+'</td><td>'+esc(titleFor(n))+'</td><td class="c">'+n.cr+'</td><td class="c">'+g+'</td></tr>';
    }).join('');
    const r=d.rows[c];
    sems+='<table class="docsem"><caption>'+r.label+' &mdash; '+DATA.sems[c].cr+' Credit</caption>'+
      '<thead><tr><th>Code</th><th>Course Title</th><th class="c">Credit</th><th class="c">Grade</th></tr></thead>'+
      '<tbody>'+rowsHtml+'</tbody>'+
      '<tfoot><tr><td colspan="2" class="r">Semester GPA</td><td class="c">'+r.den+'</td><td class="c">'+r.gpa+'</td></tr></tfoot>'+
      '</table>';
  }
  return docHead(today)+sems+
    '<div class="docsummary"><h3>Summary</h3>'+
      '<div class="srow2 big"><span>Total credits studied (passing grade A&ndash;D)</span><b>'+d.cred+' / '+TOTAL_CR+'</b></div>'+
      '<div class="srow2 big"><span>Cumulative GPA</span><b>'+d.total+'</b></div></div>'+
    '<div class="adv-comment"><div class="lbl">Academic Advisor&rsquo;s Comment</div>'+
      '<textarea id="docComment">'+esc(localStorage.getItem(LS_ADV)||'')+'</textarea></div>'+
    sigRow();
}
function buildCompact(today){
  const d=gpaData();
  let cols='';
  for(let y=1;y<=4;y++){
    const yc=[]; for(let c=0;c<DATA.sems.length;c++) if(yearOfCol(c)===y) yc.push(c);
    let num=0,den=0, body='';
    yc.forEach(c=>{
      body+='<div class="cyhdr">'+DATA.sems[c].label+'</div>';
      DATA.nodes.filter(n=>n.col===c).forEach(n=>{
        const gv=grades[n.key], g=gv||'-';
        if(gv&&gv!=='W'){ num+=GPOINTS[gv]*n.cr; den+=n.cr; }
        body+='<div class="cyrow"><span>'+esc(codeFor(n))+'</span><b>'+g+'</b></div>';
      });
    });
    const ygpa=den?(num/den).toFixed(2):'—';
    cols+='<div class="cyear"><div class="cytitle">Year '+y+'</div>'+body+
      '<div class="cygpa">Year GPA <b>'+ygpa+'</b></div></div>';
  }
  return docHead(today)+
    '<div class="compactgrid">'+cols+'</div>'+
    '<div class="docsummary compact"><span><b>Credits studied:</b> '+d.cred+' / '+TOTAL_CR+
      ' &nbsp;&middot;&nbsp; <b>Cumulative GPA:</b> '+d.total+'</span></div>'+
    sigRow();
}
let docMode='full';
function buildDoc(mode){
  docMode = mode||docMode;
  const today=new Date().toLocaleDateString('en-GB',{year:'numeric',month:'long',day:'numeric'});
  document.getElementById('docPaper').className='docpaper'+(docMode==='compact'?' compactpaper':'');
  document.getElementById('docPaper').innerHTML = warnHtml()+(docMode==='compact'?buildCompact(today):buildFull(today));
  document.getElementById('docFull').classList.toggle('on',docMode==='full');
  document.getElementById('docCompact').classList.toggle('on',docMode==='compact');
  // rebind persisted fields
  const nm=document.getElementById('docName'), id=document.getElementById('docID'), cm=document.getElementById('docComment');
  if(nm) nm.addEventListener('input',()=>{ stu.name=nm.value; localStorage.setItem(LS_STU,JSON.stringify(stu)); });
  if(id) id.addEventListener('input',()=>{ stu.id=id.value; localStorage.setItem(LS_STU,JSON.stringify(stu)); });
  if(cm) cm.addEventListener('input',()=>localStorage.setItem(LS_ADV,cm.value));
}
document.getElementById('pdfBtn').addEventListener('click',()=>{ buildDoc('full'); docview.classList.add('open'); });
document.getElementById('docFull').addEventListener('click',()=>buildDoc('full'));
document.getElementById('docCompact').addEventListener('click',()=>buildDoc('compact'));
document.getElementById('docClose').addEventListener('click',()=>docview.classList.remove('open'));
document.getElementById('docPrint').addEventListener('click',()=>{
  if(INAPP){ const w=document.querySelector('.doc-warn'); if(w){ w.scrollIntoView({block:'center'}); w.animate?w.animate([{opacity:.4},{opacity:1}],{duration:500,iterations:2}):0; } }
  try{ window.print(); }catch(e){}
});
document.addEventListener('keydown',e=>{ if(e.key==='Escape') docview.classList.remove('open'); });

// ---- zoom (CSS zoom keeps sticky header working) ----
let z=1;
function setZoom(v){ z=Math.max(0.2,Math.min(2,v)); map.style.zoom=z; colsBar.style.zoom=z;
  map.classList.toggle('codeonly', z<0.45);   // tiny zoom: show course code only
  colsBar.classList.toggle('codeonly', z<0.45);  // ...and abbreviate the year-box credit
  document.getElementById('zlevel').textContent=Math.round(z*100)+'%'; }
document.getElementById('zin').onclick=()=>setZoom(z*1.2);
document.getElementById('zout').onclick=()=>setZoom(z/1.2);
document.getElementById('zone').onclick=()=>{ setZoom(1); };
document.getElementById('zfit').onclick=()=>{
  const w=scroll.clientWidth-16, h=scroll.clientHeight-16;
  // phone (portrait OR landscape): fitting all 9 columns = unreadable (~0.2).
  const phone = window.innerWidth<=720 || (window.innerHeight<=520 && window.innerWidth<=950);
  if(phone){
    setZoom(0.25);   // whole-map overview; codeonly kicks in (<0.45) so only course codes show
  } else {
    setZoom(Math.min(w/mapW, h/(mapH+56)));
  }
  scroll.scrollTo({left:0,top:0});
};

// ---- side panel + pin-select ----
let curPanel=null;
const panel=document.getElementById('panel'); const $=id=>document.getElementById(id);
function selectNode(key){ pinned=key; clearHi(); highlight(key); openPanel(key); }
function deselect(){ pinned=null; clearHi(); panel.classList.remove('open'); curPanel=null;
  document.querySelectorAll('.node.selected').forEach(e=>e.classList.remove('selected')); }
function closePanelKeepGlow(){ panel.classList.remove('open'); curPanel=null;
  document.querySelectorAll('.node.selected').forEach(e=>e.classList.remove('selected')); }   // glow/pin stays
// touch (no hover): 1st tap = glow only; 2nd tap same course = info; tapping it again with info open, or empty space, clears
function tapNode(key){
  if(pinned===key){
    if(curPanel===key) deselect();        // info already open → clear all
    else openPanel(key);                  // glow already shown → reveal info (glow stays)
  } else {
    closePanelKeepGlow();                  // switch to a different course
    pinned=key; clearHi(); highlight(key); // glow only, no panel yet
  }
}
map.addEventListener('click',e=>{ if(!e.target.closest('.node')) deselect(); });   // tap empty space clears
function openPanel(key){
  curPanel=key; const n=byKey[key], c=DATA.cats[n.cat];
  document.querySelectorAll('.node.selected').forEach(e=>e.classList.remove('selected'));
  nodeEl[key].classList.add('selected');
  $('ptag').textContent=c.label; $('pcode').textContent=n.short; $('pname').textContent=n.name;
  $('pmeta').innerHTML='<span class="chip" style="border-color:'+c.stroke+';color:'+c.stroke+'">'+n.key+'</span>'+
    '<span class="chip">'+n.cr+' credits</span><span class="chip">'+DATA.sems[n.col].label+'</span>';
  $('pdesc').textContent=n.desc||"Description not available in source.";
  const pr=(prereqsOf[key]||[]).filter(k=>byKey[k]);
  $('pprereq').innerHTML=pr.length?pr.map(k=>'<a data-go="'+k+'">'+byKey[k].short+' <span>— '+byKey[k].name+'</span></a>').join(''):'<div class="none">No prerequisites — entry-level course.</div>';
  const un=(unlocksOf[key]||[]).filter(k=>byKey[k]);
  $('punlocks').innerHTML=un.length?un.map(k=>'<a data-go="'+k+'">'+byKey[k].short+' <span>— '+byKey[k].name+'</span></a>').join(''):'<div class="none">Does not unlock a later course directly.</div>';
  panel.querySelectorAll('[data-go]').forEach(a=>a.addEventListener('click',()=>selectNode(a.dataset.go)));
  $('pnotes').value=notes[key]||""; $('psaved').textContent=notes[key]?"saved":"";
  syncPanelStar(); panel.classList.add('open');
}
$('pclose').addEventListener('click',()=>{ if(HOVER) deselect(); else closePanelKeepGlow(); });
let t=null;
$('pnotes').addEventListener('input',()=>{
  if(!curPanel)return; notes[curPanel]=$('pnotes').value; saveNotes();
  nodeEl[curPanel].classList.toggle('hasnote',!!$('pnotes').value.trim());
  $('psaved').textContent="saving…"; clearTimeout(t); t=setTimeout(()=>$('psaved').textContent="saved ✓",350);
});
$('pstar').addEventListener('click',()=>{ if(curPanel) toggleStar(curPanel); });
function syncPanelStar(){
  const on=!!stars[curPanel]; $('pstar').classList.toggle('on',on);
  $('pstar').querySelector('b').textContent=on?'★':'☆';
  $('pstartxt').textContent=on?'Interested — starred':'Mark as interested';
}
document.addEventListener('keydown',e=>{ if(e.key==='Escape') deselect(); });

// ---- measure header so column heads never overlap it ----
function fitBar(){ document.documentElement.style.setProperty('--bar',(header.offsetHeight)+'px'); }
window.addEventListener('resize',fitBar);
window.addEventListener('load',()=>{ fitBar(); setTimeout(fitBar,300); });
fitBar();
updateCounts();
computeSummary();
</script>
</body>
</html>
"""

html = TEMPLATE.replace("__DATA__", DATA)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"[OK] wrote {OUT}")
print(f"     nodes={len(nodes)} edges={len(edges)} cats={len(cats)} cols={len(sems)}")
