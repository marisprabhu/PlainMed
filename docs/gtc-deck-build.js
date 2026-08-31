const pptxgen = require("pptxgenjs");

// Palette taken from the PlainMed logo: deep navy through the bright
// blue of the "med" wordmark.
const NAVY="17335E", TEAL="1565C0", MINT="5FA8F5", OFFW="F6F8FC", WHITE="FFFFFF",
      AMBER="C2670A", SLATE="5C6B82", LSLATE="A9C9F0", BORDER="DCE4F0",
      CARD="1E4272", CARDLINE="2C5590", GOOGLE="4285F4", NVIDIA="76B900";

const H="Cambria", B="Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "PlainMed";
pres.title = "PlainMed - GTC";

const sh = () => ({ type:"outer", color:"0A1622", blur:14, offset:2, angle:90, opacity:0.16 });

function chip(s,x,y,label,fill,color){
  s.addShape(pres.ShapeType.roundRect,{x:x,y:y,w:0.5,h:0.28,rectRadius:0.07,
    fill:{color:fill||TEAL},line:{color:fill||TEAL,width:0.5}});
  s.addText(label,{x:x,y:y,w:0.5,h:0.28,isTextBox:true,margin:0,align:"center",
    fontFace:B,fontSize:11,bold:true,color:color||WHITE});
}

function title(s,txt,kicker,dark){
  if(kicker) s.addText(kicker.toUpperCase(),{x:0.7,y:0.46,w:11.9,h:0.3,isTextBox:true,
    margin:0,fontFace:B,fontSize:13,bold:true,charSpacing:2,color:dark?MINT:TEAL});
  s.addText(txt,{x:0.7,y:0.84,w:11.9,h:0.8,isTextBox:true,margin:0,
    fontFace:H,fontSize:36,bold:true,color:dark?WHITE:NAVY});
}

function card(s,x,y,w,h,opt){
  opt=opt||{};
  s.addShape(pres.ShapeType.roundRect,{x:x,y:y,w:w,h:h,rectRadius:0.05,
    fill:{color:opt.fill||WHITE},line:{color:opt.line||BORDER,width:opt.lw||1},
    shadow:opt.flat?undefined:sh()});
}

/* ================================================================ 1 TITLE */
{
  const s=pres.addSlide(); s.background={color:NAVY};
  s.addShape(pres.ShapeType.ellipse,{x:9.9,y:-1.7,w:5.6,h:5.6,
    fill:{color:TEAL,transparency:76},line:{color:TEAL,width:0}});
  s.addShape(pres.ShapeType.ellipse,{x:11.4,y:4.6,w:3.2,h:3.2,
    fill:{color:MINT,transparency:88},line:{color:MINT,width:0}});

  s.addText("PlainMed",{x:0.9,y:2.0,w:8.6,h:1.4,isTextBox:true,margin:0,
    fontFace:H,fontSize:66,bold:true,color:WHITE});
  s.addText("Clear reports. Private by design.",{x:0.9,y:3.35,w:8.6,h:0.55,
    isTextBox:true,margin:0,fontFace:B,fontSize:24,color:MINT});
  s.addText("A patient photographs a lab report and gets back an explanation where every sentence points at the line that supports it — and the AI never learns who they are.",
    {x:0.9,y:4.05,w:8.2,h:1.0,isTextBox:true,margin:0,fontFace:B,fontSize:15,
     color:LSLATE,lineSpacing:22});

  ["S1","S3","S7"].forEach((c,i)=>chip(s,0.9+i*0.62,5.32,c,MINT,NAVY));
  s.addText("every claim traceable to a line",{x:2.85,y:5.32,w:5.0,h:0.28,
    isTextBox:true,margin:0,fontFace:B,fontSize:12,italic:true,color:LSLATE});

  s.addText("Built on Google MedGemma  ·  Served with NVIDIA TensorRT-LLM  ·  Launching India",
    {x:0.9,y:6.45,w:11.6,h:0.35,isTextBox:true,margin:0,fontFace:B,fontSize:13,
     bold:true,color:MINT});
  s.addNotes("Open holding a paper lab report. 'My mother got one of these and Googled her way to a cancer scare over a value that was fine.' Then: watch.");
}

