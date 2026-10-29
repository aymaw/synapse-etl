"""Render a self-contained explorer for an actual synthetic demo run."""

import json
from html import escape
from pathlib import Path

THEMES = {
    "AgentFlow": "#68e0c4",
    "CareLoop": "#ffa88d",
    "SynapseETL": "#b7a0ff",
    "AgentBench": "#ffcf71",
}


def view_model(data):
    project = data["project"]
    if project == "AgentFlow":
        metrics = [
            ("Final state", data["final_status"]),
            ("Checkpoint", data["checkpoint"]),
            ("Executed steps", len(data["steps"])),
            ("Replay events added", data["replay_adds_events"]),
        ]
        records = [
            {
                "title": f"{e['seq']:02} / {e['kind']}",
                "category": e["kind"],
                "subtitle": e["step_id"] or "controller",
                "detail": e,
            }
            for e in data["events"]
        ]
        description = "A tool plan moves from inventory to quote to a reviewed reservation. Every transition is recorded."
    elif project == "CareLoop":
        metrics = [
            ("Synthetic referrals", len(data["referrals"])),
            ("Closed loops", sum(r["status"] == "closed" for r in data["referrals"])),
            ("Audit verified", str(data["audit_verified"]).lower()),
            ("Messages sent", 0),
        ]
        records = [
            {
                "title": f"{e['referral']} / {e['action']}",
                "category": e["action"],
                "subtitle": e["at"],
                "detail": e,
            }
            for e in data["audit"]
        ]
        description = "Follow one fictional referral from route review to receipt-backed closure. Draft messages stay local."
    elif project == "SynapseETL":
        r = data["result"]
        metrics = [
            ("Accepted", r["accepted"]),
            ("Duplicates", r["duplicates"]),
            ("Quarantined", r["quarantined"]),
            ("Replay", str(data["replay"]["replayed"]).lower()),
        ]
        records = [
            {
                "title": f"Row {e['row']} / {e['outcome']}",
                "category": e["outcome"],
                "subtitle": e.get("event_id") or "invalid record",
                "detail": {
                    **e,
                    "errors": next((v["errors"] for v in r["errors"] if v["row"] == e["row"]), []),
                    "canonical_event": next(
                        (v for v in data["events"] if v["event_id"] == e["event_id"]), None
                    ),
                },
            }
            for e in r["outcomes"]
        ]
        description = "Inspect how a reviewed mapping turns messy synthetic telemetry into canonical events and explicit row errors."
    else:
        a, b = data["baseline"], data["candidate"]
        metrics = [
            ("Reference success", f"{b['successes']}/{b['episodes']}"),
            ("Baseline success", f"{a['successes']}/{a['episodes']}"),
            ("Reference safety", f"{b['safety_rate']:.0%}"),
            ("Paired regressions", len(data["comparison"]["regressions"])),
        ]
        records = []
        for label, report in [("safe-reference", b), ("eager-baseline", a)]:
            for r in report["results"]:
                records.append(
                    {
                        "title": r["scenario"],
                        "category": label,
                        "subtitle": ("PASS" if r["success"] else "FAIL") + " / " + r["outcome"],
                        "detail": r,
                    }
                )
        description = "Compare two authored reference policies on the same 21 synthetic scenarios. Inspect every tool call and blocked attempt."
    return {
        "project": project,
        "description": description,
        "metrics": metrics,
        "records": records,
        "raw": data,
    }


def render(data, destination):
    model = view_model(data)
    payload = (
        json.dumps(model).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    )
    html = (
        TEMPLATE.replace("%%TITLE%%", escape(model["project"]))
        .replace("%%ACCENT%%", THEMES[model["project"]])
        .replace("%%DATA%%", payload)
    )
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


