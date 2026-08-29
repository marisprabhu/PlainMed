const pptxgen = require("pptxgenjs");

const NAVY="16324F", TEAL="0F766E", MINT="2DD4BF",
      OFFW="F8FAFC", WHITE="FFFFFF", AMBER="D97706", SLATE="64748B",
      LSLATE="94A3B8", BORDER="E2E8F0", RED="B91C1C";

const HFONT="Cambria", BFONT="Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "PlainMed";
pres.title = "PlainMed - Pitch Deck";

const sh = () => ({ type:"outer", color:"0A1622", blur:12, offset:2, angle:90, opacity:0.18 });

// source-chip motif: the product's core promise, repeated as a visual signature
function chip(s, x, y, label, opt) {
  opt = opt || {};
  const w = 0.44;
  s.addShape(pres.ShapeType.roundRect, { x:x, y:y, w:w, h:0.26, rectRadius:0.06,
    fill:{ color: opt.fill || TEAL }, line:{ color: opt.fill || TEAL, width:0.5 } });
  s.addText(label, { x:x, y:y, w:w, h:0.26, isTextBox:true, margin:0, align:"center",
    fontFace:BFONT, fontSize:10, bold:true, color: opt.color || WHITE });
}

function title(s, txt, kicker, dark) {
  if (kicker) s.addText(kicker.toUpperCase(), { x:0.72, y:0.5, w:11.9, h:0.3, isTextBox:true,
    margin:0, fontFace:BFONT, fontSize:12, bold:true, charSpacing:2,
    color: dark ? MINT : TEAL });
  s.addText(txt, { x:0.72, y:0.88, w:11.9, h:0.72, isTextBox:true, margin:0,
    fontFace:HFONT, fontSize:34, bold:true, color: dark ? WHITE : NAVY });
}

function card(s, x, y, w, h, opt) {
  opt = opt || {};
  s.addShape(pres.ShapeType.roundRect, { x:x, y:y, w:w, h:h, rectRadius:0.04,
    fill:{ color: opt.fill || WHITE },
    line:{ color: opt.line || BORDER, width:1 }, shadow: opt.flat ? undefined : sh() });
}

/* ---------------------------------------------------------------- 1 TITLE */
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addShape(pres.ShapeType.ellipse, { x:9.6, y:-1.5, w:5.6, h:5.6,
    fill:{ color: TEAL, transparency:78 }, line:{ color:TEAL, width:0 } });
  s.addShape(pres.ShapeType.ellipse, { x:11.0, y:4.4, w:3.4, h:3.4,
    fill:{ color: MINT, transparency:88 }, line:{ color:MINT, width:0 } });

  s.addText("PlainMed", { x:0.9, y:2.15, w:8.4, h:1.3, isTextBox:true, margin:0,
    fontFace:HFONT, fontSize:62, bold:true, color:WHITE });
  s.addText("Clear reports. Private by design.", { x:0.9, y:3.42, w:8.4, h:0.5,
    isTextBox:true, margin:0, fontFace:BFONT, fontSize:22, color:MINT });
  s.addText("An offline medical-report explanation assistant. Every sentence links back to the line of your report that supports it — and nothing leaves your device.",
    { x:0.9, y:4.08, w:7.9, h:0.9, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:14, color:LSLATE, lineSpacing:20 });

  ["S1","S3","S7"].forEach(function(c,i){ chip(s, 0.9 + i*0.58, 5.22, c, { fill:MINT, color:NAVY }); });
  s.addText("source-linked by construction", { x:2.7, y:5.22, w:4.4, h:0.26,
    isTextBox:true, margin:0, fontFace:BFONT, fontSize:11, italic:true, color:LSLATE });

  s.addText("Research prototype — explains report content; does not diagnose or recommend treatment.",
    { x:0.9, y:6.55, w:11.5, h:0.3, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:11, color:LSLATE });
  s.addNotes("PlainMed turns confusing medical reports into clear, source-linked explanations using an open model running locally. Demo headline: disconnect the internet, understand the report.");
}

