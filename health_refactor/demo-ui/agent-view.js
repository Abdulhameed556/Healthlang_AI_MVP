/**
 * Read-only agent detail view — GET /agents/{id}
 */
window.AgentView = (function () {
  let currentAgentId = null;
  let onEdit = null;

  const $ = (id) => document.getElementById(id);

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  function formatDate(value) {
    if (!value) return "—";
    try {
      return new Date(value).toLocaleString();
    } catch {
      return String(value);
    }
  }

  function toolNameMap(tools) {
    const map = new Map();
    (tools || []).forEach((t) => map.set(t.api_tool_id, t.name));
    return map;
  }

  function renderList(items, renderItem, emptyLabel) {
    if (!items?.length) {
      return `<p class="detail-empty">${escapeHtml(emptyLabel)}</p>`;
    }
    return `<ul class="detail-list">${items.map(renderItem).join("")}</ul>`;
  }

  function renderDetail(agent, apiTools) {
    const toolsById = toolNameMap(apiTools);
    const p = agent.personalization_config || {};
    const brand = agent.brand_config || {};
    const statusClass = agent.status === "deployed" ? "deployed" : "draft";

    $("agent-view-title").textContent = agent.name || "Agent";
    $("agent-view-desc").textContent = `GET /api/v1/agents/${agent.agent_id}`;

    const kbIds = agent.knowledge_base_ids || [];
    const toolIds = agent.api_tool_ids || [];

    $("agent-view-body").innerHTML = `
      <div class="detail-hero">
        <div>
          <span class="badge ${statusClass}">${escapeHtml(agent.status)}</span>
          <span class="detail-type">${escapeHtml(agent.type)} agent</span>
        </div>
        <code class="detail-id">${escapeHtml(agent.agent_id)}</code>
      </div>

      <div class="detail-sections">
        <section class="detail-section">
          <h3>Basics</h3>
          <dl class="detail-grid">
            <div><dt>Name</dt><dd>${escapeHtml(agent.name)}</dd></div>
            <div><dt>Type</dt><dd>${escapeHtml(agent.type)}</dd></div>
            <div><dt>Status</dt><dd>${escapeHtml(agent.status)}</dd></div>
            <div><dt>Created</dt><dd>${escapeHtml(formatDate(agent.created_at))}</dd></div>
            <div><dt>Updated</dt><dd>${escapeHtml(formatDate(agent.updated_at))}</dd></div>
          </dl>
        </section>

        <section class="detail-section">
          <h3>Brand identity</h3>
          <dl class="detail-grid">
            <div><dt>Company</dt><dd>${escapeHtml(brand.company_name || "—")}</dd></div>
            <div><dt>Identity name</dt><dd>${escapeHtml(brand.identity_name || "—")}</dd></div>
            <div><dt>Timezone</dt><dd>${escapeHtml(brand.timezone || "UTC")}</dd></div>
            <div class="full"><dt>Languages</dt><dd>${escapeHtml((brand.languages || []).join(", ") || "—")}</dd></div>
            <div class="full"><dt>Brand voice prompt</dt><dd class="detail-block">${escapeHtml(brand.prompt || "—")}</dd></div>
          </dl>
        </section>

        <section class="detail-section">
          <h3>Personalization</h3>
          <dl class="detail-grid">
            <div><dt>Tone</dt><dd>${escapeHtml(p.tone_profile || "—")}</dd></div>
            <div><dt>Formality</dt><dd>${escapeHtml(p.formality || "—")}</dd></div>
            <div><dt>Pacing</dt><dd>${escapeHtml(String(p.pacing ?? "—"))}</dd></div>
            <div><dt>Voice identity</dt><dd>${escapeHtml(p.voice_identity || "—")}</dd></div>
            <div><dt>Sentiment analysis</dt><dd>${p.enable_sentiment_analysis ? "Enabled" : "Disabled"}</dd></div>
            <div class="full"><dt>Greeting</dt><dd class="detail-block">${escapeHtml(p.custom_greeting || "—")}</dd></div>
            <div class="full"><dt>Sign-off</dt><dd class="detail-block">${escapeHtml(p.custom_sign_off || "—")}</dd></div>
          </dl>
        </section>

        <section class="detail-section">
          <h3>Rules</h3>
          ${renderList(
            agent.rules,
            (r) => `
              <li>
                <strong>${escapeHtml(r.title)}</strong>
                ${r.description ? `<p>${escapeHtml(r.description)}</p>` : ""}
              </li>`,
            "No rules configured."
          )}
        </section>

        <section class="detail-section">
          <h3>Scenarios</h3>
          ${renderList(
            agent.scenarios,
            (s) => `
              <li>
                <strong>${escapeHtml(s.title)}</strong>
                ${s.short_description ? `<p class="detail-muted">${escapeHtml(s.short_description)}</p>` : ""}
                ${s.prompt ? `<pre class="detail-pre">${escapeHtml(s.prompt)}</pre>` : ""}
              </li>`,
            "No scenarios configured."
          )}
        </section>

        <section class="detail-section">
          <h3>Attachments</h3>
          <dl class="detail-grid">
            <div class="full">
              <dt>Knowledge bases</dt>
              <dd>
                ${
                  kbIds.length
                    ? `<ul class="detail-ids">${kbIds.map((id) => `<li><code>${escapeHtml(id)}</code></li>`).join("")}</ul>`
                    : "—"
                }
              </dd>
            </div>
            <div class="full">
              <dt>API tools</dt>
              <dd>
                ${
                  toolIds.length
                    ? `<ul class="detail-ids">${toolIds
                        .map((id) => {
                          const name = toolsById.get(id);
                          return `<li><span>${escapeHtml(name || "Tool")}</span> <code>${escapeHtml(id)}</code></li>`;
                        })
                        .join("")}</ul>`
                    : "—"
                }
              </dd>
            </div>
          </dl>
        </section>
      </div>`;
  }

  function showPanel() {
    $("tab-list").classList.add("hidden");
    $("tab-create").classList.add("hidden");
    ApiToolsUI.hideToolPanels();
    $("tab-view").classList.remove("hidden");
    document.querySelectorAll(".tabs .tab").forEach((t) => t.classList.remove("active"));
  }

  function closePanel() {
    currentAgentId = null;
    $("tab-view").classList.add("hidden");
    ApiToolsUI.hideToolPanels();
    $("tab-list").classList.remove("hidden");
    $("btn-view-edit").classList.remove("hidden");
    document.querySelectorAll(".tabs .tab").forEach((t) => t.classList.remove("active"));
    document.querySelector('.tab[data-tab="list"]')?.classList.add("active");
  }

  async function openView(agentId, backendFetch, unwrapData, apiTools = []) {
    currentAgentId = agentId;
    showPanel();
    $("btn-view-edit").classList.remove("hidden");
    $("agent-view-body").innerHTML = '<p class="detail-loading">Loading agent details…</p>';
    $("agent-view-error").classList.add("hidden");

    try {
      const envelope = await backendFetch(`/agents/${agentId}`);
      const agent = unwrapData(envelope);
      renderDetail(agent, apiTools);
    } catch (err) {
      $("agent-view-body").innerHTML = "";
      const errEl = $("agent-view-error");
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  }

  // Render an immutable version snapshot (same shape as the agent config) read-only.
  function viewSnapshot(snapshot, apiTools = [], opts = {}) {
    currentAgentId = snapshot.agent_id || null;
    showPanel();
    $("agent-view-error").classList.add("hidden");
    renderDetail(snapshot, apiTools);
    if (opts.title) $("agent-view-title").textContent = opts.title;
    if (opts.desc) $("agent-view-desc").textContent = opts.desc;
    // Version snapshots are immutable — hide the Edit action.
    $("btn-view-edit").classList.add("hidden");
  }

  function init(handlers) {
    onEdit = handlers.onEdit;
    $("btn-view-close").addEventListener("click", closePanel);
    $("btn-view-edit").addEventListener("click", () => {
      if (!currentAgentId || !onEdit) return;
      const id = currentAgentId;
      closePanel();
      onEdit(id);
    });
  }

  return {
    init,
    openView,
    viewSnapshot,
    closePanel,
  };
})();