/* ============================================================== 2 PROBLEM */
{
  const s=pres.addSlide(); s.background={color:OFFW};
  title(s,"A patient can read every word and understand nothing","The problem",false);

  const opts=[
    {t:"Search the web",d:"Results strip away the context of this report — this value, this range, this lab. The worst-case reading wins the click.",ic:"?"},
    {t:"Upload to a chatbot",d:"The most sensitive document a person owns leaves their device, is cached, and may train a model.",ic:"!"}
  ];
  opts.forEach((o,i)=>{
    const x=0.7+i*4.1;
    card(s,x,2.3,3.8,3.0);
    s.addShape(pres.ShapeType.ellipse,{x:x+0.3,y:2.62,w:0.54,h:0.54,
      fill:{color:AMBER},line:{color:AMBER,width:0}});
    s.addText(o.ic,{x:x+0.3,y:2.62,w:0.54,h:0.54,isTextBox:true,margin:0,align:"center",
      fontFace:B,fontSize:22,bold:true,color:WHITE});
    s.addText(o.t,{x:x+0.3,y:3.42,w:3.2,h:0.38,isTextBox:true,margin:0,
      fontFace:B,fontSize:19,bold:true,color:NAVY});
    s.addText(o.d,{x:x+0.3,y:3.9,w:3.24,h:1.3,isTextBox:true,margin:0,
      fontFace:B,fontSize:13.5,color:SLATE,lineSpacing:19});
  });

  card(s,8.9,2.3,3.7,3.0,{fill:NAVY,line:NAVY});
  s.addText("Neither can do the one thing that matters:",{x:9.2,y:2.62,w:3.15,h:0.9,
    isTextBox:true,margin:0,fontFace:B,fontSize:15,color:LSLATE,lineSpacing:21});
  s.addText("show its source",{x:9.2,y:3.72,w:3.15,h:0.5,isTextBox:true,margin:0,
    fontFace:H,fontSize:24,bold:true,color:MINT});
  s.addText("You cannot check an answer you cannot trace.",{x:9.2,y:4.35,w:3.15,h:0.7,
    isTextBox:true,margin:0,fontFace:B,fontSize:13,color:LSLATE,lineSpacing:18});

  s.addText("So patients arrive at appointments anxious about the wrong things — and without the questions that would actually help them.",
    {x:0.7,y:5.85,w:11.9,h:0.5,isTextBox:true,margin:0,fontFace:B,fontSize:16,
     italic:true,color:NAVY});
  s.addNotes("Eight minutes with a doctor. A document they cannot read about a body they own.");
}

/* ============================================================== 3 PRODUCT */
{
  const s=pres.addSlide(); s.background={color:OFFW};
  title(s,"Photograph it. Check it. Understand it.","What it does",false);

  const steps=[
    {n:"1",t:"Scan",d:"Photograph the paper\nreport on any phone"},
    {n:"2",t:"Check",d:"See exactly what was\nread. Correct anything"},
    {n:"3",t:"Understand",d:"Plain language, every\nclaim source-linked"},
    {n:"4",t:"Ask",d:"Questions to take to\nyour clinician"}
  ];
  steps.forEach((st,i)=>{
    const x=0.7+i*3.05;
    card(s,x,2.25,2.75,2.45);
    s.addShape(pres.ShapeType.ellipse,{x:x+0.28,y:2.5,w:0.5,h:0.5,
      fill:{color:TEAL},line:{color:TEAL,width:0}});
    s.addText(st.n,{x:x+0.28,y:2.5,w:0.5,h:0.5,isTextBox:true,margin:0,align:"center",
      fontFace:B,fontSize:16,bold:true,color:WHITE});
    s.addText(st.t,{x:x+0.9,y:2.55,w:1.7,h:0.4,isTextBox:true,margin:0,
      fontFace:B,fontSize:18,bold:true,color:NAVY});
    s.addText(st.d,{x:x+0.28,y:3.25,w:2.3,h:1.1,isTextBox:true,margin:0,
      fontFace:B,fontSize:12.5,color:SLATE,lineSpacing:17});
    if(i<3) s.addText("→",{x:x+2.75,y:3.2,w:0.3,h:0.4,isTextBox:true,margin:0,
      align:"center",fontFace:B,fontSize:19,bold:true,color:TEAL});
  });

  card(s,0.7,5.05,11.9,1.55,{fill:NAVY,line:NAVY});
  s.addText("Nothing is explained until a person confirms what was read.",
    {x:1.0,y:5.28,w:11.3,h:0.4,isTextBox:true,margin:0,fontFace:B,fontSize:17,
     bold:true,color:MINT});
  s.addText("Confidence tells you the OCR was sure. It does not tell you it was right — so the review step is mandatory, not conditional. It is also where a misread digit gets caught by the one person who can see the paper.",
    {x:1.0,y:5.7,w:11.3,h:0.75,isTextBox:true,margin:0,fontFace:B,fontSize:13.5,
     color:LSLATE,lineSpacing:18});
  s.addNotes("Live demo goes here: phone, photo, review screen, explanation. Roughly 1.3 seconds for OCR.");
}