/* -------------------------------------------------------------- 2 PROBLEM */
{
  const s = pres.addSlide();
  s.background = { color: OFFW };
  title(s, "A patient holding a lab report has two bad options", "The problem", false);

  const opts = [
    { t:"Search the web", d:"Results strip away the context of this report — this value, this range, this lab. The worst-case reading wins the click.", ic:"?" },
    { t:"Upload to a cloud AI", d:"The most sensitive document a person owns leaves their device, gets cached, and may be retained or indexed.", ic:"!" }
  ];
  opts.forEach(function(o,i){
    const x = 0.72 + i*4.05;
    card(s, x, 2.15, 3.72, 3.1);
    s.addShape(pres.ShapeType.ellipse, { x:x+0.28, y:2.45, w:0.52, h:0.52,
      fill:{ color: AMBER }, line:{ color:AMBER, width:0 } });
    s.addText(o.ic, { x:x+0.28, y:2.45, w:0.52, h:0.52, isTextBox:true, margin:0,
      align:"center", fontFace:BFONT, fontSize:21, bold:true, color:WHITE });
    s.addText(o.t, { x:x+0.28, y:3.18, w:3.16, h:0.36, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:18, bold:true, color:NAVY });
    s.addText(o.d, { x:x+0.28, y:3.62, w:3.16, h:1.4, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:13, color:SLATE, lineSpacing:19 });
  });

  card(s, 8.9, 2.15, 3.72, 3.1, { fill:NAVY, line:NAVY });
  s.addText("Neither option can do the one thing that matters:", { x:9.18, y:2.45, w:3.2, h:0.95,
    isTextBox:true, margin:0, fontFace:BFONT, fontSize:14.5, color:LSLATE, lineSpacing:20 });
  s.addText("show its source", { x:9.18, y:3.5, w:3.2, h:0.46, isTextBox:true, margin:0,
    fontFace:HFONT, fontSize:22, bold:true, color:MINT });
  s.addText("You cannot check an answer you cannot trace.", { x:9.18, y:4.08, w:3.2, h:0.7,
    isTextBox:true, margin:0, fontFace:BFONT, fontSize:12.5, color:LSLATE, lineSpacing:17 });

  s.addText("The result: patients arrive at appointments anxious about the wrong things, and without the questions that would actually help them.",
    { x:0.72, y:5.75, w:11.9, h:0.5, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:15, italic:true, color:NAVY });
  s.addNotes("Patients receive reports with unfamiliar terminology, numbers and abbreviations. Searching online removes context; uploading to cloud services introduces privacy concerns.");
}

