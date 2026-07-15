/**
 * SupportOS Agent Studio — demo UI
 */
(function () {
  const { backendBaseUrl, aiBaseUrl } = window.DEMO_CONFIG;

  const STORAGE_KEYS = {
    token: "demo_access_token",
    orgId: "demo_organization_id",
    email: "demo_email",
    sessionId: "demo_session_id",
    agentId: "demo_agent_id",
  };

  const state = {
    agents: [],
    apiTools: [],
    sessionId: localStorage.getItem(STORAGE_KEYS.sessionId) || null,
    selectedAgentId: localStorage.getItem(STORAGE_KEYS.agentId) || null,
    currentView: "login",
    conversationState: null,
    sessionClosed: false,
    endPromptDismissed: false,
    transferPromptDismissed: false,
    sessionLabel: null,
    versionsAgentId: null,
  };

  const CONVERSATION_STATE_LABELS = {
    in_progress: "In progress",
    waiting_on_customer: "Waiting on you",
    end_conversation: "End conversation",
    transfer_to_live_support: "Transfer to live support",
  };

  // States that close the session server-side; the UI auto-closes on these.
  const CLOSING_STATES = ["end_conversation", "transfer_to_live_support"];

  const $ = (id) => document.getElementById(id);

  function getToken() {
    return localStorage.getItem(STORAGE_KEYS.token);
  }

  function getOrgId() {
    return localStorage.getItem(STORAGE_KEYS.orgId);
  }

  function authHeaders() {
    const headers = { "Content-Type": "application/json" };
    const token = getToken();
    const orgId = getOrgId();
    if (token) headers.Authorization = `Bearer ${token}`;
    if (orgId) headers["X-Organization-Id"] = orgId;
    return headers;
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function renderMarkdown(text) {
    if (!text) return "";
    if (typeof marked === "undefined" || typeof DOMPurify === "undefined") {
      return escapeHtml(text);
    }
    marked.setOptions({ breaks: true, gfm: true });
    const html = marked.parse(String(text));
    return DOMPurify.sanitize(html, {
      USE_PROFILES: { html: true },
      ADD_ATTR: ["target", "rel"],
    });
  }

  function formatResponseTimeSeconds(ms) {
    if (ms == null || Number.isNaN(Number(ms))) return null;
    return `${(Number(ms) / 1000).toFixed(2)}s`;
  }

  function formatConversationState(value) {
    if (!value) return "—";
    return CONVERSATION_STATE_LABELS[value] || value.replace(/_/g, " ");
  }

  function conversationStateClass(value) {
    if (!value) return "";
    return value.replace(/_/g, "-");
  }

  function updateConversationState(value) {
    state.conversationState = value || null;
    const wrap = $("conversation-state-wrap");
    const pill = $("conversation-state-pill");
    if (!wrap || !pill) return;

    if (!state.sessionId || !value) {
      wrap.classList.add("hidden");
      pill.textContent = "—";
      pill.className = "state-pill";
      return;
    }

    wrap.classList.remove("hidden");
    pill.textContent = state.sessionClosed ? "Closed" : formatConversationState(value);
    pill.className = `state-pill ${state.sessionClosed ? "closed" : conversationStateClass(value)}`;
    syncSessionActionPrompts();
  }

  function hideSessionActionPrompts() {
    $("end-conversation-prompt")?.classList.add("hidden");
    $("transfer-support-prompt")?.classList.add("hidden");
  }

  function isSessionActionPromptBlocking() {
    if (state.sessionClosed || !state.sessionId) return false;
    if (
      state.conversationState === "end_conversation" &&
      !state.endPromptDismissed
    ) {
      return true;
    }
    if (
      state.conversationState === "transfer_to_live_support" &&
      !state.transferPromptDismissed
    ) {
      return true;
    }
    return false;
  }

  function syncSessionActionPrompts() {
    const showEnd =
      state.conversationState === "end_conversation" &&
      !state.sessionClosed &&
      !state.endPromptDismissed;
    const showTransfer =
      state.conversationState === "transfer_to_live_support" &&
      !state.sessionClosed &&
      !state.transferPromptDismissed;

    $("end-conversation-prompt")?.classList.toggle("hidden", !showEnd);
    $("transfer-support-prompt")?.classList.toggle("hidden", !showTransfer);

    if (showEnd || showTransfer) {
      enableChatInput(false);
    } else if (!state.sessionClosed && state.sessionId) {
      enableChatInput(true);
    }
  }

  function finishSession({ systemMessage, toastMessage, bannerMessage }) {
    state.sessionClosed = true;
    hideSessionActionPrompts();
    const banner = $("session-closed-banner");
    if (banner) {
      banner.textContent = bannerMessage;
      banner.classList.remove("hidden");
    }
    updateConversationState(state.conversationState);
    setChatComposeMode("blocked");
    appendChatMessage("system", systemMessage);
    toast(toastMessage);
  }

  function autoCloseSession(stateValue) {
    state.conversationState = stateValue;
    const isTransfer = stateValue === "transfer_to_live_support";
    finishSession({
      systemMessage: isTransfer
        ? "You've been handed off to our live support team — this AI session is now closed."
        : "This conversation has been closed.",
      toastMessage: isTransfer ? "Transferred to live support" : "Conversation ended",
      bannerMessage: isTransfer
        ? "You've been connected to live support. Start a new session to chat with the AI agent again."
        : "This conversation is closed. Start a new session to chat again.",
    });
  }

  function resetChatSessionUi() {
    state.conversationState = null;
    state.sessionClosed = false;
    state.endPromptDismissed = false;
    state.transferPromptDismissed = false;
    state.sessionLabel = null;
    hideSessionActionPrompts();
    const banner = $("session-closed-banner");
    if (banner) {
      banner.textContent = "This conversation is closed. Start a new session to test again.";
      banner.classList.add("hidden");
    }
    updateConversationState(null);
    setChatComposeMode("idle");
  }

  function handleEndConversationConfirm() {
    finishSession({
      systemMessage:
        "Conversation closed. Summary and ticket creation will be wired here next.",
      toastMessage: "Conversation ended",
      bannerMessage: "This conversation is closed. Start a new session to test again.",
    });
  }

  function handleEndConversationContinue() {
    state.endPromptDismissed = true;
    $("end-conversation-prompt")?.classList.add("hidden");
    state.conversationState = "in_progress";
    updateConversationState("in_progress");
    appendChatMessage("system", "Continuing the conversation — ask anything else.");
    enableChatInput(true);
    $("chat-input").focus();
    toast("Session still open");
  }

  function handleTransferConfirm() {
    finishSession({
      systemMessage:
        "Transferring you to live support. A human agent handoff will connect here next.",
      toastMessage: "Transfer to live support",
      bannerMessage:
        "Handed off to live support. Start a new session to test the agent again.",
    });
  }

  function handleTransferContinue() {
    state.transferPromptDismissed = true;
    $("transfer-support-prompt")?.classList.add("hidden");
    state.conversationState = "in_progress";
    updateConversationState("in_progress");
    appendChatMessage("system", "Staying with the AI agent for now — you can keep chatting here.");
    enableChatInput(true);
    $("chat-input").focus();
    toast("Staying with AI agent");
  }

  function showError(el, message) {
    if (!message) {
      el.classList.add("hidden");
      el.textContent = "";
      return;
    }
    el.textContent = message;
    el.classList.remove("hidden");
  }

  function toast(message, type = "success") {
    const stack = $("toast-stack");
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transform = "translateX(24px)";
      el.style.transition = "0.3s ease";
      setTimeout(() => el.remove(), 300);
    }, 3200);
  }

  function setLoading(btn, loading) {
    if (!btn) return;
    btn.classList.toggle("loading", loading);
    btn.disabled = loading;
  }

  function updateStepNav(view) {
    const order = ["login", "agents", "tickets", "chat", "eval", "chat-eval"];
    const idx = order.indexOf(view);
    document.querySelectorAll(".step-pill").forEach((pill) => {
      const step = pill.dataset.step;
      const stepIdx = order.indexOf(step);
      pill.classList.remove("active", "done");
      if (stepIdx < idx) pill.classList.add("done");
      if (step === view) pill.classList.add("active");
      pill.disabled = stepIdx > idx && !getToken();
    });
  }

  function showView(name) {
    state.currentView = name;
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    const target = $(`view-${name}`);
    target.classList.remove("active");
    void target.offsetWidth;
    target.classList.add("active");
    updateStepNav(name);
    updateHeader();
  }

  function updateHeader() {
    const chip = $("header-meta");
    const logoutBtn = $("btn-logout");
    const email = localStorage.getItem(STORAGE_KEYS.email);

    if (!getToken()) {
      chip.classList.remove("online");
      chip.querySelector(".user-text").textContent = "Not signed in";
      logoutBtn.classList.add("hidden");
      return;
    }

    chip.classList.add("online");
    chip.querySelector(".user-text").textContent = email || "Signed in";
    logoutBtn.classList.remove("hidden");
  }

  function logout() {
    Object.values(STORAGE_KEYS).forEach((k) => localStorage.removeItem(k));
    state.sessionId = null;
    state.selectedAgentId = null;
    state.agents = [];
    showView("login");
    toast("Signed out", "success");
  }

  async function backendFetch(path, options = {}) {
    const res = await fetch(`${backendBaseUrl}${path}`, {
      ...options,
      headers: { ...authHeaders(), ...(options.headers || {}) },
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = body.detail || body.message || JSON.stringify(body);
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return body;
  }

  async function aiFetch(path, options = {}) {
    const res = await fetch(`${aiBaseUrl}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = body.detail || body.message || JSON.stringify(body);
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return body;
  }

  function unwrapData(envelope) {
    if (envelope && envelope.data !== undefined) return envelope.data;
    return envelope;
  }

  // --- Login ---

  async function handleLogin() {
    const email = $("login-email").value.trim();
    const password = $("login-password").value;
    const btn = $("btn-login");
    showError($("login-error"), null);

    if (!email || !password) {
      showError($("login-error"), "Email and password are required.");
      return;
    }

    setLoading(btn, true);
    try {
      const envelope = await backendFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password, is_new: false }),
      });
      const data = unwrapData(envelope);
      localStorage.setItem(STORAGE_KEYS.token, data.access_token);
      localStorage.setItem(STORAGE_KEYS.email, data.email);
      const org = data.organizations?.[0];
      if (org) localStorage.setItem(STORAGE_KEYS.orgId, org.organization_id);
      toast(`Welcome back, ${data.email.split("@")[0]}!`);
      showView("agents");
      await loadAgents();
      loadApiTools();
    } catch (err) {
      showError($("login-error"), err.message);
    } finally {
      setLoading(btn, false);
    }
  }

  // --- Agents ---

  function renderAgentList() {
    const list = $("agent-list");
    const count = $("agent-count");
    list.innerHTML = "";
    count.textContent = `${state.agents.length} agent${state.agents.length === 1 ? "" : "s"}`;

    if (!state.agents.length) {
      list.innerHTML = `
        <li class="empty-state">
          <div class="empty-state-icon">🤖</div>
          <p>No agents yet — create your first one.</p>
        </li>`;
      return;
    }

    state.agents.forEach((agent, i) => {
      const li = document.createElement("li");
      li.className = "agent-item";
      li.style.animationDelay = `${i * 0.06}s`;
      const statusClass = agent.status === "deployed" ? "deployed" : "draft";
      li.innerHTML = `
        <div class="meta">
          <strong>${escapeHtml(agent.name)}</strong>
          <span>${agent.agent_id}</span>
        </div>
        <div class="agent-actions">
          <span class="badge ${statusClass}">${agent.status}</span>
          <button type="button" class="btn-ghost btn-view" data-id="${agent.agent_id}">View</button>
          <button type="button" class="btn-ghost btn-edit" data-id="${agent.agent_id}">Edit</button>
          <button type="button" class="btn-ghost btn-publish" data-id="${agent.agent_id}">Publish</button>
          <button type="button" class="btn-ghost btn-versions" data-id="${agent.agent_id}">Versions</button>
          <button type="button" class="btn-primary btn-test" data-id="${agent.agent_id}" style="padding:0.45rem 0.85rem;font-size:0.8rem">Test</button>
        </div>`;
      list.appendChild(li);
    });

    list.querySelectorAll(".btn-view").forEach((btn) => {
      btn.addEventListener("click", () => {
        AgentView.openView(btn.dataset.id, backendFetch, unwrapData, state.apiTools);
      });
    });
    list.querySelectorAll(".btn-edit").forEach((btn) => {
      btn.addEventListener("click", () => {
        openAgentEdit(btn.dataset.id);
      });
    });
    list.querySelectorAll(".btn-publish").forEach((btn) => {
      btn.addEventListener("click", () => publishAgent(btn.dataset.id, btn));
    });
    list.querySelectorAll(".btn-versions").forEach((btn) => {
      btn.addEventListener("click", () => openVersionsModal(btn.dataset.id));
    });
    list.querySelectorAll(".btn-test").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.selectedAgentId = btn.dataset.id;
        localStorage.setItem(STORAGE_KEYS.agentId, btn.dataset.id);
        showView("chat");
        populateAgentSelect();
      });
    });
  }

  function buildAgentQuery() {
    const params = new URLSearchParams();
    params.set("page", "1");
    params.set("page_size", "50");
    const search = $("agent-search")?.value.trim();
    if (search) params.set("search", search);
    const type = $("agent-filter-type")?.value;
    if (type) params.set("agent_type", type);
    const status = $("agent-filter-status")?.value;
    if (status) params.set("status", status);
    return params.toString();
  }

  async function loadAgents() {
    showError($("agents-error"), null);
    $("agents-loading").classList.remove("hidden");
    $("agent-list").classList.add("hidden");

    try {
      const envelope = await backendFetch(`/agents/?${buildAgentQuery()}`);
      const data = unwrapData(envelope);
      state.agents = data.agents || [];
      renderAgentList();
      populateAgentSelect();
      if (window.EvalUI) EvalUI.populateAgentSelect(state.agents);
    } catch (err) {
      showError($("agents-error"), err.message);
    } finally {
      $("agents-loading").classList.add("hidden");
      $("agent-list").classList.remove("hidden");
    }
  }

  async function loadApiTools() {
    try {
      const envelope = await backendFetch("/api-tools/?page=1&page_size=100");
      const data = unwrapData(envelope);
      state.apiTools = data.api_tools || [];
      AgentForm.renderApiTools(state.apiTools);
      return state.apiTools;
    } catch {
      state.apiTools = [];
      AgentForm.renderApiTools([]);
      return [];
    }
  }

  function openAgentEdit(agentId) {
    AgentView.closePanel();
    AgentForm.openEdit(agentId, backendFetch, unwrapData);
  }

  async function saveAgentForm() {
    const ok = await AgentForm.save(backendFetch);
    if (ok) {
      toast("Agent saved!");
      await loadAgents();
    }
  }

  async function publishAgent(agentId, btn) {
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Publishing…";
    }
    try {
      const envelope = await backendFetch(`/agents/${agentId}/publish`, {
        method: "POST",
      });
      const version = unwrapData(envelope).version;
      const changes = (version.changes_applied || []).join("; ");
      toast(
        `Published v${version.version_number}${changes ? ` — ${changes}` : ""} (not live yet)`
      );
      await loadAgents();
      return version;
    } catch (err) {
      toast(`Publish failed: ${err.message}`, "error");
      return null;
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Publish";
      }
    }
  }

  async function deployVersion(agentId, versionId, btn) {
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Deploying…";
    }
    try {
      await backendFetch(`/agents/${agentId}/versions/${versionId}/deploy`, {
        method: "POST",
      });
      toast("Version deployed — live for test chat!");
      await loadAgents();
      return true;
    } catch (err) {
      toast(`Deploy failed: ${err.message}`, "error");
      return false;
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Deploy";
      }
    }
  }

  // Convenience for the test-chat flow: publish the draft then immediately go live.
  async function publishAndDeploy(agentId, btn) {
    const original = btn ? btn.textContent : null;
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Publishing…";
    }
    try {
      const version = await publishAgent(agentId);
      if (version) {
        if (btn) btn.textContent = "Deploying…";
        await deployVersion(agentId, version.version_id);
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = original;
      }
    }
  }

  // --- Version history modal ---

  function closeVersionsModal() {
    $("versions-modal").classList.add("hidden");
    state.versionsAgentId = null;
  }

  async function openVersionsModal(agentId) {
    state.versionsAgentId = agentId;
    const modal = $("versions-modal");
    const body = $("versions-modal-body");
    body.innerHTML = '<p class="muted">Loading…</p>';
    modal.classList.remove("hidden");
    await refreshVersions();
  }

  async function refreshVersions() {
    const agentId = state.versionsAgentId;
    if (!agentId) return;
    const body = $("versions-modal-body");
    try {
      const envelope = await backendFetch(
        `/agents/${agentId}/versions?page=1&page_size=50`
      );
      renderVersions(agentId, unwrapData(envelope));
    } catch (err) {
      body.innerHTML = `<p class="error-text">${escapeHtml(err.message)}</p>`;
    }
  }

  function renderVersions(agentId, data) {
    const body = $("versions-modal-body");
    const items = data.items || [];
    if (!items.length) {
      body.innerHTML =
        '<p class="muted">No versions yet — publish the draft to create v1.</p>';
      return;
    }
    body.innerHTML = items
      .map((item) => {
        const changes = (item.changes_applied || []).join("; ") || "—";
        const note = item.change_note
          ? `<div class="version-note">📝 ${escapeHtml(item.change_note)}</div>`
          : "";
        const liveBadge = item.is_deployed
          ? '<span class="badge deployed">live</span>'
          : "";
        const deployBtn = item.is_deployed
          ? '<button type="button" class="btn-ghost" disabled>Deployed</button>'
          : `<button type="button" class="btn-primary btn-deploy-version" data-version="${item.version_id}" style="padding:0.4rem 0.8rem;font-size:0.8rem">Deploy</button>`;
        return `
          <div class="version-row">
            <div class="version-meta">
              <div class="version-head">
                <strong>v${item.version_number}</strong>
                ${liveBadge}
                <span class="version-date">${formatDate(item.created_at)}</span>
              </div>
              <div class="version-changes">${escapeHtml(changes)}</div>
              ${note}
            </div>
            <div class="version-actions">
              <button type="button" class="btn-ghost btn-view-version" data-version="${item.version_id}" style="padding:0.4rem 0.8rem;font-size:0.8rem">View</button>
              ${deployBtn}
            </div>
          </div>`;
      })
      .join("");

    body.querySelectorAll(".btn-view-version").forEach((btn) => {
      btn.addEventListener("click", () => {
        const item = items.find((v) => v.version_id === btn.dataset.version);
        if (!item) return;
        closeVersionsModal();
        AgentView.viewSnapshot(item.configuration_snapshot, state.apiTools, {
          title: `${item.configuration_snapshot.name || "Agent"} — v${item.version_number}`,
          desc: `Version v${item.version_number} snapshot (read-only) · ${formatDate(item.created_at)}`,
        });
      });
    });

    body.querySelectorAll(".btn-deploy-version").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const ok = await deployVersion(agentId, btn.dataset.version, btn);
        if (ok) await refreshVersions();
      });
    });
  }

  function formatDate(value) {
    if (!value) return "";
    try {
      return new Date(value).toLocaleString();
    } catch {
      return value;
    }
  }

  // --- Chat ---

  function populateAgentSelect() {
    const select = $("chat-agent-select");
    select.innerHTML = "";
    state.agents.forEach((agent) => {
      const opt = document.createElement("option");
      opt.value = agent.agent_id;
      opt.textContent = `${agent.name} (${agent.status})`;
      if (agent.agent_id === state.selectedAgentId) opt.selected = true;
      select.appendChild(opt);
    });
    if (select.value) {
      state.selectedAgentId = select.value;
      localStorage.setItem(STORAGE_KEYS.agentId, select.value);
    }
  }

  function appendChatMessage(role, text, timingMs) {
    const log = $("chat-log");
    $("chat-empty")?.classList.add("hidden");

    const wrap = document.createElement("div");
    wrap.className = `msg ${role}`;
    if (role === "system") {
      wrap.innerHTML = `<div class="msg-system">${escapeHtml(text)}</div>`;
      log.appendChild(wrap);
      log.scrollTop = log.scrollHeight;
      return;
    }

    const label = role === "user" ? "You" : "Agent";
    const responseTime =
      role === "agent" && timingMs != null ? formatResponseTimeSeconds(timingMs) : null;
    const metaExtra = responseTime ? ` · ${responseTime}` : "";
    const bodyHtml = role === "agent" ? renderMarkdown(text) : escapeHtml(text);
    wrap.innerHTML = `
      <span class="msg-meta">${label}${metaExtra}</span>
      <div class="msg-bubble${role === "agent" ? " msg-markdown" : ""}">${bodyHtml}</div>`;
    log.appendChild(wrap);
    log.scrollTop = log.scrollHeight;
  }

  function setTyping(show) {
    $("typing-indicator").classList.toggle("hidden", !show);
    if (show) {
      const log = $("chat-log");
      log.scrollTop = log.scrollHeight;
    }
  }

  function updateChatStatus(text, responseTime) {
    $("chat-status").querySelector(".session-value").textContent = text;
    const timingEl = $("chat-last-response");
    if (!timingEl) return;
    if (responseTime) {
      timingEl.textContent = `Last response: ${responseTime}`;
      timingEl.classList.remove("hidden");
    } else {
      timingEl.textContent = "";
      timingEl.classList.add("hidden");
    }
  }

  function setChatComposeMode(mode) {
    const compose = $("chat-compose");
    const startBtn = $("btn-compose-start");
    const sendBtn = $("btn-send");
    const input = $("chat-input");
    if (!compose || !startBtn || !sendBtn || !input) return;

    compose.classList.remove("chat-compose-idle", "chat-compose-active", "chat-compose-blocked");

    if (mode === "active") {
      compose.classList.add("chat-compose-active");
      startBtn.classList.add("hidden");
      sendBtn.classList.remove("hidden");
      input.placeholder = "Type a message… (Enter to send)";
      return;
    }

    if (mode === "blocked") {
      compose.classList.add("chat-compose-blocked");
      startBtn.classList.remove("hidden");
      startBtn.querySelector(".btn-label").textContent = "Start new session";
      sendBtn.classList.add("hidden");
      input.disabled = true;
      input.placeholder = "Session ended — start a new session to continue";
      return;
    }

    compose.classList.add("chat-compose-idle");
    startBtn.classList.remove("hidden");
    startBtn.querySelector(".btn-label").textContent = "Start new session";
    sendBtn.classList.add("hidden");
    input.disabled = true;
    input.placeholder = "Start a session to send messages…";
  }

  function enableChatInput(enabled) {
    if (!state.sessionId || state.sessionClosed || isSessionActionPromptBlocking()) {
      $("chat-input").disabled = true;
      $("btn-send").disabled = true;
      return;
    }
    $("chat-input").disabled = !enabled;
    $("btn-send").disabled = !enabled;
  }

  async function startSession(triggerBtn) {
    const btn = triggerBtn || $("btn-compose-start");
    const sidebarBtn = $("btn-new-session");
    showError($("chat-error"), null);
    const agentId = $("chat-agent-select").value;

    if (!agentId) {
      showError($("chat-error"), "Select an agent first.");
      return;
    }

    setLoading(btn, true);
    if (sidebarBtn && sidebarBtn !== btn) setLoading(sidebarBtn, true);
    try {
      resetChatSessionUi();
      state.sessionId = null;
      localStorage.removeItem(STORAGE_KEYS.sessionId);
      const data = await aiFetch("/chat/sessions", {
        method: "POST",
        body: JSON.stringify({ agent_id: agentId, mode: "test" }),
      });
      state.sessionId = data.session_id;
      localStorage.setItem(STORAGE_KEYS.sessionId, data.session_id);
      const log = $("chat-log");
      log.querySelectorAll(".msg").forEach((m) => m.remove());
      const empty = $("chat-empty");
      if (empty) empty.classList.remove("hidden");
      state.sessionLabel = `${data.agent_name} · v${data.version_number}`;
      updateChatStatus(state.sessionLabel);
      updateConversationState(data.conversation_state || "in_progress");
      setChatComposeMode("active");
      enableChatInput(true);
      appendChatMessage("agent", `Session started with ${data.agent_name}. How can I help?`);
      $("chat-empty")?.classList.add("hidden");
      toast("New session started");
      $("chat-input").focus();
    } catch (err) {
      showError($("chat-error"), err.message);
      setChatComposeMode("idle");
    } finally {
      setLoading(btn, false);
      if (sidebarBtn && sidebarBtn !== btn) setLoading(sidebarBtn, false);
    }
  }

  async function sendMessage() {
    showError($("chat-error"), null);
    const message = $("chat-input").value.trim();
    if (!message || !state.sessionId || state.sessionClosed) return;

    $("chat-input").value = "";
    appendChatMessage("user", message);
    enableChatInput(false);
    setTyping(true);

    try {
      const data = await aiFetch("/chat/messages", {
        method: "POST",
        body: JSON.stringify({ session_id: state.sessionId, message }),
      });
      setTyping(false);
      const reply = data.message || "(no message)";
      const totalMs = data.timing_ms?.total;
      appendChatMessage("agent", reply, totalMs);
      const responseTime = formatResponseTimeSeconds(totalMs);
      updateChatStatus(state.sessionLabel || "Session active", responseTime);
      if (CLOSING_STATES.includes(data.conversation_state)) {
        autoCloseSession(data.conversation_state);
      } else {
        updateConversationState(data.conversation_state);
      }
    } catch (err) {
      setTyping(false);
      showError($("chat-error"), err.message);
    } finally {
      if (!isSessionActionPromptBlocking() && !state.sessionClosed && state.sessionId) {
        enableChatInput(true);
        $("chat-input").focus();
      }
    }
  }

  // --- Tabs ---

  function showAgentsListPanel() {
    AgentForm.closePanel();
    AgentView.closePanel();
    ApiToolsUI.hideToolPanels();
    TagsUI.hideTagPanels();
    $("tab-list").classList.remove("hidden");
    document.querySelectorAll(".tabs .tab").forEach((t) => t.classList.remove("active"));
    document.querySelector('.tab[data-tab="list"]')?.classList.add("active");
  }

  function setupTabs() {
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        const name = tab.dataset.tab;
        if (name === "create") {
          AgentForm.openCreate();
          return;
        }
        if (name === "tool-create") {
          ApiToolsUI.openCreate();
          return;
        }
        if (name === "tools") {
          ApiToolsUI.showToolsListPanel();
          ApiToolsUI.loadTools();
          return;
        }
        if (name === "tag-create") {
          TagsUI.openCreate();
          return;
        }
        if (name === "tags") {
          TagsUI.showTagsListPanel();
          TagsUI.loadTags();
          return;
        }
        showAgentsListPanel();
      });
    });
  }

  function setupStepNav() {
    document.querySelectorAll(".step-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        if (!pill.classList.contains("done") && !pill.classList.contains("active") && !getToken()) return;
        const step = pill.dataset.step;
        if (step === "login" && getToken()) return;
        if (step === "agents" && getToken()) showView("agents");
        if (step === "tickets" && getToken()) {
          showView("tickets");
          TicketsUI.load();
        }
        if (step === "chat" && getToken()) {
          showView("chat");
          populateAgentSelect();
        }
        if (step === "eval" && getToken()) {
          if (window.EvalUI) EvalUI.populateAgentSelect(state.agents);
          showView("eval");
        }
        if (step === "chat-eval" && getToken()) showView("chat-eval");
      });
    });
  }

  // --- Init ---

  function init() {
    AgentForm.init({
      loadApiTools,
      onSave: saveAgentForm,
    });
    AgentView.init({
      onEdit: openAgentEdit,
    });
    ApiToolsUI.init({
      backendFetch,
      unwrapData,
      toast,
      onToolsChanged: (tools) => {
        state.apiTools = tools;
        AgentForm.renderApiTools(tools);
      },
    });
    TicketsUI.init({ backendFetch, unwrapData, toast });
    TagsUI.init({ backendFetch, unwrapData, toast });

    setupTabs();
    setupStepNav();

    $("btn-login").addEventListener("click", handleLogin);
    $("login-password").addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleLogin();
    });
    $("btn-logout").addEventListener("click", logout);
    $("btn-refresh-agents").addEventListener("click", loadAgents);
    $("agent-filter-type")?.addEventListener("change", loadAgents);
    $("agent-filter-status")?.addEventListener("change", loadAgents);
    $("agent-search")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") loadAgents();
    });
    $("btn-go-chat").addEventListener("click", () => {
      showView("chat");
      populateAgentSelect();
    });
    $("btn-go-tickets").addEventListener("click", () => {
      showView("tickets");
      TicketsUI.load();
    });
    $("btn-tickets-back-agents").addEventListener("click", () => showView("agents"));
    $("btn-back-agents").addEventListener("click", () => showView("agents"));
    $("btn-new-session").addEventListener("click", (e) => startSession(e.currentTarget));
    $("btn-compose-start").addEventListener("click", (e) => startSession(e.currentTarget));
    $("btn-end-confirm").addEventListener("click", handleEndConversationConfirm);
    $("btn-end-continue").addEventListener("click", handleEndConversationContinue);
    $("btn-transfer-confirm").addEventListener("click", handleTransferConfirm);
    $("btn-transfer-continue").addEventListener("click", handleTransferContinue);
    $("btn-deploy-agent").addEventListener("click", (e) => {
      const id = $("chat-agent-select").value;
      if (id) publishAndDeploy(id, e.currentTarget);
    });
    $("versions-modal-close").addEventListener("click", closeVersionsModal);
    $("versions-modal").querySelector("[data-versions-modal-close]")
      .addEventListener("click", closeVersionsModal);
    $("versions-modal-publish").addEventListener("click", async (e) => {
      if (!state.versionsAgentId) return;
      const version = await publishAgent(state.versionsAgentId, e.currentTarget);
      if (version) await refreshVersions();
    });
    $("btn-send").addEventListener("click", sendMessage);
    $("btn-go-eval")?.addEventListener("click", () => {
      if (window.EvalUI) EvalUI.populateAgentSelect(state.agents);
      showView("eval");
    });
    $("btn-back-from-eval")?.addEventListener("click", () => showView("agents"));
    $("btn-go-chat-eval")?.addEventListener("click", () => showView("chat-eval"));
    $("btn-back-from-chat-eval")?.addEventListener("click", () => showView("agents"));
    $("chat-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    $("chat-agent-select").addEventListener("change", (e) => {
      state.selectedAgentId = e.target.value;
      localStorage.setItem(STORAGE_KEYS.agentId, e.target.value);
    });

    if (window.EvalUI) EvalUI.init(state.agents);
    if (window.ChatEvalUI) ChatEvalUI.init();

    if (getToken()) {
      showView("agents");
      loadAgents();
      loadApiTools();
    } else {
      showView("login");
    }

    setChatComposeMode("idle");
    if (state.sessionId) {
      state.sessionId = null;
      localStorage.removeItem(STORAGE_KEYS.sessionId);
    }
    updateChatStatus("No active session");
  }

  document.addEventListener("DOMContentLoaded", init);
})();
