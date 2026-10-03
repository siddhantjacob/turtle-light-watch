"""Builds docs/turtle_light_brief.pdf (3-page plain-English brief) from the figures folder.
Same layout as the Revillagigedo brief. Run after scripts/09 and 10:  python docs/make_brief.py
(needs: pip install reportlab)"""
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = Path(__file__).resolve().parents[1]
D = str(ROOT / "figures") + "/"
OUT = str(ROOT / "docs" / "turtle_light_brief.pdf")
INK, MUTED, ACCENT, BOX = "#0b0b0b", "#52514e", "#1c5cab", "#eef4fc"

ss = getSampleStyleSheet()
base = ParagraphStyle("base", parent=ss["Normal"], fontName="Helvetica", fontSize=9.6,
                      leading=13.4, textColor=INK, spaceAfter=5)
small = ParagraphStyle("small", parent=base, fontSize=7.8, leading=10, textColor=MUTED)
cap = ParagraphStyle("cap", parent=small, spaceBefore=2, spaceAfter=8)
h1 = ParagraphStyle("h1", parent=base, fontName="Helvetica-Bold", fontSize=19, leading=23, spaceAfter=4)
sub = ParagraphStyle("sub", parent=base, fontSize=11, leading=15, textColor=MUTED, spaceAfter=4)
h2 = ParagraphStyle("h2", parent=base, fontName="Helvetica-Bold", fontSize=12, leading=15,
                    textColor=ACCENT, spaceBefore=8, spaceAfter=4, keepWithNext=1)
h3 = ParagraphStyle("h3", parent=base, fontName="Helvetica-Bold", fontSize=10, leading=13, spaceBefore=4, spaceAfter=2, keepWithNext=1)
bullet = ParagraphStyle("bullet", parent=base, leftIndent=11, bulletIndent=0, spaceAfter=3)

W = A4[0] - 36 * mm


def img(name, width=W):
    w, h = PILImage.open(D + name).size
    return Image(D + name, width=width, height=width * h / w)