/* -------------------------------------------------------------- 3 PRODUCT */
{
  const s = pres.addSlide();
  s.background = { color: OFFW };
  title(s, "One screen. Report on the left, plain language on the right.", "The product", false);

  card(s, 0.72, 2.25, 5.5, 3.6);
  s.addText("Original report", { x:1.0, y:2.42, w:3.0, h:0.3, isTextBox:true, margin:0,
    fontFace:BFONT, fontSize:12, bold:true, color:SLATE });
  const lines = [
    ["S3","Glucose 108 mg/dL 70-99 High"],
    ["S4","Sodium 140 mmol/L 135-145"],
    ["S5","Potassium 3.3 mmol/L 3.5-5.1 L"],
    ["S6","Chloride 102 mmol/L 98-107"]
  ];
  lines.forEach(function(l,i){
    const y = 2.85 + i*0.46;
    chip(s, 1.0, y, l[0]);
    s.addShape(pres.ShapeType.roundRect, { x:1.56, y:y, w:4.4, h:0.26, rectRadius:0.03,
      fill:{ color:"CCFBF1" }, line:{ color:"CCFBF1", width:0 } });
    s.addText(l[1], { x:1.62, y:y, w:4.3, h:0.26, isTextBox:true, margin:0,
      fontFace:"Courier New", fontSize:10, color:NAVY });
  });
  s.addText("Highlighted = read as a result. Anything PlainMed could not read is shown too, never dropped.",
    { x:1.0, y:4.95, w:4.96, h:0.6, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:10.5, italic:true, color:SLATE, lineSpacing:14 });

  card(s, 6.55, 2.25, 6.07, 3.6, { fill:WHITE });
  s.addText("Plain-language explanation", { x:6.83, y:2.42, w:4.0, h:0.3, isTextBox:true,
    margin:0, fontFace:BFONT, fontSize:12, bold:true, color:SLATE });

  card(s, 6.83, 2.82, 5.5, 1.18, { fill:"F0FDFA", line:TEAL, flat:true });
  s.addText("Glucose", { x:7.05, y:2.94, w:2.0, h:0.28, isTextBox:true, margin:0,
    fontFace:BFONT, fontSize:13, bold:true, color:NAVY });
  s.addShape(pres.ShapeType.roundRect, { x:8.35, y:2.95, w:1.85, h:0.26, rectRadius:0.06,
    fill:{ color:"FEF3C7" }, line:{ color:"FEF3C7", width:0 } });
  s.addText("Marked high", { x:8.35, y:2.95, w:1.85, h:0.26, isTextBox:true, margin:0,
    align:"center", fontFace:BFONT, fontSize:9.5, bold:true, color:"92400E" });
  s.addText("Your report lists Glucose as 108 mg/dL. The reference range listed next to it is 70-99.",
    { x:7.05, y:3.27, w:5.06, h:0.44, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:11, color:NAVY, lineSpacing:14 });
  s.addText("Sources: S3", { x:7.05, y:3.7, w:2.0, h:0.22, isTextBox:true, margin:0,
    fontFace:BFONT, fontSize:9.5, color:TEAL });

  card(s, 6.83, 4.12, 5.5, 1.42, { fill:WHITE, line:BORDER, flat:true });
  s.addText("What Glucose means", { x:7.05, y:4.26, w:4.0, h:0.28, isTextBox:true, margin:0,
    fontFace:BFONT, fontSize:13, bold:true, color:NAVY });
  s.addText("Glucose is the main sugar the body uses for energy. This test measures the amount in the blood at the time the sample was taken.",
    { x:7.05, y:4.58, w:5.06, h:0.58, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:11, color:SLATE, lineSpacing:14 });
  s.addText("Source: PlainMed local glossary — not your report", { x:7.05, y:5.2, w:4.8, h:0.24,
    isTextBox:true, margin:0, fontFace:BFONT, fontSize:9.5, bold:true, color:AMBER });

  const feats = ["Extraction you confirm before anything is explained",
                 "Questions to take to your clinician",
                 "A two-question understanding check",
                 "Clear session wipes the report"];
  feats.forEach(function(f,i){
    const x = 0.72 + i*3.06;
    s.addShape(pres.ShapeType.ellipse, { x:x, y:6.24, w:0.2, h:0.2,
      fill:{ color:TEAL }, line:{ color:TEAL, width:0 } });
    s.addText(f, { x:x+0.3, y:6.16, w:2.66, h:0.6, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:11, color:NAVY, lineSpacing:14 });
  });
  s.addNotes("Left: original report with highlighted source passages. Right: cards for findings, terminology and information not specified. Bottom: comprehension questions and questions for the clinician.");
}

/* ------------------------------------------------------- 4 DIFFERENTIATOR */
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  title(s, "The distinction nobody else draws", "Why it is trustworthy", true);
  s.addText("A report may name a test without defining it. PlainMed never lets an added explanation borrow the report's authority.",
    { x:0.72, y:1.74, w:11.5, h:0.4, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:14, color:LSLATE });

  const cards = [
    { h:"“Your report says…”", c:MINT, b:"Supported by the uploaded document. Carries source IDs. Every number is checked against the cited line.", tag:"Sources: S3" },
    { h:"“What this term means…”", c:"CBD5E1", b:"From a small, local, reviewed glossary of 40 blood tests. Carries no source IDs, and says so on the card.", tag:"Source: local glossary" },
    { h:"“Not specified…”", c:"FCD34D", b:"The report does not answer this. PlainMed says so plainly instead of filling the gap with a plausible guess.", tag:"Becomes a question for your clinician" }
  ];
  cards.forEach(function(c,i){
    const x = 0.72 + i*4.03;
    s.addShape(pres.ShapeType.roundRect, { x:x, y:2.42, w:3.7, h:3.15, rectRadius:0.05,
      fill:{ color:"1E4160" }, line:{ color:"2A5578", width:1 } });
    s.addText(c.h, { x:x+0.3, y:2.72, w:3.14, h:0.7, isTextBox:true, margin:0,
      fontFace:HFONT, fontSize:17.5, bold:true, color:c.c, lineSpacing:22 });
    s.addText(c.b, { x:x+0.3, y:3.56, w:3.14, h:1.25, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:12.5, color:"CBD5E1", lineSpacing:17 });
    s.addText(c.tag, { x:x+0.3, y:4.98, w:3.14, h:0.36, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:10, bold:true, color:c.c });
  });

  s.addText("Source links alone do not prove an explanation is correct — so PlainMed also checks that each statement actually follows from the line it cites.",
    { x:0.72, y:6.05, w:11.7, h:0.5, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:14, italic:true, color:MINT });
  s.addNotes("Separate clearly in the interface: what the report says versus what a term means. Labels like 'Marked high in your report', never 'Dangerous'. Being inside a reference range is never equated with being healthy.");
}

