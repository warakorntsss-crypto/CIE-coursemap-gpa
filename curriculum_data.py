"""
Shared curriculum data for the CIE Civil Engineering (International Program) map.
Single source of truth — imported by build-map.py (.drawio) and
build-interactive.py (index.html). Source: NotebookLM notebook `cie_curriculum`.

Edit here, then re-run either generator.
"""

# category -> (fill, stroke)
CAT = {
    "ge":   ("#DAE8FC", "#6C8EBF"),  # General Education
    "core": ("#D5E8D4", "#82B366"),  # Core math/sci/basic eng
    "major":("#FFE6CC", "#D79B00"),  # Civil major lecture
    "lab":  ("#FFF2CC", "#D6B656"),  # Lab / testing / training
    "elec": ("#F5F5F5", "#999999"),  # Elective placeholders
}
CAT_LABEL = {
    "ge": "General Education", "core": "Core (Math/Sci/Basic Eng)",
    "major": "Civil Major", "lab": "Lab / Testing / Training",
    "elec": "Elective (placeholder)",
}

# semester columns: (label, credit total)
SEMS = [
    ("Y1 S1", 21), ("Y1 S2", 22), ("Y2 S1", 21), ("Y2 S2", 20),
    ("Y3 S1", 20), ("Y3 S2", 21), ("Summer", 3), ("Y4 S1", 13), ("Y4 S2", 8),
]

# course key -> (semester_index, short, full name, credits, category)
COURSES = {
    # Y1 S1 (col 0)
    "ENGL101": (0, "ENGL101", "Fundamental English 1", 3, "ge"),
    "CHEM162": (0, "CHEM162", "General Chemistry for Engineers", 3, "core"),
    "CHEM167": (0, "CHEM167", "General Chemistry Laboratory", 1, "lab"),
    "MATH161": (0, "MATH161", "Calculus for Engineering 1", 3, "core"),
    "PHYS105": (0, "PHYS105", "Physics for Engineering 1", 3, "core"),
    "PHYS115": (0, "PHYS115", "Physics Laboratory 1", 1, "lab"),
    "ENGR103": (0, "ENGR103", "Engineering Materials", 3, "core"),
    "ENGR104": (0, "ENGR104", "Engineering Drawing", 3, "core"),
    "ENGR191": (0, "ENGR191", "Principle of Being Professional", 1, "ge"),
    # Y1 S2 (col 1)
    "ENGL102": (1, "ENGL102", "Fundamental English 2", 3, "ge"),
    "PG104":   (1, "PG104", "Citizenship", 3, "ge"),
    "MATH162": (1, "MATH162", "Calculus for Engineering 2", 3, "core"),
    "PHYS106": (1, "PHYS106", "Physics for Engineering 2", 3, "core"),
    "PHYS116": (1, "PHYS116", "Physics Laboratory 2", 1, "lab"),
    "CE102":   (1, "CE102", "Civil Engineering Fundamentals", 2, "major"),
    "ENGR106": (1, "ENGR106", "Workshop Technology", 1, "lab"),
    "ENGR107": (1, "ENGR107", "Engineering Mechanics 1", 3, "core"),
    "GE_ELEC1":(1, "GE Elec", "Innovative Co-creator (GE)", 3, "elec"),
    # Y2 S1 (col 2)
    "ENGL201": (2, "ENGL201", "Critical Reading & Effective Writing", 3, "ge"),
    "CS100":   (2, "CS100", "Information Technology & Modern Life", 3, "ge"),
    "GEOL275": (2, "GEOL275", "Geology for Engineers", 3, "core"),
    "MATH261": (2, "MATH261", "Calculus for Engineering 3", 3, "core"),
    "STAT263": (2, "STAT263", "Elementary Statistics", 3, "core"),
    "CE211":   (2, "CE211", "Strength of Materials 1", 3, "major"),
    "CE261":   (2, "CE261", "Hydraulics", 3, "major"),
    # Y2 S2 (col 3)
    "ENGL225": (3, "ENGL225", "English in Science & Technology", 3, "ge"),
    "MATH362": (3, "MATH362", "Applied Differential Equations", 3, "core"),
    "CE212":   (3, "CE212", "Theory & Analysis of Structures", 3, "major"),
    "CE216":   (3, "CE216", "Structural Materials & Testing", 4, "lab"),
    "CE262":   (3, "CE262", "Hydraulic Models & Testing", 1, "lab"),
    "ENGR201": (3, "ENGR201", "Computer Programming for Engineers", 3, "core"),
    "GE_ELEC2":(3, "GE Elec", "General Education Elective", 3, "elec"),
    # Y3 S1 (col 4)
    "CE292":   (4, "CE292", "Diff. Eq. & Numerical Methods (CE)", 3, "major"),
    "CE311":   (4, "CE311", "Steel & Timber Structure Design", 4, "major"),
    "CE336":   (4, "CE336", "Transportation Systems Engineering", 3, "major"),
    "CE363":   (4, "CE363", "Engineering Hydrology", 3, "major"),
    "CE371":   (4, "CE371", "Soil Mechanics", 3, "major"),
    "CE372":   (4, "CE372", "Engineering Soil Tests", 1, "lab"),
    "GE_ELEC3":(4, "GE Elec", "General Education Elective", 3, "elec"),
    # Y3 S2 (col 5)
    "CE313":   (5, "CE313", "Reinforced Concrete Design", 4, "major"),
    "CE333":   (5, "CE333", "Highway Engineering", 3, "major"),
    "CE334":   (5, "CE334", "Highway Engineering Laboratory", 1, "lab"),
    "CE343":   (5, "CE343", "Surveying for Civil Engineering", 4, "major"),
    "CE364":   (5, "CE364", "Water Resource Engineering", 3, "major"),
    "CE374":   (5, "CE374", "Geotech. Eng. & Building Foundations", 3, "major"),
    "FREE_ELEC1":(5, "Free Elec", "Free Elective", 3, "elec"),
    # Summer (col 6)
    "CE400":   (6, "CE400", "Training in Civil Engineering", 3, "lab"),
    # Y4 S1 (col 7)
    "CE413":   (7, "CE413", "Reinforced Concrete Building Design", 4, "major"),
    "CE451":   (7, "CE451", "Construction Techniques & Management", 3, "major"),
    "MAJ_ELEC1":(7, "Major Elec", "Major Elective", 3, "elec"),
    "FREE_ELEC2":(7, "Free Elec", "Free Elective", 3, "elec"),
    # Y4 S2 (col 8)
    "ENGR192": (8, "ENGR192", "Skills for Professionalism & Entrep.", 1, "ge"),
    "ENGR194": (8, "ENGR194", "Values for Professional Entrepreneur", 1, "ge"),
    "DESIGN_DEV":(8, "CE491-498", "Civil Eng. Design Development", 3, "elec"),
    "MAJ_ELEC2":(8, "Major Elec", "Major Elective", 3, "elec"),
}

