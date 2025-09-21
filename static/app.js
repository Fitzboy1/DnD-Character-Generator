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

  if (!root.hasAttribute("data-theme")) root.setAttribute("data-theme", "light");
  themeToggle.addEventListener("click", () => {
    const cur = root.getAttribute("data-theme");
    const next = cur === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    themeToggle.textContent = next === "dark" ? "🌙" : "🌤️";
  });

  const ABILITY_LABELS = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"];

  let lastCharacter = null;

  function computeModifiersFromScores(scores) {
    return scores.map(s => {
      const n = Number(s) || 0;
      return Math.floor((n - 10) / 2);
    });
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

    const payload = { name, pronouns, gender, method };
    const resp = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!resp.ok) {
      console.error("Server returned", resp.status);
      return;
    }
    const body = await resp.json();

    // Validate & coerce ability_scores
    if (!body.ability_scores || !Array.isArray(body.ability_scores) || body.ability_scores.length !== 6) {
      const fallbackScores = [];
      for (let i = 0; i < 6; i++) {
        const rolls = [];
        for (let r = 0; r < 4; r++) rolls.push(Math.floor(Math.random() * 6) + 1);
        rolls.sort((a,b) => a-b);
        fallbackScores.push(rolls[1] + rolls[2] + rolls[3]);
      }
      body.ability_scores = fallbackScores;
      body.ability_average = fallbackScores.reduce((a,b)=>a+b,0)/6;
    } else {
      body.ability_scores = body.ability_scores.map(s => Number(s));
      body.ability_average = body.ability_average ? Number(body.ability_average) : (body.ability_scores.reduce((a,b)=>a+b,0)/6);
    }

    // Ensure modifiers exist and are numbers
    if (!body.modifiers || !Array.isArray(body.modifiers) || body.modifiers.length !== 6) {
      body.modifiers = computeModifiersFromScores(body.ability_scores);
    } else {
      body.modifiers = body.modifiers.map(m => Number(m));
      if (body.modifiers.some(m => Number.isNaN(m))) {
        body.modifiers = computeModifiersFromScores(body.ability_scores);
      }
    }

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
    document.getElementById("traits").textContent = `${data.personality_trait} · Ideal: ${data.ideal} · Bond: ${data.bond} · Flaw: ${data.flaw}`;

    document.getElementById("race").textContent = data.race;
    document.getElementById("size").textContent = `${data.height} · ${data.weight}`;
    document.getElementById("age").textContent = `Age: ${data.age} years`;

    document.getElementById("class").textContent = data.class;
    document.getElementById("subclass").textContent = data.subclass ? `Subclass: ${data.subclass}` : "";

    const abilityRows = document.getElementById("abilityRows");
    abilityRows.innerHTML = "";
    const scores = data.ability_scores;
    const mods = data.modifiers;
    for (let i = 0; i < ABILITY_LABELS.length; i++) {
      const row = document.createElement("div");
      row.className = "abilityRow";
      row.setAttribute("role", "row");

      const nameCell = document.createElement("div");
      nameCell.className = "abilityName";
      nameCell.textContent = ABILITY_LABELS[i];
      nameCell.setAttribute("role", "cell");

      const scoreCell = document.createElement("div");
      scoreCell.className = "abilityScore";
      const scoreVal = Number(scores[i]) || 0;
      scoreCell.textContent = scoreVal;
      scoreCell.setAttribute("role", "cell");
      scoreCell.setAttribute("aria-label", `${ABILITY_LABELS[i]} score ${scoreVal}`);

      const modVal = Number(mods[i]);
      const modCell = document.createElement("div");
      modCell.className = "abilityMod";
      const modText = (modVal >= 0 ? "+" : "") + modVal;
      modCell.textContent = modText;
      modCell.setAttribute("role", "cell");
      modCell.setAttribute("aria-label", `${ABILITY_LABELS[i]} modifier ${modText}`);

      row.appendChild(nameCell);
      row.appendChild(scoreCell);
      row.appendChild(modCell);
      abilityRows.appendChild(row);
    }

    document.getElementById("avg").textContent = `Average: ${Number(data.ability_average).toFixed(2)}`;
    document.getElementById("mods").textContent = `Modifiers: [${data.modifiers.join(", ")}]`;
    document.getElementById("method").textContent = `Method: ${data.stat_method}`;

    document.getElementById("languages").textContent = (data.languages || []).join(", ");
    document.getElementById("proficiencies").textContent = (data.proficiencies || []).join(", ") || "—";
    document.getElementById("doubleProfs").textContent = data.double_proficiencies && data.double_proficiencies.length ? "Double prof: " + data.double_proficiencies.join(", ") : "";
    document.getElementById("equipment").textContent = (data.equipment || []).join(", ");
    document.getElementById("money").textContent = data.money || "";

    resultDiv.focus({ preventScroll: true });
    resultDiv.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  async function saveFavorite(character) {
    if (!character) return;
    const resp = await fetch("/api/favorites", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ character })
    });
    const body = await resp.json();
    if (body.ok) {
      saveFavBtn.textContent = "Saved!";
      setTimeout(() => saveFavBtn.textContent = "Save Favorite", 1200);
      loadFavorites();
    }
  }

  async function loadFavorites(){
    const resp = await fetch("/api/favorites");
    const favs = await resp.json();
    favList.innerHTML = "";
    if (!favs.length) {
      favList.innerHTML = "<div class='muted'>No favorites yet — save a character to see it here.</div>";
      return;
    }
    favs.forEach(f => {
      const card = document.createElement("div");
      card.className = "favCard box";
      card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div>
            <strong>${f.name}</strong>
            <div class="muted" style="font-size:0.85rem">${f.pronouns} · ${f.alignment} · ${f.race} · Age ${f.age}</div>
            <div class="muted" style="font-size:0.85rem">${f.class}${f.subclass ? " — " + f.subclass : ""}</div>
          </div>
          <div style="display:flex;gap:0.5rem">
            <button data-id="${f.id}" class="loadFav">Load</button>
            <button data-id="${f.id}" class="delFav">Delete</button>
          </div>
        </div>
        <div style="margin-top:0.5rem;font-size:0.9rem" class="muted">
          ${f.background} · Scores: [${(f.ability_scores||[]).join(", ")}]
        </div>
      `;
      favList.appendChild(card);
    });
    document.querySelectorAll(".loadFav").forEach(b => {
      b.addEventListener("click", (e) => {
        const id = Number(e.currentTarget.getAttribute("data-id"));
        const card = favs.find(x => x.id === id);
        if (card) {
          if (!card.modifiers || card.modifiers.length !== 6) {
            card.modifiers = computeModifiersFromScores(card.ability_scores || [10,10,10,10,10,10]);
          }
          lastCharacter = card;
          showResult(card);
        }
      });
    });
    document.querySelectorAll(".delFav").forEach(b => {
      b.addEventListener("click", async (e) => {
        const id = Number(e.currentTarget.getAttribute("data-id"));
        await fetch(`/api/favorites/${id}`, { method: "DELETE" });
        loadFavorites();
      });
    });
  }

  generateBtn.addEventListener("click", generateCharacter);
  saveFavBtn.addEventListener("click", () => saveFavorite(lastCharacter));
  saveFavInline.addEventListener("click", () => saveFavorite(lastCharacter));
  viewFavsBtn.addEventListener("click", async () => {
    resultDiv.classList.add("hidden");
    emptyDiv.style.display = "none";
    favoritesView.classList.remove("hidden");
    document.getElementById("favoritesView").classList.remove("hidden");
    await loadFavorites();
  });
  if (viewFavsNav) viewFavsNav.addEventListener("click", () => viewFavsBtn.click());
  backFromFavs.addEventListener("click", () => {
    favoritesView.classList.add("hidden");
    resultDiv.classList.remove("hidden");
  });

  clearBtn.addEventListener("click", () => {
    document.getElementById("name").value = "";
    document.getElementById("gender").value = "";
    document.getElementById("customPronouns").value = "";
    document.getElementById("pronouns").value = "they/them";
    document.getElementById("customPronounsWrap").style.display = "none";
    document.getElementById("empty").style.display = "block";
    document.getElementById("result").classList.add("hidden");
    lastCharacter = null;
  });

  copyBtn.addEventListener("click", () => {
    if (!lastCharacter) return;
    if (!lastCharacter.modifiers || lastCharacter.modifiers.length !== 6) {
      lastCharacter.modifiers = computeModifiersFromScores(lastCharacter.ability_scores || [10,10,10,10,10,10]);
    }
    let out = `${lastCharacter.name} — ${lastCharacter.pronouns} · ${lastCharacter.gender || "—"} · ${lastCharacter.alignment} · Age ${lastCharacter.age}\n\n`;
    out += `Background: ${lastCharacter.background}\n`;
    out += `Race: ${lastCharacter.race} (${lastCharacter.height} · ${lastCharacter.weight}) · Age: ${lastCharacter.age}\n`;
    out += `Class: ${lastCharacter.class}${lastCharacter.subclass ? " — " + lastCharacter.subclass : ""}\n\n`;
    out += `Ability Scores: ${lastCharacter.ability_scores.join(", ")}\n`;
    out += `Modifiers: [${lastCharacter.modifiers.join(", ")}]\n\n`;
    out += `Languages: ${(lastCharacter.languages||[]).join(", ")}\n`;
    out += `Proficiencies: ${(lastCharacter.proficiencies||[]).join(", ")}\n\n`;
    out += `Equipment: ${(lastCharacter.equipment||[]).join(", ")}\n`;
    out += `Money: ${lastCharacter.money}\n`;
    navigator.clipboard.writeText(out).then(() => {
      copyBtn.textContent = "Copied!";
      setTimeout(() => copyBtn.textContent = "Copy", 1200);
    });
  });

  printBtn.addEventListener("click", () => {
    window.print();
  });

  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "r") {
      e.preventDefault();
      generateCharacter();
    }
  });

  // Optional: generate one on load
  // generateCharacter();
});