/* --------------------------------------------------------- 5 ARCHITECTURE */
{
  const s = pres.addSlide();
  s.background = { color: OFFW };
  title(s, "Deterministic core, model on the side", "Architecture", false);
  s.addText("Numbers are never parsed by a language model. Extraction, findings, gaps and questions are pure Python — reproducible and unit-tested.",
    { x:0.72, y:1.72, w:11.7, h:0.4, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:13.5, color:SLATE });

  const steps = [
    { n:"1", t:"Ingest", d:"Paste or text-PDF\npypdf · scans rejected" },
    { n:"2", t:"Extract", d:"Values, units, ranges,\nflags + stable source IDs" },
    { n:"3", t:"Explain", d:"Report / glossary / gap\ncards from parsed data" },
    { n:"4", t:"Validate", d:"Citation · number · claim\nchecks on every sentence" },
    { n:"5", t:"Present", d:"Cards, clinician questions,\nunderstanding check" }
  ];
  steps.forEach(function(st,i){
    const x = 0.72 + i*2.42;
    card(s, x, 2.35, 2.2, 2.0);
    s.addShape(pres.ShapeType.ellipse, { x:x+0.22, y:2.57, w:0.42, h:0.42,
      fill:{ color:TEAL }, line:{ color:TEAL, width:0 } });
    s.addText(st.n, { x:x+0.22, y:2.57, w:0.42, h:0.42, isTextBox:true, margin:0,
      align:"center", fontFace:BFONT, fontSize:14, bold:true, color:WHITE });
    s.addText(st.t, { x:x+0.74, y:2.61, w:1.4, h:0.34, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:15, bold:true, color:NAVY });
    s.addText(st.d, { x:x+0.22, y:3.2, w:1.9, h:0.95, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:10.5, color:SLATE, lineSpacing:14 });
    if (i<4) s.addText("→", { x:x+2.2, y:3.15, w:0.22, h:0.4, isTextBox:true, margin:0,
      align:"center", fontFace:BFONT, fontSize:17, bold:true, color:TEAL });
  });

  card(s, 0.72, 4.68, 6.1, 1.95, { fill:WHITE });
  s.addText("Narrative backend — pluggable", { x:1.0, y:4.86, w:4.5, h:0.3, isTextBox:true,
    margin:0, fontFace:BFONT, fontSize:12.5, bold:true, color:NAVY });
  s.addShape(pres.ShapeType.roundRect, { x:1.0, y:5.28, w:2.6, h:1.02, rectRadius:0.05,
    fill:{ color:"F0FDFA" }, line:{ color:TEAL, width:1 } });
  s.addText("Deterministic\ntemplate engine", { x:1.02, y:5.38, w:2.56, h:0.5, isTextBox:true,
    margin:0, align:"center", fontFace:BFONT, fontSize:11.5, bold:true, color:TEAL, lineSpacing:15 });
  s.addText("default · no GPU", { x:1.02, y:5.92, w:2.56, h:0.24, isTextBox:true, margin:0,
    align:"center", fontFace:BFONT, fontSize:9.5, color:SLATE });
  s.addShape(pres.ShapeType.roundRect, { x:3.85, y:5.28, w:2.6, h:1.02, rectRadius:0.05,
    fill:{ color:"F0FDFA" }, line:{ color:TEAL, width:1 } });
  s.addText("MedGemma 1.5 4B\nlocal inference", { x:3.87, y:5.38, w:2.56, h:0.5, isTextBox:true,
    margin:0, align:"center", fontFace:BFONT, fontSize:11.5, bold:true, color:TEAL, lineSpacing:15 });
  s.addText("optional · NVIDIA CUDA", { x:3.87, y:5.92, w:2.56, h:0.24, isTextBox:true, margin:0,
    align:"center", fontFace:BFONT, fontSize:9.5, color:SLATE });

  card(s, 7.05, 4.68, 5.57, 1.95, { fill:NAVY, line:NAVY });
  s.addText("Both backends pass the same validator.", { x:7.33, y:4.88, w:5.05, h:0.32,
    isTextBox:true, margin:0, fontFace:BFONT, fontSize:14, bold:true, color:MINT });
  s.addText("The model can add fluency. It cannot add facts. If it is missing, fails to load, or its output fails validation, PlainMed degrades to the deterministic summary and tells the user which backend produced what they are reading.",
    { x:7.33, y:5.3, w:5.05, h:1.2, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:11.5, color:LSLATE, lineSpacing:16 });
  s.addNotes("This is the deliberate change from the original plan: the deterministic engine is the core and the model is an optional enhancement, so the app is useful and safe on any machine.");
}