# short one-line course descriptions (source: NotebookLM `cie_curriculum`).
# Electives are generic (curriculum lists options, not a fixed course).
DESC = {
    "ENGL101": "Basic listening, speaking, reading and writing skills in English for varied cultural contexts.",
    "ENGL102": "Advanced English communication skills for complex social contexts and life-long learning.",
    "ENGL201": "Analytical reading from various sources and effective writing on topics of interest.",
    "ENGL225": "English language functions and skills for communication in science and technology contexts.",
    "PG104": "Concept of citizenship, social awareness and positive attitudes for peaceful conflict resolution.",
    "CHEM162": "Stoichiometry, atomic structure, chemical bonding, states of matter and reaction rates.",
    "CHEM167": "Basic chemistry lab experiments: gas constants, titrations and polymer synthesis.",
    "CS100": "Computer usage, online collaboration, productivity software and IT security.",
    "GEOL275": "Minerals, rocks and geological processes relevant to civil engineering site investigations.",
    "MATH161": "Vector algebra and derivatives and integrals of functions of one variable.",
    "MATH162": "First and second order differential equations, partial derivatives and multiple integrals.",
    "MATH261": "Advanced calculus: vector calculus, complex variables and Fourier series.",
    "MATH362": "Ordinary and partial differential equations, Laplace transforms and series solutions for engineering.",
    "PHYS105": "Fundamental physics: mechanics, matter, sound and thermodynamics.",
    "PHYS106": "Electromagnetism, DC and AC circuits, optics and introductory modern physics.",
    "PHYS115": "Lab experiments in mechanics, thermal physics and mechanical waves.",
    "PHYS116": "Lab experiments in electricity, optics and modern physics.",
    "STAT263": "Basic statistics, probability distributions, hypothesis testing and regression analysis.",
    "CE102": "Introduction to civil engineering disciplines, professional responsibilities and sustainable development.",
    "CE211": "Analysis of stresses, strains, torsion and beam deflections in structural materials.",
    "CE212": "Analysis of determinate and indeterminate structures using classical and matrix methods.",
    "CE216": "Concrete technology, structural material properties and standard material testing methods.",
    "CE261": "Fluid properties, hydrostatics and mechanics of flow in pipes and open channels.",
    "CE262": "Experiments on fluid measurements, flow through orifices and pump performance.",
    "CE292": "Numerical methods and application of differential equations to civil engineering systems.",
    "CE311": "Design of structural steel and timber members and connections.",
    "CE313": "Design of reinforced concrete beams, slabs, columns and foundations by ultimate strength methods.",
    "CE333": "Highway planning, geometric design, traffic characteristics and pavement materials.",
    "CE334": "Lab tests on road materials: soils, aggregates and bituminous mixtures.",
    "CE336": "Multimodal transportation systems, planning principles and freight logistics infrastructure.",
    "CE343": "Distance and angle measurement, leveling, topographic mapping and field-camp practice.",
    "CE363": "Hydrologic cycle, precipitation, streamflow and groundwater hydrology.",
    "CE364": "Planning and design of water resource systems: reservoirs, dams and pipe networks.",
    "CE371": "Fundamental soil mechanics: classification, settlement analysis and shear strength.",
    "CE372": "Standard lab and field tests for engineering properties of soils.",
    "CE374": "Design of shallow and deep foundations, lateral earth pressure and slope stability.",
    "CE400": "Supervised professional training in engineering organizations (min. 270 hours).",
    "CE413": "Design of reinforced concrete buildings including wind and seismic analysis.",
    "CE451": "Construction project management, cost estimation, scheduling and engineering economics.",
    "ENGR103": "Classification, microstructure and mechanical properties of engineering materials.",
    "ENGR104": "Orthographic projection, dimensioning and 3D engineering drawing.",
    "ENGR106": "Workshop safety, hand tools, machining and rapid prototyping.",
    "ENGR107": "Principles of statics and dynamics, force systems and equilibrium.",
    "ENGR191": "Preparation for professional practice: discipline, institutional loyalty and ethics.",
    "ENGR192": "Professional and entrepreneurial skills including safety consciousness and moral awareness.",
    "ENGR194": "Characters and values for becoming a successful professional entrepreneur.",
    "ENGR201": "High-level computer programming applied to solving engineering problems.",
    "GE_ELEC1": "Innovative Co-creator general-education course — chosen from the approved GE list.",
    "GE_ELEC2": "General-education elective — chosen from the approved GE list.",
    "GE_ELEC3": "General-education elective — chosen from the approved GE list.",
    "FREE_ELEC1": "Free elective — any course offered within the university.",
    "FREE_ELEC2": "Free elective — any course offered within the university.",
    "MAJ_ELEC1": "Major elective — advanced civil-engineering topic (e.g. Rail Engineering, BIM) from the approved list.",
    "MAJ_ELEC2": "Major elective — advanced civil-engineering topic (e.g. Rail Engineering, BIM) from the approved list.",
    "DESIGN_DEV": "A course from the Civil Engineering Design Development category (CE 491-498).",
}