/* ============================================================ 4 INSIGHT */
{
  const s=pres.addSlide(); s.background={color:NAVY};
  title(s,"A generated 13.5 is indistinguishable from a hallucinated 13.5","The core idea",true);
  s.addText("So the language model is never allowed to produce one.",
    {x:0.7,y:1.72,w:11.6,h:0.4,isTextBox:true,margin:0,fontFace:B,fontSize:16,color:LSLATE});

  const cols=[
    {h:"Parser owns the numbers",b:"Every value, unit, range and flag is extracted deterministically. Reproducible, unit-tested, and incapable of inventing a digit.",c:MINT},
    {h:"Model owns the prose",b:"MedGemma writes the explanation around values that were already extracted. It can improve how this reads. It cannot change what it says.",c:MINT},
    {h:"Validator owns the truth",b:"Cited line must exist. Every number must appear in it. No diagnosis, no treatment advice, no reassurance.",c:"FCD34D"}
  ];
  cols.forEach((c,i)=>{
    const x=0.7+i*4.07;
    s.addShape(pres.ShapeType.roundRect,{x:x,y:2.45,w:3.75,h:3.25,rectRadius:0.06,
      fill:{color:CARD},line:{color:CARDLINE,width:1}});
    s.addText(c.h,{x:x+0.3,y:2.72,w:3.15,h:0.8,isTextBox:true,margin:0,
      fontFace:H,fontSize:19,bold:true,color:c.c,lineSpacing:24});
    s.addText(c.b,{x:x+0.3,y:3.62,w:3.18,h:1.9,isTextBox:true,margin:0,
      fontFace:B,fontSize:13,color:"CBD5E1",lineSpacing:18});
  });

  s.addText("Judges see hallucination demos constantly. PlainMed demonstrates catching one — live, on stage.",
    {x:0.7,y:6.0,w:11.9,h:0.5,isTextBox:true,margin:0,fontFace:B,fontSize:15,
     italic:true,color:MINT});
  s.addNotes("Demo moment: feed it a statement with a wrong number and a diagnosis, and show the validator dropping both.");
}