/* ------------------------------------------------------------ 6 VALIDATOR */
{
  const s = pres.addSlide();
  s.background = { color: OFFW };
  title(s, "Three gates every sentence must pass", "The validation layer", false);
  s.addText("Applied identically to template output and model output. A statement that fails is removed and reported — never silently shown.",
    { x:0.72, y:1.72, w:11.7, h:0.4, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:13.5, color:SLATE });

  const gates = [
    { t:"Citation exists", d:"Every cited source ID must resolve to a real line in this document." },
    { t:"Numbers match", d:"Every number in the sentence must appear in the cited line, compared as decimals — 13.5 matches 13.50, never 13.6." },
    { t:"No forbidden claim", d:"Diagnosis, treatment advice and reassurance are rejected — unless the report itself says it." }
  ];
  gates.forEach(function(g,i){
    const x = 0.72 + i*4.03;
    card(s, x, 2.35, 3.7, 1.85);
    s.addShape(pres.ShapeType.ellipse, { x:x+0.28, y:2.58, w:0.4, h:0.4,
      fill:{ color:TEAL }, line:{ color:TEAL, width:0 } });
    s.addText(String(i+1), { x:x+0.28, y:2.58, w:0.4, h:0.4, isTextBox:true, margin:0,
      align:"center", fontFace:BFONT, fontSize:13, bold:true, color:WHITE });
    s.addText(g.t, { x:x+0.78, y:2.61, w:2.8, h:0.34, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:15, bold:true, color:NAVY });
    s.addText(g.d, { x:x+0.28, y:3.14, w:3.16, h:0.92, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:11.5, color:SLATE, lineSpacing:16 });
  });

  s.addText("What that rejects, in practice", { x:0.72, y:4.45, w:6.0, h:0.34, isTextBox:true,
    margin:0, fontFace:BFONT, fontSize:14, bold:true, color:NAVY });

  const rows = [
    { bad:"“Your hemoglobin is 14.2 g/dL.”", why:"report says 13.5 — number absent from cited line", code:"number_mismatch" },
    { bad:"“Your Glucose of 108 means you have diabetes.”", why:"diagnostic claim", code:"forbidden_claim" },
    { bad:"“Nothing to worry about here.”", why:"reassurance PlainMed is not entitled to give", code:"forbidden_claim" }
  ];
  rows.forEach(function(r,i){
    const y = 4.92 + i*0.64;
    card(s, 0.72, y, 11.9, 0.54, { fill:WHITE, flat:true });
    s.addText("✕", { x:0.88, y:y, w:0.3, h:0.54, isTextBox:true, margin:0, align:"center",
      valign:"middle", fontFace:BFONT, fontSize:12, bold:true, color:RED });
    s.addText(r.bad, { x:1.28, y:y, w:4.6, h:0.54, isTextBox:true, margin:0, valign:"middle",
      fontFace:BFONT, fontSize:12, bold:true, color:NAVY });
    s.addText(r.why, { x:6.0, y:y, w:4.3, h:0.54, isTextBox:true, margin:0, valign:"middle",
      fontFace:BFONT, fontSize:11.5, color:SLATE });
    s.addText(r.code, { x:10.4, y:y, w:2.05, h:0.54, isTextBox:true, margin:0, valign:"middle",
      align:"right", fontFace:"Courier New", fontSize:10.5, color:TEAL });
  });
  s.addNotes("Report text is untrusted data and model output is untrusted until validated. Instructions embedded in a report cannot change application behaviour - covered by a test.");
}