# prerequisites: (source, target, is_coreq)
PREREQS = [
    ("MATH161", "MATH162", False), ("MATH162", "MATH261", False),
    ("MATH261", "MATH362", False),
    ("PHYS105", "PHYS106", False), ("PHYS115", "PHYS116", False),
    ("CHEM162", "CHEM167", True),
    ("PHYS105", "ENGR107", False), ("MATH161", "ENGR107", False),
    ("ENGR107", "CE211", False), ("MATH162", "CE292", False),
    ("CE211", "CE212", False),
    ("ENGR103", "CE216", False), ("CE211", "CE216", False),
    ("ENGR104", "CE311", False), ("CE212", "CE311", False),
    ("CE216", "CE313", False), ("CE212", "CE313", False),
    ("CE313", "CE413", False),
    ("GEOL275", "CE371", False), ("CE261", "CE371", False), ("CE211", "CE371", False),
    ("CE371", "CE372", False), ("CE371", "CE374", False), ("CE372", "CE374", False),
    ("ENGR107", "CE261", False), ("CE261", "CE262", False),
    ("STAT263", "CE363", False), ("CE261", "CE363", False), ("CE363", "CE364", False),
    ("MATH162", "CE343", False), ("STAT263", "CE343", False),
    ("CE371", "CE333", False), ("CE372", "CE334", False), ("CE333", "CE334", False),
    ("CE313", "CE451", False), ("CE333", "CE451", False),
    ("ENGL101", "ENGL102", False), ("ENGL102", "ENGL201", False),
    ("ENGL102", "ENGL225", False),
]
