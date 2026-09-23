const state = { recipes: [], query: "", tag: "All" };
const grid = document.querySelector("#recipe-grid");
const count = document.querySelector("#recipe-count");
const empty = document.querySelector("#empty");
const filters = document.querySelector("#filters");
const search = document.querySelector("#search");
const dialog = document.querySelector("#recipe-dialog");
const detail = document.querySelector("#recipe-detail");
const takeoutGrid = document.querySelector("#takeout-grid");

function showCollection() {
  const section = window.location.hash === "#healthy-takeouts" ? "healthy-takeouts" : "recipes";
  for (const id of ["recipes", "healthy-takeouts"]) {
    document.getElementById(id).hidden = id !== section;
  }
  document.querySelectorAll(".section-nav a").forEach(link => {
    if (link.dataset.section === section) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  if (!dialog.open) document.title = section === "healthy-takeouts" ? "Healthy takeouts · Food Vault" : "Food Vault";
}

window.addEventListener("hashchange", showCollection);
showCollection();

const escapeHtml = value => String(value).replace(/[&<>'"]/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
}[char]));

function visibleRecipes() {
  const query = state.query.toLowerCase().trim();
  return state.recipes.filter(recipe => {
    const haystack = [recipe.title, recipe.subtitle, recipe.creator, ...recipe.tags, ...recipe.ingredients].join(" ").toLowerCase();
    return (!query || haystack.includes(query)) && (state.tag === "All" || recipe.tags.includes(state.tag));
  });
}

function renderFilters() {
  const tags = ["All", ...new Set(state.recipes.flatMap(recipe => recipe.tags))];
  filters.innerHTML = tags.map(tag => `<button class="filter ${tag === state.tag ? "active" : ""}" data-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`).join("");
  filters.querySelectorAll("button").forEach(button => button.addEventListener("click", () => {
    state.tag = button.dataset.tag;
    renderFilters();
    renderCards();
  }));
}

function renderCards() {
  const recipes = visibleRecipes();
  count.textContent = recipes.length;
  empty.hidden = recipes.length > 0;
  grid.innerHTML = recipes.map(recipe => `
    <article class="card" data-slug="${escapeHtml(recipe.slug)}" tabindex="0" role="link" aria-label="Open ${escapeHtml(recipe.title)}">
      <div class="card-image">
        <img src="${escapeHtml(recipe.image)}" alt="${escapeHtml(recipe.title)}" loading="lazy" style="object-position:${escapeHtml(recipe.imagePosition || "center 55%")}">
        <span class="source-pill">${escapeHtml(recipe.platform)} · ${escapeHtml(recipe.creator)}</span>
      </div>
      <div class="card-body">
        <h3>${escapeHtml(recipe.title)}</h3>
        <p class="card-subtitle">${escapeHtml(recipe.subtitle)}</p>
        <div class="meta"><span>${escapeHtml(recipe.time)}</span><span>${escapeHtml(recipe.duration)}</span></div>
        <div class="tags">${recipe.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div>
      </div>
    </article>
  `).join("");
  grid.querySelectorAll(".card").forEach(card => {
    const open = () => openRecipe(card.dataset.slug, true);
    card.addEventListener("click", open);
    card.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        open();
      }
    });
  });
}

function recipePath(slug) {
  return `/recipes/${encodeURIComponent(slug)}/`;
}