/* -------------------------------------------------------------- 7 OFFLINE */
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  title(s, "Offline is a property we test, not a promise we make", "Privacy", true);

  const rows = [
    ["No inference leaves the device", "Weights loaded local-files-only; HF_HUB_OFFLINE forced before import"],
    ["No telemetry", "Usage stats disabled; no analytics, no external fonts or assets"],
    ["Local access only", "Server bound to 127.0.0.1"],
    ["No report persistence", "Session memory only; Clear session wipes it; report text never logged"],
    ["Verified, not assumed", "offline_check.py blocks socket creation, then runs all 5 samples end to end"]
  ];
  rows.forEach(function(r,i){
    const y = 2.08 + i*0.79;
    s.addShape(pres.ShapeType.roundRect, { x:0.72, y:y, w:11.9, h:0.66, rectRadius:0.04,
      fill:{ color: i===4 ? "115E52" : "1E4160" }, line:{ color: i===4 ? MINT : "2A5578", width:1 } });
    s.addText("✓", { x:0.95, y:y, w:0.34, h:0.66, isTextBox:true, margin:0, align:"center",
      valign:"middle", fontFace:BFONT, fontSize:14, bold:true, color:MINT });
    s.addText(r[0], { x:1.38, y:y, w:3.9, h:0.66, isTextBox:true, margin:0, valign:"middle",
      fontFace:BFONT, fontSize:13.5, bold:true, color:WHITE });
    s.addText(r[1], { x:5.35, y:y, w:7.0, h:0.66, isTextBox:true, margin:0, valign:"middle",
      fontFace:BFONT, fontSize:11.5, color:"CBD5E1" });
  });

  s.addText("Offline processing reduces transmission risk. It does not by itself secure the device or guarantee memory is scrubbed — and we say so in the product.",
    { x:0.72, y:6.28, w:11.9, h:0.5, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:12.5, italic:true, color:LSLATE });
  s.addNotes("Demo moment: disconnect the network in front of the audience, then run a full report through the app.");
}

