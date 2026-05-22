const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const number = new Intl.NumberFormat("en-US");

const parseCsv = (text) => {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines[0].split(",");
  return lines.slice(1).map((line) => {
    const values = [];
    let current = "";
    let quoted = false;
    for (let index = 0; index < line.length; index += 1) {
      const char = line[index];
      const next = line[index + 1];
      if (char === '"' && quoted && next === '"') {
        current += '"';
        index += 1;
      } else if (char === '"') {
        quoted = !quoted;
      } else if (char === "," && !quoted) {
        values.push(current);
        current = "";
      } else {
        current += char;
      }
    }
    values.push(current);
    return Object.fromEntries(headers.map((header, index) => [header, values[index] || ""]));
  });
};

const loadCsv = async (path) => parseCsv(await fetch(path).then((response) => response.text()));
const loadJson = async (path) => fetch(path).then((response) => response.json());

const money = (value) => currency.format(Number(value));
const compact = (value) => number.format(Number(value));
const pct = (value) => `${Math.round(Number(value) * 100)}%`;

const metricCard = (label, value, detail) => `
  <article class="metric-card">
    <span>${label}</span>
    <strong>${value}</strong>
    <small>${detail}</small>
  </article>
`;

const scoreTone = (score) => {
  if (Number(score) >= 64) return "high";
  if (Number(score) >= 52) return "medium";
  return "watch";
};

const renderSummary = (summary) => {
  document.querySelector("#summaryMetrics").innerHTML = [
    metricCard("Latest week", summary.latest_week, "Operating package date"),
    metricCard("Avoidable contacts", compact(summary.avoidable_contacts), "Latest week estimate"),
    metricCard("Cost leakage", money(summary.weekly_cost_leakage), "Weekly service exposure"),
    metricCard("Active segments", compact(summary.active_segments), "Business unit queue"),
  ].join("");

  document.querySelector("#topSegment").textContent = summary.top_segment;
  document.querySelector("#topSegmentDetail").textContent =
    `${summary.top_business_unit} priority score ${summary.top_priority_score}`;
  document.querySelector("#topScore").textContent = summary.top_priority_score;
  document.querySelector("#avoidableRate").textContent = pct(summary.avoidable_contact_rate);
  document.querySelector("#utilizationExposure").textContent = money(summary.weekly_utilization_exposure);
};

const renderExposure = (queue) => {
  const topRows = queue.slice(0, 7);
  const maxExposure = Math.max(
    ...topRows.map((row) => Number(row.estimated_cost_leakage) + Number(row.utilization_exposure)),
  );
  document.querySelector("#exposureBars").innerHTML = topRows.map((row) => {
    const exposure = Number(row.estimated_cost_leakage) + Number(row.utilization_exposure);
    const width = Math.max(7, exposure / maxExposure * 100);
    return `
      <article class="bar-row">
        <div>
          <b>${row.segment_name}</b>
          <span>${row.business_unit}</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill ${scoreTone(row.priority_score)}" style="width:${width}%"></div>
        </div>
        <strong>${money(exposure)}</strong>
      </article>
    `;
  }).join("");
};

const renderQueue = (queue) => {
  document.querySelector("#priorityRows").innerHTML = queue.slice(0, 10).map((row) => {
    const exposure = Number(row.estimated_cost_leakage) + Number(row.utilization_exposure);
    return `
      <tr>
        <td>${row.rank}</td>
        <td>${row.segment_name}</td>
        <td>${row.business_unit}</td>
        <td><span class="score ${scoreTone(row.priority_score)}">${row.priority_score}</span></td>
        <td>${money(exposure)}</td>
        <td>${row.recommended_action}</td>
      </tr>
    `;
  }).join("");

  document.querySelector("#leadershipNotes").innerHTML = queue.slice(0, 4).map((row) => `
    <article>
      <span>${row.inefficiency_theme}</span>
      <h3>${row.segment_name}</h3>
      <p>${row.leadership_note}</p>
    </article>
  `).join("");
};

const renderRequirements = (requirements) => {
  document.querySelector("#requirementCards").innerHTML = requirements.slice(0, 6).map((row) => `
    <article class="requirement-card">
      <div>
        <span>${row.request_type}</span>
        <strong>${row.dashboard_gap}</strong>
      </div>
      <p>${row.business_unit}. Supports ${row.decision_supported.toLowerCase()}.</p>
      <small>${row.status}</small>
    </article>
  `).join("");
};

const renderQuality = (qualityRows) => {
  document.querySelector("#qualityCards").innerHTML = qualityRows.map((row) => `
    <article class="quality-card ${row.certification.toLowerCase().replace(" ", "-")}">
      <div>
        <span>${row.source_system}</span>
        <strong>${pct(row.pass_rate)}</strong>
      </div>
      <p>${row.check_name.replaceAll("_", " ")}. ${row.failing_records} failing records, ${row.freshness_hours} hour freshness.</p>
      <small>${row.operating_fix}</small>
    </article>
  `).join("");
};

const renderInitiatives = (initiatives) => {
  document.querySelector("#initiativeCards").innerHTML = initiatives.map((row) => {
    const target = Number(row.target_reduction);
    const current = Number(row.current_reduction);
    const width = Math.min(100, Math.round(current / target * 100));
    return `
      <article class="initiative-card ${row.status.toLowerCase().replace(" ", "-")}">
        <span>${row.owner} / ${row.status}</span>
        <h3>${row.initiative}</h3>
        <p>${row.segment_name}</p>
        <div class="progress">
          <div style="width:${width}%"></div>
        </div>
        <strong>${compact(row.estimated_contacts_avoided)} contacts avoided</strong>
        <small>${money(row.estimated_cost_avoided)} modeled cost avoided</small>
      </article>
    `;
  }).join("");
};

const boot = async () => {
  const [summary, queue, requirements, quality, initiatives] = await Promise.all([
    loadJson("analysis/outputs/summary.json"),
    loadCsv("analysis/outputs/priority_queue.csv"),
    loadCsv("data/dashboard_requirements.csv"),
    loadCsv("data/data_quality_checks.csv"),
    loadCsv("data/initiative_monitor.csv"),
  ]);

  renderSummary(summary);
  renderExposure(queue);
  renderQueue(queue);
  renderRequirements(requirements);
  renderQuality(quality);
  renderInitiatives(initiatives);
};

boot();
