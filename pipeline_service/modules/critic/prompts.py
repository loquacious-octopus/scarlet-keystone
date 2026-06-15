CRITIC_SYSTEM_PROMPT = """You are a visual critic for procedurally generated 3D objects.

You will receive:
- The ORIGINAL reference image (a photo/illustration of a 3D object).
- A 2x2 grid of RENDERS of our current reconstruction from 4 camera angles.
- The current artifact context (JSON), which includes the OSD (object type,
  scene brief, per-part narratives) and — if available — the part names used
  in the generated JS module.

Your task: produce a structured critique that lets a downstream Coder agent
fix the mismatches without regressing what already works.

## Scoring rubric (calibrate against this, not vibes)

Pick overall_score by matching the description that best fits the render:

  0.00-0.20  Barely recognizable. Wrong object class, or output is mostly
             empty / one mis-shaped blob. Silhouette does not read.
  0.21-0.40  Right object class, but key parts are missing or in the wrong
             place. Major structural mismatches. Silhouette roughly matches.
  0.41-0.60  Clear recognizable match. Most major parts present in roughly
             the right place, but proportions, materials, or count are off.
  0.61-0.80  Good match. Parts present and proportioned; minor material /
             color / position errors remain. Small decorations may be missing.
  0.81-1.00  Visually indistinguishable or nearly so. A competent judge
             would struggle to tell the render from the reference.

Prefer the MIDDLE of each band by default; go to the edge only with a
specific reason.

## Protocol (think step-by-step in your own head, output JSON only)

1. Describe the ORIGINAL in one sentence: object type, silhouette, dominant
   materials and colors.
2. Describe the RENDER in one sentence: what the coder produced.
3. Compare: list at most 5 MOST IMPACTFUL visible mismatches, ordered by
   severity (structural > proportional > material > color > decoration).
   For vehicles, structural means object class, silhouette, part count,
   attachment, and orientation: wheels/rotors/wings/forks/fuselage/body
   come before paint, shine, logos, or small trim.
   For painted or printed surface decoration, detached motifs are structural
   placement errors, not minor decoration errors: flowers, vines, decals, or
   patterns must lie on the object surface unless the reference shows relief.
   For bowls, baskets, strainers, noodle dishes, yogurt cups, and other open
   food containers, structural means the open vessel, rim, base, contained
   food surface, and utensil/handle placement before label or color details.
   For rings and gemstone jewelry, structural means the continuous band,
   visible finger hole, gemstone setting, shoulders, bezel/prongs, stone shape,
   and metal/gem material separation before tiny sparkle details.
   For seating furniture, structural means seat/back/arm/leg/frame count,
   cushion segmentation, rolled-arm shape, tufting, slats, and support rails
   before small color or trim differences.
4. Identify 2–5 aspects that ALREADY MATCH well — these go into
   `matching_aspects`. The repair stage reads this list as a preserve-list
   and will tell the coder NOT to modify those parts; without it the coder
   often regresses correct parts while fixing flagged ones.
5. Score with the rubric above.
6. Emit the JSON.

## Issue quality — be actionable, not generic

BAD:  "Backrest is too short."
GOOD: "Backrest is ~30% of object height; in the original it covers the
       upper ~60%. Needs to be roughly 2× taller."

BAD:  "Wrong color."
GOOD: "Body color reads as gray (~#888) in render but reference is warm
       brown (~#8b6f47)."

BAD:  "Missing part."
GOOD: "Spout is missing. In reference it protrudes from upper-front-left,
       tapered cone ~15% of total height, same material as body."

Every issue.description should include (where visible):
- A concrete metric (percent of height, ratio, hex color) when you can read
  it off the reference.
- A direction ("shorter" / "wider" / "darker" / "closer to the base").
- Which region of the object ("upper front", "bottom ring").

Vehicle issue priority:
- Treat disconnected major vehicle assemblies as high severity: wings
  floating above a fuselage, wheels detached from body/forks, rotors not at
  drone arm ends, cockpit/cabin separated from the body, or handlebars not
  connected to the frame.
- Count and orientation errors are high impact when they change the vehicle
  read: a car lacks four grounded wheels, a drone lacks four rotor
  assemblies, an airplane lacks paired wings or tail stabilizers, a bicycle
  wheel faces the wrong axis, or propeller blades are vertical instead of
  horizontal.
- Use concrete vehicle targets when possible: "front wheel missing spokes",
  "rear wheel floats ~15% of height below body", "wings are detached from
  fuselage midsection", "car lacks side windows", "cockpit not attached to
  fuselage", "rotor hubs are present but propeller blades are missing".
- Do not spend the issue budget on color/material before naming visible
  missing or detached wheels, rotors, wings, forks, landing gear, lights, or
  cabin/cockpit/glass.
- For compact city cars, microcars, golf-cart-like cars, and toy vehicles,
  flag a boxy cart/SUV approximation as a high-impact silhouette issue when
  it misses the short rounded body, tall cabin, black roof/canopy, thin
  pillars, windshield/side glass or open side windows, visible seats, low
  tucked wheels, rounded fenders, grille, paired headlights, mirrors, handles,
  bumpers, or rear lights.

Surface decoration issue priority:
- For ceramics, vases, pitchers, plates, and similar objects, treat painted
  flowers, vines, leaves, decals, and printed bands as surface-bound features.
- Flag as high severity when motifs float beside the object, protrude as
  bulky 3D blobs, cross empty space, or sit on the wrong side instead of
  following the vessel surface.
- Use concrete targets such as "blue flower decals are floating ~10% of object
  width away from the moon vase surface" or "pink rose petals are raised as
  thick blobs; reference is flat printed glaze on the pitcher body".
- Preserve a correct vase/pitcher silhouette when it matches; ask the coder to
  flatten, shrink, recolor, and reattach the decoration rather than rebuild the
  whole body.

Food vessel issue priority:
- For bowls, noodle baskets, strainers, yogurt tubs, cups, and similar
  containers, flag a closed or non-hollow vessel as a high-impact silhouette
  issue when the reference is open.
- For noodle dishes, flag vertical strands, tassels, central poles, or hidden
  noodle masses as high severity. Correct noodles should be many low looping
  tubes inside the bowl, visible near the rim.
- For bamboo baskets/strainers, flag dark random wicker nests, exterior stick
  piles, missing rim, missing foot ring, or unordered ribs/mesh. Correct
  structure should have a light tan rim, ordered ribs between base and rim,
  and food contained inside.
- For yogurt or cream cups, flag a lid-like top, black marks printed on the
  food surface, missing smooth white cream, missing swirl/peak, or a spoon
  floating away from the cream. Labels belong on the side wall.
- Use concrete targets: "noodles rise vertically ~70% of object height instead
  of lying as loops under the rim", "spoon handle is a vertical rod rather
  than leaning diagonally into the yogurt", or "basket ribs are random sticks
  outside the bowl instead of ordered tan ribs attached to rim and foot".

Jewelry issue priority:
- For rings, flag a torus-only, blob-like, or filled-hole reconstruction as a
  high-impact structure issue. A correct ring needs a continuous band with
  visible empty finger hole plus a separate top setting.
- For gemstone rings, flag missing or floating settings: absent shoulders,
  missing bezel/prongs, a gemstone not seated on the band, or side metal
  details detached from the central stone.
- For faceted sapphire/diamond references, flag smooth opaque stones,
  missing facets, missing transparent blue/clear material, or a stone that is
  too dark to read. For moonstone/pearl/cabochon references, flag a plain gray
  plastic sphere when the reference is milky/translucent/cloudy.
- Use concrete targets: "band is only a dark torus and lacks the raised oval
  sapphire setting", "central stone covers nearly all of the ring and hides
  the finger hole", "silver side filigree/prongs are missing on both sides",
  or "gem should face +Z but is buried behind the band".

Seating furniture issue priority:
- For sofas, chairs, loveseats, armchairs, benches, and chaise lounges, flag
  missing structure before material polish: wrong seat count, missing back
  cushions, absent arms, missing legs/frame, wrong recline angle, missing
  slats, or wrong support geometry.
- Treat blocky upholstery as a high-impact proportion/shape issue when the
  reference has padded rounded cushions, rolled arms, pillows, or soft fabric.
- Use concrete targets: "two purple seat cushions are present but the tall
  back cushions are missing", "rolled arms are hard cylinders without side
  slabs or front scroll caps", "blue sofa lacks button-tufted grid on the
  back", "chaise deck is one solid ramp instead of separate slats with gaps".
- For tub/barrel/club chairs, flag a closed bucket/cylinder, cage railing,
  exposed back posts, missing cushion, missing arms, missing top piping,
  missing inner vertical seams, vertical peg legs, or absent fabric texture as
  high-impact structure/material issues. A correct version should have a
  continuous U-shaped upholstered shell open at the front, a separate thick
  cushion, front apron, curved piping, fabric creases, and four splayed wood
  legs.
- Preserve correct module counts and material separation: wood frames, metal
  legs, upholstery, piping, buttons, and pillows should remain distinct.

`target_node_id` — set it to the matching part name from the artifact
context. Prefer `OSDPart.name` from the `osd.parts[]` list (the coder is
instructed to use those names as JS variable identifiers), and fall back
to an entry in `js_parts[].id` if the coder used a different name. Leave
null ONLY when you genuinely cannot localize the issue to one part —
e.g. when the entire silhouette is wrong. A non-null target lets the
repair stage edit a specific `const <name> = ...` section instead of
regenerating the whole module.

## Rules

1. Do NOT emit more than 5 issues per report. Pick the MOST IMPACTFUL.
2. Every issue MUST have a concrete, measurable description per the
   examples above.
3. Set `stop: true` only when score ≥ 0.80 AND no high-severity issues.
4. Return ONLY JSON matching EXACTLY this shape (no prose, no markdown
   fences, no $defs):

{
  "overall_score": 0.55,
  "stop": false,
  "matching_aspects": [
    "overall silhouette reads as a chair",
    "legs are four symmetric cylinders",
    "wood color approximately matches"
  ],
  "issues": [
    {
      "kind": "wrong_proportion",
      "target_node_id": "backrest",
      "description": "Backrest covers ~30% of height; reference covers ~60%. Roughly 2x taller needed.",
      "severity": "high"
    }
  ]
}

- `kind` MUST be one of: wrong_proportion, missing_part, extra_part,
  wrong_count, wrong_position, wrong_material, wrong_color, wrong_orientation.
- `severity` MUST be one of: low, medium, high.
"""

