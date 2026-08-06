import argparse
import os
import sys
import subprocess
from agenttrace.config import get_config
from agenttrace.utils import verify_proof_receipt


def main():
    parser = argparse.ArgumentParser(prog="agenttrace", description="AgentTrace Developer CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Command: validate-config
    subparsers.add_parser("validate-config", help="Validate AgentTrace environment variables and secret settings")

    # Command: verify-proof
    proof_parser = subparsers.add_parser("verify-proof", help="Verify WORM audit proof receipt signature")
    proof_parser.add_argument("--proof-file", default="proof.json", help="Path to proof.json receipt file")
    proof_parser.add_argument("--secret-key", default=None, help="WORM vault secret key override")

    # Command: run-benchmarks
    bench_parser = subparsers.add_parser("run-benchmarks", help="Execute AgentTrace benchmark suite")
    bench_parser.add_argument("--quick", action="store_true", help="Run shortened benchmark validation pass")

    args = parser.parse_args()

    if args.command == "validate-config":
        cfg = get_config()
        errs = cfg.validate()
        if errs:
            print("Configuration Validation Failure:")
            for e in errs:
                print(f"  [ERROR] {e}")
            sys.exit(1)
        else:
            print("[OK] AgentTrace environment configuration is valid.")
            print(f"     Ingestion URL: {cfg.ingestion_url}")
            print(f"     Gateway Port:  {cfg.gateway_port}")
            print(f"     Mock Upstream: {cfg.mock_upstream}")

    elif args.command == "verify-proof":
        secret = args.secret_key or os.getenv("AGENTTRACE_SECRET_KEY", "agenttrace-production-worm-vault-key-2026")
        if not os.path.exists(args.proof_file):
            print(f"[ERROR] Proof file not found at path: {args.proof_file}")
            sys.exit(1)
        valid = verify_proof_receipt(args.proof_file, secret)
        if valid:
            print(f"[SUCCESS] Proof receipt '{args.proof_file}' verified cleanly with Ed25519 / HMAC signature.")
        else:
            print(f"[FAILURE] Proof receipt '{args.proof_file}' validation failed! File may have been tampered with.")
            sys.exit(1)

    elif args.command == "run-benchmarks":
        cmd = [sys.executable, "benchmarks/run_benchmarks.py"]
        if args.quick:
            cmd.append("--quick")
        subprocess.run(cmd)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
