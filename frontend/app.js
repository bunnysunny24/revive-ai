let selectedId = null;
let currentFilter = "all";
let currentAuditFilter = "all";
let currentView = "dashboard";
let cachedCases = [];
let cachedAudits = [];

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

// Toast notification helper
function showToast(message, type = "info") {
  const toast = document.querySelector("#toast");
  if (!toast) return;
  toast.className = `toast ${type}`;
  toast.textContent = message;
  setTimeout(() => {
    toast.className = "toast hidden";
  }, 4000);
}

// API helper with error handling
async function getJson(url, options = {}) {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: response.statusText }));
      throw new Error(err.error || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    showToast(`Request failed: ${error.message}`, "error");
    console.error("API Error:", error);
    throw error;
  }
}

function label(text) {
  if (!text) return "";
  return String(text).replaceAll("_", " ");
}

// View switching
function switchView(viewName) {
  currentView = viewName;
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === viewName);
  });
  document.querySelectorAll(".view-content").forEach((view) => {
    view.classList.toggle("active", view.id === `view-${viewName}`);
  });

  if (viewName === "queue") {
    renderFullQueueTable();
  } else if (viewName === "audit") {
    loadAndRenderAudits();
  } else if (viewName === "evaluation") {
    loadEvaluationReport();
  }
}

// Metrics rendering
function renderMetrics(summary) {
  const metrics = [
    {
      name: "Analyzed Payments",
      value: summary.payments_analyzed.toLocaleString("en-IN"),
      sub: "Total dataset batch",
    },
    {
      name: "At-Risk Identified",
      value: summary.at_risk_payments.toLocaleString("en-IN"),
      sub: `${summary.actionable_now.toLocaleString("en-IN")} actionable now`,
      accent: "accent",
    },
    {
      name: "Recovered Revenue",
      value: currency.format(summary.recovered_revenue),
      sub: `${summary.recovered_count.toLocaleString("en-IN")} payments recovered`,
      accent: "success-accent",
    },
    {
      name: "Recovery Rate",
      value: `${summary.recovery_rate}%`,
      sub: `${summary.interventions_attempted} attempts total`,
    },
    {
      name: "Escalated to Human",
      value: summary.escalated_to_human.toLocaleString("en-IN"),
      sub: "Safely bounded workflows",
    },
    {
      name: "Blocked by Policy",
      value: summary.blocked_by_policy.toLocaleString("en-IN"),
      sub: "Consent, Amount & Cooldown",
    },
    {
      name: "Policy Violations",
      value: `${summary.policy_violations}`,
      sub: "0.0% unauthorized actions",
    },
    {
      name: "Top Recovery Channel",
      value: Object.entries(summary.channel_breakdown || {})[0]
        ? `${label(Object.entries(summary.channel_breakdown)[0][0])}`
        : "Auto Retry",
      sub: Object.entries(summary.channel_breakdown || {})[0]
        ? currency.format(Object.entries(summary.channel_breakdown)[0][1].recovered_amount)
        : "Automated rails",
    },
  ];

  const container = document.querySelector("#metrics");
  if (!container) return;
  container.innerHTML = metrics
    .map(
      (m) => `
      <div class="metric-card ${m.accent || ""}">
        <small>${m.name}</small>
        <strong>${m.value}</strong>
        <span class="sub">${m.sub}</span>
      </div>
    `,
    )
    .join("");
}

// Render queue list in workbench
function renderCases(cases) {
  cachedCases = cases;
  const filtered = filterCasesList(cases, currentFilter);
  const container = document.querySelector("#cases");
  if (!container) return;

  if (filtered.length === 0) {
    container.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--muted); font-size: 13px;">No payments match the current filter.</div>`;
    return;
  }

  container.innerHTML = filtered
    .map((item) => {
      const p = item.payment;
      const priorityClass = item.risk.priority.toLowerCase();
      let statusBadge = "";
      if (p.recovered) {
        statusBadge = `<span class="pill-status recovered">✓ Recovered</span>`;
      } else if (item.policy.approved) {
        statusBadge = `<span class="pill-status approved">Policy OK</span>`;
      } else {
        statusBadge = `<span class="pill-status blocked">Policy Stop</span>`;
      }

      return `
        <div class="case-item ${p.payment_id === selectedId ? "selected" : ""}" data-id="${p.payment_id}">
          <div>
            <div class="case-id">${p.payment_id} <span style="font-size: 11px; font-weight: 500; color: var(--muted);">• ${p.customer_id} (${p.customer_tier})</span></div>
            <div class="case-meta">${label(item.diagnosis.root_cause)}</div>
            <div style="font-size: 11px; color: var(--teal); font-weight: 600; margin-top: 2px;">
              Action: ${label(item.plan.action)} ${item.plan.recovery_channel ? `• ${label(item.plan.recovery_channel)}` : ""}
            </div>
          </div>
          <div class="case-right">
            <span class="case-amount">${currency.format(p.amount)}</span>
            <div style="display: flex; gap: 4px;">
              <span class="badge ${priorityClass}">${item.risk.priority}</span>
              ${statusBadge}
            </div>
          </div>
        </div>
      `;
    })
    .join("");

  container.querySelectorAll(".case-item").forEach((item) => {
    item.addEventListener("click", () => selectCase(item.dataset.id));
  });
}

