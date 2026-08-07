"""LLMWitness Community command-line interface."""

import argparse
import json
import os

from llmwitness.config import get_config
from llmwitness.utils import verify_proof_receipt


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="llmwitness", description="Inspect and verify local LLMWitness receipts"
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "validate-config", help="Validate local environment configuration"
    )

    verify_parser = subparsers.add_parser(
        "verify", help="Verify a tamper-evident local receipt"
    )
    verify_parser.add_argument("receipt", help="Path to a receipt JSON file")
    verify_parser.add_argument(
        "--secret-key",
        default=None,
        help="Also verify the optional HMAC with this secret (prefer the environment variable)",
    )
    verify_parser.add_argument(
        "--trusted-fingerprint",
        default=None,
        help="Require the receipt's Ed25519 public-key fingerprint to match this value",
    )

    args = parser.parse_args()
    if args.command == "validate-config":
        errors = get_config().validate()
        if errors:
            for error in errors:
                print(f"[ERROR] {error}")
            raise SystemExit(1)
        print("[OK] Local LLMWitness configuration is valid.")
        return

    if args.command == "verify":
        secret = args.secret_key or os.getenv("LLMWITNESS_SECRET_KEY")
        if not os.path.isfile(args.receipt):
            print(f"[ERROR] Receipt file not found: {args.receipt}")
            raise SystemExit(1)
        if not verify_proof_receipt(args.receipt, secret):
            print("[FAIL] Receipt signature verification failed.")
            raise SystemExit(1)
        try:
            with open(args.receipt, encoding="utf-8") as handle:
                fingerprint = json.load(handle).get("public_key_fingerprint")
        except (OSError, ValueError, AttributeError):
            print("[FAIL] Receipt fingerprint could not be read.")
            raise SystemExit(1) from None
        if not isinstance(fingerprint, str) or not fingerprint:
            print("[FAIL] Receipt does not contain a public-key fingerprint.")
            raise SystemExit(1)
        if (
            args.trusted_fingerprint is not None
            and fingerprint.lower() != args.trusted_fingerprint.lower()
        ):
            print("[FAIL] Receipt signer fingerprint does not match the trusted value.")
            raise SystemExit(1)
        if secret:
            print("[OK] Ed25519 signature and HMAC verified.")
        else:
            print(
                "[OK] Ed25519 signature verified. Trust the signer only after checking its fingerprint."
            )
        print(f"Signer fingerprint: {fingerprint}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
