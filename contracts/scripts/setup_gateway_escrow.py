import os
import asyncio
from typing import Tuple

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer

from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import (
    get_associated_token_address,
    create_associated_token_account,
    mint_to,
    MintToParams,
)

from contracts.client.gateway_escrow_client import GatewayEscrowClient


async def create_mint_and_accounts(
    client: AsyncClient,
    payer: Keypair,
    escrow_pda: Pubkey,
    decimals: int = 6,
) -> Tuple[Pubkey, Pubkey, Pubkey]:
    """
    Create a new SPL mint on devnet, the client's ATA, and the escrow PDA's ATA.

    Returns (mint, client_ata, escrow_pda_ata)
    """
    from spl.token._layouts import MINT_LAYOUT  # type: ignore
    from spl.token.instructions import initialize_mint, InitializeMintParams

    # Create mint account
    mint = Keypair()
    rent = await client.get_minimum_balance_for_rent_exemption(MINT_LAYOUT.sizeof())

    # Create account for the mint
    from solana.rpc.types import TxOpts
    from solana.system_program import SYS_PROGRAM_ID, CreateAccountParams, create_account

    create_mint_acc_ix = create_account(
        CreateAccountParams(
            from_pubkey=payer.pubkey(),
            new_account_pubkey=mint.pubkey(),
            lamports=rent.value,
            space=MINT_LAYOUT.sizeof(),
            program_id=TOKEN_PROGRAM_ID,
        )
    )

    init_mint_ix = initialize_mint(
        InitializeMintParams(
            decimals=decimals,
            mint=mint.pubkey(),
            mint_authority=payer.pubkey(),
            freeze_authority=None,
            program_id=TOKEN_PROGRAM_ID,
        )
    )

    tx = Transaction()
    tx.add(create_mint_acc_ix)
    tx.add(init_mint_ix)
    recent = await client.get_latest_blockhash()
    tx.recent_blockhash = recent.value.blockhash
    tx.fee_payer = payer.pubkey()
    tx.sign(payer, mint)
    await client.send_transaction(tx, payer, mint, opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed))

    # Create client ATA
    client_ata = get_associated_token_address(payer.pubkey(), mint.pubkey())
    create_client_ata_ix = create_associated_token_account(
        payer=payer.pubkey(), owner=payer.pubkey(), mint=mint.pubkey()
    )

    # Create escrow PDA ATA (allow owner off-curve)
    escrow_ata = get_associated_token_address(escrow_pda, mint.pubkey(), allow_owner_off_curve=True)
    create_escrow_ata_ix = create_associated_token_account(
        payer=payer.pubkey(), owner=escrow_pda, mint=mint.pubkey()
    )

    tx2 = Transaction().add(create_client_ata_ix, create_escrow_ata_ix)
    recent2 = await client.get_latest_blockhash()
    tx2.recent_blockhash = recent2.value.blockhash
    tx2.fee_payer = payer.pubkey()
    tx2.sign(payer)
    await client.send_transaction(tx2, payer, opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed))

    # Mint tokens to client ATA so escrow can lock funds
    mint_amount = 1_000_000_000  # 1,000 tokens with 6 decimals
    mint_ix = mint_to(
        MintToParams(
            program_id=TOKEN_PROGRAM_ID,
            mint=mint.pubkey(),
            dest=client_ata,
            authority=payer.pubkey(),
            amount=mint_amount,
        )
    )
    tx3 = Transaction().add(mint_ix)
    recent3 = await client.get_latest_blockhash()
    tx3.recent_blockhash = recent3.value.blockhash
    tx3.fee_payer = payer.pubkey()
    tx3.sign(payer)
    await client.send_transaction(tx3, payer, opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed))

    return mint.pubkey(), client_ata, escrow_ata


async def main():
    # Load env
    from dotenv import load_dotenv

    load_dotenv()
    rpc = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    client = AsyncClient(rpc, commitment=Confirmed)

    # Load payer from CLI wallet
    import json

    wallet_path = os.path.expanduser(os.getenv("SOLANA_WALLET_PATH", "~/.config/solana/id.json"))
    with open(wallet_path, "r") as f:
        secret = json.load(f)
    payer = Keypair.from_bytes(bytes(secret))

    # Derive escrow PDA as in program (escrow, client, provider)
    # For demo, provider is a new key
    provider_kp = Keypair()
    seeds = [b"escrow", bytes(payer.pubkey()), bytes(provider_kp.pubkey())]
    # Program id from env
    program_id = Pubkey.from_string(os.getenv("ESCROW_PROGRAM_ID"))
    escrow_pda, _ = Pubkey.find_program_address(seeds, program_id)

    # Ensure payer has some SOL on devnet
    # (optional top-up: transfer to self is not needed; skip)

    # Create mint and token accounts
    mint, client_ata, escrow_ata = await create_mint_and_accounts(client, payer, escrow_pda, decimals=6)

    # Initialize escrow via Gateway
    gw = GatewayEscrowClient()
    sig = await gw.initialize_escrow_via_gateway(
        provider_pubkey=provider_kp.pubkey(),
        amount=100_000_000,  # nominal amount
        service_id="data_analysis_001",
        task_data="Analyze sales data",
        client_token_account=client_ata,
        escrow_token_account=escrow_ata,
    )
    print("Gateway escrow initialized:", sig)

    await gw.close()
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