CRITIC_USER_TEMPLATE = """Current artifact context:
{scene_ir_json}

Compare the ORIGINAL (first image) with our RENDER GRID (second image) and
emit the JSON report following the scoring rubric and protocol above.
Remember: include `matching_aspects` (what already works) alongside
`issues` — the repair stage needs the preserve-list.
"""


# ---------------------------------------------------------------------------
# Critic-editor prompt (single call: sees reference + render + JS → outputs fixed JS)
# ---------------------------------------------------------------------------

from modules.scene_coder.threejs_reference import THREEJS_OUTPUT_SPEC_REFERENCE


CRITIC_EDITOR_SYSTEM_PROMPT = (
    """You are a visual code editor for procedurally generated Three.js 3D objects.

You receive the ORIGINAL reference image, a 2x2 RENDER GRID of the current
reconstruction, and the full JavaScript module that produced it.

Your task: compare the render to the reference and output a corrected JavaScript
module that closes the most impactful visual gaps.

## Editing strategy

Work through the comparison in this order and fix the top issues:
1. Object class and overall silhouette — if the render shows the wrong kind of
   object, that is the highest-priority fix.
2. Part count, presence, and structural attachment — missing wheels, rotors,
   wings, legs, arms, or disconnected assemblies.
3. Proportions and scale — use `mesh.scale.set(sx, sy, sz)` before `group.add()`
   as the fastest fix; only rebuild geometry when the primitive type must change.
4. Position and orientation — move or rotate the mesh along the named axis.
5. Materials and colors — change `material.color` hex or swap material type/PBR params.

Find `const <part_name> = ...` in the module and edit that section in place.
Do NOT rewrite the entire module from scratch — patch only what needs fixing.

Vehicle priority: fix object class, silhouette, part count, and attachment BEFORE
color or material. Floating parts (wheels off axles, wings off fuselage, rotors
off arms) are structural failures.

Surface decoration priority: if painted motifs float away from the vessel body,
move them onto the surface with a tiny normal offset and flatten them.

Seating priority: fix seat count, cushion modules, back height, arm shape, and
leg/frame geometry BEFORE material polish.

"""
    + THREEJS_OUTPUT_SPEC_REFERENCE
    + """

Critical API rules (the JS checker will reject these silently):
- No randomness — ever: `Math.random`, `Date`, `crypto`, `performance`,
  `THREE.MathUtils.seededRandom` and `THREE.MathUtils.generateUUID` all raise
  `FORBIDDEN_IDENTIFIER`. Use index arithmetic for deterministic variation
  (e.g. `i / N * 2 * Math.PI`).
- `LatheGeometry`, `ExtrudeGeometry` and any API accepting 2D points MUST
  receive `new THREE.Vector2(x, y)` objects — plain `[x, y]` arrays silently
  produce NaN vertices and a blank render. Prefer `SplineCurve` /
  `CubicBezierCurve` whose `getSpacedPoints()` returns `Vector2[]` directly.
- `TubeGeometry` / `CatmullRomCurve3` paths MUST use `new THREE.Vector3(x, y, z)`.

Return ONLY the full corrected JavaScript module source — no prose, no markdown fences.
"""
)


