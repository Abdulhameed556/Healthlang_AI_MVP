/**
 * API tool list, create/edit form, view, test — mirrors /api/v1/api-tools
 */
window.ApiToolsUI = (function () {
  let mode = "create";
  let tools = [];
  let backendFetch = null;
  let unwrapData = null;
  let onToolsChanged = null;
  let showToast = null;

  const $ = (id) => document.getElementById(id);

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  function showFormError(message) {
    const el = $("tool-form-error");
    if (!message) {
      el.classList.add("hidden");
      el.textContent = "";
      return;
    }
    el.textContent = message;
    el.classList.remove("hidden");
  }

  function showListError(message) {
    const el = $("tools-error");
    if (!message) {
      el.classList.add("hidden");
      el.textContent = "";
      return;
    }
    el.textContent = message;
    el.classList.remove("hidden");
  }

  function hideAgentPanels() {
    $("tab-list")?.classList.add("hidden");
    $("tab-create")?.classList.add("hidden");
    $("tab-view")?.classList.add("hidden");
    window.TagsUI?.hideTagPanels?.();
  }

  function hideToolPanels() {
    $("tab-tools-list")?.classList.add("hidden");
    $("tab-tool-form")?.classList.add("hidden");
    $("tab-tool-view")?.classList.add("hidden");
  }

  function showToolsListPanel() {
    hideAgentPanels();
    hideToolPanels();
    $("tab-tools-list")?.classList.remove("hidden");
    document.querySelectorAll(".tabs .tab").forEach((t) => t.classList.remove("active"));
    document.querySelector('.tab[data-tab="tools"]')?.classList.add("active");
  }

  function showToolFormPanel() {
    hideAgentPanels();
    hideToolPanels();
    $("tab-tool-form")?.classList.remove("hidden");
    document.querySelectorAll(".tabs .tab").forEach((t) => t.classList.remove("active"));
    document.querySelector('.tab[data-tab="tool-create"]')?.classList.add("active");
  }

  function showToolViewPanel() {
    hideAgentPanels();
    hideToolPanels();
    $("tab-tool-view")?.classList.remove("hidden");
  }

  function parseDefaultValue(raw, type) {
    if (raw === "" || raw == null) return null;
    if (type === "integer") {
      const n = parseInt(raw, 10);
      if (Number.isNaN(n)) throw new Error(`Default must be an integer for type ${type}.`);
      return n;
    }
    if (type === "number") {
      const n = parseFloat(raw);
      if (Number.isNaN(n)) throw new Error(`Default must be a number for type ${type}.`);
      return n;
    }
    if (type === "boolean") {
      const lower = String(raw).toLowerCase();
      if (lower === "true") return true;
      if (lower === "false") return false;
      throw new Error("Boolean default must be true or false.");
    }
    return String(raw);
  }

  function addHeaderBlock(data = {}) {
    const list = $("tool-headers-list");
    const block = document.createElement("div");
    block.className = "repeatable-item compact-repeatable";
    block.innerHTML = `
      <div class="repeatable-head">
        <span class="repeatable-label">Header</span>
        <button type="button" class="btn-icon-remove" title="Remove header">×</button>
      </div>
      <div class="form-grid three-col">
        <div class="form-field">
          <label>Key <span class="req">*</span></label>
          <input class="header-key" maxlength="255" value="${escapeHtml(data.key || "")}" placeholder="Accept" />
        </div>
        <div class="form-field">
          <label>Value <span class="req">*</span></label>
          <input class="header-value" maxlength="2000" value="${escapeHtml(data.value || "")}" placeholder="application/json" />
        </div>
        <div class="form-field">
          <label class="checkbox-pill inline-check header-secret-label">
            <input type="checkbox" class="header-secret" ${data.is_secret ? "checked" : ""} />
            Secret (encrypted)
          </label>
        </div>
      </div>`;
    block.querySelector(".btn-icon-remove").addEventListener("click", () => block.remove());
    list.appendChild(block);
  }

  function addParameterBlock(data = {}) {
    const list = $("tool-params-list");
    const block = document.createElement("div");
    block.className = "repeatable-item";
    block.innerHTML = `
      <div class="repeatable-head">
        <span class="repeatable-label">Parameter</span>
        <button type="button" class="btn-icon-remove" title="Remove parameter">×</button>
      </div>
      <div class="form-grid">
        <div class="form-field">
          <label>Name <span class="req">*</span></label>
          <input class="param-name" maxlength="100" value="${escapeHtml(data.name || "")}" placeholder="phoneNumber" />
        </div>
        <div class="form-field">
          <label>Type</label>
          <select class="param-type">
            <option value="string">string</option>
            <option value="integer">integer</option>
            <option value="number">number</option>
            <option value="boolean">boolean</option>
          </select>
        </div>
        <div class="form-field">
          <label>Location</label>
          <select class="param-location">
            <option value="query">query</option>
            <option value="path">path</option>
          </select>
        </div>
        <div class="form-field">
          <label class="checkbox-pill inline-check">
            <input type="checkbox" class="param-required" ${data.required ? "checked" : ""} />
            Required
          </label>
        </div>
        <div class="form-field full">
          <label>Description</label>
          <input class="param-desc" maxlength="500" value="${escapeHtml(data.description || "")}" />
        </div>
        <div class="form-field">
          <label>Default</label>
          <input class="param-default" placeholder="optional" value="${escapeHtml(
            data.default != null ? String(data.default) : ""
          )}" />
        </div>
      </div>`;
    block.querySelector(".param-type").value = data.type || "string";
    block.querySelector(".param-location").value = data.location || "query";
    block.querySelector(".btn-icon-remove").addEventListener("click", () => block.remove());
    list.appendChild(block);
  }

  function collectHeaders() {
    return [...document.querySelectorAll("#tool-headers-list .repeatable-item")].map((block) => ({
      key: block.querySelector(".header-key").value.trim(),
      value: block.querySelector(".header-value").value.trim(),
      is_secret: block.querySelector(".header-secret").checked,
    }));
  }

  function collectParameters() {
    return [...document.querySelectorAll("#tool-params-list .repeatable-item")].map((block) => {
      const type = block.querySelector(".param-type").value;
      const defaultRaw = block.querySelector(".param-default").value.trim();
      const item = {
        name: block.querySelector(".param-name").value.trim(),
        type,
        location: block.querySelector(".param-location").value,
        required: block.querySelector(".param-required").checked,
        description: block.querySelector(".param-desc").value.trim(),
      };
      if (defaultRaw) {
        item.default = parseDefaultValue(defaultRaw, type);
      }
      return item;
    });
  }

  function buildPayload({ includeAuthKey }) {
    const name = $("at-name").value.trim();
    const description = $("at-description").value.trim();
    const endpointUrl = $("at-endpoint").value.trim();
    if (!name) throw new Error("Tool name is required (snake_case).");
    if (!/^[a-z][a-z0-9_]*$/.test(name)) {
      throw new Error("Tool name must be snake_case (e.g. get_customer_context).");
    }
    if (!description) throw new Error("Description is required.");
    if (!endpointUrl) throw new Error("Endpoint URL is required.");

    const headers = collectHeaders().filter((h) => h.key && h.value);
    const requestParameters = collectParameters().filter((p) => p.name);

    const payload = {
      name,
      description,
      endpoint_url: endpointUrl,
      headers,
      request_parameters: requestParameters,
    };

    if (mode === "create") {
      payload.http_method = "GET";
    }

    if (includeAuthKey) {
      const auth = $("at-auth-key").value.trim();
      if (auth) payload.auth_key = auth;
      else if (mode === "create") payload.auth_key = null;
    }

    return payload;
  }

  function renderTestParamInputs(parameters, containerId = "tool-test-params") {
    const wrap = $(containerId);
    if (!wrap) return;
    if (!parameters.length) {
      wrap.innerHTML = '<p class="field-hint">No parameters — test will call the URL as configured.</p>';
      return;
    }
    wrap.innerHTML = parameters
      .map(
        (p) => `
      <div class="form-field">
        <label>${escapeHtml(p.name)} <span class="muted">(${escapeHtml(p.type)}, ${escapeHtml(p.location)})</span></label>
        <input class="test-param-input" data-param-name="${escapeHtml(p.name)}" data-param-type="${escapeHtml(
          p.type
        )}" placeholder="${p.required ? "required" : "optional"}" value="${escapeHtml(
          p.default != null ? String(p.default) : ""
        )}" />
      </div>`
      )
      .join("");
  }

  function collectTestParameters(containerId = "tool-test-params") {
    const params = {};
    const root = $(containerId);
    if (!root) return params;
    root.querySelectorAll(".test-param-input").forEach((input) => {
      const name = input.dataset.paramName;
      const type = input.dataset.paramType;
      const raw = input.value.trim();
      if (!raw) return;
      params[name] = parseDefaultValue(raw, type);
    });
    return params;
  }

  function showTestResult(result) {
    const el = $("tool-test-result");
    el.classList.remove("hidden");
    el.textContent = JSON.stringify(result, null, 2);
  }

  function resetForm() {
    mode = "create";
    $("tool-form-id").value = "";
    $("tool-form-title").textContent = "Create API tool";
    $("tool-form-desc").innerHTML = 'Matches <code>POST /api/v1/api-tools</code>';
    $("tab-tool-create-label").textContent = "Create tool";
    $("tool-form-hint").textContent = "New API tool configuration";
    $("at-name").value = "get_customer_context";
    $("at-description").value =
      "Fetch customer account and order context from the internal API.";
    $("at-endpoint").value = "https://jsonplaceholder.typicode.com/users/{user_id}";
    $("at-auth-key").value = "";
    $("at-auth-hint").textContent = "Optional bearer token (encrypted at rest).";
    $("tool-headers-list").innerHTML = "";
    $("tool-params-list").innerHTML = "";
    addHeaderBlock({ key: "Accept", value: "application/json", is_secret: false });
    addParameterBlock({
      name: "user_id",
      type: "string",
      location: "path",
      required: true,
      description: "User ID",
    });
    renderTestParamInputs(collectParameters());
    $("tool-test-result").classList.add("hidden");
    showFormError(null);
  }

  function populateForm(tool) {
    mode = "edit";
    $("tool-form-id").value = tool.api_tool_id;
    $("tool-form-title").textContent = `Edit · ${tool.name}`;
    $("tool-form-desc").textContent = `Updates via PUT /api/v1/api-tools/${tool.api_tool_id}`;
    $("tab-tool-create-label").textContent = "Edit tool";
    $("tool-form-hint").textContent = `Editing ${tool.name}`;
    $("at-name").value = tool.name || "";
    $("at-description").value = tool.description || "";
    $("at-endpoint").value = tool.endpoint_url || "";
    $("at-auth-key").value = "";
    $("at-auth-hint").textContent =
      "Leave blank to keep the existing encrypted token. Enter a value to replace it.";
    $("tool-headers-list").innerHTML = "";
    (tool.headers || []).forEach((h) => addHeaderBlock(h));
    if (!$("tool-headers-list").children.length) addHeaderBlock();
    $("tool-params-list").innerHTML = "";
    (tool.request_parameters || []).forEach((p) => addParameterBlock(p));
    if (!$("tool-params-list").children.length) addParameterBlock();
    renderTestParamInputs(tool.request_parameters || []);
    $("tool-test-result").classList.add("hidden");
    showFormError(null);
  }

  function renderToolList() {
    const list = $("tool-list");
    const count = $("tool-count");
    list.innerHTML = "";
    count.textContent = `${tools.length} tool${tools.length === 1 ? "" : "s"}`;

    if (!tools.length) {
      list.innerHTML = `
        <li class="empty-state">
          <div class="empty-state-icon">🔧</div>
          <p>No API tools yet — create one to attach to agents.</p>
        </li>`;
      return;
    }

    tools.forEach((tool, i) => {
      const li = document.createElement("li");
      li.className = "agent-item";
      li.style.animationDelay = `${i * 0.06}s`;
      li.innerHTML = `
        <div class="meta">
          <strong>${escapeHtml(tool.name)}</strong>
          <span>${escapeHtml(tool.endpoint_url)}</span>
        </div>
        <div class="agent-actions">
          <span class="badge draft">GET</span>
          <button type="button" class="btn-ghost btn-tool-view" data-id="${tool.api_tool_id}">View</button>
          <button type="button" class="btn-ghost btn-tool-edit" data-id="${tool.api_tool_id}">Edit</button>
          <button type="button" class="btn-ghost btn-tool-delete" data-id="${tool.api_tool_id}">Delete</button>
        </div>`;
      list.appendChild(li);
    });

    list.querySelectorAll(".btn-tool-view").forEach((btn) => {
      btn.addEventListener("click", () => openView(btn.dataset.id));
    });
    list.querySelectorAll(".btn-tool-edit").forEach((btn) => {
      btn.addEventListener("click", () => openEdit(btn.dataset.id));
    });
    list.querySelectorAll(".btn-tool-delete").forEach((btn) => {
      btn.addEventListener("click", () => deleteTool(btn.dataset.id));
    });
  }

  async function loadTools() {
    showListError(null);
    $("tools-loading")?.classList.remove("hidden");
    $("tool-list")?.classList.add("hidden");
    try {
      const envelope = await backendFetch("/api-tools/?page=1&page_size=100");
      const data = unwrapData(envelope);
      tools = data.api_tools || [];
      renderToolList();
      if (onToolsChanged) onToolsChanged(tools);
    } catch (err) {
      showListError(err.message);
    } finally {
      $("tools-loading")?.classList.add("hidden");
      $("tool-list")?.classList.remove("hidden");
    }
  }

  function renderToolView(tool) {
    $("tool-view-title").textContent = tool.name;
    $("tool-view-desc").textContent = `GET /api/v1/api-tools/${tool.api_tool_id}`;

    const headers =
      tool.headers?.length ?
        `<ul class="detail-list">${tool.headers
          .map(
            (h) =>
              `<li><strong>${escapeHtml(h.key)}</strong>${h.is_secret ? " (secret)" : ""}<p>${escapeHtml(h.value)}</p></li>`
          )
          .join("")}</ul>`
      : '<p class="detail-empty">No headers.</p>';

    const params =
      tool.request_parameters?.length ?
        `<ul class="detail-list">${tool.request_parameters
          .map(
            (p) =>
              `<li><strong>${escapeHtml(p.name)}</strong> · ${escapeHtml(p.type)} · ${escapeHtml(p.location)}${
                p.required ? " · required" : ""
              }<p>${escapeHtml(p.description || "—")}</p>${
                p.default != null ? `<code>default: ${escapeHtml(String(p.default))}</code>` : ""
              }</li>`
          )
          .join("")}</ul>`
      : '<p class="detail-empty">No parameters.</p>';

    $("tool-view-body").innerHTML = `
      <div class="detail-hero">
        <span class="badge draft">GET</span>
        <code class="detail-id">${escapeHtml(tool.api_tool_id)}</code>
      </div>
      <div class="detail-sections">
        <section class="detail-section">
          <h3>Basics</h3>
          <dl class="detail-grid">
            <div><dt>Name</dt><dd>${escapeHtml(tool.name)}</dd></div>
            <div class="full"><dt>Description</dt><dd class="detail-block">${escapeHtml(tool.description)}</dd></div>
            <div class="full"><dt>Endpoint</dt><dd><code>${escapeHtml(tool.endpoint_url)}</code></dd></div>
            <div><dt>Auth</dt><dd>${tool.auth_key ? "Configured (hidden)" : "—"}</dd></div>
          </dl>
        </section>
        <section class="detail-section"><h3>Headers</h3>${headers}</section>
        <section class="detail-section"><h3>Request parameters</h3>${params}</section>
      </div>`;

    renderTestParamInputs(tool.request_parameters || [], "tool-view-test-params");
    $("tool-view-test-result").classList.add("hidden");
    $("tool-view-body").dataset.toolId = tool.api_tool_id;
  }

  async function openView(toolId) {
    showToolViewPanel();
    $("tool-view-body").innerHTML = '<p class="detail-loading">Loading…</p>';
    try {
      const envelope = await backendFetch(`/api-tools/${toolId}`);
      renderToolView(unwrapData(envelope));
    } catch (err) {
      $("tool-view-body").innerHTML = `<p class="alert alert-error">${escapeHtml(err.message)}</p>`;
    }
  }

  function openCreate() {
    resetForm();
    showToolFormPanel();
  }

  async function openEdit(toolId) {
    resetForm();
    mode = "edit";
    showFormError(null);
    showToolFormPanel();
    $("tool-form-hint").textContent = "Loading…";
    try {
      const envelope = await backendFetch(`/api-tools/${toolId}`);
      populateForm(unwrapData(envelope));
    } catch (err) {
      showFormError(err.message);
    }
  }

  function closeForm() {
    showToolsListPanel();
  }

  function closeView() {
    showToolsListPanel();
  }

  async function save() {
    const btn = $("btn-save-tool");
    showFormError(null);
    let payload;
    try {
      payload = buildPayload({ includeAuthKey: true });
    } catch (err) {
      showFormError(err.message);
      return false;
    }

    btn.classList.add("loading");
    btn.disabled = true;
    try {
      if (mode === "edit") {
        const id = $("tool-form-id").value;
        await backendFetch(`/api-tools/${id}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
      } else {
        await backendFetch("/api-tools/", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }
      await loadTools();
      showToolsListPanel();
      if (showToast) showToast("API tool saved!");
      return true;
    } catch (err) {
      showFormError(err.message);
      return false;
    } finally {
      btn.classList.remove("loading");
      btn.disabled = false;
    }
  }

  async function deleteTool(toolId) {
    const tool = tools.find((t) => t.api_tool_id === toolId);
    const label = tool?.name || toolId;
    if (!window.confirm(`Delete API tool "${label}"?`)) return;
    try {
      await backendFetch(`/api-tools/${toolId}`, { method: "DELETE" });
      if (showToast) showToast("API tool deleted");
      await loadTools();
    } catch (err) {
      showListError(err.message);
    }
  }

  async function runTest(useSavedId, fromView = false) {
    showFormError(null);
    const paramContainer = fromView ? "tool-view-test-params" : "tool-test-params";
    const authEl = fromView ? $("at-view-test-auth") : $("at-test-auth");
    try {
      const parameters = collectTestParameters(paramContainer);
      const authOverride = authEl?.value.trim() || "";
      if (useSavedId) {
        const id =
          fromView ?
            $("tool-view-body").dataset.toolId
          : $("tool-form-id").value;
        if (!id) throw new Error("Save the tool first or open a saved tool to test.");
        const payload = { parameters };
        if (authOverride) payload.auth_key = authOverride;
        const envelope = await backendFetch(`/api-tools/${id}/test`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        const result = unwrapData(envelope);
        if (fromView) {
          const el = $("tool-view-test-result");
          el.classList.remove("hidden");
          el.textContent = JSON.stringify(result, null, 2);
        } else {
          showTestResult(result);
        }
      } else {
        const payload = {
          endpoint_url: $("at-endpoint").value.trim(),
          headers: collectHeaders().filter((h) => h.key && h.value),
          request_parameters: collectParameters().filter((p) => p.name),
          parameters,
        };
        const auth = authOverride || $("at-auth-key").value.trim();
        if (auth) payload.auth_key = auth;
        const envelope = await backendFetch("/api-tools/test", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        showTestResult(unwrapData(envelope));
      }
      if (showToast) showToast("Test completed");
    } catch (err) {
      if (fromView) {
        const el = $("tool-view-test-result");
        el.classList.remove("hidden");
        el.textContent = err.message;
      } else {
        showFormError(err.message);
      }
    }
  }

  function init(handlers) {
    backendFetch = handlers.backendFetch;
    unwrapData = handlers.unwrapData;
    onToolsChanged = handlers.onToolsChanged;
    showToast = handlers.toast;

    $("btn-add-header")?.addEventListener("click", () => addHeaderBlock());
    $("btn-add-param")?.addEventListener("click", () => {
      addParameterBlock();
      renderTestParamInputs(collectParameters());
    });
    $("tool-params-list")?.addEventListener("input", () => renderTestParamInputs(collectParameters()));
    $("btn-tool-form-cancel")?.addEventListener("click", closeForm);
    $("btn-tool-view-close")?.addEventListener("click", closeView);
    $("btn-view-tool-edit")?.addEventListener("click", () => {
      const id = $("tool-view-body").dataset.toolId;
      if (id) openEdit(id);
    });
    $("btn-save-tool")?.addEventListener("click", save);
    $("btn-test-tool-draft")?.addEventListener("click", () => runTest(false));
    $("btn-test-tool-saved")?.addEventListener("click", () => runTest(true));
    $("btn-test-tool-view")?.addEventListener("click", () => runTest(true, true));
    $("btn-refresh-tools")?.addEventListener("click", loadTools);

    resetForm();
  }

  return {
    init,
    loadTools,
    openCreate,
    openEdit,
    openView,
    closeForm,
    closeView,
    showToolsListPanel,
    hideToolPanels,
  };
})();
