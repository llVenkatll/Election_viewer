const DATA_URL = "https://llvenkatll.github.io/Election_viewer/data.json";
const SITE_URL = "https://llvenkatll.github.io/Election_viewer/";
const TOTAL_SEATS = 234;
const MAJORITY = 118;

const req = new Request(DATA_URL + "?ts=" + Date.now());
const json = await req.loadJSON();
const rows = json.data.S22.chartData;

let partyMap = {};
for (const row of rows) {
  const party = row[0];
  const color = row[4];
  if (!partyMap[party]) partyMap[party] = { party, total: 0, color };
  partyMap[party].total += 1;
}

const parties = Object.values(partyMap).sort((a, b) => b.total - a.total);
const leader = parties[0];
const counted = parties.reduce((s, p) => s + p.total, 0);
const remaining = TOTAL_SEATS - counted;
const leaderShare = ((leader.total / TOTAL_SEATS) * 100).toFixed(1);

const w = new ListWidget();
w.url = SITE_URL;
w.backgroundColor = new Color("#f7f7fb");
w.setPadding(12, 12, 10, 12);

// Header
let header = w.addStack();
header.layoutHorizontally();
header.centerAlignContent();

let title = header.addText("Tamil Nadu Results");
title.font = Font.boldSystemFont(15);
title.textColor = new Color("#111111");

header.addSpacer();

let live = header.addText("● LIVE");
live.font = Font.boldSystemFont(10);
live.textColor = new Color("#e53935");

w.addSpacer(5);

// Leader summary
let summary = w.addStack();
summary.layoutHorizontally();
summary.centerAlignContent();

let leaderBox = summary.addStack();
leaderBox.layoutVertically();

let lead = leaderBox.addText(`${leader.party} leading`);
lead.font = Font.boldSystemFont(20);
lead.textColor = new Color(leader.color);

let sub = leaderBox.addText(`${leader.total}/${TOTAL_SEATS} seats · ${leaderShare}%`);
sub.font = Font.mediumSystemFont(11);
sub.textColor = new Color("#555555");

summary.addSpacer();

let majorityBox = summary.addStack();
majorityBox.layoutVertically();

let maj = majorityBox.addText("Majority");
maj.font = Font.systemFont(9);
maj.textColor = new Color("#777777");
maj.rightAlignText();

let majNo = majorityBox.addText(String(MAJORITY));
majNo.font = Font.boldSystemFont(16);
majNo.textColor = leader.total >= MAJORITY ? new Color("#0a8f3c") : new Color("#444444");
majNo.rightAlignText();

w.addSpacer(7);

// Full seat bar
let bar = w.addStack();
bar.layoutHorizontally();
bar.size = new Size(0, 9);
bar.backgroundColor = new Color("#e6e6ec");
bar.cornerRadius = 5;

for (const p of parties.slice(0, 8)) {
  let seg = bar.addStack();
  seg.size = new Size(Math.max(2, Math.round((p.total / TOTAL_SEATS) * 300)), 9);
  seg.backgroundColor = new Color(p.color);
}
bar.addSpacer();

w.addSpacer(8);

// Table header
let th = w.addStack();
th.layoutHorizontally();

let h1 = th.addText("Party");
h1.font = Font.boldSystemFont(10);
h1.textColor = new Color("#777777");

th.addSpacer();

let h2 = th.addText("Seats");
h2.font = Font.boldSystemFont(10);
h2.textColor = new Color("#777777");

w.addSpacer(3);

// 2-column compact table: top 8
const top = parties.slice(0, 8);
for (let i = 0; i < 4; i++) {
  let row = w.addStack();
  row.layoutHorizontally();
  row.centerAlignContent();

  addPartyCell(row, top[i]);
  row.addSpacer(12);
  addPartyCell(row, top[i + 4]);

  w.addSpacer(5);
}

w.addSpacer();

// Footer
const updated = new Date(json.updated_utc).toLocaleTimeString([], {
  hour: "2-digit",
  minute: "2-digit"
});

let footer = w.addStack();
footer.layoutHorizontally();

let f1 = footer.addText(`Counted ${counted}/${TOTAL_SEATS}`);
f1.font = Font.systemFont(10);
f1.textColor = new Color("#666666");

footer.addSpacer();

let f2 = footer.addText(`Updated ${updated}`);
f2.font = Font.systemFont(10);
f2.textColor = new Color("#666666");

Script.setWidget(w);
Script.complete();

function addPartyCell(parent, p) {
  let cell = parent.addStack();
  cell.layoutHorizontally();
  cell.centerAlignContent();
  cell.size = new Size(125, 18);

  if (!p) {
    cell.addSpacer();
    return;
  }

  let dot = cell.addText("●");
  dot.font = Font.systemFont(9);
  dot.textColor = new Color(p.color);

  cell.addSpacer(5);

  let name = cell.addText(p.party);
  name.font = Font.boldSystemFont(12);
  name.textColor = new Color("#111111");

  cell.addSpacer();

  let seats = cell.addText(String(p.total));
  seats.font = Font.boldSystemFont(13);
  seats.textColor = new Color("#111111");
}