function slugFromPath() {
  const match = window.location.pathname.match(/^\/recipes\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : null;
}

function openRecipe(slug, updateHistory = false) {
  const recipe = state.recipes.find(item => item.slug === slug);
  if (!recipe) return;
  if (updateHistory && window.location.pathname !== recipePath(slug)) {
    history.pushState({ recipe: slug }, "", recipePath(slug));
  }
  document.title = `${recipe.title} · Food Vault`;
  const sourceLink = recipe.sourceUrl
    ? `<a class="source-link" href="${escapeHtml(recipe.sourceUrl)}" target="_blank" rel="noopener">${escapeHtml(recipe.sourceLabel || "Watch the original reel")} ↗</a>`
    : "";
  const imageCredit = recipe.imageCredit
    ? recipe.imageSourceUrl
      ? `<a class="source-link" href="${escapeHtml(recipe.imageSourceUrl)}" target="_blank" rel="noopener">${escapeHtml(recipe.imageCredit)} ↗</a>`
      : `<span class="image-credit">${escapeHtml(recipe.imageCredit)}</span>`
    : "";
  const additionalSources = (recipe.additionalSources || []).map(source =>
    `<li><a class="source-link" href="${escapeHtml(source.url)}" target="_blank" rel="noopener">${escapeHtml(source.label)} ↗</a></li>`
  ).join("");
  detail.innerHTML = `
    <section class="detail-hero" style="background-image:url('${escapeHtml(recipe.image)}');background-position:${escapeHtml(recipe.imagePosition || "center 55%")} ">
      <div class="detail-title">
        <p class="eyebrow">${escapeHtml(recipe.platform)} · ${escapeHtml(recipe.creator)}</p>
        <h2>${escapeHtml(recipe.title)}</h2>
        <p>${escapeHtml(recipe.subtitle)} · ${escapeHtml(recipe.time)}</p>
      </div>
    </section>
    <section class="detail-content">
      <div>
        <div class="detail-block">
          <h3>Ingredients</h3>
          <ul>${recipe.ingredients.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
        <span class="confidence">${escapeHtml(recipe.confidenceLabel || "Draft confidence")} · ${escapeHtml(recipe.confidence)}</span><br>
        ${sourceLink}${additionalSources ? `<ul class="additional-sources">${additionalSources}</ul>` : ""}${sourceLink && imageCredit ? "<br>" : ""}${imageCredit}
      </div>
      <div>
        <div class="detail-block">
          <h3>Method</h3>
          <ol>${recipe.steps.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol>
        </div>
        <div class="detail-block notes">
          <h3>${escapeHtml(recipe.evidenceLabel || "What the video told us")}</h3>
          <ul>${recipe.evidence.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
      </div>
    </section>
  `;
  dialog.showModal();
}

function closeRecipe(updateHistory = true) {
  if (dialog.open) dialog.close();
  document.title = "Food Vault";
  if (updateHistory && slugFromPath()) history.pushState({}, "", "/");
  showCollection();
}

document.querySelector(".close").addEventListener("click", () => closeRecipe());
dialog.addEventListener("click", event => { if (event.target === dialog) closeRecipe(); });
dialog.addEventListener("cancel", event => {
  event.preventDefault();
  closeRecipe();
});
search.addEventListener("input", () => { state.query = search.value; renderCards(); });
window.addEventListener("popstate", () => {
  const slug = slugFromPath();
  if (slug) openRecipe(slug);
  else closeRecipe(false);
  showCollection();
});

fetch("data/recipes.json")
  .then(response => {
    if (!response.ok) throw new Error(`Recipe data failed to load: ${response.status}`);
    return response.json();
  })
  .then(recipes => {
    state.recipes = recipes;
    renderFilters();
    renderCards();
    const slug = slugFromPath();
    if (slug) openRecipe(slug);
  })
  .catch(error => {
    grid.innerHTML = `<p>Food Vault could not load its recipes. ${escapeHtml(error.message)}</p>`;
  });

fetch("data/takeouts.json")
  .then(response => {
    if (!response.ok) throw new Error(`Restaurant data failed to load: ${response.status}`);
    return response.json();
  })
  .then(takeouts => {
    takeoutGrid.innerHTML = takeouts.map(place => `
      <article class="takeout-card" data-takeout="${escapeHtml(place.slug)}">
        <p class="eyebrow">${escapeHtml(place.cuisine)}</p>
        <h3>${escapeHtml(place.name)}</h3>
        <p class="takeout-area">${escapeHtml(place.area)}</p>
        <p class="takeout-order"><strong>Order idea</strong><br>${escapeHtml(place.order)}</p>
        <p class="takeout-tip">${escapeHtml(place.tip)}</p>
        <a class="source-link" href="${escapeHtml(place.sourceUrl)}" target="_blank" rel="noopener" aria-label="View ${escapeHtml(place.name)} menu and ordering">Menu &amp; ordering ↗</a>
      </article>
    `).join("");
  })
  .catch(error => {
    takeoutGrid.innerHTML = `<p>Food Vault could not load its takeout ideas. ${escapeHtml(error.message)}</p>`;
  });

fetch("data/recipe-links.json")
  .then(response => {
    if (!response.ok) throw new Error(`Saved links failed to load: ${response.status}`);
    return response.json();
  })
  .then(links => {
    document.querySelector("#saved-recipe-links").innerHTML = links.map(link => `
      <article class="saved-link" data-saved-link="${escapeHtml(link.slug)}">
        <a href="${escapeHtml(link.sourceUrl)}" target="_blank" rel="noopener">${escapeHtml(link.title)} ↗</a>
        <span class="saved-status">${escapeHtml(link.status)}</span>
        <p>${escapeHtml(link.note)}</p>
      </article>
    `).join("");
  })
  .catch(error => {
    document.querySelector("#saved-recipe-links").textContent = error.message;
  });
