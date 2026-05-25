"""Command line interface for SciTrace."""

from __future__ import annotations

import argparse
import json

from .ctv import CompositionalToolChainVerifier, ToolCall
from .pipeline import SciTracePipeline
from .risk_state import CumulativeRiskState
from .taxonomy import RISK_TAXONOMY


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scitrace")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_task = subparsers.add_parser("run-task", help="Run the four-stage SciTrace scaffold.")
    run_task.add_argument("--task", required=True)
    run_task.add_argument("--tool", action="append", default=[], help="Tool call as name:arguments.")
    run_task.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    verify = subparsers.add_parser("verify-tools", help="Verify a proposed tool trajectory.")
    verify.add_argument("--request", required=True)
    verify.add_argument("--tool", action="append", required=True, help="Tool call as name:arguments.")
    verify.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    subparsers.add_parser("taxonomy", help="Print the SciTrace S1-S9 risk taxonomy.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "taxonomy":
        print(json.dumps(RISK_TAXONOMY, indent=2, sort_keys=True))
        return 0

    if args.command == "run-task":
        pipeline = SciTracePipeline()
        calls = [ToolCall.parse(raw) for raw in args.tool]
        summary = pipeline.run(args.task, calls).summary()
        _emit(summary, as_json=args.json)
        return 0

    if args.command == "verify-tools":
        verifier = CompositionalToolChainVerifier()
        state = CumulativeRiskState()
        history: list[ToolCall] = []
        results = []
        for raw in args.tool:
            call = ToolCall.parse(raw)
            result = verifier.verify(args.request, call, history, state)
            results.append(
                {
                    "tool": call.name,
                    "action": result.action,
                    "score": result.score,
                    "feedback": result.feedback,
                    "risk": result.signal.level.label,
                    "category": result.signal.category,
                }
            )
            if result.action == "allow":
                history.append(call)
        _emit({"results": results, "risk_state": state.summary()}, as_json=args.json)
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


def _emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
