import argparse
import json
from pathlib import Path

from .pipeline import Pipeline, approve_mapping, profile, propose_mapping

SYNTHETIC_CSV = b"""reading_key,sensor_key,collected_at,temp_f,health
DEMO-E001,DEMO-S001,2030-01-01T12:00:00Z,68,healthy
DEMO-E002,DEMO-S002,2030-01-01T12:01:00Z,77,warn
DEMO-E003,DEMO-S003,2030-01-01T12:02:00Z,not-a-number,ok
DEMO-E001,DEMO-S001,2030-01-01T12:00:00Z,68,healthy
DEMO-E004,DEMO-S004,2030-01-01T12:04:00Z,86,offline
DEMO-E005,DEMO-S005,not-a-date,68,ok
"""


def demo():
    proposal = propose_mapping(SYNTHETIC_CSV)
    mapping = approve_mapping(proposal, "demo-reviewer")
    pipeline = Pipeline()
    try:
        first = pipeline.ingest(SYNTHETIC_CSV, mapping)
        replay = pipeline.ingest(SYNTHETIC_CSV, mapping)
        return {
            "project": "SynapseETL",
            "mode": "synthetic-telemetry",
            "proposal": proposal,
            "approved_mapping": mapping,
            "result": first,
            "replay": replay,
            "events": pipeline.events(),
        }
    finally:
        pipeline.close()


def run_cli():
    parser = argparse.ArgumentParser(description="Evidence-based schema mapping and ingestion")
    parser.add_argument("--db", default=".runs/synapse.sqlite")
    sub = parser.add_subparsers(dest="command", required=True)
    demo_command = sub.add_parser("demo")
    demo_command.add_argument("--html", type=Path)
    for name in ("profile", "propose"):
        command = sub.add_parser(name)
        command.add_argument("csv", type=Path)
        if name == "propose":
            command.add_argument("--model", action="store_true")
    approve = sub.add_parser("approve")
    approve.add_argument("proposal", type=Path)
    approve.add_argument("actor")
    ingest = sub.add_parser("ingest")
    ingest.add_argument("csv", type=Path)
    ingest.add_argument("mapping", type=Path)
    args = parser.parse_args()
    if args.command == "demo":
        result = demo()
        if args.html:
            from .report import render

            render(result, args.html)
    elif args.command == "profile":
        result = profile(args.csv.read_bytes())
    elif args.command == "propose":
        from .provider import ChatPlanner

        result = propose_mapping(
            args.csv.read_bytes(), ChatPlanner.from_env() if args.model else None
        )
    elif args.command == "approve":
        result = approve_mapping(json.loads(args.proposal.read_text()), args.actor)
    else:
        Path(args.db).parent.mkdir(parents=True, exist_ok=True)
        pipeline = Pipeline(args.db)
        try:
            result = pipeline.ingest(args.csv.read_bytes(), json.loads(args.mapping.read_text()))
        finally:
            pipeline.close()
    print(json.dumps(result, indent=2))


def main():
    import sqlite3
    import sys

    try:
        run_cli()
    except (ValueError, KeyError, OSError, sqlite3.Error, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        raise SystemExit(2) from None