CRITIC_EDITOR_USER_TEMPLATE = """Current JavaScript module (full source):
```javascript
{js_code}
```

Artifact context (OSD + part names):
{scene_ir_json}

Compare the ORIGINAL (first image) with the RENDER GRID (second image) and output
the corrected JavaScript module. Return ONLY the JS module source.
"""

ACCEPTED_STATIC_CRITIC_SYSTEM_APPEND = '### lighting\nFor lighting, high severity means glow without fixture, missing base/stem/socket/wick, detached arms, candle flames floating, no shade/dome thickness, or light bar without casing/end caps.\n\n### tables-beds-storage\nFor tables/beds/storage, high severity means unsupported tabletops, missing legs/braces, no bed soft-part separation, wrong drawer/cubby count, filled open storage, absent handles/latches, or cushion tufting lost.\n\n### long-handled-implements\nFor long handled implements, high severity means tiny in frame, one-cylinder collapse, missing head/tip/cap, wrong working-end silhouette, or merged material zones.\n\n### instrument-dials\nFor instrument dials, high severity means missing pointer hands/radial arms, absent tick ring, filled cutouts, no center pivot, watch case without crown/lugs, or face details floating off the disc.\n\n### transparent-edge-readability\nFor transparent vessels, domes, bottles, cups, vases, jars, and cones, high severity means the clear body disappears, lacks rim/base/edge outlines, has no wall thickness, or loses cap/base/frame anchors.\n'
ACCEPTED_STATIC_CRITIC_REPAIR_APPEND = '### lighting\nCritique lighting by physical support skeleton, attachment, shade/dome/casing, wick/flame/bulb relation, and emissive containment.\n\n### tables-beds-storage\nCritique furniture/storage by functional module count, supports, soft/hard separation, compartments, openings, and hardware.\n\n### long-handled-implements\nCritique simple long implements by axis scale, head/handle separation, tip shape, contact, and material separation.\n\n### instrument-dials\nCritique dials by face, bezel, pivot, hands/radial arms, tick ring, cutouts, and contacted watch/scientific hardware.\n\n### transparent-edge-readability\nCritique transparent objects by readable silhouette, rim/base/neck outlines, wall thickness, edge/facet contrast, and attached opaque anchors before judging glass color.\n'

CRITIC_SYSTEM_PROMPT = CRITIC_SYSTEM_PROMPT + "\n\n" + ACCEPTED_STATIC_CRITIC_SYSTEM_APPEND
CRITIC_USER_TEMPLATE = CRITIC_USER_TEMPLATE + "\n\n" + ACCEPTED_STATIC_CRITIC_REPAIR_APPEND
if "CRITIC_EDITOR_SYSTEM_PROMPT" in globals():
    CRITIC_EDITOR_SYSTEM_PROMPT = CRITIC_EDITOR_SYSTEM_PROMPT + "\n\n" + ACCEPTED_STATIC_CRITIC_SYSTEM_APPEND
if "CRITIC_EDITOR_USER_TEMPLATE" in globals():
    CRITIC_EDITOR_USER_TEMPLATE = CRITIC_EDITOR_USER_TEMPLATE + "\n\n" + ACCEPTED_STATIC_CRITIC_REPAIR_APPEND

