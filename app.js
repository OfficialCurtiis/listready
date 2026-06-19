/* ============================================================
   ListReady — client-side image toolkit
   CONFIG: Gumroad product "ListReady Pro" ($9, license key per sale)
   ============================================================ */
const GUMROAD_PERMALINK = "cwvorz";                              // product permalink (verified against Gumroad)
const GUMROAD_BUY_URL   = "https://risxmain.gumroad.com/l/cwvorz"; // your product page URL
const FREE_BATCH_LIMIT  = 15;

/* ---------- state ---------- */
let files = [];          // selected File objects
let isPro = localStorage.getItem("lr_pro") === "1";
let lastResults = [];    // {name, blob, url}

/* ---------- elements ---------- */
const $ = (id) => document.getElementById(id);
const drop = $("drop"), fileInput = $("fileInput");
const fmtSel = $("fmt"), presetSel = $("preset"), customDims = $("customDims");
const qualitySlider = $("quality"), qval = $("qval");
const processBtn = $("processBtn"), clearBtn = $("clearBtn"), fileCount = $("fileCount");
const bar = $("bar"), barFill = $("barFill");
const resultsCard = $("resultsCard"), grid = $("grid"), resCount = $("resCount");
const wmField = $("wmField");

/* ---------- pro UI ---------- */
function refreshProUI(){
  isPro = localStorage.getItem("lr_pro") === "1";
  const pill = $("statusPill");
  if(isPro){
    pill.textContent = "PRO"; pill.className = "status-pill status-pro";
    $("openPro").style.display = "none";
    wmField.classList.remove("locked");
    // unlock webp option label
    [...fmtSel.options].forEach(o=>{ if(o.value==="image/webp") o.textContent="WEBP — smallest size"; });
  } else {
    pill.textContent = "Free"; pill.className = "status-pill status-free";
  }
}
refreshProUI();

/* ---------- file selection ---------- */
$("browseBtn").addEventListener("click",()=>fileInput.click());
drop.addEventListener("click",(e)=>{ if(e.target.id!=="browseBtn") fileInput.click(); });
fileInput.addEventListener("change",()=>addFiles(fileInput.files));
;["dragenter","dragover"].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add("drag");}));
;["dragleave","drop"].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove("drag");}));
drop.addEventListener("drop",e=>addFiles(e.dataTransfer.files));

function isImage(f){
  return f.type.startsWith("image/") || /\.(heic|heif)$/i.test(f.name);
}
function addFiles(list){
  for(const f of list){ if(isImage(f)) files.push(f); }
  updateFileCount();
}
function updateFileCount(){
  const n = files.length;
  fileCount.textContent = n ? `${n} photo${n>1?"s":""} ready` : "No photos selected";
  processBtn.disabled = n===0;
  clearBtn.disabled = n===0;
  if(!isPro && n>FREE_BATCH_LIMIT){
    fileCount.textContent += ` — Free processes the first ${FREE_BATCH_LIMIT}`;
  }
}
clearBtn.addEventListener("click",()=>{ files=[]; updateFileCount(); });

/* ---------- controls ---------- */
qualitySlider.addEventListener("input",()=>qval.textContent=qualitySlider.value);
presetSel.addEventListener("change",()=>{
  customDims.classList.toggle("show", presetSel.value==="custom");
});
fmtSel.addEventListener("change",()=>{
  if(fmtSel.value==="image/webp" && !isPro){
    toast("WEBP output is a Pro feature");
    openModal();
    fmtSel.value="image/jpeg";
  }
});

/* ---------- core processing ---------- */
processBtn.addEventListener("click",processAll);