TEMPLATE = """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%%TITLE%% · Run explorer</title>
<style>
:root{color-scheme:dark;--accent:%%ACCENT%%;--bg:#101519;--line:#2c363d;--muted:#a9b5bc}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#f0f3f5;font:15px/1.6 system-ui,-apple-system,sans-serif}a{color:var(--accent)}button,select{font:inherit}header,main,footer{max-width:1260px;margin:auto;padding:28px 36px}header{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line)}.wordmark{font-size:19px;font-weight:700;letter-spacing:-.4px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--accent);margin-right:10px}.badge,.eyebrow{text-transform:uppercase;font-size:11px;letter-spacing:2px;color:var(--accent)}.badge{border:1px solid var(--line);padding:5px 12px;border-radius:20px}.hero{padding:36px 0 30px;max-width:830px}h1{font-size:clamp(36px,5vw,60px);line-height:1.08;letter-spacing:-2px;margin:14px 0 20px}p{color:var(--muted);margin:0}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 40px}.metric{border:1px solid var(--line);border-radius:12px;padding:22px;background:#151d22}.metric span{display:block;color:var(--muted);font-size:12px}.metric strong{display:block;font-size:clamp(18px,2.4vw,28px);font-weight:550;letter-spacing:-.5px;color:var(--accent);overflow-wrap:anywhere}.sectiontop{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;gap:16px}h2{font-size:20px;letter-spacing:-.5px;margin:0}select,button{border:1px solid var(--line);background:#19242b;color:#f0f3f5;padding:8px 13px;border-radius:6px}button{cursor:pointer}button:hover{border-color:var(--accent)}button:focus-visible,select:focus-visible,a:focus-visible{outline:2px solid var(--accent);outline-offset:3px}.grid{display:grid;grid-template-columns:360px minmax(0,1fr);border:1px solid var(--line);border-radius:12px;overflow:hidden;min-height:440px}.list{height:520px;overflow:auto;background:#141c21;border-right:1px solid var(--line);padding:8px}.record{display:block;text-align:left;width:100%;background:transparent;border:1px solid transparent;border-radius:7px;padding:12px 14px;margin:3px 0}.record.active{border-color:var(--accent);background:#202c33}.record b{display:block;font-size:13px;font-weight:550}.record small{color:var(--muted);font-size:11px}.detail{min-width:0;padding:24px;background:#11191e}.detail p{font-size:12px}.detail h3{font-size:17px;margin:0 0 4px}pre{font:12px/1.65 ui-monospace,SFMono-Regular,Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;color:#c8d8df;background:#0b1216;padding:20px;border-radius:8px;max-height:410px;overflow:auto;margin-top:20px}details{margin-top:26px;border:1px solid var(--line);padding:18px;border-radius:10px}summary{cursor:pointer;color:var(--muted)}footer{font-size:12px;color:var(--muted);border-top:1px solid var(--line);margin-top:36px}.note{margin:18px 0;color:var(--muted);font-size:12px}.actions{display:flex;gap:10px;align-items:center}@media(max-width:850px){header,main,footer{padding:24px}.metrics{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.list{height:240px;border-right:0;border-bottom:1px solid var(--line)}.sectiontop{align-items:flex-start;flex-direction:column}.detail{padding:18px}h1{letter-spacing:-1px}}
</style>
<header><div class="wordmark"><span class="dot"></span>%%TITLE%%</div><span class="badge">Recorded synthetic run</span></header>
<main><section class="hero"><div class="eyebrow">Independent engineering / run explorer</div><h1 id="headline"></h1><p id="description"></p></section>
<section class="metrics" id="metrics" aria-label="Run metrics"></section>
<div class="sectiontop"><h2>Evidence, step by step</h2><div class="actions"><label for="filter">Show</label><select id="filter"><option value="all">All records</option></select><button id="download">Export JSON</button></div></div>
<section class="grid" aria-label="Recorded run explorer"><div id="records" class="list" aria-label="Records"></div><div class="detail" aria-live="polite"><h3 id="record-title"></h3><p id="record-subtitle"></p><pre id="record-detail"></pre></div></section>
<p class="note">This viewer explores output from a completed local CLI run. Controls filter and inspect recorded evidence; they do not execute tools or contact a model.</p>
<details><summary>Full run artifact and provenance</summary><pre id="raw"></pre></details></main>
<footer>Original personal portfolio project by Ayma Waqar · MIT license · Synthetic data only · No external assets or network requests</footer>
<script id="run-data" type="application/json">%%DATA%%</script>
<script>
const model=JSON.parse(document.getElementById('run-data').textContent);
const titles={AgentFlow:'A plan is only the beginning.',CareLoop:'Close the loop. Keep the evidence.',SynapseETL:'Messy inputs. Explicit decisions.',AgentBench:'Measure the behavior behind the answer.'};
document.getElementById('headline').textContent=titles[model.project];document.getElementById('description').textContent=model.description;
for(const [label,value] of model.metrics){const box=document.createElement('div');box.className='metric';const span=document.createElement('span');span.textContent=label;const strong=document.createElement('strong');strong.textContent=String(value);box.append(span,strong);document.getElementById('metrics').append(box)}
const filter=document.getElementById('filter');for(const key of new Set(model.records.map(x=>x.category))){const option=document.createElement('option');option.value=key;option.textContent=key.replaceAll('_',' ');filter.append(option)}
function show(record,button){for(const b of document.querySelectorAll('.record')){b.classList.remove('active');b.setAttribute('aria-pressed','false')}button.classList.add('active');button.setAttribute('aria-pressed','true');document.getElementById('record-title').textContent=record.title;document.getElementById('record-subtitle').textContent=record.subtitle;document.getElementById('record-detail').textContent=JSON.stringify(record.detail,null,2)}
function draw(){const list=document.getElementById('records');list.replaceChildren();const records=model.records.filter(x=>filter.value==='all'||x.category===filter.value);records.forEach((record,i)=>{const button=document.createElement('button');button.className='record';button.setAttribute('aria-pressed','false');const b=document.createElement('b');b.textContent=record.title;const small=document.createElement('small');small.textContent=record.subtitle;button.append(b,small);button.addEventListener('click',()=>show(record,button));list.append(button);if(i===0)show(record,button)})}
filter.addEventListener('change',draw);draw();document.getElementById('raw').textContent=JSON.stringify(model.raw,null,2);
document.getElementById('download').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(model.raw,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=model.project.toLowerCase()+'-run.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
</script></html>"""