/* ======================================================= 5 ARCHITECTURE */
{
  const s=pres.addSlide(); s.background={color:OFFW};
  title(s,"The GPU never learns who the patient is","Architecture",false);
  s.addText("Cheap GPU marketplaces will not sign healthcare data agreements. So we made the GPU not handle patient data at all.",
    {x:0.7,y:1.74,w:11.7,h:0.4,isTextBox:true,margin:0,fontFace:B,fontSize:14.5,color:SLATE});

  // trusted tier
  card(s,0.7,2.35,5.7,2.45,{line:SLATE});
  s.addText("TRUSTED TIER",{x:1.0,y:2.53,w:3.0,h:0.3,isTextBox:true,margin:0,
    fontFace:B,fontSize:11,bold:true,charSpacing:1.5,color:SLATE});
  s.addText("CPU · handles identifiable data",{x:1.0,y:2.81,w:4.0,h:0.3,isTextBox:true,
    margin:0,fontFace:B,fontSize:12.5,color:NAVY});
  s.addText("decode  →  OCR  →  parse  →  de-identify",{x:1.0,y:3.25,w:5.1,h:0.35,
    isTextBox:true,margin:0,fontFace:"Courier New",fontSize:12,bold:true,color:NAVY});
  s.addText("Compliance burden lives here — and it is the cheap tier to run.",
    {x:1.0,y:3.72,w:5.1,h:0.6,isTextBox:true,margin:0,fontFace:B,fontSize:12,
     color:SLATE,lineSpacing:16});
  s.addText("~$0.03/hr",{x:1.0,y:4.3,w:2.0,h:0.35,isTextBox:true,margin:0,
    fontFace:H,fontSize:17,bold:true,color:TEAL});

  // arrow
  s.addText("→",{x:6.45,y:3.3,w:0.6,h:0.5,isTextBox:true,margin:0,align:"center",
    fontFace:B,fontSize:26,bold:true,color:TEAL});
  s.addText("values only",{x:5.85,y:4.95,w:1.8,h:0.3,isTextBox:true,margin:0,
    align:"center",fontFace:B,fontSize:10.5,color:TEAL});

  // model tier
  card(s,7.5,2.35,5.1,2.45,{line:TEAL,lw:2});
  s.addText("MODEL TIER",{x:7.8,y:2.48,w:3.0,h:0.3,isTextBox:true,margin:0,
    fontFace:B,fontSize:11,bold:true,charSpacing:1.5,color:TEAL});
  s.addText("GPU · no identifiers, no BAA needed",{x:7.8,y:2.81,w:4.55,h:0.3,
    isTextBox:true,margin:0,fontFace:B,fontSize:12.5,color:NAVY});
  s.addText("Glucose 108 mg/dL (ref 70-99) [H]",{x:7.8,y:3.25,w:4.55,h:0.35,
    isTextBox:true,margin:0,fontFace:"Courier New",fontSize:12,bold:true,color:TEAL});
  s.addText("No name, no DOB, no record number. Verified in CI against 14 identifier categories.",
    {x:7.8,y:3.72,w:4.55,h:0.6,isTextBox:true,margin:0,fontFace:B,fontSize:12,
     color:SLATE,lineSpacing:16});
  s.addText("$0.17/hr",{x:7.8,y:4.3,w:2.0,h:0.35,isTextBox:true,margin:0,
    fontFace:H,fontSize:17,bold:true,color:TEAL});

  card(s,0.7,5.45,11.9,1.15,{fill:NAVY,line:NAVY});
  s.addText("The tier that is expensive to comply with is CPU-cheap. The tier that is expensive to run carries no compliance burden.",
    {x:1.0,y:5.68,w:11.3,h:0.35,isTextBox:true,margin:0,fontFace:B,fontSize:15,
     bold:true,color:MINT});
  s.addText("De-identification is an allowlist, not a scrubber: the text is rebuilt from parsed fields, so a line containing a name never had a path through.",
    {x:1.0,y:6.08,w:11.3,h:0.35,isTextBox:true,margin:0,fontFace:B,fontSize:12.5,color:LSLATE});
  s.addNotes("Run scripts/deident_check.py live here. 0.36 seconds, 14 identifier categories withheld, clinical content preserved.");
}

