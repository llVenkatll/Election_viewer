const DATA_URL = "REPLACE_WITH_YOUR_GITHUB_PAGES_DATA_JSON_URL";

const widget = await createWidget();
Script.setWidget(widget);
Script.complete();
if (!config.runsInWidget) {
  await widget.presentMedium();
}

async function createWidget() {
  const widget = new ListWidget();
  widget.backgroundColor = new Color("#0f172a");
  widget.setPadding(14, 14, 14, 14);
  widget.refreshAfterDate = new Date(Date.now() + 10 * 60 * 1000);

  try {
    const payload = await fetchData();
    const parties = summarizeParties(payload?.data?.S22?.chartData || []);
    renderWidget(widget, payload, parties);
  } catch (error) {
    renderError(widget, error);
  }

  return widget;
}

async function fetchData() {
  const request = new Request(`${DATA_URL}?ts=${Date.now()}`);
  request.timeoutInterval = 20;
  return await request.loadJSON();
}

function summarizeParties(rows) {
  const map = {};

  rows.forEach(row => {
    if (!Array.isArray(row) || row.length < 5) return;

    const party = String(row[0] || "Unknown").trim() || "Unknown";
    const color = normalizeColor(row[4]);

    if (!map[party]) {
      map[party] = { party, color, leading: 0, won: 0, total: 0 };
    }

    map[party].leading += 1;
    map[party].total += 1;
  });

  return Object.values(map).sort((a, b) => b.total - a.total || a.party.localeCompare(b.party));
}

function renderWidget(widget, payload, parties) {
  const leader = parties[0];
  const title = widget.addText("Tamil Nadu Results");
  title.textColor = Color.white();
  title.font = Font.semiboldSystemFont(13);
  title.lineLimit = 1;

  widget.addSpacer(6);

  const leaderRow = widget.addStack();
  leaderRow.layoutHorizontally();
  leaderRow.centerAlignContent();

  const leaderStripe = leaderRow.addStack();
  leaderStripe.size = new Size(5, 34);
  leaderStripe.backgroundColor = new Color(leader ? leader.color : "#64748b");
  leaderStripe.cornerRadius = 2;

  leaderRow.addSpacer(8);

  const leaderText = leaderRow.addStack();
  leaderText.layoutVertically();

  const leadingLabel = leaderText.addText("Leading party");
  leadingLabel.textColor = new Color("#94a3b8");
  leadingLabel.font = Font.mediumSystemFont(9);

  const leadingParty = leaderText.addText(leader ? `${leader.party} - ${leader.total}` : "No data");
  leadingParty.textColor = Color.white();
  leadingParty.font = Font.boldSystemFont(22);
  leadingParty.minimumScaleFactor = 0.6;
  leadingParty.lineLimit = 1;

  widget.addSpacer(8);

  const topParties = parties.slice(0, 5);
  topParties.forEach((party, index) => {
    const row = widget.addStack();
    row.layoutHorizontally();
    row.centerAlignContent();

    const dot = row.addStack();
    dot.size = new Size(8, 8);
    dot.backgroundColor = new Color(party.color);
    dot.cornerRadius = 4;

    row.addSpacer(7);

    const name = row.addText(`${index + 1}. ${party.party}`);
    name.textColor = new Color("#e2e8f0");
    name.font = Font.semiboldSystemFont(11);
    name.lineLimit = 1;
    name.minimumScaleFactor = 0.7;

    row.addSpacer();

    const count = row.addText(String(party.total));
    count.textColor = Color.white();
    count.font = Font.boldSystemFont(12);
    count.rightAlignText();

    if (index < topParties.length - 1) widget.addSpacer(3);
  });

  widget.addSpacer();

  const footer = widget.addStack();
  footer.layoutHorizontally();

  const updated = footer.addText(`Updated ${formatUpdated(payload?.updated_utc)}`);
  updated.textColor = new Color("#94a3b8");
  updated.font = Font.mediumSystemFont(9);
  updated.lineLimit = 1;

  footer.addSpacer();

  const source = footer.addText("ECI");
  source.textColor = new Color("#5eead4");
  source.font = Font.semiboldSystemFont(9);
}

function renderError(widget, error) {
  const title = widget.addText("Tamil Nadu Results");
  title.textColor = Color.white();
  title.font = Font.boldSystemFont(14);

  widget.addSpacer(10);

  const message = widget.addText("Unable to load data.json");
  message.textColor = new Color("#fecaca");
  message.font = Font.semiboldSystemFont(13);

  widget.addSpacer(4);

  const detail = widget.addText(String(error.message || error));
  detail.textColor = new Color("#94a3b8");
  detail.font = Font.mediumSystemFont(10);
  detail.lineLimit = 3;
}

function normalizeColor(color) {
  return /^#[0-9a-f]{6}$/i.test(color || "") ? color : "#64748b";
}

function formatUpdated(isoString) {
  if (!isoString) return "-";

  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "-";

  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}
