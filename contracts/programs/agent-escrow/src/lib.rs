use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount, Transfer};

declare_id!("HgzpCVSzmSwveikHVTpt85jVXpcqnJWQNcZzFbnjMEz9");

#[program]
pub mod agent_escrow {
    use super::*;

    /// Initialize a new escrow for an agent service request
    pub fn initialize_escrow(
        ctx: Context<InitializeEscrow>,
        amount: u64,
        service_id: String,
        task_hash: [u8; 32],
    ) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        escrow.client = ctx.accounts.client.key();
        escrow.provider = ctx.accounts.provider.key();
        escrow.amount = amount;
        escrow.service_id = service_id.clone();
        escrow.task_hash = task_hash;
        escrow.status = EscrowStatus::Pending;
        escrow.created_at = Clock::get()?.unix_timestamp;
        escrow.bump = ctx.bumps.escrow;

        // Transfer funds from client to escrow
        let cpi_accounts = Transfer {
            from: ctx.accounts.client_token_account.to_account_info(),
            to: ctx.accounts.escrow_token_account.to_account_info(),
            authority: ctx.accounts.client.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        token::transfer(cpi_ctx, amount)?;

        msg!("Escrow initialized: {} SOL locked for service {}", amount, service_id);
        Ok(())
    }

    /// Provider submits proof of task completion
    pub fn submit_proof(
        ctx: Context<SubmitProof>,
        proof_hash: [u8; 32],
    ) -> Result<()> {
        let escrow = &mut ctx.accounts.escrow;
        
        require!(
            escrow.status == EscrowStatus::Pending,
            EscrowError::InvalidStatus
        );
        
        escrow.proof_hash = Some(proof_hash);
        escrow.status = EscrowStatus::ProofSubmitted;
        escrow.completed_at = Some(Clock::get()?.unix_timestamp);

        msg!("Proof submitted for escrow");
        Ok(())
    }

    /// Release payment to provider after verification
    pub fn release_payment(ctx: Context<ReleasePayment>) -> Result<()> {
        // Extract values and check status
        let (amount, client, provider, task_hash, bump) = {
            let escrow = &ctx.accounts.escrow;
            require!(
                escrow.status == EscrowStatus::ProofSubmitted,
                EscrowError::InvalidStatus
            );
            (escrow.amount, escrow.client, escrow.provider, escrow.task_hash, escrow.bump)
        };

        // Transfer funds from escrow to provider
        let seeds = &[
            b"escrow",
            client.as_ref(),
            provider.as_ref(),
            task_hash.as_ref(),
            &[bump],
        ];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.provider_token_account.to_account_info(),
            authority: ctx.accounts.escrow.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new_with_signer(cpi_program, cpi_accounts, signer);
        token::transfer(cpi_ctx, amount)?;

        // Update escrow status after transfer
        let escrow = &mut ctx.accounts.escrow;
        escrow.status = EscrowStatus::Completed;
        escrow.released_at = Some(Clock::get()?.unix_timestamp);

        msg!("Payment released: {} SOL to provider", amount);
        Ok(())
    }

    /// Cancel escrow and refund client (only if proof not submitted)
    pub fn cancel_escrow(ctx: Context<CancelEscrow>) -> Result<()> {
        // Extract values and check status
        let (amount, client, provider, task_hash, bump) = {
            let escrow = &ctx.accounts.escrow;
            require!(
                escrow.status == EscrowStatus::Pending,
                EscrowError::CannotCancel
            );
            (escrow.amount, escrow.client, escrow.provider, escrow.task_hash, escrow.bump)
        };

        // Refund client
        let seeds = &[
            b"escrow",
            client.as_ref(),
            provider.as_ref(),
            task_hash.as_ref(),
            &[bump],
        ];
        let signer = &[&seeds[..]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.escrow_token_account.to_account_info(),
            to: ctx.accounts.client_token_account.to_account_info(),
            authority: ctx.accounts.escrow.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new_with_signer(cpi_program, cpi_accounts, signer);
        token::transfer(cpi_ctx, amount)?;

        // Update escrow status after transfer
        let escrow = &mut ctx.accounts.escrow;
        escrow.status = EscrowStatus::Cancelled;

        msg!("Escrow cancelled and refunded");
        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(amount: u64, service_id: String, task_hash: [u8; 32])]
pub struct InitializeEscrow<'info> {
    #[account(
        init,
        payer = client,
        space = 8 + Escrow::INIT_SPACE,
        // Include task_hash in seeds to derive a unique PDA per task
        seeds = [b"escrow", client.key().as_ref(), provider.key().as_ref(), task_hash.as_ref()],
        bump
    )]
    pub escrow: Account<'info, Escrow>,
    
    #[account(mut)]
    pub client: Signer<'info>,
    
    /// CHECK: Provider's public key
    pub provider: AccountInfo<'info>,
    
    #[account(mut)]
    pub client_token_account: Account<'info, TokenAccount>,
    
    #[account(mut)]
    pub escrow_token_account: Account<'info, TokenAccount>,
    
    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct SubmitProof<'info> {
    #[account(
        mut,
        // Use stored task_hash to match the initialize seeds
        seeds = [b"escrow", escrow.client.as_ref(), escrow.provider.as_ref(), escrow.task_hash.as_ref()],
        bump = escrow.bump,
        has_one = provider
    )]
    pub escrow: Account<'info, Escrow>,
    
    pub provider: Signer<'info>,
}

#[derive(Accounts)]
pub struct ReleasePayment<'info> {
    #[account(
        mut,
        // Use stored task_hash to match the initialize seeds
        seeds = [b"escrow", escrow.client.as_ref(), escrow.provider.as_ref(), escrow.task_hash.as_ref()],
        bump = escrow.bump,
    )]
    pub escrow: Account<'info, Escrow>,
    
    #[account(mut)]
    pub escrow_token_account: Account<'info, TokenAccount>,
    
    #[account(mut)]
    pub provider_token_account: Account<'info, TokenAccount>,
    
    /// CHECK: Can be client or authorized verifier
    pub authority: Signer<'info>,
    
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct CancelEscrow<'info> {
    #[account(
        mut,
        // Use stored task_hash to match the initialize seeds
        seeds = [b"escrow", escrow.client.as_ref(), escrow.provider.as_ref(), escrow.task_hash.as_ref()],
        bump = escrow.bump,
        has_one = client
    )]
    pub escrow: Account<'info, Escrow>,
    
    pub client: Signer<'info>,
    
    #[account(mut)]
    pub escrow_token_account: Account<'info, TokenAccount>,
    
    #[account(mut)]
    pub client_token_account: Account<'info, TokenAccount>,
    
    pub token_program: Program<'info, Token>,
}

#[account]
#[derive(InitSpace)]
pub struct Escrow {
    pub client: Pubkey,
    pub provider: Pubkey,
    pub amount: u64,
    #[max_len(64)]
    pub service_id: String,
    pub task_hash: [u8; 32],
    pub proof_hash: Option<[u8; 32]>,
    pub status: EscrowStatus,
    pub created_at: i64,
    pub completed_at: Option<i64>,
    pub released_at: Option<i64>,
    pub bump: u8,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq, InitSpace)]
pub enum EscrowStatus {
    Pending,
    ProofSubmitted,
    Completed,
    Cancelled,
}

#[error_code]
pub enum EscrowError {
    #[msg("Invalid escrow status for this operation")]
    InvalidStatus,
    #[msg("Cannot cancel escrow after proof submission")]
    CannotCancel,
}