def box(flowables):
    t = Table([[flowables]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(BOX)),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


def B(text):
    return Paragraph(text, bullet, bulletText="•")


s = []
s += [Paragraph("Are Odisha's turtle nesting beaches getting brighter at night?", h1),
      Paragraph("What satellite night-light data show, and don't show, about artificial light near the "
                "olive ridley mass-nesting beaches of Gahirmatha, Devi and Rushikulya, 2014–2025", sub),
      Paragraph("Conservation brief · Siddhant Jacob · October 2026", small),
      Spacer(1, 6)]

s.append(box([Paragraph("<b>In brief</b>", h3),
    B("Night light rose along <b>almost the whole Odisha coast</b> between 2014 and 2025: 94 of 99 five-km "
      "stretches show a clear increase."),
    B("<b>Rushikulya</b> sits at the edge of a brightening zone. The strongest new light is inland and to the "
      "south-west, led by an <b>industrial site about 4 km from the river mouth</b>."),
    B("<b>Gahirmatha's</b> island nesting beach stayed dark. The largest increase in that area is at "
      "<b>Dhamra port, about 15 km away</b>."),
    B("<b>Devi</b> changed about as slowly as unlit countryside."),
    B("The satellite cannot see blue-rich LED light well, which is the light turtles respond to most. "
      "A beach can look <b>dimmer from space while getting worse for hatchlings</b>."),
]))
s.append(Spacer(1, 8))
s.append(img("fig1_coast_map.png", W * 0.62))
s.append(Paragraph("<b>Figure 1.</b> How fast each 5 km stretch of the Odisha coast got brighter at night, 2014–2025 "
                   "(darker blue = faster; grey = no clear trend). Orange outlines mark the mass-nesting beaches.", cap))

s.append(Paragraph("Why this matters", h2))
s.append(Paragraph(
    "Sea turtle hatchlings emerge at night and crawl towards the brightest, lowest horizon, which on a natural beach "
    "is the sea. Artificial light can pull them inland, where many die from exhaustion, predators or traffic. "
    "Odisha hosts three of the world's largest olive ridley <i>arribadas</i>, where hundreds of thousands of females "
    "nest together. Because so many eggs hatch on a few kilometres of sand within a few nights, a single nearby light "
    "can affect a large share of a year's hatchlings. Field work at Rushikulya has already shown that lights from "
    "villages, a highway and a factory misorient hatchlings (Karnad et al. 2009). This brief asks what fifteen "
    "years of free satellite data add to that picture.", base))

s.append(Paragraph("What we found", h2))
s.append(Paragraph("1. Most of the coast is getting brighter", h3))
s.append(Paragraph(
    "After correcting for the satellite's own drift (see below), 94 of 99 stretches brightened beyond the sensor's "
    "noise. The fastest changes are around the Paradip port area, Puri and the Dhamra port area. Against this "
    "background, the question is whether the turtle beaches stand out.", base))
s.append(img("fig2_where_beaches_sit.png", W * 0.85))
s.append(Paragraph("<b>Figure 2.</b> All 99 stretches ranked from fastest to slowest brightening. "
                   "Rushikulya ranks 26th, Gahirmatha's mainland 34th and Devi 78th.", cap))

s.append(Paragraph("2. Rushikulya: new light is growing just inland of the nesting beach", h3))
s.append(Paragraph(
    "Brightening is strongest to the south-west of the river mouth and fades north-east along the nesting beach: the "
    "stretches rank 10th, 13th, 18th and 26th approaching the mouth, then 69th and 88th further north. The largest "
    "single increase is at an industrial site about 4 km from the river mouth. Its built-up area grew only slightly, "
    "which is consistent with more or brighter lighting on a similar footprint. From space we cannot tell the type, "
    "direction or shielding of those lights, or whether they are visible from the beach.", base))
s.append(img("fig4_rushikulya_story.png"))
s.append(Paragraph("<b>Figure 3.</b> Rushikulya, same colour scale in A and B. Night light 2014–16 (A) and 2023–25 (B), "
                   "and a daytime satellite image from early 2025 (C).", cap))

s.append(Paragraph("3. Gahirmatha: the island stayed dark; the port did not", h3))
s.append(Paragraph(
    "Since about 2009 the Gahirmatha arribada has used a short beach on Abdul Kalam Island. Light within 5 km of the "
    "island barely changed. The largest increase in the area, one of the biggest on the whole coast, is at Dhamra "
    "port about 15 km to the north. Whether its glow is visible from the island at hatchling eye level can only be "
    "checked on the beach at night.", base))

s.append(Paragraph("4. Devi: little change", h3))
s.append(Paragraph("The Devi river-mouth stretch brightened about as slowly as unlit countryside (78th of 99).", base))

s.append(Paragraph("5. Nesting season: no turtle-specific signal", h3))
s.append(Paragraph(
    "In some places the nesting months (February–May) brightened faster than the rest of the year, but the same "
    "pattern appears along more than half the coast, so it is probably regional (for example seasonal fires or haze) "
    "rather than linked to the beaches.", base))

s.append(Paragraph("A check that changed the result", h3))
s.append(Paragraph(
    "In the raw data even empty sea 100 km offshore appeared to get brighter, in step with the beaches. That drift "
    "belongs to the satellite product, not the coast. Without removing it, every nesting beach would have looked "
    "3–5 times brighter than in 2014. A second, independent NOAA product gives almost the same ranking of the coast. (Chart: see the project repository.)", base))

s.append(Paragraph("What this data can't see", h2))
for t in [
    "<b>Blue and white LED light.</b> The sensor barely sees wavelengths below ~500 nm, where white LEDs emit much of "
    "their light and where turtles are most sensitive. A switch to LEDs can make a place look dimmer from space while "
    "it gets brighter for hatchlings.",
    "<b>Horizon glow.</b> Hatchlings respond to glow along the horizon; the satellite measures light escaping upwards. "
    "Shielding, direction and lamp height are invisible.",
    "<b>Fine detail.</b> One pixel is about 460 m across, wider than the beach itself, and light blurs between pixels.",
    "<b>One snapshot a night</b>, at about 01:30 local time. Lights switched off earlier are missed.",
    "<b>No hatchling data.</b> Nothing here measures disorientation or deaths; radiance is a proxy, not a measure of harm.",
    "<b>Cloud.</b> The June–September monsoon leaves few clear nights.",
]:
    s.append(B(t))

s.append(Paragraph("Questions worth asking", h2))
for t in [
    "During hatching nights, is light from the industrial site and roads south-west of Rushikulya visible from the "
    "nesting beach, and does it affect hatchling orientation?",
    "Is the glow from Dhamra port visible from Abdul Kalam Island at hatchling eye level?",
    "Would simple ground measurements of horizon brightness during the hatching season be feasible for local teams?",
    "Are turtle-friendly lighting measures (shielding, long-wavelength lamps, lights off during emergence) already "
    "in place near these beaches, and could satellite monitoring help track them each year?",
]:
    s.append(B(t))

s.append(Paragraph("How this was done", h2))
s.append(Paragraph(
    "Monthly night-light averages (2014–2025) were measured for circles around each nesting beach and for the whole "
    "coast cut into 99 stretches of 5 km. Cloudy months were dropped, and the level measured over empty sea was "
    "subtracted each month. A trend counts only if it is consistent over the years (Mann–Kendall test) <i>and</i> "
    "larger than trends seen in 30 empty-sea locations (the noise floor). Results were checked with three circle sizes, "
    "NOAA's independent annual product (rank agreement 0.96), and daytime satellite images. Only the three widely "
    "published mass-nesting beaches are used, at about 1 km precision; no new nest locations are added. "
    "Code, full method and limitations: github.com/siddhantjacob/turtle-light-watch.", base))

s.append(Paragraph("Data and credits", h2))
s.append(Paragraph(
    "Night lights: VIIRS Day/Night Band monthly and annual composites, Earth Observation Group, Payne Institute for "
    "Public Policy, Colorado School of Mines (Elvidge et al. 2017, 2021), via Google Earth Engine. Land/water: MODIS "
    "MOD44W (NASA LP DAAC). Coastline: US Department of State LSIB. Daytime images: contains modified Copernicus "
    "Sentinel-2 data (2025). Land cover: Dynamic World, Google and World Resources Institute (CC BY 4.0). "
    "Background studies: Karnad et al. (2009) <i>Biological Conservation</i> 142; Behera et al. (2016) <i>Indian "
    "Journal of Geo-Marine Sciences</i> 45(2); Kyba et al. (2023) <i>Science</i> 379; Hu et al. (2018) "
    "<i>Environmental Pollution</i> 239.", small))
s.append(Spacer(1, 6))
s.append(Paragraph(
    "Findings describe changes in night-time light measured from space. They are not allegations against any "
    "facility, company or authority, and they do not measure harm to turtles.", small))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(18 * mm, 10 * mm, "Dark Skies for Hatchlings · Siddhant Jacob · VIIRS night lights, NOAA/EOG")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=15 * mm, bottomMargin=16 * mm,
                        title="Are Odisha's turtle nesting beaches getting brighter at night?", author="Siddhant Jacob")
doc.build(s, onFirstPage=footer, onLaterPages=footer)
print(f"Saved {OUT}")
