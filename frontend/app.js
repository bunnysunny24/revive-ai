let selectedId = null;

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

async function getJson(url, options) {
  const response = await fetch(url, options);
  return response.json();
}

function renderMetrics(summary) {
  const metrics = [
    ["Payments analyzed", summary.payments_analyzed.toLocaleString("en-IN")],
    ["At-risk payments", summary.at_risk_payments.toLocaleString("en-IN")],
    ["Recovered revenue", currency.format(summary.recovered_revenue)],
    ["Recovery rate", `${summary.recovery_rate}%`],
    ["Interventions", summary.interventions_attempted],
    ["Escalated", summary.escalated_to_human],
    ["Policy blocks", summary.blocked_by_policy],
    ["Policy violations", summary.policy_violations],
  ];

  document.querySelector("#metrics").innerHTML = metrics
    .map(([label, value]) => `<div class="metric"><small>${label}</small><strong>${value}</strong></div>`)
    .join("");
}

function renderCases(cases) {
  document.querySelector("#queue-count").textContent = `${cases.length} highest priority`;
  document.querySelector("#cases").innerHTML = cases
    .map((item) => {
      const payment = item.payment;
      const priority = item.risk.priority.toLowerCase();
      return `
        <button class="case ${payment.payment_id === selectedId ? "selected" : ""}" data-id="${payment.payment_id}">
          <span>
            <strong>${payment.payment_id}</strong>
            <small>${item.diagnosis.root_cause.replaceAll("_", " ")}</small>
          </span>
          <span>
            <span class="amount">${currency.format(payment.amount)}</span>
            <span class="badge ${priority}">${item.risk.priority}</span>
          </span>
        </button>
      `;
    })
    .join("");

  document.querySelectorAll(".case").forEach((button) => {
    button.addEventListener("click", () => selectCase(button.dataset.id));
  });
}

function renderDetail(item) {
  const payment = item.payment;
  document.querySelector("#selected-id").textContent = payment.payment_id;
  document.querySelector("#detail").innerHTML = `
    <div class="split">
      <div class="tile"><small>Amount</small><strong>${currency.format(payment.amount)}</strong></div>
      <div class="tile"><small>Status</small><strong>${payment.status}</strong></div>
      <div class="tile"><small>Recovery probability</small><strong>${Math.round(item.risk.probability * 100)}%</strong></div>
      <div class="tile"><small>Policy</small><strong>${item.policy.approved ? "Approved" : "Blocked"}</strong></div>
    </div>

    <div class="tile">
      <small>Diagnosis</small>
      <strong>${item.diagnosis.root_cause.replaceAll("_", " ")}</strong>
      <p class="muted">${item.diagnosis.reasoning}</p>
    </div>

    <div class="tile">
      <small>Recovery Plan</small>
      <strong>${item.plan.action.replaceAll("_", " ")}</strong>
      <p class="muted">${item.plan.explanation}</p>
      <p class="muted">Policy decision: ${item.policy.reason}</p>
      <button class="primary" id="execute">Execute Recovery</button>
    </div>

    <div class="tile">
      <small>Audit Trail</small>
      <div class="timeline">
        ${item.audit
          .map(
            (event) => `
              <div class="event">
                <strong>${event.event_type.replaceAll("_", " ")}</strong>
                <small>${event.timestamp}</small>
                <p class="muted">${Object.entries(event.detail)
                  .map(([key, value]) => `${key}: ${value}`)
                  .join(" | ")}</p>
              </div>
            `,
          )
          .join("")}
      </div>
    </div>
  `;

  document.querySelector("#execute").addEventListener("click", async () => {
    const updated = await getJson(`/api/payments/${payment.payment_id}/execute`, { method: "POST" });
    await refresh();
    renderDetail(updated);
  });
}

async function selectCase(paymentId) {
  selectedId = paymentId;
  const item = await getJson(`/api/payments/${paymentId}`);
  renderDetail(item);
  document.querySelectorAll(".case").forEach((button) => {
    button.classList.toggle("selected", button.dataset.id === paymentId);
  });
}

async function refresh() {
  const [summary, cases] = await Promise.all([getJson("/api/summary"), getJson("/api/payments?limit=30")]);
  renderMetrics(summary);
  renderCases(cases);
  if (!selectedId && cases.length > 0) {
    await selectCase(cases[0].payment.payment_id);
  }
}

document.querySelector("#reset").addEventListener("click", async () => {
  await getJson("/api/demo/reset", { method: "POST" });
  selectedId = null;
  await refresh();
});

document.querySelector("#run-batch").addEventListener("click", async () => {
  await getJson("/api/demo/run-batch", { method: "POST" });
  selectedId = null;
  await refresh();
});

document.querySelectorAll("[data-demo]").forEach((button) => {
  button.addEventListener("click", () => selectCase(button.dataset.demo));
});

refresh();
