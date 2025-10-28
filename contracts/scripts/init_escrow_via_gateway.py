import os
import asyncio
from typing import Optional

from dotenv import load_dotenv
from solders.pubkey import Pubkey

from client.gateway_escrow_client import GatewayEscrowClient


async def main():
    load_dotenv()

    rpc = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    program_id = os.getenv("ESCROW_PROGRAM_ID")
    if not program_id:
        raise RuntimeError("ESCROW_PROGRAM_ID not set in environment")

    provider_pubkey_str = os.getenv("PROVIDER_PUBLIC_KEY")
    client_ata_str = os.getenv("CLIENT_TOKEN_ACCOUNT")
    escrow_ata_str = os.getenv("ESCROW_TOKEN_ACCOUNT")

    missing = [name for name, val in [
        ("PROVIDER_PUBLIC_KEY", provider_pubkey_str),
        ("CLIENT_TOKEN_ACCOUNT", client_ata_str),
        ("ESCROW_TOKEN_ACCOUNT", escrow_ata_str),
    ] if not val]
    if missing:
        raise RuntimeError(
            "Missing required env vars: " + ", ".join(missing) +
            "\nPlease create a mint and ATAs on devnet (as in tests/escrow.test.ts) and set these addresses."
        )

    provider_pubkey = Pubkey.from_string(provider_pubkey_str)
    client_ata = Pubkey.from_string(client_ata_str)
    escrow_ata = Pubkey.from_string(escrow_ata_str)

    amount = int(os.getenv("ESCROW_AMOUNT", "100000000"))  # default 0.1 units
    service_id = os.getenv("ESCROW_SERVICE_ID", "data_analysis_001")
    task_data = os.getenv("ESCROW_TASK_DATA", "Analyze sales data")

    gw = GatewayEscrowClient(rpc_url=rpc)
    sig = await gw.initialize_escrow_via_gateway(
        provider_pubkey=provider_pubkey,
        amount=amount,
        service_id=service_id,
        task_data=task_data,
        client_token_account=client_ata,
        escrow_token_account=escrow_ata,
    )
    print("Gateway escrow initialized signature:", sig)

    await gw.close()


if __name__ == "__main__":
    asyncio.run(main())
