/**
 * Tags tab — org tag catalog CRUD (mirrors /api/v1/tags).
 * Tags classify tickets; the ticketing agent assigns them from this catalog.
 */
window.TagsUI = (function () {
  let mode = "create";
  let tags = [];
  let backendFetch = null;
  let unwrapData = null;
  let showToast = null;
  let search = "";

  const SNAKE_CASE = /^[a-z0-9]+(_[a-z0-9]+)*$/;

  const $ = (id) => document.getElementById(id);

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  function showFormError(message) {
    const el = $("tag-form-error");
    if (!el) return;
    if (!message) {
      el.classList.add("hidden");
      el.textContent = "";
      return;
    }
    el.textContent = message;
    el.classList.remove("hidden");
  }

  function showListError(message) {
    const el = $("tags-error");
    if (!el) return;
    if (!message) {
      el.classList.add("hidden");
      el.textContent = "";
      return;
    }
    el.textContent = message;
    el.classList.remove("hidden");
  }

  function hideOtherPanels() {
    // Hide agent + API-tool panels so the tags panels own the view.
    $("tab-list")?.classList.add("hidden");
    $("tab-create")?.classList.add("hidden");
    $("tab-view")?.classList.add("hidden");
    window.ApiToolsUI?.hideToolPanels?.();
  }

  function hideTagPanels() {
    $("tab-tags-list")?.classList.add("hidden");
    $("tab-tag-form")?.classList.add("hidden");
  }

  function setActiveTab(tabName) {
    document.querySelectorAll(".tabs .tab").forEach((t) => t.classList.remove("active"));
    document.querySelector(`.tab[data-tab="${tabName}"]`)?.classList.add("active");
  }

  function showTagsListPanel() {
    hideOtherPanels();
    hideTagPanels();
    $("tab-tags-list")?.classList.remove("hidden");
    setActiveTab("tags");
  }

  function showTagFormPanel() {
    hideOtherPanels();
    hideTagPanels();
    $("tab-tag-form")?.classList.remove("hidden");
    setActiveTab("tag-create");
  }

  function resetForm() {
    mode = "create";
    $("tag-form-id").value = "";
    $("tag-form-title").textContent = "Create tag";
    $("tag-form-desc").innerHTML = 'Matches <code>POST /api/v1/tags</code>';
    $("tag-form-hint").textContent = "New classification tag";
    $("tag-value").value = "";
    $("tag-value").disabled = false;
    $("tag-description").value = "";
    showFormError(null);
  }

  function populateForm(tag) {
    mode = "edit";
    $("tag-form-id").value = tag.tag_id;
    $("tag-form-title").textContent = `Edit · ${tag.value}`;
    $("tag-form-desc").textContent = `Updates via PUT /api/v1/tags/${tag.tag_id}`;
    $("tag-form-hint").textContent = `Editing ${tag.value}`;
    $("tag-value").value = tag.value || "";
    $("tag-value").disabled = false;
    $("tag-description").value = tag.description || "";
    showFormError(null);
  }

  function renderList() {
    const list = $("tag-list");
    const count = $("tag-count");
    if (!list || !count) return;
    list.innerHTML = "";
    count.textContent = `${tags.length} tag${tags.length === 1 ? "" : "s"}`;

    if (!tags.length) {
      list.innerHTML = `
        <li class="empty-state">
          <div class="empty-state-icon">🏷️</div>
          <p>No tags yet — create one so the AI can classify tickets.</p>
        </li>`;
      return;
    }

    tags.forEach((tag, i) => {
      const li = document.createElement("li");
      li.className = "agent-item";
      li.style.animationDelay = `${i * 0.06}s`;
      li.innerHTML = `
        <div class="meta">
          <strong><code class="ticket-tag">${escapeHtml(tag.value)}</code></strong>
          <span>${escapeHtml(tag.description || "No description")}</span>
        </div>
        <div class="agent-actions">
          <button type="button" class="btn-ghost btn-tag-edit" data-id="${tag.tag_id}">Edit</button>
          <button type="button" class="btn-ghost btn-tag-delete" data-id="${tag.tag_id}">Delete</button>
        </div>`;
      list.appendChild(li);
    });

    list.querySelectorAll(".btn-tag-edit").forEach((btn) => {
      btn.addEventListener("click", () => openEdit(btn.dataset.id));
    });
    list.querySelectorAll(".btn-tag-delete").forEach((btn) => {
      btn.addEventListener("click", () => deleteTag(btn.dataset.id));
    });
  }

  function buildQuery() {
    const params = new URLSearchParams();
    params.set("page", "1");
    params.set("page_size", "100");
    if (search) params.set("search", search);
    return params.toString();
  }

  async function loadTags() {
    showListError(null);
    $("tags-loading")?.classList.remove("hidden");
    $("tag-list")?.classList.add("hidden");
    try {
      const envelope = await backendFetch(`/tags/?${buildQuery()}`);
      const data = unwrapData(envelope);
      tags = data.tags || [];
      renderList();
    } catch (err) {
      showListError(err.message);
    } finally {
      $("tags-loading")?.classList.add("hidden");
      $("tag-list")?.classList.remove("hidden");
    }
  }

  function openCreate() {
    resetForm();
    showTagFormPanel();
  }

  function findTag(tagId) {
    return tags.find((t) => t.tag_id === tagId);
  }

  async function openEdit(tagId) {
    resetForm();
    showTagFormPanel();
    const cached = findTag(tagId);
    if (cached) {
      populateForm(cached);
      return;
    }
    $("tag-form-hint").textContent = "Loading…";
    try {
      const envelope = await backendFetch(`/tags/${tagId}`);
      populateForm(unwrapData(envelope));
    } catch (err) {
      showFormError(err.message);
    }
  }

  function closeForm() {
    showTagsListPanel();
  }

  function buildPayload() {
    const value = $("tag-value").value.trim();
    const description = $("tag-description").value.trim();
    if (!value) throw new Error("Tag value is required (snake_case).");
    if (!SNAKE_CASE.test(value)) {
      throw new Error("Tag value must be snake_case (e.g. refund_request).");
    }
    return { value, description };
  }

  async function save() {
    const btn = $("btn-save-tag");
    showFormError(null);
    let payload;
    try {
      payload = buildPayload();
    } catch (err) {
      showFormError(err.message);
      return;
    }

    btn.classList.add("loading");
    btn.disabled = true;
    try {
      if (mode === "edit") {
        const id = $("tag-form-id").value;
        await backendFetch(`/tags/${id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
      } else {
        await backendFetch("/tags/", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }
      await loadTags();
      showTagsListPanel();
      if (showToast) showToast("Tag saved!");
    } catch (err) {
      showFormError(err.message);
    } finally {
      btn.classList.remove("loading");
      btn.disabled = false;
    }
  }

  async function deleteTag(tagId) {
    const tag = findTag(tagId);
    const label = tag?.value || tagId;
    if (!window.confirm(`Delete tag "${label}"?`)) return;
    try {
      await backendFetch(`/tags/${tagId}`, { method: "DELETE" });
      if (showToast) showToast("Tag deleted");
      await loadTags();
    } catch (err) {
      showListError(err.message);
    }
  }

  function init(handlers) {
    backendFetch = handlers.backendFetch;
    unwrapData = handlers.unwrapData;
    showToast = handlers.toast;

    $("btn-refresh-tags")?.addEventListener("click", loadTags);
    $("btn-tag-form-cancel")?.addEventListener("click", closeForm);
    $("btn-save-tag")?.addEventListener("click", save);
    $("tag-search")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        search = e.target.value.trim();
        loadTags();
      }
    });

    resetForm();
  }

  return {
    init,
    loadTags,
    openCreate,
    openEdit,
    closeForm,
    showTagsListPanel,
    hideTagPanels,
  };
})();
