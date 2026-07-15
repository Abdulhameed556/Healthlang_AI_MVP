/**
 * Agent create / edit form — mirrors POST /agents and PUT /agents/{id}
 */
window.AgentForm = (function () {
  const DEFAULT_RULE = {
    title: "Privacy",
    description: "Never ask for passwords or full card numbers.",
  };
  const DEFAULT_SCENARIO = {
    title: "Refund request",
    short_description: "Customer asks for a refund.",
    prompt: "Verify order details, explain policy, and escalate when needed.",
  };

  let mode = "create";
  let apiTools = [];

  const $ = (id) => document.getElementById(id);

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function selectedLanguages() {
    return [...document.querySelectorAll("#af-languages input:checked")].map((el) => el.value);
  }

  function populateTimezoneSelect() {
    const select = $("af-timezone");
    if (!select) return;
    const zones = window.AgentCatalog?.TIMEZONES || [{ value: "UTC", label: "UTC" }];
    select.innerHTML = "";
    zones.forEach((zone) => {
      const opt = document.createElement("option");
      opt.value = zone.value;
      opt.textContent = zone.label;
      select.appendChild(opt);
    });
  }

  function setTimezone(value) {
    const select = $("af-timezone");
    if (!select) return;
    const normalized = (value || "UTC").trim() || "UTC";
    const hasOption = [...select.options].some((option) => option.value === normalized);
    select.value = hasOption ? normalized : "UTC";
  }

  function setLanguages(languages) {
    const set = new Set(languages || ["english"]);
    document.querySelectorAll("#af-languages input").forEach((el) => {
      el.checked = set.has(el.value);
    });
  }

  function toggleVoiceField() {
    const isVoice = $("af-type").value === "voice";
    $("voice-identity-field").classList.toggle("highlight-required", isVoice);
    $("af-voice-identity").required = isVoice;
  }

  function parseUuidList(raw) {
    if (!raw || !raw.trim()) return [];
    return raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  function selectedToolIds() {
    return [...document.querySelectorAll("#af-tools-checkboxes input:checked")].map(
      (el) => el.value
    );
  }

  function selectedKbIds() {
    const fromChecks = [...document.querySelectorAll("#af-kb-checkboxes input:checked")].map(
      (el) => el.value
    );
    const fromInput = parseUuidList($("af-kb-ids").value);
    return [...new Set([...fromChecks, ...fromInput])];
  }

  function addRuleBlock(data = {}, ruleId = "") {
    const list = $("rules-list");
    const block = document.createElement("div");
    block.className = "repeatable-item";
    if (ruleId) block.dataset.ruleId = ruleId;
    block.innerHTML = `
      <div class="repeatable-head">
        <span class="repeatable-label">Rule</span>
        <button type="button" class="btn-icon-remove" title="Remove rule" aria-label="Remove rule">×</button>
      </div>
      <div class="form-grid">
        <div class="form-field full">
          <label>Title <span class="req">*</span></label>
          <input class="rule-title" maxlength="255" value="${escapeHtml(data.title || "")}" placeholder="Privacy" />
        </div>
        <div class="form-field full">
          <label>Description</label>
          <textarea class="rule-desc" rows="2" maxlength="10000" placeholder="Never ask for passwords…">${escapeHtml(data.description || "")}</textarea>
          <button type="button" class="btn-ghost btn-sm btn-expand">⤢ Expand editor</button>
        </div>
      </div>`;
    block.querySelector(".btn-icon-remove").addEventListener("click", () => {
      if (list.children.length > 1) block.remove();
    });
    list.appendChild(block);
  }

  function addScenarioBlock(data = {}, scenarioId = "") {
    const list = $("scenarios-list");
    const block = document.createElement("div");
    block.className = "repeatable-item";
    if (scenarioId) block.dataset.scenarioId = scenarioId;
    block.innerHTML = `
      <div class="repeatable-head">
        <span class="repeatable-label">Scenario</span>
        <button type="button" class="btn-icon-remove" title="Remove scenario" aria-label="Remove scenario">×</button>
      </div>
      <div class="form-grid">
        <div class="form-field full">
          <label>Title <span class="req">*</span></label>
          <input class="scenario-title" maxlength="255" value="${escapeHtml(data.title || "")}" placeholder="Refund request" />
        </div>
        <div class="form-field full">
          <label>Short description</label>
          <input class="scenario-short" maxlength="500" value="${escapeHtml(data.short_description || "")}" placeholder="Customer asks for a refund." />
        </div>
        <div class="form-field full">
          <label>Prompt</label>
          <textarea class="scenario-prompt" rows="3" maxlength="4000" placeholder="Verify order details…">${escapeHtml(data.prompt || "")}</textarea>
          <button type="button" class="btn-ghost btn-sm btn-expand">⤢ Expand editor</button>
        </div>
      </div>`;
    block.querySelector(".btn-icon-remove").addEventListener("click", () => {
      if (list.children.length > 1) block.remove();
    });
    list.appendChild(block);
  }

  function collectRules() {
    return [...document.querySelectorAll("#rules-list .repeatable-item")].map((block) => {
      const item = {
        title: block.querySelector(".rule-title").value.trim(),
        description: block.querySelector(".rule-desc").value.trim(),
      };
      if (mode === "edit" && block.dataset.ruleId) {
        item.id = block.dataset.ruleId;
      }
      return item;
    });
  }

  function collectScenarios() {
    return [...document.querySelectorAll("#scenarios-list .repeatable-item")].map((block) => {
      const item = {
        title: block.querySelector(".scenario-title").value.trim(),
        short_description: block.querySelector(".scenario-short").value.trim(),
        prompt: block.querySelector(".scenario-prompt").value.trim(),
      };
      if (mode === "edit" && block.dataset.scenarioId) {
        item.id = block.dataset.scenarioId;
      }
      return item;
    });
  }

  function buildPayload() {
    const languages = selectedLanguages();
    if (!languages.length) {
      throw new Error("Select at least one language.");
    }

    const name = $("af-name").value.trim();
    if (!name) throw new Error("Agent name is required.");

    const type = $("af-type").value;
    const voiceIdentity = $("af-voice-identity").value.trim() || null;
    if (type === "voice" && !voiceIdentity) {
      throw new Error("Voice identity is required for voice agents.");
    }

    const rules = collectRules().filter((r) => r.title);
    const scenarios = collectScenarios().filter((s) => s.title);

    const pacing = parseFloat($("af-pacing").value);
    if (Number.isNaN(pacing) || pacing < 0.5 || pacing > 2) {
      throw new Error("Pacing must be between 0.5 and 2.0.");
    }

    const payload = {
      name,
      type,
      brand_config: {
        company_name: $("af-company-name").value.trim(),
        languages,
        prompt: $("af-brand-prompt").value.trim(),
        identity_name: $("af-identity-name").value.trim(),
        timezone: $("af-timezone").value || "UTC",
      },
      personalization_config: {
        tone_profile: $("af-tone").value,
        voice_identity: voiceIdentity,
        pacing,
        formality: $("af-formality").value,
        custom_greeting: $("af-greeting").value.trim(),
        custom_sign_off: $("af-signoff").value.trim(),
        enable_sentiment_analysis: $("af-sentiment").checked,
      },
      rules,
      scenarios,
      knowledge_base_ids: selectedKbIds(),
      api_tool_ids: selectedToolIds(),
    };

    return payload;
  }

  function resetToDefaults() {
    mode = "create";
    $("agent-form-id").value = "";
    $("agent-form-title").textContent = "Create agent";
    $("agent-form-desc").innerHTML =
      'Matches <code>POST /api/v1/agents</code> — all fields from the product API.';
    $("tab-create-label").textContent = "Create agent";
    $("form-sticky-hint").textContent = "New agent configuration";

    $("af-name").value = "Support Bot";
    $("af-type").value = "chat";
    $("af-type").disabled = false;
    $("af-company-name").value = "Acme Global Solutions";
    $("af-identity-name").value = "Alex";
    setTimezone("America/New_York");
    $("af-brand-prompt").value =
      "Represent Acme with warmth and clarity. Never promise refunds without checking policy.";
    setLanguages(["english"]);
    $("af-tone").value = "empathetic_professional";
    $("af-formality").value = "balanced";
    $("af-pacing").value = "1.0";
    $("af-voice-identity").value = "";
    $("af-greeting").value =
      "Hello! Thank you for contacting Acme Support. How can I help you today?";
    $("af-signoff").value =
      "Is there anything else I can assist you with before we finish?";
    $("af-sentiment").checked = true;
    $("af-kb-ids").value = "";

    $("rules-list").innerHTML = "";
    $("scenarios-list").innerHTML = "";
    addRuleBlock(DEFAULT_RULE);
    addScenarioBlock(DEFAULT_SCENARIO);

    document.querySelectorAll("#af-tools-checkboxes input").forEach((el) => {
      el.checked = false;
    });
    document.querySelectorAll("#af-kb-checkboxes input").forEach((el) => {
      el.checked = false;
    });

    toggleVoiceField();
    showError(null);
  }

  function populateFromAgent(agent) {
    mode = "edit";
    $("agent-form-id").value = agent.agent_id;
    $("agent-form-title").textContent = `Edit · ${agent.name}`;
    $("agent-form-desc").textContent = `Updates via PUT /api/v1/agents/${agent.agent_id}`;
    $("tab-create-label").textContent = "Edit agent";
    $("form-sticky-hint").textContent = `Editing ${agent.name}`;

    $("af-name").value = agent.name || "";
    $("af-type").value = agent.type || "chat";
    $("af-type").disabled = true;
    $("af-company-name").value = agent.brand_config?.company_name || "";
    $("af-identity-name").value = agent.brand_config?.identity_name || "";
    setTimezone(agent.brand_config?.timezone || "UTC");
    $("af-brand-prompt").value = agent.brand_config?.prompt || "";
    setLanguages(agent.brand_config?.languages || ["english"]);

    const p = agent.personalization_config || {};
    $("af-tone").value = p.tone_profile || "empathetic_professional";
    $("af-formality").value = p.formality || "balanced";
    $("af-pacing").value = String(p.pacing ?? 1.0);
    $("af-voice-identity").value = p.voice_identity || "";
    $("af-greeting").value = p.custom_greeting || "";
    $("af-signoff").value = p.custom_sign_off || "";
    $("af-sentiment").checked = Boolean(p.enable_sentiment_analysis);

    $("rules-list").innerHTML = "";
    (agent.rules || []).forEach((r) =>
      addRuleBlock({ title: r.title, description: r.description }, r.id)
    );
    if (!$("rules-list").children.length) addRuleBlock(DEFAULT_RULE);

    $("scenarios-list").innerHTML = "";
    (agent.scenarios || []).forEach((s) =>
      addScenarioBlock(
        { title: s.title, short_description: s.short_description, prompt: s.prompt },
        s.id
      )
    );
    if (!$("scenarios-list").children.length) addScenarioBlock(DEFAULT_SCENARIO);

    const kbIds = new Set(agent.knowledge_base_ids || []);
    $("af-kb-ids").value = [...kbIds].join(", ");
    document.querySelectorAll("#af-kb-checkboxes input").forEach((el) => {
      el.checked = kbIds.has(el.value);
    });

    const toolIds = new Set(agent.api_tool_ids || []);
    document.querySelectorAll("#af-tools-checkboxes input").forEach((el) => {
      el.checked = toolIds.has(el.value);
    });

    toggleVoiceField();
    showError(null);
  }

  let expandTarget = null;

  function updateFieldModalCount() {
    const box = $("field-modal-textarea");
    const max = box.maxLength > 0 ? box.maxLength : null;
    $("field-modal-count").textContent = max
      ? `${box.value.length} / ${max} characters`
      : `${box.value.length} characters`;
  }

  function openFieldModal(textarea, label) {
    const modal = $("field-modal");
    const box = $("field-modal-textarea");
    if (!modal || !box) return;
    $("field-modal-title").textContent = label ? `Edit · ${label}` : "Edit";
    box.maxLength = textarea.maxLength > 0 ? textarea.maxLength : 100000;
    box.value = textarea.value;
    expandTarget = textarea;
    modal.classList.remove("hidden");
    updateFieldModalCount();
    box.focus();
    box.setSelectionRange(box.value.length, box.value.length);
  }

  function closeFieldModal() {
    $("field-modal")?.classList.add("hidden");
    expandTarget = null;
  }

  function saveFieldModal() {
    if (expandTarget) {
      expandTarget.value = $("field-modal-textarea").value;
      expandTarget.dispatchEvent(new Event("input", { bubbles: true }));
    }
    closeFieldModal();
  }

  function initFieldModal() {
    document.addEventListener("click", (e) => {
      const expandBtn = e.target.closest(".btn-expand");
      if (expandBtn) {
        const field = expandBtn.closest(".form-field");
        const ta = field?.querySelector("textarea");
        if (ta) {
          const labelEl = field.querySelector("label");
          const label = labelEl ? labelEl.textContent.replace("*", "").trim() : "";
          openFieldModal(ta, label);
        }
        return;
      }
      if (e.target.closest("#field-modal-close, #field-modal-cancel, [data-field-modal-close]")) {
        closeFieldModal();
      }
    });
    $("field-modal-save")?.addEventListener("click", saveFieldModal);
    $("field-modal-textarea")?.addEventListener("input", updateFieldModalCount);
    document.addEventListener("keydown", (e) => {
      const modal = $("field-modal");
      if (e.key === "Escape" && modal && !modal.classList.contains("hidden")) {
        closeFieldModal();
      }
    });
  }

  function showError(message) {
    const el = $("form-error");
    if (!message) {
      el.classList.add("hidden");
      el.textContent = "";
      return;
    }
    el.textContent = message;
    el.classList.remove("hidden");
  }

  function renderApiTools(tools) {
    apiTools = tools || [];
    renderApiToolsInternal(apiTools);
  }

  function renderApiToolsInternal(tools) {
    apiTools = tools;
    const container = $("af-tools-checkboxes");
    if (!tools.length) {
      container.innerHTML =
        '<span class="field-hint">No API tools yet — use the <strong>API tools</strong> tab to create one.</span>';
      return;
    }
    container.innerHTML = tools
      .map(
        (t) => `
      <label class="checkbox-pill block-check">
        <input type="checkbox" value="${t.api_tool_id}" />
        <span>${escapeHtml(t.name)}</span>
        <code class="tool-id">${t.api_tool_id}</code>
      </label>`
      )
      .join("");
  }

  function openCreate() {
    resetToDefaults();
    showPanel();
  }

  async function openEdit(agentId, backendFetch, unwrapData) {
    resetToDefaults();
    mode = "edit";
    showError(null);
    $("form-sticky-hint").textContent = "Loading agent…";
    try {
      const envelope = await backendFetch(`/agents/${agentId}`);
      const agent = unwrapData(envelope);
      populateFromAgent(agent);
      showPanel();
    } catch (err) {
      showError(err.message);
    }
  }

  function showPanel() {
    $("tab-view")?.classList.add("hidden");
    ApiToolsUI.hideToolPanels();
    window.TagsUI?.hideTagPanels?.();
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelector('.tab[data-tab="create"]').classList.add("active");
    $("tab-list").classList.add("hidden");
    $("tab-create").classList.remove("hidden");
  }

  function closePanel() {
    $("tab-create").classList.add("hidden");
    $("tab-view")?.classList.add("hidden");
    ApiToolsUI.hideToolPanels();
    window.TagsUI?.hideTagPanels?.();
    $("tab-list").classList.remove("hidden");
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelector('.tab[data-tab="list"]').classList.add("active");
  }

  async function save(backendFetch) {
    const btn = $("btn-save-agent");
    showError(null);
    let payload;
    try {
      payload = buildPayload();
    } catch (err) {
      showError(err.message);
      return false;
    }

    btn.classList.add("loading");
    btn.disabled = true;
    try {
      if (mode === "edit") {
        const id = $("agent-form-id").value;
        const { type: _type, ...updatePayload } = payload;
        await backendFetch(`/agents/${id}`, {
          method: "PUT",
          body: JSON.stringify(updatePayload),
        });
      } else {
        await backendFetch("/agents/", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }
      closePanel();
      return true;
    } catch (err) {
      showError(err.message);
      return false;
    } finally {
      btn.classList.remove("loading");
      btn.disabled = false;
    }
  }

  function init(handlers) {
    populateTimezoneSelect();
    initFieldModal();
    $("af-type").addEventListener("change", toggleVoiceField);
    $("btn-add-rule").addEventListener("click", () => addRuleBlock({ title: "", description: "" }));
    $("btn-add-scenario").addEventListener("click", () =>
      addScenarioBlock({ title: "", short_description: "", prompt: "" })
    );
    $("btn-form-cancel").addEventListener("click", closePanel);
    $("btn-save-agent").addEventListener("click", () => handlers.onSave());

    resetToDefaults();

    if (handlers.loadApiTools) {
      handlers.loadApiTools().then(renderApiTools).catch(() => renderApiTools([]));
    }
  }

  return {
    init,
    openCreate,
    openEdit,
    closePanel,
    save,
    buildPayload,
    resetToDefaults,
    showError,
    renderApiTools,
  };
})();
