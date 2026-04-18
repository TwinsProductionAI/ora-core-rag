"""Command-line interface for ORA_CORE_RAG."""

from __future__ import annotations

import argparse
import json

from .github_sources import GitHubSourceDiscovery
from .index import ORACoreIndex
from .neroflux import NerofluxFanoutRegulator
from .orchestrator import ORAOrchestratorConnector
from .registry import RAGRegistry
from .route_gate import ClientRouteGate


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _index_from_args(args: argparse.Namespace) -> ORACoreIndex:
    return ORACoreIndex(args.db, audit_log=getattr(args, "audit_log", None))


def _signal_from_args(args: argparse.Namespace) -> dict[str, object]:
    return {
        "retrieval_pressure": args.retrieval_pressure,
        "source_conflict": args.source_conflict,
        "permission_risk": args.permission_risk,
        "injection_risk": args.injection_risk,
        "latency_pressure": args.latency_pressure,
        "cost_pressure": args.cost_pressure,
        "client_sensitivity": args.client_sensitivity,
        "urgency": args.urgency,
        "agent_count": getattr(args, "agent_count", 0),
        "contradiction": args.contradiction,
    }


def cmd_init(args: argparse.Namespace) -> None:
    index = _index_from_args(args)
    index.initialize()
    _print_json({"status": "READY", "db": str(index.db_path)})


def cmd_ingest(args: argparse.Namespace) -> None:
    index = _index_from_args(args)
    result = index.ingest_manifest(args.manifest)
    _print_json({"status": "INGESTED", "sources": result})


def cmd_discover_github(args: argparse.Namespace) -> None:
    discovery = GitHubSourceDiscovery()
    manifest = discovery.manifest(
        args.repo,
        ref=args.ref,
        canon_level=args.canon_level,
        tags=args.tag or [],
        limit=args.limit,
    )
    _print_json(manifest)


def cmd_ingest_github(args: argparse.Namespace) -> None:
    index = _index_from_args(args)
    result = index.ingest_github_repo(
        args.repo,
        ref=args.ref,
        canon_level=args.canon_level,
        tags=args.tag or [],
        limit=args.limit,
    )
    _print_json({"status": "INGESTED", "repo": args.repo, "ref": args.ref, "sources": result})


def cmd_query(args: argparse.Namespace) -> None:
    index = _index_from_args(args)
    _print_json(index.query(args.query, top_k=args.top_k))


def cmd_orchestrate_query(args: argparse.Namespace) -> None:
    index = _index_from_args(args)
    connector = ORAOrchestratorConnector(index)
    packet = connector.route({
        "request_id": args.request_id,
        "query": args.query,
        "intent": args.intent,
        "risk_level": args.risk_level,
        "freshness_need": args.freshness_need,
        "source_required": args.source_required,
        "top_k": args.top_k,
    })
    index.audit.emit(
        "orchestrator_packet",
        {
            "request_id": packet["request_id"],
            "verify_status": packet["verify_status"],
            "retrieval_status": packet["retrieval"]["status"],
        },
    )
    _print_json(packet)


def cmd_neroflux_regulate(args: argparse.Namespace) -> None:
    _print_json(NerofluxFanoutRegulator().regulate(_signal_from_args(args)))


def cmd_plan_client(args: argparse.Namespace) -> None:
    gate = ClientRouteGate()
    route = gate.load_manifest(args.route_manifest)
    registry = RAGRegistry.from_path(args.registry)
    plan = registry.plan(route_manifest=route, requested_ids=args.resource or None, neroflux_signal=_signal_from_args(args))
    _print_json(plan)


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


def _add_db_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", default="data/index/ora_core_rag.sqlite")
    parser.add_argument("--audit-log", default=None, help="Optional JSONL audit log path")


def _add_github_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("repo", help="GitHub repository in owner/name form")
    parser.add_argument("--ref", default="main")
    parser.add_argument("--canon-level", default="RUNTIME")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--limit", type=int, default=None)


def _add_neroflux_args(parser: argparse.ArgumentParser, *, include_agent_count: bool = True) -> None:
    parser.add_argument("--retrieval-pressure", type=float, default=0.0)
    parser.add_argument("--source-conflict", type=float, default=0.0)
    parser.add_argument("--permission-risk", type=float, default=0.0)
    parser.add_argument("--injection-risk", type=float, default=0.0)
    parser.add_argument("--latency-pressure", type=float, default=0.0)
    parser.add_argument("--cost-pressure", type=float, default=0.0)
    parser.add_argument("--client-sensitivity", type=float, default=0.0)
    parser.add_argument("--urgency", type=float, default=0.0)
    if include_agent_count:
        parser.add_argument("--agent-count", type=int, default=0)
    parser.add_argument("--contradiction", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ora-core-rag", description="ORA_CORE_RAG local retrieval CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize the SQLite index")
    _add_db_args(init)
    init.set_defaults(func=cmd_init)

    ingest = sub.add_parser("ingest", help="Ingest a source manifest")
    ingest.add_argument("--manifest", required=True)
    _add_db_args(ingest)
    ingest.set_defaults(func=cmd_ingest)

    discover_github = sub.add_parser("discover-github", help="Build a source manifest from a public GitHub repo")
    _add_github_args(discover_github)
    discover_github.set_defaults(func=cmd_discover_github)

    ingest_github = sub.add_parser("ingest-github", help="Discover and ingest files from a public GitHub repo")
    _add_github_args(ingest_github)
    _add_db_args(ingest_github)
    ingest_github.set_defaults(func=cmd_ingest_github)

    query = sub.add_parser("query", help="Query the ORA core index")
    query.add_argument("query")
    query.add_argument("--top-k", type=int, default=5)
    _add_db_args(query)
    query.set_defaults(func=cmd_query)

    orchestrate = sub.add_parser("orchestrate-query", help="Return an ORCHESTRATEUR_LLM-shaped retrieval packet")
    orchestrate.add_argument("query")
    orchestrate.add_argument("--request-id", default=None)
    orchestrate.add_argument("--intent", default="canonical_retrieval")
    orchestrate.add_argument("--risk-level", default="LOW", choices=["LOW", "MID", "HIGH", "CRITICAL"])
    orchestrate.add_argument("--freshness-need", default="LOW")
    orchestrate.add_argument("--source-required", action=argparse.BooleanOptionalAction, default=True)
    orchestrate.add_argument("--top-k", type=int, default=5)
    _add_db_args(orchestrate)
    orchestrate.set_defaults(func=cmd_orchestrate_query)

    neroflux = sub.add_parser("neroflux-regulate", help="Regulate multi-RAG fanout with deterministic Neroflux policy")
    _add_neroflux_args(neroflux)
    neroflux.set_defaults(func=cmd_neroflux_regulate)

    plan_client = sub.add_parser("plan-client", help="Build a route-gated multi-RAG/client activation plan")
    plan_client.add_argument("--route-manifest", required=True)
    plan_client.add_argument("--registry", required=True)
    plan_client.add_argument("--resource", action="append", default=[])
    _add_neroflux_args(plan_client, include_agent_count=False)
    plan_client.set_defaults(func=cmd_plan_client)

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
