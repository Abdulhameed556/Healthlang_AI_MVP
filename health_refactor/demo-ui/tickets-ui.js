/**
 * Tickets tab — list/search (GET /tickets) + detail (GET /tickets/{id}).
 */
window.TicketsUI = (function () {
  let backendFetch = null;
  let unwrapData = null;
  let toast = null;
  let currentTicketId = null;

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

  function formatDuration(seconds) {
    if (seconds == null) return "—";
    const total = Number(seconds);
    if (Number.isNaN(total)) return "—";
    if (total < 60) return `${total}s`;
    const mins = Math.floor(total / 60);
    const secs = total % 60;
    return secs ? `${mins}m ${secs}s` : `${mins}m`;
  }

  function statusClass(status) {
    switch ((status || "").toLowerCase()) {
      case "resolved":
        return "ticket-pill-resolved";
      case "open":
        return "ticket-pill-open";
      case "transferred":
        return "ticket-pill-transferred";
      case "failed":
        return "ticket-pill-failed";
      default:
        return "ticket-pill-unknown";
    }
  }

  function sentimentClass(sentiment) {
    switch ((sentiment || "").toLowerCase()) {
      case "positive":
        return "ticket-pill-resolved";
      case "negative":
        return "ticket-pill-failed";
      case "neutral":
        return "ticket-pill-unknown";
      default:
        return "ticket-pill-unknown";
    }
  }

  function renderTags(tags) {
    if (!tags?.length) return '<span class="detail-muted">No tags</span>';
    return `<div class="ticket-tags">${tags
      .map((t) => `<span class="ticket-tag">${escapeHtml(t)}</span>`)
      .join("")}</div>`;
  }

  function renderList(tickets) {
    const list = $("ticket-list");
    const count = $("ticket-count");
    list.innerHTML = "";
    count.textContent = `${tickets.length} ticket${tickets.length === 1 ? "" : "s"}`;

    if (!tickets.length) {
      list.innerHTML = `
        <li class="empty-state">
          <div class="empty-state-icon">🎫</div>
          <p>No tickets match these filters yet.</p>
        </li>`;
      return;
    }

    tickets.forEach((ticket, i) => {
      const li = document.createElement("li");
      li.className = "agent-item ticket-item";
      li.style.animationDelay = `${i * 0.05}s`;
      const agentLabel = ticket.agent_name
        ? `${escapeHtml(ticket.agent_name)}${
            ticket.agent_type ? ` · ${escapeHtml(ticket.agent_type)}` : ""
          }`
        : "Unassigned";
      const customer = ticket.customer_details
        ? escapeHtml(ticket.customer_details)
        : "—";
      li.innerHTML = `
        <div class="meta">
          <strong><code class="ticket-ref">${escapeHtml(ticket.reference)}</code></strong>
          <span>${agentLabel} · ${customer} · ${escapeHtml(formatDate(ticket.created_at))}</span>
        </div>
        <div class="agent-actions">
          <span class="ticket-pill ${statusClass(ticket.status)}">${escapeHtml(ticket.status)}</span>
          <span class="badge draft">${escapeHtml(ticket.interface_type)}</span>
          <button type="button" class="btn-ghost btn-ticket-view" data-id="${ticket.ticket_id}">View</button>
        </div>`;
      list.appendChild(li);
    });

    list.querySelectorAll(".btn-ticket-view").forEach((btn) => {
      btn.addEventListener("click", () => openDetail(btn.dataset.id));
    });
  }

  function buildQuery() {
    const params = new URLSearchParams();
    params.set("page", "1");
    params.set("page_size", "50");
    const search = $("ticket-search").value.trim();
    if (search) params.set("search", search);
    const status = $("ticket-filter-status").value;
    if (status) params.set("status", status);
    const interfaceType = $("ticket-filter-interface").value;
    if (interfaceType) params.set("interface_type", interfaceType);
    const dateRange = $("ticket-filter-date").value;
    if (dateRange) params.set("date_range", dateRange);
    const tagRaw = $("ticket-filter-tag")?.value || "";
    tagRaw
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean)
      .forEach((tag) => params.append("tag", tag));
    return params.toString();
  }

  async function load() {
    closeDetail();
    const errEl = $("tickets-error");
    errEl.classList.add("hidden");
    $("tickets-loading").classList.remove("hidden");
    $("ticket-list").classList.add("hidden");

    try {
      const envelope = await backendFetch(`/tickets/?${buildQuery()}`);
      const data = unwrapData(envelope);
      renderList(data.tickets || []);
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    } finally {
      $("tickets-loading").classList.add("hidden");
      $("ticket-list").classList.remove("hidden");
    }
  }

  function renderMessages(messages) {
    if (!messages?.length) {
      return '<p class="detail-empty">No conversation history recorded.</p>';
    }
    return `<div class="ticket-transcript">${messages
      .map((m) => {
        const isUser = (m.speaker || "").toLowerCase() === "user";
        const label = isUser ? "Customer" : "Agent";
        return `
          <div class="ticket-msg ${isUser ? "user" : "ai"}">
            <span class="ticket-msg-meta">${label} · ${escapeHtml(formatDate(m.spoken_at))}</span>
            <div class="ticket-msg-bubble">${escapeHtml(m.content)}</div>
          </div>`;
      })
      .join("")}</div>`;
  }

  function renderDetail(t) {
    $("ticket-detail-title").textContent = t.reference || "Ticket";
    $("ticket-detail-desc").textContent = `GET /api/v1/tickets/${t.ticket_id}`;

    const number = t.agent_number ? escapeHtml(t.agent_number) : "—";

    $("ticket-detail-body").innerHTML = `
      <div class="detail-hero">
        <div>
          <span class="ticket-pill ${statusClass(t.status)}">${escapeHtml(t.status)}</span>
          <span class="badge draft">${escapeHtml(t.interface_type)}</span>
          ${
            t.sentiment
              ? `<span class="ticket-pill ${sentimentClass(t.sentiment)}">${escapeHtml(t.sentiment)}</span>`
              : ""
          }
        </div>
        <code class="detail-id">${escapeHtml(t.reference)}</code>
      </div>

      <div class="detail-sections">
        <section class="detail-section">
          <h3>Metadata</h3>
          <dl class="detail-grid">
            <div><dt>Status</dt><dd>${escapeHtml(t.status)}</dd></div>
            <div><dt>Sentiment</dt><dd>${escapeHtml(t.sentiment || "—")}</dd></div>
            <div><dt>Resolution</dt><dd>${escapeHtml(t.resolution || "—")}</dd></div>
            <div><dt>Channel</dt><dd>${escapeHtml(t.interface_type)}</dd></div>
            <div><dt>From</dt><dd>${escapeHtml(t.from_number || "—")}</dd></div>
            <div><dt>Customer</dt><dd>${escapeHtml(t.customer_details || "—")}</dd></div>
            <div><dt>Duration</dt><dd>${escapeHtml(formatDuration(t.duration_seconds))}</dd></div>
            <div><dt>Created</dt><dd>${escapeHtml(formatDate(t.created_at))}</dd></div>
            <div><dt>Updated</dt><dd>${escapeHtml(formatDate(t.updated_at))}</dd></div>
            <div class="full"><dt>Tags</dt><dd>${renderTags(t.tags)}</dd></div>
          </dl>
        </section>

        <section class="detail-section">
          <h3>Agent</h3>
          <dl class="detail-grid">
            <div><dt>Name</dt><dd>${escapeHtml(t.agent_name || "—")}</dd></div>
            <div><dt>Type</dt><dd>${escapeHtml(t.agent_type || "—")}</dd></div>
            <div><dt>Number</dt><dd>${number}</dd></div>
          </dl>
        </section>

        <section class="detail-section">
          <h3>Summary</h3>
          <dl class="detail-grid">
            <div class="full"><dt>General summary</dt><dd class="detail-block">${escapeHtml(t.general_summary || "—")}</dd></div>
            <div class="full"><dt>Journey</dt><dd class="detail-block">${escapeHtml(t.journey || "—")}</dd></div>
          </dl>
        </section>

        <section class="detail-section">
          <h3>Session history</h3>
          ${renderMessages(t.messages)}
        </section>
      </div>`;
  }

  function showPanel() {
    $("ticket-list-card").classList.add("hidden");
    $("ticket-detail-panel").classList.remove("hidden");
  }

  function closeDetail() {
    currentTicketId = null;
    $("ticket-detail-panel").classList.add("hidden");
    $("ticket-list-card").classList.remove("hidden");
  }

  async function openDetail(ticketId) {
    currentTicketId = ticketId;
    showPanel();
    $("ticket-detail-body").innerHTML =
      '<p class="detail-loading">Loading ticket details…</p>';
    $("ticket-detail-error").classList.add("hidden");

    try {
      const envelope = await backendFetch(`/tickets/${ticketId}`);
      const ticket = unwrapData(envelope);
      renderDetail(ticket);
    } catch (err) {
      $("ticket-detail-body").innerHTML = "";
      const errEl = $("ticket-detail-error");
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  }

  function init(handlers) {
    backendFetch = handlers.backendFetch;
    unwrapData = handlers.unwrapData;
    toast = handlers.toast;

    $("btn-refresh-tickets").addEventListener("click", load);
    $("btn-ticket-detail-close").addEventListener("click", closeDetail);
    $("ticket-filter-status").addEventListener("change", load);
    $("ticket-filter-interface").addEventListener("change", load);
    $("ticket-filter-date").addEventListener("change", load);
    $("ticket-search").addEventListener("keydown", (e) => {
      if (e.key === "Enter") load();
    });
    $("ticket-filter-tag")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") load();
    });
  }

  return {
    init,
    load,
    openDetail,
    closeDetail,
  };
})();
