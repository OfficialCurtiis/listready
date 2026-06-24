/* ============================================================
   ListReady — iPhone video → MP4 converter (Pro feature)
   Uses a HEVC-enabled ffmpeg.wasm core, single-thread (no special
   server headers needed). Everything runs on the user's device.
   ============================================================ */
const GUMROAD_PRODUCT_ID = "0YmEXwtR7cTpcKMV-w_Otg==";
const GUMROAD_BUY_URL    = "https://risxmain.gumroad.com/l/cwvorz";
const abs = (p) => new URL(p, location.href).href; // same-origin asset URL
const FREE_MAX_SECONDS = 60;                 // clips up to 1 min are free
const FREE_MAX_BYTES = 80 * 1024 * 1024;     // ...and up to 80 MB

const $ = (id) => document.getElementById(id);
let isPro = localStorage.getItem("lr_pro") === "1";
let ffmpeg = null, ffLoaded = false, videoFile = null, needsPro = false;

/* ---------- Pro state ---------- */
function refreshPro(){
  isPro = localStorage.getItem("lr_pro") === "1";
  document.body.classList.toggle("is-pro", isPro);
  const pill = $("statusPill");
  pill.textContent = isPro ? "PRO" : "Free";
  pill.className = "status-pill " + (isPro ? "status-pro" : "status-free");
  if (isPro) $("openPro").style.display = "none";
  $("convertBtn").disabled = !(videoFile && (isPro || !needsPro));
  if (videoFile) showGate(window.__lastDur);
}
refreshPro();

/* ---------- file selection ---------- */
const drop = $("vdrop"), fileInput = $("vfile");
$("vbrowse").addEventListener("click", () => fileInput.click());
drop.addEventListener("click", (e) => { if (e.target.id !== "vbrowse") fileInput.click(); });
fileInput.addEventListener("change", () => setFile(fileInput.files[0]));
;["dragenter","dragover"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("drag"); }));
;["dragleave","drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("drag"); }));
drop.addEventListener("drop", e => { if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]); });

function setFile(f){
  if (!f) return;
  if (!/\.(mov|mp4|m4v|hevc)$/i.test(f.name) && !f.type.startsWith("video/")) { toast("Please choose a video file (.mov or .mp4)."); return; }
  videoFile = f;
  $("vname").textContent = f.name + "  ·  " + fmtBytes(f.size);
  $("vname").style.display = "block";
  $("vresult").style.display = "none";
  gateFor(f);
}

// Decide free vs Pro from clip length (preferred) and file size (fallback for HEVC the browser can't read).
function gateFor(f){
  let done = false;
  const decide = (dur) => {
    if (done) return; done = true;
    window.__lastDur = dur;
    const longClip = isFinite(dur) && dur > FREE_MAX_SECONDS;
    const bigFile  = f.size > FREE_MAX_BYTES;
    needsPro = longClip || bigFile;
    showGate(dur);
  };
  const v = document.createElement("video");
  v.preload = "metadata";
  v.onloadedmetadata = () => { const d = v.duration; URL.revokeObjectURL(v.src); decide(d); };
  v.onerror = () => { try{URL.revokeObjectURL(v.src);}catch(e){} decide(NaN); };
  try { v.src = URL.createObjectURL(f); } catch (e) { decide(NaN); }
  setTimeout(() => decide(NaN), 4000);
}

function showGate(dur){
  const g = $("vgate"); if (!g) return;
  const durTxt = isFinite(dur) ? (Math.round(dur) + "s") : null;
  if (isPro){
    g.textContent = "PRO — convert any length or size.";
    g.className = "vgate ok";
  } else if (!needsPro){
    g.textContent = "✓ Free to convert" + (durTxt ? " (" + durTxt + " clip)." : ".");
    g.className = "vgate ok";
  } else {
    g.textContent = (durTxt ? ("This " + durTxt + " clip") : "This video") + " needs Pro. Free covers clips under 1 min and 80 MB.";
    g.className = "vgate locked";
  }
  g.style.display = "block";
  $("convertBtn").disabled = !(isPro || !needsPro);
}
function fmtBytes(b){ if (b < 1048576) return (b/1024).toFixed(0) + " KB"; return (b/1048576).toFixed(1) + " MB"; }

/* ---------- lazy-load the ffmpeg engine ---------- */
async function ensureFfmpeg(){
  if (ffLoaded) return;
  if (!window.FFmpegWASM) throw new Error("FFmpeg library failed to load");
  setStatus("Loading the converter engine (~30 MB, first time only)… please wait.");
  const { FFmpeg } = window.FFmpegWASM;
  ffmpeg = new FFmpeg();
  ffmpeg.on("progress", ({ progress }) => { if (progress >= 0 && progress <= 1) setProgress(Math.min(99, Math.round(progress * 100))); });
  const CORE = "https://cdn.jsdelivr.net/npm/@ffmpeg/core@0.12.6/dist/esm";
  await ffmpeg.load({
    classWorkerURL: abs("814.ffmpeg.js"),   // same-origin worker
    coreURL: `${CORE}/ffmpeg-core.js`,        // full FFmpeg core (mov demux + HEVC decode + libx264)
    wasmURL: `${CORE}/ffmpeg-core.wasm`,
  });
  ffLoaded = true;
}