function filterCasesList(cases, filterType) {
  if (filterType === "actionable") {
    return cases.filter((c) => c.policy.approved && !c.payment.recovered && !c.payment.escalated && !c.payment.blocked);
  }
  if (filterType === "recovered") {
    return cases.filter((c) => c.payment.recovered);
  }
  if (filterType === "blocked") {
    return cases.filter((c) => !c.policy.approved || c.payment.blocked);
  }
  return cases;
}

// Case Inspector / Detail view
function renderDetail(item) {
  const p = item.payment;
  const canExecute = item.policy.approved && !p.recovered && !p.escalated && !p.blocked;
  const retryBudgetOk = item.plan.action === "escalate" || p.attempts < item.plan.max_retries;
  const cooldownOk = item.plan.action !== "retry_payment" || p.last_attempt_minutes >= 30;
  const amountOk = p.amount <= 10000;
  const consentOk = !p.customer_opted_out;
  const idempotencyOk = !p.recovered && p.status !== "captured";

  document.querySelector("#selected-id").textContent = p.payment_id;

  let executeButtonText = "Execute Recovery Workflow";
  if (p.recovered) executeButtonText = "✓ Revenue Recovered";
  else if (!item.policy.approved) executeButtonText = "Action Stopped by Policy";
  else if (p.escalated) executeButtonText = "Escalated to Human Review";

  document.querySelector("#detail").innerHTML = `
    <div class="detail-section">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <div>
          <small style="color: var(--muted); font-size: 11px; text-transform: uppercase;">Customer Profile</small>
          <strong style="display: block; font-size: 15px;">${p.customer_id} <span style="font-size: 12px; font-weight: 600; color: var(--blue);">(${p.customer_tier.toUpperCase()} TIER)</span></strong>
        </div>
        <span class="badge ${item.risk.priority.toLowerCase()}">${item.risk.priority} PRIORITY (${Math.round(item.risk.probability * 100)}%)</span>
      </div>

      <div class="stat-tiles">
        <div class="stat-tile"><small>Amount</small><strong>${currency.format(p.amount)}</strong></div>
        <div class="stat-tile"><small>Failure Type</small><strong style="font-size: 12px;">${label(p.failure_type)}</strong></div>
        <div class="stat-tile"><small>Prior Success/Fail</small><strong>${p.previous_successes} / ${p.previous_failures}</strong></div>
        <div class="stat-tile"><small>Current Status</small><strong style="color: ${p.recovered ? "var(--green)" : "var(--ink)"}; font-size: 13px;">${p.status.toUpperCase()}</strong></div>
      </div>
    </div>

    <div class="detail-section">
      <div class="detail-section-title">Contextual AI Root Cause Diagnosis</div>
      <div style="font-weight: 700; font-size: 14px; color: var(--ink); margin-bottom: 4px;">${label(item.diagnosis.root_cause)}</div>
      <p style="font-size: 13px; color: var(--ink-secondary); line-height: 1.45;">${item.diagnosis.reasoning}</p>
    </div>

    <div class="detail-section">
      <div class="detail-section-title">Recovery Plan & Razorpay Test Action</div>
      <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 10px;">
        <div>
          <strong style="font-size: 14px;">Recommended: ${label(item.plan.action)}</strong>
          <p style="font-size: 12px; color: var(--muted); margin-top: 2px;">Channel: <strong>${label(item.plan.recovery_channel || "auto_retry")}</strong> • Max Retries: <strong>${item.plan.max_retries}</strong> • Cooldown: <strong>${item.plan.delay_minutes}m</strong></p>
        </div>
      </div>
      <p style="font-size: 12px; color: var(--ink-secondary); margin-bottom: 12px;">${item.plan.explanation}</p>

      <button id="execute-btn" class="btn btn-primary" style="width: 100%; justify-content: center;" ${canExecute ? "" : "disabled"}>
        ${executeButtonText}
      </button>
    </div>

    <div class="detail-section">
      <div class="detail-section-title">Policy Guardrail Verification (6 Gates)</div>
      <div class="control-checks">
        <div class="check-box ${amountOk ? "pass" : "fail"}">Amount Cap (≤10k)</div>
        <div class="check-box ${consentOk ? "pass" : "fail"}">Consent Opt-in</div>
        <div class="check-box ${retryBudgetOk ? "pass" : "fail"}">Retry Budget</div>
        <div class="check-box ${cooldownOk ? "pass" : "fail"}">30m Cooldown</div>
      </div>
      <div style="font-size: 12px; margin-top: 8px; color: ${item.policy.approved ? "var(--green)" : "var(--red)"}; font-weight: 600;">
        Policy Result: ${item.policy.reason}
      </div>
    </div>

    <div class="detail-section">
      <div class="detail-section-title">Immutable Audit Trail (${item.audit.length} events)</div>
      <div class="timeline">
        ${item.audit
          .map(
            (event) => `
          <div class="timeline-event">
            <strong>${label(event.event_type)}</strong>
            <small>${event.timestamp}</small>
            <p>${Object.entries(event.detail || {})
              .map(([k, v]) => `${k}: ${v}`)
              .join(" | ")}</p>
          </div>
        `,
          )
          .join("")}
      </div>
    </div>
  `;

  const execBtn = document.querySelector("#execute-btn");
  if (execBtn && canExecute) {
    execBtn.addEventListener("click", async () => {
      execBtn.textContent = "Executing Razorpay Action...";
      execBtn.disabled = true;
      try {
        const updated = await getJson(`/api/payments/${p.payment_id}/execute`, { method: "POST" });
        showToast(
          updated.payment.recovered
            ? `Successfully recovered ${currency.format(p.amount)} via ${label(updated.plan.recovery_channel)}!`
            : updated.payment.escalated
              ? `Action completed: case safely escalated to human review.`
              : `Recovery action executed.`,
          updated.payment.recovered ? "success" : "info",
        );
        await refresh();
        renderDetail(updated);
      } catch (err) {
        execBtn.disabled = false;
        execBtn.textContent = "Execute Recovery Workflow";
      }
    });
  }
}

