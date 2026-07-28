const state = { recipes: [], query: "", tag: "All" };
const grid = document.querySelector("#recipe-grid");
const count = document.querySelector("#recipe-count");
const empty = document.querySelector("#empty");
const filters = document.querySelector("#filters");
const search = document.querySelector("#search");
const dialog = document.querySelector("#recipe-dialog");
const detail = document.querySelector("#recipe-detail");

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
    <article class="card" data-slug="${escapeHtml(recipe.slug)}" tabindex="0" role="button" aria-label="Open ${escapeHtml(recipe.title)}">
      <div class="card-image">
        <img src="${escapeHtml(recipe.image)}" alt="${escapeHtml(recipe.title)}" loading="lazy">
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
    const open = () => openRecipe(card.dataset.slug);
    card.addEventListener("click", open);
    card.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") open(); });
  });
}

function openRecipe(slug) {
  const recipe = state.recipes.find(item => item.slug === slug);
  if (!recipe) return;
  detail.innerHTML = `
    <section class="detail-hero" style="background-image:url('${escapeHtml(recipe.image)}')">
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
        <span class="confidence">Draft confidence · ${escapeHtml(recipe.confidence)}</span><br>
        <a class="source-link" href="${escapeHtml(recipe.sourceUrl)}" target="_blank" rel="noopener">Watch the original reel ↗</a>
      </div>
      <div>
        <div class="detail-block">
          <h3>Method</h3>
          <ol>${recipe.steps.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ol>
        </div>
        <div class="detail-block notes">
          <h3>What the video told us</h3>
          <ul>${recipe.evidence.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
      </div>
    </section>
  `;
  dialog.showModal();
}

document.querySelector(".close").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
search.addEventListener("input", () => { state.query = search.value; renderCards(); });

fetch("data/recipes.json")
  .then(response => {
    if (!response.ok) throw new Error(`Recipe data failed to load: ${response.status}`);
    return response.json();
  })
  .then(recipes => {
    state.recipes = recipes;
    renderFilters();
    renderCards();
  })
  .catch(error => {
    grid.innerHTML = `<p>Food Vault could not load its recipes. ${escapeHtml(error.message)}</p>`;
  });
