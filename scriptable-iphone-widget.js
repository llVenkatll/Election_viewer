const DATA_URL = "https://llvenkatll.github.io/Election_viewer/data.json";

// fetch data
const req = new Request(DATA_URL + "?ts=" + Date.now());
const json = await req.loadJSON();

const rows = json.data.S22.chartData;

// build party counts
let partyMap = {};

for (const row of rows) {
  const party = row[0];
  const color = row[4];

  if (!partyMap[party]) {
    partyMap[party] = {
      party,
      total: 0,
      color
    };
  }

  partyMap[party].total += 1;
}

// sort
const parties = Object.values(partyMap)
  .sort((a, b) => b.total - a.total);

// widget UI
const w = new ListWidget();
w.backgroundColor = new Color("#111"); // dark mode look

// title
const title = w.addText("TN Elections");
title.font = Font.boldSystemFont(16);
title.textColor = Color.white();

w.addSpacer(6);

// leader
const leader = parties[0];
const leadText = w.addText(`Leading: ${leader.party} (${leader.total})`);
leadText.font = Font.systemFont(12);
leadText.textColor = new Color(leader.color);

w.addSpacer(8);

// top 5 parties
const top = parties.slice(0, 5);

for (const p of top) {
  const row = w.addStack();
  row.layoutHorizontally();

  const name = row.addText(p.party);
  name.font = Font.boldSystemFont(13);
  name.textColor = new Color(p.color);

  row.addSpacer();

  const seats = row.addText(String(p.total));
  seats.font = Font.boldSystemFont(14);
  seats.textColor = Color.white();

  w.addSpacer(4);
}

w.addSpacer();

// updated time
const updated = new Date(json.updated_utc).toLocaleTimeString([], {
  hour: "2-digit",
  minute: "2-digit"
});

const footer = w.addText("Updated " + updated);
footer.font = Font.systemFont(10);
footer.textColor = Color.gray();

Script.setWidget(w);
Script.complete();