/* ------------------------------------------------------------- 8 EVIDENCE */
{
  const s = pres.addSlide();
  s.background = { color: OFFW };
  title(s, "What is actually verified today", "Evidence", false);

  const stats = [
    { v:"42", l:"tests passing", s:"parser, validation,\nend-to-end, injection" },
    { v:"0.9 ms", l:"median end-to-end", s:"p95 1.2 ms, CPU only\n100 runs, 5 reports" },
    { v:"5 / 5", l:"samples pass offline", s:"sockets blocked,\n0 validation errors" },
    { v:"40", l:"glossary terms", s:"local, reviewed,\nversioned in git" }
  ];
  stats.forEach(function(st,i){
    const x = 0.72 + i*3.02;
    card(s, x, 2.1, 2.72, 1.95);
    s.addText(st.v, { x:x+0.22, y:2.24, w:2.4, h:0.68, isTextBox:true, margin:0,
      fontFace:HFONT, fontSize:32, bold:true, color:TEAL });
    s.addText(st.l, { x:x+0.22, y:2.94, w:2.4, h:0.3, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:12.5, bold:true, color:NAVY });
    s.addText(st.s, { x:x+0.22, y:3.26, w:2.4, h:0.62, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:10, color:SLATE, lineSpacing:13 });
  });

  s.addChart(pres.ChartType.bar, [
    { name:"Values extracted", labels:["CBC","Metabolic","Lipid","Thyroid/Iron","Liver"], values:[6,7,4,5,7] },
    { name:"Explanation cards", labels:["CBC","Metabolic","Lipid","Thyroid/Iron","Liver"], values:[13,15,13,12,15] }
  ], { x:0.72, y:4.3, w:7.1, h:2.42, barDir:"col", barGrouping:"clustered",
    showTitle:true, title:"Coverage across the 5 synthetic reports", titleFontSize:12,
    titleColor:NAVY, titleFontFace:BFONT,
    chartColors:[TEAL, "9AD4C8"], showValue:true, dataLabelPosition:"outEnd",
    dataLabelFontSize:9, dataLabelColor:SLATE, dataLabelFontFace:BFONT,
    catAxisLabelColor:SLATE, valAxisLabelColor:SLATE, catAxisLabelFontSize:10,
    valAxisLabelFontSize:9, catAxisLabelFontFace:BFONT, valAxisLabelFontFace:BFONT,
    valGridLine:{ color:BORDER, size:1 }, catGridLine:{ style:"none" },
    showLegend:true, legendPos:"b", legendFontSize:10, legendColor:SLATE });

  card(s, 8.05, 4.3, 4.57, 2.42, { fill:WHITE, line:AMBER });
  s.addText("Not yet measured", { x:8.33, y:4.44, w:4.0, h:0.32, isTextBox:true, margin:0,
    fontFace:BFONT, fontSize:13.5, bold:true, color:AMBER });
  s.addText("The MedGemma path is implemented but has never run on real weights — no CUDA device on the build machine.",
    { x:8.33, y:4.8, w:4.05, h:0.7, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:11.5, color:SLATE, lineSpacing:15 });
  ["Model latency per report:  ____","Peak GPU memory:  ____ GB","Statements rejected:  ____ %"].forEach(function(t,i){
    s.addText(t, { x:8.33, y:5.52+i*0.3, w:4.05, h:0.28, isTextBox:true, margin:0,
      fontFace:"Courier New", fontSize:10.5, color:NAVY });
  });
  s.addText("Fill these from your first GPU run — do not ship estimates.",
    { x:8.33, y:6.42, w:4.05, h:0.26, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:10, italic:true, color:AMBER });
  s.addNotes("Publish failures as well as successes. Synthetic tests demonstrate engineering behaviour, not clinical safety or improved patient outcomes.");
}

