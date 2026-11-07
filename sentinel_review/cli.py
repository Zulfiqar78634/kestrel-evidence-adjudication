"""Local operator CLI. --tenant is local scope, not authenticated identity."""
import argparse
import json
from pathlib import Path
from .service import ReviewService, replay
from .storage import SQLiteRepository
from .workbook import WorkbookCatalog


def main():
    parser = argparse.ArgumentParser(description="Private workbook evidence review; no product disposition")
    parser.add_argument("--db", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("review")
    run.add_argument("workbook")
    run.add_argument("--event")
    run.add_argument("--tenant")
    run.add_argument("--out", required=True)
    again = commands.add_parser("replay")
    again.add_argument("bundle")
    again.add_argument("--tenant", required=True)
    queue = commands.add_parser("obligations")
    queue.add_argument("--tenant", required=True)
    args = parser.parse_args()
    repository = SQLiteRepository(args.db)
    try:
        if args.command == "review":
            catalog = WorkbookCatalog(args.workbook)
            service = ReviewService(catalog, repository)
            rows = catalog.rows("01_Excursion_Events")
            if args.event:
                rows = tuple(r for r in rows if r.values.get("event_id") == args.event)
            if args.tenant:
                rows = tuple(r for r in rows if r.values.get("tenant_code") == args.tenant)
            if not rows:
                raise ValueError("no matching events")
            result = [service.review(r, args.tenant or r.values["tenant_code"]) for r in rows]
            Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            print(json.dumps({"events": len(result), "output": args.out, "product_dispositions": 0}))
        elif args.command == "replay":
            print(json.dumps(replay(repository, args.tenant, args.bundle), indent=2))
        else:
            print(json.dumps(repository.obligations(args.tenant), indent=2))
    finally:
        repository.close()


if __name__ == "__main__":
    main()
