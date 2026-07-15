/**
 * SupportOS — Retrieval Evaluation UI
 * Talks to POST /ai/api/v1/retrieval-evaluation/run
 *            GET  /ai/api/v1/retrieval-evaluation/{run_id}
 */
(function () {
  const $ = (id) => document.getElementById(id);

  let _pollTimer = null;

  function evalFetch(path, options = {}) {
    const base = window.DEMO_CONFIG.evalBaseUrl;
    return fetch(`${base}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    }).then(async (res) => {
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body.detail || body.message || JSON.stringify(body);
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }
      return body;
    });
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text || "";
    return div.innerHTML;
  }

  function stopPolling() {
    if (_pollTimer) {
      clearInterval(_pollTimer);
      _pollTimer = null;
    }
  }

  function setStatusBadge(status) {
    const badge = $("eval-status-badge");
    if (!badge) return;
    badge.textContent = status;
    badge.className = `eval-status-badge eval-status-${(status || "").toLowerCase()}`;
  }

  function renderAggregateScores(scores) {
    const container = $("eval-aggregate-scores");
    if (!container) return;
    const entries = Object.entries(scores || {});
    if (!entries.length) {
      container.innerHTML = "<p class='eval-empty'>No aggregate scores yet.</p>";
      return;
    }
    container.innerHTML = `
      <table class="eval-scores-table">
        <thead><tr><th>Metric</th><th>Score</th></tr></thead>
        <tbody>
          ${entries
            .map(
              ([name, score]) => `
            <tr>
              <td>${escapeHtml(name)}</td>
              <td class="eval-score-cell ${score >= 0.5 ? "score-pass" : "score-fail"}">
                ${score.toFixed(3)}
              </td>
            </tr>`
            )
            .join("")}
        </tbody>
      </table>`;
  }

  function renderQuestionResults(results) {
    if (!results || !results.length) return "<p class='eval-empty'>No question results.</p>";
    return results
      .map(
        (r, idx) => `
      <details class="eval-question-item" ${idx === 0 ? "open" : ""}>
        <summary class="eval-question-summary">
          <span class="eval-q-num">Q${idx + 1}</span>
          <span class="eval-q-text">${escapeHtml(r.question)}</span>
        </summary>
        <div class="eval-question-body">
          <p class="eval-field-label">Expected output</p>
          <p class="eval-field-value">${escapeHtml(r.expected_output)}</p>

          <p class="eval-field-label">Retrieved context (${r.retrieved_context.length})</p>
          <ol class="eval-context-list">
            ${r.retrieved_context.map((c) => `<li>${escapeHtml(c)}</li>`).join("")}
          </ol>

          <p class="eval-field-label">Metrics</p>
          <table class="eval-metrics-table">
            <thead>
              <tr><th>Metric</th><th>Score</th><th>Threshold</th><th>Pass</th><th>Reason</th></tr>
            </thead>
            <tbody>
              ${r.metrics
                .map(
                  (m) => `
                <tr>
                  <td>${escapeHtml(m.name)}</td>
                  <td class="${m.success ? "score-pass" : "score-fail"}">${m.score.toFixed(3)}</td>
                  <td>${m.threshold.toFixed(2)}</td>
                  <td class="${m.success ? "score-pass" : "score-fail"}">${m.success ? "✓" : "✗"}</td>
                  <td class="eval-reason">${escapeHtml(m.reason)}</td>
                </tr>`
                )
                .join("")}
            </tbody>
          </table>
        </div>
      </details>`
      )
      .join("");
  }

  function renderEntryReports(entryReports) {
    const container = $("eval-entry-reports");
    if (!container) return;
    if (!entryReports || !entryReports.length) {
      container.innerHTML = "<p class='eval-empty'>No entry reports yet.</p>";
      return;
    }

    container.innerHTML = entryReports
      .map((entry, i) => {
        const shortId = String(entry.kb_entry_id).slice(0, 8);
        const statusClass = entry.status === "COMPLETED" ? "score-pass" : entry.status === "FAILED" ? "score-fail" : "";
        const aggEntries = Object.entries(entry.aggregate_scores || {});
        const aggHtml = aggEntries.length
          ? `<table class="eval-scores-table" style="margin-bottom:0.75rem">
              <thead><tr><th>Metric</th><th>Score</th></tr></thead>
              <tbody>
                ${aggEntries
                  .map(
                    ([name, score]) => `
                  <tr>
                    <td>${escapeHtml(name)}</td>
                    <td class="eval-score-cell ${score >= 0.5 ? "score-pass" : "score-fail"}">${score.toFixed(3)}</td>
                  </tr>`
                  )
                  .join("")}
              </tbody>
            </table>`
          : "";

        return `
          <div class="eval-entry-item" data-open="${i === 0}">
            <button type="button" class="eval-entry-summary" onclick="this.parentElement.dataset.open = this.parentElement.dataset.open === 'true' ? 'false' : 'true'">
              <span class="eval-q-num">Entry ${i + 1}</span>
              <code class="eval-entry-id">${escapeHtml(shortId)}…</code>
              <span class="${statusClass}" style="margin-left:auto;font-size:0.75rem">${escapeHtml(entry.status)}</span>
            </button>
            <div class="eval-entry-body">
              ${entry.error ? `<p class="alert alert-error" style="margin-bottom:0.75rem">${escapeHtml(entry.error)}</p>` : ""}
              ${aggHtml}
              ${renderQuestionResults(entry.question_results || [])}
            </div>
          </div>`;
      })
      .join("");
  }

  async function pollStatus(runId) {
    try {
      const report = await evalFetch(`/retrieval-evaluation/${runId}`);
      setStatusBadge(report.status);
      renderAggregateScores(report.aggregate_scores || {});
      renderEntryReports(report.entry_reports || []);

      if (report.status === "COMPLETED" || report.status === "FAILED") {
        stopPolling();
        const btn = $("btn-run-eval");
        if (btn) {
          btn.disabled = false;
          btn.querySelector(".btn-label").textContent = "Run evaluation";
        }
        if (report.status === "FAILED" && report.error) {
          const errorEl = $("eval-error");
          errorEl.textContent = report.error;
          errorEl.classList.remove("hidden");
        }
      }
    } catch {
      // network blip — keep polling
    }
  }

  function parseEntryIds(raw) {
    return raw
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  async function runEvaluation() {
    const agentId = $("eval-agent-select")?.value;
    const rawIds = ($("eval-kb-entry-ids")?.value || "").trim();
    const kbEntryIds = parseEntryIds(rawIds);
    const topK = parseInt($("eval-top-k")?.value || "5", 10);
    const maxContexts = parseInt($("eval-max-contexts")?.value || "4", 10);
    const maxGoldens = parseInt($("eval-max-goldens")?.value || "2", 10);
    const errorEl = $("eval-error");
    const btn = $("btn-run-eval");

    errorEl.classList.add("hidden");
    errorEl.textContent = "";

    if (!agentId) {
      errorEl.textContent = "Select an agent first.";
      errorEl.classList.remove("hidden");
      return;
    }
    if (!kbEntryIds.length) {
      errorEl.textContent = "At least one KB Entry ID is required.";
      errorEl.classList.remove("hidden");
      return;
    }
    if (kbEntryIds.length > 10) {
      errorEl.textContent = "Maximum 10 KB Entry IDs allowed.";
      errorEl.classList.remove("hidden");
      return;
    }

    stopPolling();
    btn.disabled = true;
    btn.querySelector(".btn-label").textContent = "Starting…";
    setStatusBadge("PENDING");
    $("eval-run-id").textContent = "—";
    $("eval-aggregate-scores").innerHTML = "";
    $("eval-entry-reports").innerHTML = "";
    $("eval-results-panel").classList.remove("hidden");

    try {
      const res = await evalFetch("/retrieval-evaluation/run", {
        method: "POST",
        body: JSON.stringify({
          agent_id: agentId,
          kb_entry_ids: kbEntryIds,
          top_k: topK,
          max_contexts: maxContexts,
          max_goldens_per_context: maxGoldens,
        }),
      });
      $("eval-run-id").textContent = res.run_id;
      setStatusBadge(res.status);
      btn.querySelector(".btn-label").textContent = "Running…";
      _pollTimer = setInterval(() => pollStatus(res.run_id), 2500);
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.classList.remove("hidden");
      btn.disabled = false;
      btn.querySelector(".btn-label").textContent = "Run evaluation";
    }
  }

  function populateAgentSelect(agents) {
    // agent input is now a plain text field — pre-fill only if exactly one agent exists
    const input = $("eval-agent-select");
    if (!input || input.value) return;
    if (agents && agents.length === 1) {
      input.value = agents[0].agent_id;
    }
  }

  function init(agents) {
    populateAgentSelect(agents || []);
    $("btn-run-eval")?.addEventListener("click", runEvaluation);
  }

  window.EvalUI = { init, populateAgentSelect };
})();
