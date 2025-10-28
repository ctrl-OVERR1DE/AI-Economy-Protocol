"""
Register Agent A (Chat Protocol) with Agentverse using environment variables.

Required env vars:
- AGENTVERSE_KEY           -> your Agentverse API key (copied from the UI)
- AGENT_SEED_PHRASE        -> the SAME seed phrase used by your agent code
- AGENT_A_PUBLIC_URL       -> public HTTPS endpoint to your agent (e.g., ngrok URL + /submit)
Optional env vars:
- AGENT_A_NAME             -> defaults to 'DataAnalystAgent'

Usage (PowerShell):
  $env:AGENTVERSE_KEY="<key>"
  $env:AGENT_SEED_PHRASE="data_analyst_seed_phrase_12345"
  $env:AGENT_A_PUBLIC_URL="https://<your-subdomain>.ngrok-free.app/submit"
  python utils/register_agent.py
"""

import os
import sys

try:
    # Optional: load .env if python-dotenv is installed
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

from uagents_core.utils.registration import (
    register_chat_agent,
    RegistrationRequestCredentials,
)


def die(msg: str) -> None:
    print(f"✗ {msg}")
    sys.exit(1)


def main() -> None:
    agent_name = os.environ.get("AGENT_A_NAME", "DataAnalystAgent")
    endpoint = os.environ.get("AGENT_A_PUBLIC_URL", "").strip()
    api_key = os.environ.get("AGENTVERSE_KEY", "").strip()
    seed = os.environ.get("AGENT_SEED_PHRASE", "").strip()

    print("=== Chat Protocol Registration ===")
    print(f"Agent Name: {agent_name}")
    print(f"Endpoint:  {endpoint if endpoint else '<MISSING>'}")

    if not endpoint:
        die("AGENT_A_PUBLIC_URL is not set. Set it to your HTTPS public URL (ending with /submit).")
    if not api_key:
        die("AGENTVERSE_KEY is not set. Copy it from the Agentverse UI and set it in your environment.")
    if not seed:
        die("AGENT_SEED_PHRASE is not set. It must match the seed used by your running agent.")

    # Perform registration
    print("\nRegistering agent with Agentverse...")
    try:
        register_chat_agent(
            agent_name,
            endpoint,
            active=True,
            credentials=RegistrationRequestCredentials(
                agentverse_api_key=api_key,
                agent_seed_phrase=seed,
            ),
        )
        print("\n✓ Registration request submitted.")
        print("Next: Return to the Agentverse UI and click 'Evaluate registration'.")
    except Exception as e:
        die(f"Registration failed: {e}")


if __name__ == "__main__":
    main()