/* ------------------------------------------------------------------ 9 GPU */
{
  const s = pres.addSlide();
  s.background = { color: OFFW };
  title(s, "What the GPU buys — and what it must never buy", "The NVIDIA story", false);

  card(s, 0.72, 2.05, 5.9, 2.6, { fill:WHITE, line:TEAL });
  s.addText("What local GPU inference unlocks", { x:1.0, y:2.24, w:5.2, h:0.32, isTextBox:true,
    margin:0, fontFace:BFONT, fontSize:14, bold:true, color:TEAL });
  [ "Fluent summaries pitched at the patient's reading level",
    "Free-text sections — impressions, comments — not just tables",
    "Report layouts the deterministic parser cannot read today",
    "All of it without a single byte leaving the device" ].forEach(function(t,i){
    s.addShape(pres.ShapeType.ellipse, { x:1.02, y:2.83+i*0.43, w:0.16, h:0.16,
      fill:{ color:TEAL }, line:{ color:TEAL, width:0 } });
    s.addText(t, { x:1.3, y:2.74+i*0.43, w:5.15, h:0.34, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:12, color:NAVY });
  });

  card(s, 6.9, 2.05, 5.72, 2.6, { fill:NAVY, line:NAVY });
  s.addText("What it must never buy", { x:7.18, y:2.24, w:5.0, h:0.32, isTextBox:true,
    margin:0, fontFace:BFONT, fontSize:14, bold:true, color:"FCD34D" });
  s.addText("A GPU makes wrong answers arrive faster and read more convincingly. That is why the validator sits after the model rather than before it, and why the deterministic path is the floor rather than a fallback of last resort.",
    { x:7.18, y:2.68, w:5.2, h:1.2, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:12.5, color:"CBD5E1", lineSpacing:17 });
  s.addText("Fluency is not evidence.", { x:7.18, y:4.02, w:5.2, h:0.36, isTextBox:true,
    margin:0, fontFace:HFONT, fontSize:16, bold:true, color:MINT });

  s.addText("Stack", { x:0.72, y:5.0, w:3.0, h:0.3, isTextBox:true, margin:0,
    fontFace:BFONT, fontSize:13, bold:true, color:NAVY });
  const tools = [
    ["Python 3.10+","language"], ["Streamlit","interface"], ["Pydantic v2","output schemas"],
    ["pypdf","text-PDF extraction"], ["PyTorch + Transformers","local inference"],
    ["MedGemma 1.5 4B","open medical model"], ["pytest","42 tests"], ["NVIDIA CUDA","GPU runtime"]
  ];
  tools.forEach(function(t,i){
    const x = 0.72 + (i%4)*3.02, y = 5.42 + Math.floor(i/4)*0.78;
    card(s, x, y, 2.72, 0.64, { fill:WHITE, flat:true });
    s.addText(t[0], { x:x+0.18, y:y+0.06, w:2.44, h:0.27, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:12, bold:true, color:NAVY });
    s.addText(t[1], { x:x+0.18, y:y+0.33, w:2.44, h:0.24, isTextBox:true, margin:0,
      fontFace:BFONT, fontSize:10, color:SLATE });
  });
  s.addNotes("MedGemma supports medical document understanding and Google provides local GPU inference examples. It is a starting point requiring application-specific validation, not a clinically validated product. Its model terms are separate from the application licence.");
}

/* --------------------------------------------------------------- 10 CLOSE */
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  // decorative art kept clear of every text block
  s.addShape(pres.ShapeType.ellipse, { x:10.9, y:-1.7, w:4.6, h:4.6,
    fill:{ color: TEAL, transparency:80 }, line:{ color:TEAL, width:0 } });

  s.addText("Disconnect the internet.\nUnderstand the report.", { x:0.9, y:1.45, w:9.4, h:1.8,
    isTextBox:true, margin:0, fontFace:HFONT, fontSize:40, bold:true, color:WHITE, lineSpacing:47 });
  s.addText("That is the whole demo. It takes eleven seconds and it cannot be faked.",
    { x:0.9, y:3.3, w:9.4, h:0.38, isTextBox:true, margin:0, fontFace:BFONT,
      fontSize:15, color:MINT });

  const st = [
    { k:"Working today", v:"Full pipeline, 42 tests green, offline check passing on 5 synthetic reports" },
    { k:"Next", v:"First MedGemma run on CUDA; publish real latency and peak VRAM, including failures" },
    { k:"Before any real use", v:"Clinician review of the 40-term glossary and the safety wording" }
  ];
  st.forEach(function(r,i){
    const y = 4.15 + i*0.8;
    s.addText(r.k, { x:0.9, y:y, w:2.8, h:0.62, isTextBox:true, margin:0, valign:"middle",
      fontFace:BFONT, fontSize:12.5, bold:true, color:MINT });
    s.addText(r.v, { x:3.8, y:y, w:8.6, h:0.62, isTextBox:true, margin:0, valign:"middle",
      fontFace:BFONT, fontSize:12.5, color:"CBD5E1" });
  });

  ["S1","S3","S7"].forEach(function(c,i){ chip(s, 0.9 + i*0.58, 6.7, c, { fill:MINT, color:NAVY }); });
  s.addText("PlainMed — clear reports, private by design", { x:2.7, y:6.7, w:6.0, h:0.26,
    isTextBox:true, margin:0, fontFace:BFONT, fontSize:11.5, italic:true, color:LSLATE });
  s.addNotes("The strongest submission is a small working app with evidence, not a large feature list.");
}

pres.writeFile({ fileName: "PlainMed-Pitch.pptx" }).then(function(f){ console.log("wrote", f); });