async function processAll(){
  let queue = files.slice();
  if(!isPro && queue.length>FREE_BATCH_LIMIT){
    queue = queue.slice(0,FREE_BATCH_LIMIT);
    toast(`Free tier: processing first ${FREE_BATCH_LIMIT}. Upgrade for unlimited.`);
  }
  processBtn.disabled=true; clearBtn.disabled=true;
  bar.classList.add("show"); barFill.style.width="0%";
  grid.innerHTML=""; lastResults=[]; resultsCard.style.display="none";

  const fmt = fmtSel.value;
  const q = parseInt(qualitySlider.value,10)/100;
  const ext = fmt==="image/png"?"png":fmt==="image/webp"?"webp":"jpg";

  for(let i=0;i<queue.length;i++){
    try{
      const out = await processOne(queue[i], fmt, q);
      const baseName = queue[i].name.replace(/\.[^.]+$/,"");
      const name = `${baseName}.${ext}`;
      const url = URL.createObjectURL(out.blob);
      lastResults.push({name, blob:out.blob, url});
      addThumb(name, url, queue[i].size, out.blob.size);
    }catch(err){
      console.error("Failed on",queue[i].name,err);
      addThumb(queue[i].name+" (failed)","", queue[i].size, 0, true);
    }
    barFill.style.width = Math.round(((i+1)/queue.length)*100)+"%";
  }

  resCount.textContent = `· ${lastResults.length} file${lastResults.length>1?"s":""}`;
  resultsCard.style.display = lastResults.length? "block":"none";
  processBtn.disabled=false; clearBtn.disabled=false;
  setTimeout(()=>bar.classList.remove("show"),600);
}

async function processOne(file, fmt, quality){
  // 1. Get a decodable bitmap source (HEIC needs conversion first)
  let srcBlob = file;
  if(/\.(heic|heif)$/i.test(file.name) || file.type==="image/heic" || file.type==="image/heif"){
    if(typeof heic2any!=="function") throw new Error("HEIC library not loaded");
    srcBlob = await heic2any({ blob:file, toType:"image/jpeg", quality:0.92 });
    if(Array.isArray(srcBlob)) srcBlob = srcBlob[0];
  }

  // 2. Decode with correct EXIF orientation when supported
  let bmp;
  try{ bmp = await createImageBitmap(srcBlob,{imageOrientation:"from-image"}); }
  catch(e){ bmp = await loadViaImg(srcBlob); }

  // 3. Compute target dimensions
  const {w,h} = targetSize(bmp.width, bmp.height);

  // 4. Draw to canvas (this also strips ALL metadata incl. GPS)
  const canvas = document.createElement("canvas");
  canvas.width=w; canvas.height=h;
  const ctx = canvas.getContext("2d");
  if(fmt==="image/jpeg"){ ctx.fillStyle="#fff"; ctx.fillRect(0,0,w,h); } // flatten transparency for JPG
  ctx.drawImage(bmp,0,0,w,h);

  // 5. Watermark (Pro)
  if(isPro){
    const wm = $("wmText").value.trim();
    if(wm) drawWatermark(ctx,w,h,wm);
  }

  // 6. Encode
  const blob = await new Promise((res,rej)=>{
    canvas.toBlob(b=> b?res(b):rej(new Error("encode failed")), fmt, quality);
  });
  if(bmp.close) bmp.close();
  return {blob};
}

function loadViaImg(blob){
  return new Promise((res,rej)=>{
    const img=new Image();
    img.onload=()=>res(img);
    img.onerror=()=>rej(new Error("decode failed"));
    img.src=URL.createObjectURL(blob);
  });
}

function targetSize(ow, oh){
  const p = presetSel.value;
  if(p==="0") return {w:ow,h:oh};
  if(p==="1080s"){ return {w:1080,h:1080}; }
  if(p==="custom"){
    const cw=parseInt($("cw").value,10), ch=parseInt($("ch").value,10);
    if(cw && ch) return {w:cw,h:ch};
    if(cw){ const r=cw/ow; return {w:cw,h:Math.round(oh*r)}; }
    if(ch){ const r=ch/oh; return {w:Math.round(ow*r),h:ch}; }
    return {w:ow,h:oh};
  }
  // numeric preset = max longest side
  const max=parseInt(p,10);
  if(Math.max(ow,oh)<=max) return {w:ow,h:oh}; // never upscale
  const r = max/Math.max(ow,oh);
  return {w:Math.round(ow*r), h:Math.round(oh*r)};
}