/* ============================================================== 6 GOOGLE */
{
  const s=pres.addSlide(); s.background={color:OFFW};
  title(s,"MedGemma, used as a second reader","Google",false);
  s.addText("The obvious build hands the photo to MedGemma and deletes the OCR pipeline. We deliberately did not.",
    {x:0.7,y:1.74,w:11.7,h:0.4,isTextBox:true,margin:0,fontFace:B,fontSize:14.5,color:SLATE});

  card(s,0.7,2.4,5.85,3.35,{line:GOOGLE});
  s.addText("What MedGemma 1.5 4B gives us",{x:1.0,y:2.65,w:5.2,h:0.35,isTextBox:true,
    margin:0,fontFace:B,fontSize:15,bold:true,color:GOOGLE});
  ["Open weights — runs on hardware we control",
   "Medically tuned, with document understanding",
   "Multimodal: a vision encoder that reads the page",
   "128K context, and a 4B size that fits cheap GPUs"].forEach((t,i)=>{
    s.addShape(pres.ShapeType.ellipse,{x:1.02,y:3.28+i*0.5,w:0.16,h:0.16,
      fill:{color:GOOGLE},line:{color:GOOGLE,width:0}});
    s.addText(t,{x:1.32,y:3.19+i*0.5,w:5.1,h:0.36,isTextBox:true,margin:0,
      fontFace:B,fontSize:13,color:NAVY});
  });

  card(s,6.75,2.4,5.85,3.35,{fill:NAVY,line:NAVY});
  s.addText("How we use the vision encoder",{x:7.05,y:2.65,w:5.2,h:0.35,isTextBox:true,
    margin:0,fontFace:B,fontSize:15,bold:true,color:MINT});
  s.addText("It reads the same photo independently — a second radiologist, not a replacement for the first.",
    {x:7.05,y:3.15,w:5.25,h:0.65,isTextBox:true,margin:0,fontFace:B,fontSize:13,
     color:"CBD5E1",lineSpacing:18});
  s.addText("Readers agree  →  real confidence",{x:7.05,y:4.0,w:5.25,h:0.32,
    isTextBox:true,margin:0,fontFace:B,fontSize:13.5,bold:true,color:MINT});
  s.addText("Readers differ  →  a human is asked",{x:7.05,y:4.4,w:5.25,h:0.32,
    isTextBox:true,margin:0,fontFace:B,fontSize:13.5,bold:true,color:"FCD34D"});
  s.addText("The model can raise a question. It can never overwrite an answer.",
    {x:7.05,y:4.95,w:5.25,h:0.6,isTextBox:true,margin:0,fontFace:B,fontSize:13,
     italic:true,color:LSLATE,lineSpacing:18});

  s.addText("Model weights are used under Google's Health AI Developer Foundations terms.",
    {x:0.7,y:6.05,w:11.9,h:0.4,isTextBox:true,margin:0,fontFace:B,fontSize:12,color:SLATE});
  s.addNotes("This is the novel contribution: using a multimodal medical model as an independent verifier rather than as a generator of facts.");
}

/* ============================================================== 7 NVIDIA */
{
  const s=pres.addSlide(); s.background={color:NAVY};
  title(s,"We measured the naive baseline. It is the argument.","NVIDIA",true);
  s.addText("MedGemma 1.5 4B, measured on a T4 with HuggingFace transformers and bitsandbytes NF4 — deliberately the unoptimised path.",
    {x:0.7,y:1.74,w:11.7,h:0.4,isTextBox:true,margin:0,fontFace:B,fontSize:14.5,color:LSLATE});

  const items=[
    {t:"3.23 GB peak — measured",d:"MedGemma 4B at NF4. Fits a 16 GB commodity card with headroom to spare"},
    {t:"121 s per report — measured",d:"On a T4 with naive HF serving. Turing has no native 4-bit kernel"},
    {t:"Most of that is reasoning",d:"MedGemma emits a thinking trace we cannot disable on this runtime"},
    {t:"That gap is what NIM closes",d:"TensorRT-LLM: FP8, XQA, paged attention. Built and configured, not yet measured"}
  ];
  items.forEach((it,i)=>{
    const x=0.7+(i%2)*6.05, y=2.45+Math.floor(i/2)*1.62;
    s.addShape(pres.ShapeType.roundRect,{x:x,y:y,w:5.75,h:1.42,rectRadius:0.06,
      fill:{color:CARD},line:{color:NVIDIA,width:1}});
    s.addText(it.t,{x:x+0.3,y:y+0.16,w:5.1,h:0.34,isTextBox:true,margin:0,
      fontFace:B,fontSize:15,bold:true,color:NVIDIA});
    s.addText(it.d,{x:x+0.3,y:y+0.55,w:5.15,h:0.55,isTextBox:true,margin:0,
      fontFace:B,fontSize:12.5,color:"CBD5E1",lineSpacing:17});
  });

  card(s,0.7,5.85,11.9,1.05,{fill:"14503F",line:MINT});
  s.addText("3.23 GB is the number that matters: it puts MedGemma on the cheap GPU our architecture already keeps patient data away from.",
    {x:1.0,y:6.1,w:11.3,h:0.5,isTextBox:true,margin:0,fontFace:B,fontSize:14.5,
     bold:true,color:MINT});
  s.addNotes("These are our own measurements on Colab's free T4, not estimates. The 121s is the naive path; that is the point. Ask is GPU access to measure the TensorRT-LLM half.");
}