/* ---------- convert ---------- */
$("convertBtn").addEventListener("click", convert);
async function convert(){
  if (!videoFile) { toast("Choose a video first."); return; }
  if (needsPro && !isPro) { openModal(); return; }
  $("convertBtn").disabled = true;
  $("vresult").style.display = "none";
  $("bar").classList.add("show"); setProgress(0);
  try {
    const { fetchFile } = window.FFmpegUtil;
    await ensureFfmpeg();
    setStatus("Converting to MP4… longer clips can take a few minutes. Keep this tab open.");
    const ext = (videoFile.name.match(/\.[a-z0-9]+$/i) || [".mov"])[0];
    const inName = "input" + ext;
    await ffmpeg.writeFile(inName, await fetchFile(videoFile));
    // Downscale anything over 1080p (long side -> 1920px max) so 4K phone clips
    // don't blow the browser's memory. Aspect preserved; -2 keeps even dimensions.
    const scale = "scale='if(gt(iw,ih),min(1920,iw),-2)':'if(gt(iw,ih),-2,min(1920,ih))'";
    await ffmpeg.exec([
      "-i", inName,
      "-vf", scale,
      "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
      "-c:a", "aac", "-b:a", "128k",
      "-movflags", "+faststart",
      "output.mp4"
    ]);
    const data = await ffmpeg.readFile("output.mp4");
    const blob = new Blob([data.buffer], { type: "video/mp4" });
    const url = URL.createObjectURL(blob);
    $("vpreview").src = url;
    const a = $("vdownload");
    a.href = url;
    a.download = (videoFile.name.replace(/\.[^.]+$/, "") || "video") + ".mp4";
    $("vsize").textContent = fmtBytes(blob.size);
    $("vresult").style.display = "block";
    setProgress(100);
    setStatus("Done ✓  Your MP4 plays on any Windows PC — no codec needed.");
    try { await ffmpeg.deleteFile(inName); await ffmpeg.deleteFile("output.mp4"); } catch(e){}
  } catch (err) {
    console.error(err);
    setStatus("Conversion failed — the clip may be too large for the browser's memory. Try a shorter clip (under ~1–2 min).");
  }
  $("convertBtn").disabled = false;
  setTimeout(() => $("bar").classList.remove("show"), 1000);
}

function setProgress(p){ $("barFill").style.width = p + "%"; }
function setStatus(t){ $("vstatus").textContent = t; $("vstatus").style.display = "block"; }

/* ---------- Pro modal + Gumroad license (shared $9 unlock) ---------- */
const proModal = $("proModal");
function openModal(){ proModal.classList.add("show"); }
$("openPro").addEventListener("click", openModal);
$("unlockBtn").addEventListener("click", openModal);
$("closePro").addEventListener("click", () => proModal.classList.remove("show"));
proModal.addEventListener("click", e => { if (e.target === proModal) proModal.classList.remove("show"); });
$("buyBtn").href = GUMROAD_BUY_URL;

$("activateBtn").addEventListener("click", async () => {
  const key = $("licenseInput").value.trim(), msg = $("licenseMsg");
  if (!key) { msg.className = "msg err"; msg.textContent = "Enter your license key."; return; }
  msg.className = "msg"; msg.textContent = "Checking…";
  try {
    const body = new URLSearchParams({ product_id: GUMROAD_PRODUCT_ID, license_key: key, increment_uses_count: "false" });
    const r = await fetch("https://api.gumroad.com/v2/licenses/verify", { method: "POST", body });
    const d = await r.json();
    if (d.success && !d.purchase?.refunded && !d.purchase?.chargebacked) {
      localStorage.setItem("lr_pro", "1"); localStorage.setItem("lr_key", key);
      refreshPro();
      msg.className = "msg ok"; msg.textContent = "✓ Pro activated. Thank you!";
      setTimeout(() => proModal.classList.remove("show"), 1200);
    } else {
      msg.className = "msg err"; msg.textContent = "That key wasn't valid. Double-check it or contact support.";
    }
  } catch (e) {
    msg.className = "msg err"; msg.textContent = "Couldn't reach the license server. Try again.";
  }
});

/* ---------- toast ---------- */
let tT;
function toast(t){ const e = $("toast"); e.textContent = t; e.classList.add("show"); clearTimeout(tT); tT = setTimeout(() => e.classList.remove("show"), 2800); }
