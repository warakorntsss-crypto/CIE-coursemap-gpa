#!/usr/bin/env python3
"""
Build a draw.io (.drawio) study course map for the
B.Eng. Civil Engineering (International Program) curriculum (CIE 2568).

Layout: 9 semester columns, courses stacked, prerequisite arrows.
Color: by category. Data: shared curriculum_data.py (NotebookLM `cie_curriculum`).

Re-run after editing curriculum_data.py:
    python build-map.py
"""

import os
from xml.sax.saxutils import escape

from curriculum_data import CAT, CAT_LABEL, SEMS, COURSES, PREREQS

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "CIE-CivilEng-CourseMap.drawio")

# ---- geometry -------------------------------------------------------------
COL_W   = 200          # column pitch
BOX_W   = 180
BOX_H   = 54
GAP_Y   = 16           # vertical gap between boxes
X0      = 40
HDR_Y   = 140          # header band y
BODY_Y  = 210          # first course box y
HDR_H   = 50


def style(cat):
    fill, stroke = CAT[cat]
    return (f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};"
            f"strokeColor={stroke};fontSize=10;arcSize=12;")


def main():
    cells = []
    cid = [10]  # mutable id counter, leave 0/1 for root

    def nid():
        cid[0] += 1
        return f"n{cid[0]}"

    node_id = {}  # course key -> cell id

    # title
    cells.append(
        f'<mxCell id="title" value="B.Eng. Civil Engineering (International Program) '
        f'&#8212; Study Course Map (CIE 2568, 149 cr)" '
        f'style="text;html=1;fontSize=18;fontStyle=1;align=left;verticalAlign=middle;" '
        f'vertex="1" parent="1"><mxGeometry x="40" y="20" width="900" height="30" as="geometry"/></mxCell>'
    )

    # legend
    lx, ly = 40, 60
    leg_items = "".join(
        f'&#8226; {escape(CAT_LABEL[k])}&#10;' for k in CAT
    )
    legend_val = ("Legend&#10;" + leg_items +
                  "&#10;&#8594; solid = prerequisite&#10;"
                  "&#8594; dashed = co-requisite option")
    cells.append(
        f'<mxCell id="legend" value="{legend_val}" '
        f'style="rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;'
        f'fillColor=#FFFFFF;strokeColor=#666666;fontSize=10;spacing=6;" '
        f'vertex="1" parent="1"><mxGeometry x="{lx}" y="{ly}" width="300" height="70" as="geometry"/></mxCell>'
    )

    # group courses by column preserving insertion order
    by_col = {}
    for key, (col, *_rest) in COURSES.items():
        by_col.setdefault(col, []).append(key)

    # per-column: header + stacked boxes
    for col, (label, cr) in enumerate(SEMS):
        x = X0 + col * COL_W
        fill, stroke = "#E1D5E7", "#9673A6"
        cells.append(
            f'<mxCell id="hdr{col}" value="{escape(label)}&#10;{cr} cr" '
            f'style="rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};'
            f'fontSize=12;fontStyle=1;" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{HDR_Y}" width="{BOX_W}" height="{HDR_H}" as="geometry"/></mxCell>'
        )
        y = BODY_Y
        for key in by_col.get(col, []):
            _c, short, name, credits, cat = COURSES[key]
            i = nid()
            node_id[key] = i
            val = f"{escape(short)}&#10;{escape(name)}&#10;{credits} cr"
            cells.append(
                f'<mxCell id="{i}" value="{val}" style="{style(cat)}" '
                f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" '
                f'width="{BOX_W}" height="{BOX_H}" as="geometry"/></mxCell>'
            )
            y += BOX_H + GAP_Y

    # edges
    for src, dst, coreq in PREREQS:
        if src not in node_id or dst not in node_id:
            continue  # skip dangling (e.g. placeholder targets)
        e = nid()
        dash = "dashed=1;" if coreq else ""
        st = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;{dash}"
              f"strokeColor=#555555;endArrow=block;endFill=1;exitX=1;exitY=0.5;"
              f"entryX=0;entryY=0.5;")
        cells.append(
            f'<mxCell id="{e}" style="{st}" edge="1" parent="1" '
            f'source="{node_id[src]}" target="{node_id[dst]}">'
            f'<mxGeometry relative="1" as="geometry"/></mxCell>'
        )

    body = "\n        ".join(cells)
    xml = f'''<mxfile host="app.diagrams.net" modified="2026-06-07" agent="curriculum-map-generator" version="24.0.0">
  <diagram id="cie-civil-map" name="CIE Civil Eng Course Map">
    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2000" pageHeight="1200" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        {body}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"[OK] wrote {OUT}")
    print(f"     courses={len(node_id)}  edges<={len(PREREQS)}  columns={len(SEMS)}")


if __name__ == "__main__":
    main()