/* =============================================== 8 INDIA AND LANGUAGES */
{
  const s=pres.addSlide(); s.background={color:OFFW};
  title(s,"India first, in the language the patient actually reads","Where we launch",false);

  const stats=[
    {v:"$20.5B",l:"India diagnostics market, 2026"},
    {v:"2.5B+",l:"tests/year projected by 2031"},
    {v:"56%",l:"of that is pathology — our input"},
    {v:"2 → 10",l:"languages, English + Hindi today"}
  ];
  stats.forEach((st,i)=>{
    const x=0.7+i*3.05;
    card(s,x,2.25,2.75,1.62);
    s.addText(st.v,{x:x+0.24,y:2.4,w:2.3,h:0.62,isTextBox:true,margin:0,
      fontFace:H,fontSize:28,bold:true,color:TEAL});
    s.addText(st.l,{x:x+0.24,y:3.06,w:2.34,h:0.6,isTextBox:true,margin:0,
      fontFace:B,fontSize:11.5,color:SLATE,lineSpacing:15});
  });

  card(s,0.7,4.15,5.85,2.42,{line:TEAL});
  s.addText("Language is a legal requirement, not a feature",{x:1.0,y:4.38,w:5.2,h:0.35,
    isTextBox:true,margin:0,fontFace:B,fontSize:14.5,bold:true,color:TEAL});
  s.addText("India's DPDP Act requires the consent notice in English or an Eighth Schedule language. A patient who cannot read the notice cannot consent to it.",
    {x:1.0,y:4.8,w:5.3,h:0.85,isTextBox:true,margin:0,fontFace:B,fontSize:12.5,
     color:NAVY,lineSpacing:17});
  s.addText("Shipping: English, हिन्दी  →  Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi",
    {x:1.0,y:5.72,w:5.3,h:0.68,isTextBox:true,margin:0,fontFace:B,fontSize:12,
     bold:true,color:TEAL,lineSpacing:16});

  card(s,6.75,4.15,5.85,2.42,{fill:NAVY,line:NAVY});
  s.addText("Built for DPDP from the start",{x:7.05,y:4.38,w:5.2,h:0.35,isTextBox:true,
    margin:0,fontFace:B,fontSize:14.5,bold:true,color:MINT});
  ["Itemised notice before any processing (Rule 3)",
   "Consent withdrawal as easy as giving it",
   "Under-18 excluded and enforced in code",
   "Nothing stored, so nothing to breach"].forEach((t,i)=>{
    s.addText("✓",{x:7.05,y:4.86+i*0.42,w:0.25,h:0.3,isTextBox:true,margin:0,
      fontFace:B,fontSize:12,bold:true,color:MINT});
    s.addText(t,{x:7.35,y:4.86+i*0.42,w:5.0,h:0.3,isTextBox:true,margin:0,
      fontFace:B,fontSize:12.5,color:"CBD5E1"});
  });
  s.addNotes("India is also a cheaper compliance path than the US or EU: no BAA regime, health data has no special category, and cross-border transfer is permissive.");
}

