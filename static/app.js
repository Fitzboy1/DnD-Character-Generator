document.addEventListener("DOMContentLoaded", () => {
  const generateBtn = document.getElementById("generate");
  const saveFavBtn = document.getElementById("saveFav");
  const viewFavsBtn = document.getElementById("viewFavs");
  const viewFavsNav = document.getElementById("viewFavsNav");
  const clearBtn = document.getElementById("clear");
  const copyBtn = document.getElementById("copyBtn");
  const printBtn = document.getElementById("printBtn");
  const resultDiv = document.getElementById("result");
  const emptyDiv = document.getElementById("empty");
  const favoritesView = document.getElementById("favoritesView");
  const favList = document.getElementById("favList");
  const backFromFavs = document.getElementById("backFromFavs");
  const saveFavInline = document.getElementById("saveFavInline");
  const methodEl = document.getElementById("statMethod");
  const themeToggle = document.getElementById("themeToggle");
  const root = document.documentElement;

  if (!root.hasAttribute("data-theme")) root.setAttribute("data-theme","light");
  themeToggle.addEventListener("click", () => {
    const cur = root.getAttribute("data-theme");
    const next = cur === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    themeToggle.textContent = next === "dark" ? "🌙" : "🌤️";
  });

  const ABILITY_LABELS = ["Strength","Dexterity","Constitution","Intelligence","Wisdom","Charisma"];
  let lastCharacter = null;

  function computeModifiersFromScores(scores){
    return scores.map(s => Math.floor((Number(s)||0 - 10)/2));
  }

  function formatNumber(n){
    return new Intl.NumberFormat().format(n);
  }

  function formatMoney(gp){
    if (!Number.isFinite(gp)) return gp;
    const rounded = Math.round(gp * 100) / 100;
    if (Math.abs(rounded - Math.round(rounded)) < 0.005){
      return `${Math.round(rounded)} gp`;
    } else {
      return `${rounded.toFixed(2)} gp`;
    }
  }

  function equipmentToString(item){
    if (!item) return "";
    if (typeof item === "string") return item;
    const parts=[];
    parts.push(item.name || "Unknown");
    if (item.qty && item.qty>1) parts.push(`x${formatNumber(item.qty)}`);
    if (item.type) parts.push(`(${item.type})`);
    if (item.notes) parts.push(`- ${item.notes}`);
    if (item.contents && Array.isArray(item.contents) && item.contents.length) {
      parts.push(`contains: ${item.contents.join(", ")}`);
    }
    return parts.join(" ");
  }

  function renderEquipmentList(equipmentArray, containerEl){
    containerEl.innerHTML = "";
    if (!Array.isArray(equipmentArray) || equipmentArray.length===0){
      containerEl.textContent = "—"; return;
    }
    const ul=document.createElement("ul"); ul.className="equipmentList";
    equipmentArray.forEach(it => {
      const li=document.createElement("li"); li.textContent=equipmentToString(it); ul.appendChild(li);
    });
    containerEl.appendChild(ul);
  }

  function renderCoins(coins, containerEl, totalGp){
    containerEl.innerHTML = "";
    if (!coins || typeof coins !== "object") return;
    const ul = document.createElement("ul");
    ul.className = "coinList";
    for (const cur of ["gp","sp","cp"]){
      if (coins[cur] !== undefined){
        const li = document.createElement("li");
        li.textContent = `${cur.toUpperCase()}: ${formatNumber(Number(coins[cur]||0))}`;
        ul.appendChild(li);
      }
    }
    containerEl.appendChild(ul);
    const total = document.createElement("div");
    total.className = "muted";
    total.textContent = `Total Value: ${formatMoney(totalGp)}`;
    containerEl.appendChild(total);
  }

  async function generateCharacter(){
    const name = document.getElementById("name").value.trim();
    let pronouns = document.getElementById("pronouns").value;
    if (pronouns === "custom") {
      const cp = document.getElementById("customPronouns").value.trim();
      pronouns = cp || "they/them";
    }
    const gender = document.getElementById("gender").value.trim();
    const method = methodEl ? methodEl.value : "4d6";

    // Call your backend API
    const payload = { name, pronouns, gender, method };
    const resp = await fetch("/api/generate", {
      method:"POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload)
    });
    if (!resp.ok) { console.error("Server error", resp.status); return; }
    const body = await resp.json();
    lastCharacter = body;
    showResult(body);
  }

  function showResult(data){
    emptyDiv.style.display = "none";
    favoritesView.classList.add("hidden");
    resultDiv.classList.remove("hidden");

    document.getElementById("charName").textContent = `${data.name}`;
    document.getElementById("subInfo").textContent = `${data.pronouns} · ${data.gender || "—"} · ${data.alignment} · Age ${data.age}`;
    document.getElementById("background").textContent = data.background;
    document.getElementById("traits").textContent = `${data.personality_trait || ""} · Ideal: ${data.ideal || ""} · Bond: ${data.bond || ""} · Flaw: ${data.flaw || ""}`;
    document.getElementById("race").textContent = data.race;
    document.getElementById("size").textContent = `${data.height} · ${data.weight}`;
    document.getElementById("age").textContent = `Age: ${data.age} years`;
    document.getElementById("class").textContent = data.class;
    document.getElementById("subclass").textContent = data.subclass ? `Subclass: ${data.subclass}` : "";

    const abilityRows = document.getElementById("abilityRows"); abilityRows.innerHTML = "";
    const scores = data.ability_scores; const mods = data.modifiers;
    for (let i=0;i<ABILITY_LABELS.length;i++){
      const row=document.createElement("div"); row.className="abilityRow"; row.setAttribute("role","row");
      const nameCell=document.createElement("div"); nameCell.className="abilityName"; nameCell.textContent=ABILITY_LABELS[i];
      const scoreCell=document.createElement("div"); scoreCell.className="abilityScore"; scoreCell.textContent=Number(scores[i])||0;
      const modCell=document.createElement("div"); modCell.className="abilityMod"; modCell.textContent=(mods[i]>=0?"+":"")+mods[i];
      row.appendChild(nameCell); row.appendChild(scoreCell); row.appendChild(modCell); abilityRows.appendChild(row);
    }

    document.getElementById("avg").textContent = `Average: ${Number(data.ability_average).toFixed(2)}`;
    document.getElementById("mods").textContent = `Modifiers: [${data.modifiers.join(", ")}]`;
    document.getElementById("method").textContent = `Method: ${data.stat_method}`;

    document.getElementById("languages").textContent = (data.languages||[]).join(", ");
    document.getElementById("proficiencies").textContent = (data.proficiencies||[]||[]).join(", ") || "—";
    document.getElementById("doubleProfs").textContent = data.double_proficiencies && data.double_proficiencies.length ? "Double prof: " + data.double_proficiencies.join(", ") : "";

    renderEquipmentList(data.equipment || [], document.getElementById("equipment"));
    renderCoins(data.coins || {}, document.getElementById("coinSection"), data.money_gp_total || data.money || 0);

    resultDiv.focus({preventScroll:true}); resultDiv.scrollIntoView({behavior:"smooth", block:"center"});
  }

  async function saveFavorite(character){
    if (!character) return;
    const favs = JSON.parse(localStorage.getItem("favorites")||"[]");
    character.id = Date.now();
    favs.push(character);
    localStorage.setItem("favorites", JSON.stringify(favs));
    saveFavBtn.textContent="Saved!";
    setTimeout(()=>saveFavBtn.textContent="Save Favorite",1200);
    loadFavorites();
  }

  async function loadFavorites(){
    const favs = JSON.parse(localStorage.getItem("favorites")||"[]");
    favList.innerHTML="";
    if (!favs.length){ favList.innerHTML="<div class='muted'>No favorites yet — save a character to see it here.</div>"; return; }
    favs.forEach(f=>{
      const card=document.createElement("div"); card.className="favCard box";
      card.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>${f.name}</strong><div class="muted" style="font-size:0.85rem">${f.pronouns} · ${f.alignment} · ${f.race} · Age ${f.age}</div>
        <div class="muted" style="font-size:0.85rem">${f.class}${f.subclass ? " — " + f.subclass : ""}</div></div>
        <div style="display:flex;gap:0.5rem"><button data-id="${f.id}" class="loadFav">Load</button><button data-id="${f.id}" class="delFav">Delete</button></div></div>
        <div style="margin-top:0.5rem;font-size:0.9rem" class="muted">${f.background} · Scores: [${(f.ability_scores||[]).join(", ")}]</div>`;
      favList.appendChild(card);
    });
    document.querySelectorAll(".loadFav").forEach(b=>b.addEventListener("click",(e)=>{
      const id=Number(e.currentTarget.getAttribute("data-id")); 
      const favs = JSON.parse(localStorage.getItem("favorites")||"[]");
      const card = favs.find(x=>x.id===id);
      if(card){ 
        if (!card.modifiers||card.modifiers.length!==6) card.modifiers = computeModifiersFromScores(card.ability_scores||[10,10,10,10,10,10]);
        lastCharacter=card; 
        showResult(card); 
      }
    }));
    document.querySelectorAll(".delFav").forEach(b=>b.addEventListener("click",(e)=>{
      const id=Number(e.currentTarget.getAttribute("data-id")); 
      const favs = JSON.parse(localStorage.getItem("favorites")||"[]").filter(f=>f.id!==id);
      localStorage.setItem("favorites", JSON.stringify(favs));
      loadFavorites();
    }));
  }

  generateBtn.addEventListener("click", generateCharacter);
  saveFavBtn.addEventListener("click", ()=>saveFavorite(lastCharacter));
  saveFavInline.addEventListener("click", ()=>saveFavorite(lastCharacter));
  viewFavsBtn.addEventListener("click", async ()=>{ resultDiv.classList.add("hidden"); emptyDiv.style.display="none"; favoritesView.classList.remove("hidden"); await loadFavorites(); });
  if(viewFavsNav) viewFavsNav.addEventListener("click", ()=>viewFavsBtn.click());
  backFromFavs.addEventListener("click", ()=>{ favoritesView.classList.add("hidden"); resultDiv.classList.remove("hidden"); });

  clearBtn.addEventListener("click", ()=>{
    document.getElementById("name").value="";
    document.getElementById("gender").value="";
    document.getElementById("customPronouns").value="";
    document.getElementById("pronouns").value="they/them";
    document.getElementById("customPronounsWrap").style.display="none";
    document.getElementById("empty").style.display="block";
    document.getElementById("result").classList.add("hidden");
    lastCharacter=null;
  });

  copyBtn.addEventListener("click", ()=>{
    if (!lastCharacter) return;
    if (!lastCharacter.modifiers || lastCharacter.modifiers.length!==6) lastCharacter.modifiers = computeModifiersFromScores(lastCharacter.ability_scores||[10,10,10,10,10,10]);
    let out = `${lastCharacter.name} — ${lastCharacter.pronouns} · ${lastCharacter.gender||"—"} · ${lastCharacter.alignment} · Age ${lastCharacter.age}\n\n`;
    out += `Background: ${lastCharacter.background}\n`;
    out += `Race: ${lastCharacter.race} (${lastCharacter.height} · ${lastCharacter.weight}) · Age: ${lastCharacter.age}\n`;
    out += `Class: ${lastCharacter.class}${lastCharacter.subclass ? " — " + lastCharacter.subclass : ""}\n\n`;
    out += `Ability Scores: ${lastCharacter.ability_scores.join(", ")}\n`;
    out += `Modifiers: [${lastCharacter.modifiers.join(", ")}]\n\n`;
    out += `Languages: ${(lastCharacter.languages||[]).join(", ")}\n`;
    out += `Proficiencies: ${(lastCharacter.proficiencies||[]).join(", ")}\n\n`;
    const eq = lastCharacter.equipment || [];
    if (!eq.length) out += `Equipment: —\n`; else { const eqLines = eq.map(equipmentToString); out += `Equipment:\n- ${eqLines.join("\n- ")}\n`; }
    const coins = lastCharacter.coins || {};
    const coinLines = Object.entries(coins).map(([cur, qty]) => `${cur.toUpperCase()}: ${formatNumber(qty)}`);
    if (coinLines.length) {
      out += `\nCoins:\n- ${coinLines.join("\n- ")}\n`;
      out += `Total Value: ${formatMoney(lastCharacter.money_gp_total || lastCharacter.money || 0)}\n`;
    } else {
      out += `Money: ${lastCharacter.money}\n`;
    }
    navigator.clipboard.writeText(out).then(()=>{ copyBtn.textContent="Copied!"; setTimeout(()=>copyBtn.textContent="Copy",1200); });
  });

  printBtn.addEventListener("click", ()=>window.print());
  window.addEventListener("keydown", (e)=>{ if ((e.ctrlKey||e.metaKey) && e.key.toLowerCase()==="r") { e.preventDefault(); generateCharacter(); } });
});