function drawWatermark(ctx,w,h,text){
  const fs=Math.max(16,Math.round(w*0.04));
  ctx.font=`700 ${fs}px -apple-system,Arial,sans-serif`;
  ctx.textAlign="right"; ctx.textBaseline="bottom";
  const pad=Math.round(fs*0.6);
  ctx.shadowColor="rgba(0,0,0,.55)"; ctx.shadowBlur=fs*0.4;
  ctx.fillStyle="rgba(255,255,255,.85)";
  ctx.fillText(text, w-pad, h-pad);
  ctx.shadowBlur=0;
}

function addThumb(name,url,oldSize,newSize,failed){
  const el=document.createElement("div");
  el.className="thumb";
  const saved = oldSize&&newSize? Math.max(0,Math.round((1-newSize/oldSize)*100)) : 0;
  el.innerHTML=`
    ${url?`<img src="${url}" alt="${name}">`:`<div style="height:120px;display:flex;align-items:center;justify-content:center;color:var(--danger)">⚠️ failed</div>`}
    <div class="meta">
      <div class="name" title="${name}">${name}</div>
      ${url?`<div>${fmtBytes(newSize)} <span class="saved">${saved>0?`−${saved}%`:""}</span></div>`:`<div>could not process</div>`}
    </div>
    ${url?`<a class="dl" href="${url}" download="${name}">⬇ Download</a>`:""}`;
  grid.appendChild(el);
}
function fmtBytes(b){ if(b<1024)return b+" B"; if(b<1048576)return (b/1024).toFixed(0)+" KB"; return (b/1048576).toFixed(1)+" MB"; }

/* ---------- download all (zip) ---------- */
$("downloadAll").addEventListener("click",async()=>{
  if(!lastResults.length) return;
  if(typeof JSZip==="undefined"){ toast("ZIP library not loaded"); return; }
  const zip=new JSZip();
  lastResults.forEach(r=>zip.file(r.name,r.blob));
  const blob=await zip.generateAsync({type:"blob"});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);
  a.download="listready-photos.zip"; a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),3000);
});

/* ---------- Pro modal + Gumroad license ---------- */
const proModal=$("proModal");
function openModal(){ proModal.classList.add("show"); }
$("openPro").addEventListener("click",openModal);
$("closePro").addEventListener("click",()=>proModal.classList.remove("show"));
proModal.addEventListener("click",e=>{ if(e.target===proModal) proModal.classList.remove("show"); });
$("buyBtn").href = GUMROAD_BUY_URL;

$("activateBtn").addEventListener("click",async()=>{
  const key=$("licenseInput").value.trim();
  const msg=$("licenseMsg");
  if(!key){ msg.className="msg err"; msg.textContent="Enter your license key."; return; }
  msg.className="msg"; msg.textContent="Checking…";
  try{
    const body=new URLSearchParams({product_permalink:GUMROAD_PERMALINK,license_key:key,increment_uses_count:"false"});
    const r=await fetch("https://api.gumroad.com/v2/licenses/verify",{method:"POST",body});
    const data=await r.json();
    if(data.success && !data.purchase?.refunded && !data.purchase?.chargebacked){
      localStorage.setItem("lr_pro","1");
      localStorage.setItem("lr_key",key);
      refreshProUI();
      msg.className="msg ok"; msg.textContent="✓ Pro activated. Thank you!";
      setTimeout(()=>proModal.classList.remove("show"),1200);
    }else{
      msg.className="msg err"; msg.textContent="That key wasn't valid. Double-check it or contact support.";
    }
  }catch(e){
    msg.className="msg err"; msg.textContent="Couldn't reach the license server. Try again.";
  }
});

/* ---------- toast ---------- */
let toastTimer;
function toast(t){
  const el=$("toast"); el.textContent=t; el.classList.add("show");
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.classList.remove("show"),2600);
}