/* ============================================================ 9 EVIDENCE */
{
  const s=pres.addSlide(); s.background={color:OFFW};
  title(s,"None of this is a claim. All of it is measured.","Evidence",false);

  const stats=[
    {v:"149",l:"tests passing",s:"parser, validation,\nOCR, security"},
    {v:"5 / 5",l:"reports explained",s:"MedGemma on a\nGPU, end to end"},
    {v:"0 / 23",l:"statements rejected",s:"validator accepted\nevery one"},
    {v:"0",l:"bytes stored",s:"verified from\noutside the app"}
  ];
  stats.forEach((st,i)=>{
    const x=0.7+i*3.05;
    card(s,x,2.25,2.75,2.05);
    s.addText(st.v,{x:x+0.24,y:2.4,w:2.3,h:0.68,isTextBox:true,margin:0,
      fontFace:H,fontSize:32,bold:true,color:TEAL});
    s.addText(st.l,{x:x+0.24,y:3.13,w:2.3,h:0.3,isTextBox:true,margin:0,
      fontFace:B,fontSize:13,bold:true,color:NAVY});
    s.addText(st.s,{x:x+0.24,y:3.47,w:2.34,h:0.6,isTextBox:true,margin:0,
      fontFace:B,fontSize:10.5,color:SLATE,lineSpacing:14});
  });

  const rows=[
    ["offline_check","full pipeline runs with every socket blocked","0.55 s"],
    ["retention_check","no file written, no report content in any log","2.6 s"],
    ["deident_check","14 identifier categories never reach the model","0.36 s"]
  ];
  rows.forEach((r,i)=>{
    const y=4.68+i*0.66;
    card(s,0.7,y,11.9,0.56,{flat:true});
    s.addText("PASS",{x:0.9,y:y,w:0.75,h:0.56,isTextBox:true,margin:0,valign:"middle",
      fontFace:B,fontSize:11.5,bold:true,color:TEAL});
    s.addText(r[0],{x:1.75,y:y,w:2.6,h:0.56,isTextBox:true,margin:0,valign:"middle",
      fontFace:"Courier New",fontSize:11.5,color:NAVY});
    s.addText(r[1],{x:4.5,y:y,w:6.6,h:0.56,isTextBox:true,margin:0,valign:"middle",
      fontFace:B,fontSize:12.5,color:SLATE});
    s.addText(r[2],{x:11.2,y:y,w:1.2,h:0.56,isTextBox:true,margin:0,valign:"middle",
      align:"right",fontFace:"Courier New",fontSize:11.5,color:TEAL});
  });
  s.addNotes("Run the three checks live. Then note the model numbers are ours, from a free Colab T4 - reproducible from the notebook in the repo.");
}

/* =============================================================== 10 ASK */
{
  const s=pres.addSlide(); s.background={color:NAVY};
  s.addShape(pres.ShapeType.ellipse,{x:10.6,y:-1.6,w:4.4,h:4.4,
    fill:{color:TEAL,transparency:78},line:{color:TEAL,width:0}});

  s.addText("Photograph the report.\nUnderstand it. Own it.",{x:0.9,y:1.35,w:9.4,h:1.8,
    isTextBox:true,margin:0,fontFace:H,fontSize:42,bold:true,color:WHITE,lineSpacing:50});
  s.addText("A medical AI that shows its work, and never learns your name.",
    {x:0.9,y:3.25,w:9.4,h:0.4,isTextBox:true,margin:0,fontFace:B,fontSize:16,color:MINT});

  const st=[
    {k:"Working today",v:"Camera to explanation on a GPU. 149 tests, 3 safety proofs green in CI"},
    {k:"Measured ourselves",v:"3.23 GB peak, 121 s/report naive, 0 of 23 statements rejected — free Colab T4"},
    {k:"The ask",v:"GPU access to measure the TensorRT-LLM half of that comparison"}
  ];
  st.forEach((r,i)=>{
    const y=4.05+i*0.78;
    s.addText(r.k,{x:0.9,y:y,w:2.9,h:0.6,isTextBox:true,margin:0,valign:"middle",
      fontFace:B,fontSize:13,bold:true,color:MINT});
    s.addText(r.v,{x:3.95,y:y,w:8.5,h:0.6,isTextBox:true,margin:0,valign:"middle",
      fontFace:B,fontSize:13,color:"CBD5E1"});
  });

  ["S1","S3","S7"].forEach((c,i)=>chip(s,0.9+i*0.62,6.5,c,MINT,NAVY));
  s.addText("PlainMed  ·  clear reports, private by design",{x:2.85,y:6.5,w:6.5,h:0.28,
    isTextBox:true,margin:0,fontFace:B,fontSize:12,italic:true,color:LSLATE});
  s.addNotes("Close on the ask. Do not keep talking after this slide.");
}

pres.writeFile({fileName:"PlainMed-GTC.pptx"}).then(f=>console.log("wrote",f));