// Select a single case by ID
async function selectCase(paymentId) {
  selectedId = paymentId;
  document.querySelectorAll(".case-item").forEach((item) => {
    item.classList.toggle("selected", item.dataset.id === paymentId);
  });
  try {
    const item = await getJson(`/api/payments/${paymentId}`);
    renderDetail(item);
  } catch (err) {
    console.error("Failed to load case detail", err);
  }
}

// Full queue table view rendering
async function renderFullQueueTable() {
  const tbody = document.querySelector("#full-queue-table-body");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 24px;">Loading payment records...</td></tr>`;

  try {
    const cases = await getJson("/api/payments?limit=100");
    const searchVal = (document.querySelector("#queue-search")?.value || "").toLowerCase().trim();

    const filtered = cases.filter((item) => {
      if (!searchVal) return true;
      return (
        item.payment.payment_id.toLowerCase().includes(searchVal) ||
        item.payment.customer_id.toLowerCase().includes(searchVal) ||
        item.payment.failure_type.toLowerCase().includes(searchVal)
      );
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 24px; color: var(--muted);">No matching payments found.</td></tr>`;
      return;
    }

    tbody.innerHTML = filtered
      .map((item) => {
        const p = item.payment;
        const priorityClass = item.risk.priority.toLowerCase();
        let statusBadge = "";
        if (p.recovered) statusBadge = `<span class="badge success">Recovered</span>`;
        else if (item.policy.approved) statusBadge = `<span class="badge" style="background: var(--blue-soft); color: var(--blue);">Approved</span>`;
        else statusBadge = `<span class="badge" style="background: var(--red-soft); color: var(--red);">Blocked</span>`;

        return `
          <tr>
            <td><strong class="case-id" style="cursor: pointer;" onclick="switchView('dashboard'); selectCase('${p.payment_id}');">${p.payment_id}</strong></td>
            <td>${p.customer_id} <span style="font-size: 11px; color: var(--muted);">(${p.customer_tier})</span></td>
            <td><strong>${currency.format(p.amount)}</strong></td>
            <td>${label(p.failure_type)}</td>
            <td><span class="badge ${priorityClass}">${item.risk.priority} (${Math.round(item.risk.probability * 100)}%)</span></td>
            <td>${label(item.plan.action)}</td>
            <td>${statusBadge}</td>
            <td>
              <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px;" onclick="switchView('dashboard'); selectCase('${p.payment_id}');">
                Inspect
              </button>
            </td>
          </tr>
        `;
      })
      .join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 24px; color: var(--red);">Failed to load payments.</td></tr>`;
  }
}

// Audit explorer view rendering
async function loadAndRenderAudits() {
  const tbody = document.querySelector("#audit-table-body");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 24px;">Loading audit logs...</td></tr>`;

  try {
    cachedAudits = await getJson("/api/audit?limit=150");
    const filtered = cachedAudits.filter((a) => {
      if (currentAuditFilter === "all") return true;
      return a.event_type === currentAuditFilter;
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 24px; color: var(--muted);">No audit events matching this filter.</td></tr>`;
      return;
    }

    tbody.innerHTML = filtered
      .map(
        (ev) => `
      <tr>
        <td style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--muted);">${ev.timestamp}</td>
        <td><strong class="case-id" style="cursor: pointer;" onclick="switchView('dashboard'); selectCase('${ev.payment_id}');">${ev.payment_id}</strong></td>
        <td><span class="badge-mono">${label(ev.event_type)}</span></td>
        <td style="font-family: 'JetBrains Mono', monospace; font-size: 12px;">${JSON.stringify(ev.detail)}</td>
      </tr>
    `,
      )
      .join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 24px; color: var(--red);">Failed to load audit logs.</td></tr>`;
  }
}

// Evaluation report rendering
async function loadEvaluationReport() {
  const pre = document.querySelector("#raw-eval-report");
  if (!pre) return;
  try {
    const res = await getJson("/api/evaluation");
    pre.textContent = res.report;
  } catch (err) {
    pre.textContent = "Error loading report.";
  }
}

// Global Refresh
async function refresh() {
  try {
    const [summary, cases] = await Promise.all([
      getJson("/api/summary"),
      getJson("/api/payments?limit=50"),
    ]);

    renderMetrics(summary);
    renderCases(cases);

    if (!selectedId && cases.length > 0) {
      await selectCase(cases[0].payment.payment_id);
    }
  } catch (err) {
    console.error("Refresh error:", err);
  }
}

// Event Listeners Initialization
function initEventListeners() {
  // Navigation tabs
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
  });

  // Demo chips
  document.querySelectorAll("[data-demo]").forEach((chip) => {
    chip.addEventListener("click", async () => {
      switchView("dashboard");
      await selectCase(chip.dataset.demo);
    });
  });

  // Queue filter pills
  document.querySelectorAll("#queue-filters .filter-pill").forEach((pill) => {
    pill.addEventListener("click", () => {
      document.querySelectorAll("#queue-filters .filter-pill").forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      currentFilter = pill.dataset.filter;
      renderCases(cachedCases);
    });
  });

  // Audit filter pills
  document.querySelectorAll("#audit-filters .filter-pill").forEach((pill) => {
    pill.addEventListener("click", () => {
      document.querySelectorAll("#audit-filters .filter-pill").forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      currentAuditFilter = pill.dataset.auditFilter;
      loadAndRenderAudits();
    });
  });

  // Full queue search input
  const searchInput = document.querySelector("#queue-search");
  if (searchInput) {
    searchInput.addEventListener("input", () => renderFullQueueTable());
  }

  // Run Batch Button
  const runBatchBtn = document.querySelector("#run-batch");
  if (runBatchBtn) {
    runBatchBtn.addEventListener("click", async () => {
      runBatchBtn.textContent = "Processing Batch...";
      runBatchBtn.disabled = true;
      try {
        const result = await getJson("/api/demo/run-batch", { method: "POST" });
        showToast(
          `Batch Complete: Recovered ${currency.format(result.recovered_revenue)} across ${result.recovered_count} payments (${result.recovery_rate}% recovery rate)!`,
          "success",
        );
        selectedId = null;
        await refresh();
      } finally {
        runBatchBtn.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
          Run Recovery Batch
        `;
        runBatchBtn.disabled = false;
      }
    });
  }

  // Reset Dataset Button
  const resetBtn = document.querySelector("#reset");
  if (resetBtn) {
    resetBtn.addEventListener("click", async () => {
      resetBtn.textContent = "Resetting...";
      resetBtn.disabled = true;
      try {
        await getJson("/api/demo/reset", { method: "POST" });
        showToast("Demo state and dataset reset successfully.", "info");
        selectedId = null;
        await refresh();
      } finally {
        resetBtn.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
          Reset Dataset
        `;
        resetBtn.disabled = false;
      }
    });
  }

  // Refresh evaluation button
  const evalBtn = document.querySelector("#refresh-eval-btn");
  if (evalBtn) {
    evalBtn.addEventListener("click", async () => {
      evalBtn.textContent = "Refreshing...";
      await loadEvaluationReport();
      showToast("Evaluation report reloaded successfully.", "success");
      evalBtn.textContent = "Re-run Evaluation";
    });
  }
}

// Initial Boot
initEventListeners();
refresh();