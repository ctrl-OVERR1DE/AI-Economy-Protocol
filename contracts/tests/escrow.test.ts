import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { AgentEscrow } from "../target/types/agent_escrow";
import { expect } from "chai";
import {
  createMint,
  createAssociatedTokenAccount,
  mintTo,
  getAccount,
  TOKEN_PROGRAM_ID,
  getAssociatedTokenAddress,
  createAssociatedTokenAccountInstruction,
} from "@solana/spl-token";

describe("agent-escrow", () => {
  // Configure the client to use the local cluster
  // Force local validator to avoid RPC rate limits during tests
  process.env.ANCHOR_PROVIDER_URL = "http://127.0.0.1:8899";
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.AgentEscrow as Program<AgentEscrow>;
  
  let clientKeypair: anchor.web3.Keypair;
  let providerKeypair: anchor.web3.Keypair;
  let escrowPda: anchor.web3.PublicKey;
  let bump: number;

  // SPL token test artifacts
  let mint: anchor.web3.PublicKey;
  let clientTokenAccount: anchor.web3.PublicKey;
  let providerTokenAccount: anchor.web3.PublicKey;
  let escrowTokenAccount: anchor.web3.PublicKey;
  const DECIMALS = 6;
  const FUND_PROVIDER_MIN = 2 * anchor.web3.LAMPORTS_PER_SOL; // ensure payer can cover rents
  const FUND_CLIENT_AMOUNT = 0.5 * anchor.web3.LAMPORTS_PER_SOL; // enough for fees on localnet

  // Helper: fund an account via airdrop, with fallback to transfer from provider wallet
  const fundAccount = async (
    pubkey: anchor.web3.PublicKey,
    lamports: number
  ) => {
    try {
      const sig = await provider.connection.requestAirdrop(pubkey, lamports);
      await provider.connection.confirmTransaction(sig);
      return;
    } catch (e) {
      // Fallback: transfer from provider wallet (works on localnet where payer has funds)
      const tx = new anchor.web3.Transaction().add(
        anchor.web3.SystemProgram.transfer({
          fromPubkey: provider.wallet.publicKey,
          toPubkey: pubkey,
          lamports,
        })
      );
      await provider.sendAndConfirm(tx, []);
    }
  };

  // Helper: ensure a wallet has at least minLamports; try airdrop, else transfer from a provided funder
  const ensureWalletHasLamports = async (
    targetPubkey: anchor.web3.PublicKey,
    minLamports: number,
    fallbackFunder?: anchor.web3.Keypair
  ) => {
    const current = await provider.connection.getBalance(targetPubkey);
    if (current >= minLamports) return;
    try {
      const sig = await provider.connection.requestAirdrop(targetPubkey, minLamports - current);
      await provider.connection.confirmTransaction(sig);
      return;
    } catch (e) {
      if (!fallbackFunder) return;
      const missing = minLamports - current;
      const tx = new anchor.web3.Transaction().add(
        anchor.web3.SystemProgram.transfer({
          fromPubkey: fallbackFunder.publicKey,
          toPubkey: targetPubkey,
          lamports: missing,
        })
      );
      await provider.sendAndConfirm(tx, [fallbackFunder]);
    }
  };

  before(async () => {
    // Create test keypairs
    clientKeypair = anchor.web3.Keypair.generate();
    providerKeypair = anchor.web3.Keypair.generate();

    // Ensure provider wallet (payer) has funds first
    await ensureWalletHasLamports(
      provider.wallet.publicKey,
      FUND_PROVIDER_MIN
    );

    // Fund client for testing (airdrop or fallback transfer from provider)
    await fundAccount(clientKeypair.publicKey, FUND_CLIENT_AMOUNT);

    // Ensure provider wallet (payer) has funds to create mint/token accounts
    await ensureWalletHasLamports(provider.wallet.publicKey, 2 * anchor.web3.LAMPORTS_PER_SOL, clientKeypair);

    // Derive escrow PDA
    [escrowPda, bump] = anchor.web3.PublicKey.findProgramAddressSync(
      [
        Buffer.from("escrow"),
        clientKeypair.publicKey.toBuffer(),
        providerKeypair.publicKey.toBuffer(),
      ],
      program.programId
    );

    // Create test SPL mint
    mint = await createMint(
      provider.connection,
      // payer
      (provider.wallet as any).payer,
      // mint authority
      provider.wallet.publicKey,
      // freeze authority
      null,
      DECIMALS
    );

    // Create token accounts
    clientTokenAccount = await createAssociatedTokenAccount(
      provider.connection,
      (provider.wallet as any).payer,
      mint,
      clientKeypair.publicKey
    );

    providerTokenAccount = await createAssociatedTokenAccount(
      provider.connection,
      (provider.wallet as any).payer,
      mint,
      providerKeypair.publicKey
    );

    // Create escrow PDA's associated token account (allow owner off-curve)
    const escrowAta = await getAssociatedTokenAddress(
      mint,
      escrowPda,
      true // allowOwnerOffCurve
    );
    const createEscrowAtaIx = createAssociatedTokenAccountInstruction(
      provider.wallet.publicKey, // payer
      escrowAta,
      escrowPda, // owner (PDA)
      mint
    );
    await provider.sendAndConfirm(new anchor.web3.Transaction().add(createEscrowAtaIx), []);
    escrowTokenAccount = escrowAta;

    // Mint tokens to client
    await mintTo(
      provider.connection,
      (provider.wallet as any).payer,
      mint,
      clientTokenAccount,
      provider.wallet.publicKey,
      1_000_000_000n // 1,000 tokens with 6 decimals
    );
  });

  it("Initializes escrow", async () => {
    const amount = new anchor.BN(100_000_000); // 0.1 SOL
    const serviceId = "data_analysis_001";
    const taskHash = Array(32).fill(1); // Mock task hash

    const tx = await program.methods
      .initializeEscrow(amount, serviceId, taskHash)
      .accounts({
        client: clientKeypair.publicKey,
        provider: providerKeypair.publicKey,
        clientTokenAccount,
        escrowTokenAccount,
        // tokenProgram/systemProgram auto-filled by Anchor 0.31 (fixed addresses)
      })
      .signers([clientKeypair])
      .rpc();

    console.log("Initialize escrow transaction:", tx);

    // Fetch escrow account
    const escrowAccount = await program.account.escrow.fetch(escrowPda);
    
    expect(escrowAccount.client.toString()).to.equal(clientKeypair.publicKey.toString());
    expect(escrowAccount.provider.toString()).to.equal(providerKeypair.publicKey.toString());
    expect(escrowAccount.amount.toNumber()).to.equal(amount.toNumber());
    expect(escrowAccount.serviceId).to.equal(serviceId);
    expect(escrowAccount.status).to.deep.equal({ pending: {} });
  });

  it("Submits proof of completion", async () => {
    const proofHash = Array(32).fill(2); // Mock proof hash

    const tx = await program.methods
      .submitProof(proofHash)
      .accountsPartial({
        escrow: escrowPda,
        provider: providerKeypair.publicKey,
      })
      .signers([providerKeypair])
      .rpc();

    console.log("Submit proof transaction:", tx);

    // Fetch updated escrow account
    const escrowAccount = await program.account.escrow.fetch(escrowPda);
    
    expect(escrowAccount.status).to.deep.equal({ proofSubmitted: {} });
    expect(escrowAccount.proofHash).to.not.be.null;
  });

  it("Releases payment to provider", async () => {
    const providerTokenBefore = await getAccount(
      provider.connection,
      providerTokenAccount
    );

    const tx = await program.methods
      .releasePayment()
      .accountsPartial({
        escrow: escrowPda,
        escrowTokenAccount,
        providerTokenAccount,
        authority: clientKeypair.publicKey,
      })
      .signers([clientKeypair])
      .rpc();

    console.log("Release payment transaction:", tx);

    // Fetch final escrow account
    const escrowAccount = await program.account.escrow.fetch(escrowPda);
    
    expect(escrowAccount.status).to.deep.equal({ completed: {} });

    // Verify provider received tokens
    const providerTokenAfter = await getAccount(
      provider.connection,
      providerTokenAccount
    );
    expect(providerTokenAfter.amount > providerTokenBefore.amount).to.be.true;
  });

  it("Cancels escrow and refunds client", async () => {
    // Create a new escrow for cancellation test
    const newClientKeypair = anchor.web3.Keypair.generate();
    const newProviderKeypair = anchor.web3.Keypair.generate();

    // Fund new client
    await fundAccount(newClientKeypair.publicKey, FUND_CLIENT_AMOUNT);

    const [newEscrowPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [
        Buffer.from("escrow"),
        newClientKeypair.publicKey.toBuffer(),
        newProviderKeypair.publicKey.toBuffer(),
      ],
      program.programId
    );

    // Initialize new escrow
    const amount = new anchor.BN(50_000_000);
    // Create token accounts for new client and new escrow PDA
    const newClientTokenAccount = await createAssociatedTokenAccount(
      provider.connection,
      (provider.wallet as any).payer,
      mint,
      newClientKeypair.publicKey
    );
    const newEscrowAta = await getAssociatedTokenAddress(
      mint,
      newEscrowPda,
      true // allowOwnerOffCurve
    );
    const createNewEscrowAtaIx = createAssociatedTokenAccountInstruction(
      provider.wallet.publicKey, // payer
      newEscrowAta,
      newEscrowPda, // owner (PDA)
      mint
    );
    await provider.sendAndConfirm(new anchor.web3.Transaction().add(createNewEscrowAtaIx), []);
    const newEscrowTokenAccount = newEscrowAta;
    // Fund new client's token account
    await mintTo(
      provider.connection,
      (provider.wallet as any).payer,
      mint,
      newClientTokenAccount,
      provider.wallet.publicKey,
      500_000_000n // 500 tokens
    );
    await program.methods
      .initializeEscrow(amount, "test_service", Array(32).fill(3))
      .accounts({
        client: newClientKeypair.publicKey,
        provider: newProviderKeypair.publicKey,
        clientTokenAccount: newClientTokenAccount,
        escrowTokenAccount: newEscrowTokenAccount,
      })
      .signers([newClientKeypair])
      .rpc();

    // Cancel escrow
    const clientTokenBefore = await getAccount(
      provider.connection,
      newClientTokenAccount
    );

    const tx = await program.methods
      .cancelEscrow()
      .accountsPartial({
        escrow: newEscrowPda,
        client: newClientKeypair.publicKey,
        escrowTokenAccount: newEscrowTokenAccount,
        clientTokenAccount: newClientTokenAccount,
      })
      .signers([newClientKeypair])
      .rpc();

    console.log("Cancel escrow transaction:", tx);

    // Verify escrow is cancelled
    const escrowAccount = await program.account.escrow.fetch(newEscrowPda);
    expect(escrowAccount.status).to.deep.equal({ cancelled: {} });

    // Verify client received token refund
    const clientTokenAfter = await getAccount(
      provider.connection,
      newClientTokenAccount
    );
    expect(clientTokenAfter.amount > clientTokenBefore.amount).to.be.true;
  });
});
