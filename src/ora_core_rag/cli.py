"""Command-line interface for ORA_CORE_RAG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .index import ORACoreIndex
from .route_gate import ClientRouteGate


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def cmd_init(args: argparse.Namespace) -> None:
    index = ORACoreIndex(args.db)
    index.initialize()
    _print_json({"status": "READY", "db": str(index.db_path)})


def cmd_ingest(args: argparse.Namespace) -> None:
    index = ORACoreIndex(args.db)
    result = index.ingest_manifest(args.manifest)
    _print_json({"status": "INGESTED", "sources": result})


def cmd_query(args: argparse.Namespace) -> None:
    index = ORACoreIndex(args.db)
    _print_json(index.query(args.query, top_k=args.top_k))


def cmd_validate_route(args: argparse.Namespace) -> None:
    gate = ClientRouteGate()
    route = gate.load_manifest(args.manifest)
    _print_json({
        "status": "VALID",
        "route_id": route["route_id"],
        "tenant_id": route["tenant_id"],
        "manifest_hash": route["manifest_hash"],
    })


def cmd_authorize(args: argparse.Namespace) -> None:
    gate = ClientRouteGate()
    route = gate.load_manifest(args.manifest)
    _print_json(gate.authorize(route, resource_type=args.resource_type, resource_id=args.resource_id))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ora-core-rag", description="ORA_CORE_RAG local retrieval CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize the SQLite index")
    init.add_argument("--db", default="data/index/ora_core_rag.sqlite")
    init.set_defaults(func=cmd_init)

    ingest = sub.add_parser("ingest", help="Ingest a source manifest")
    ingest.add_argument("--manifest", required=True)
    ingest.add_argument("--db", default="data/index/ora_core_rag.sqlite")
    ingest.set_defaults(func=cmd_ingest)

    query = sub.add_parser("query", help="Query the ORA core index")
    query.add_argument("query")
    query.add_argument("--top-k", type=int, default=5)
    query.add_argument("--db", default="data/index/ora_core_rag.sqlite")
    query.set_defaults(func=cmd_query)

    validate_route = sub.add_parser("validate-route", help="Validate a GLK client route manifest")
    validate_route.add_argument("--manifest", required=True)
    validate_route.set_defaults(func=cmd_validate_route)

    authorize = sub.add_parser("authorize", help="Authorize a tenant RAG or agent against a GLK route")
    authorize.add_argument("--manifest", required=True)
    authorize.add_argument("--resource-type", required=True, choices=["rag", "agent"])
    authorize.add_argument("--resource-id", required=True)
    authorize.set_defaults(func=cmd_authorize)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
