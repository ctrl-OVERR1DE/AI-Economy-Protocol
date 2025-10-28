# Multi-Client Scalability Demo

## Quick Start

Demonstrates concurrent autonomous agent requests with Sanctum Gateway payment processing.

### Step 1: Start Provider Agent

```bash
# Terminal 1
python agents/agent_a.py
```

Wait for:
```
INFO: [DataAnalystAgent]: Ready to provide data analysis services!
INFO: [DataAnalystAgent]: Starting server on http://0.0.0.0:5051
```

### Step 2: Start Client B

```bash
# Terminal 2
python agents/agent_b.py
```

### Step 3: Start Client C

```bash
# Terminal 3
python agents/agent_c.py
```

## What to Watch For

### Agent A (Provider) Logs:
```
✅ Proof submitted!
💼 Ready to accept new service requests!  ← Shows it can handle multiple clients
```

### Agent B & C (Clients) Logs:
```
✅ Escrow initialized!
   Transaction: [Gateway tx signature]
✅ Payment released!
   Transaction: [Gateway tx signature]
```

## Expected Flow

1. **Both clients discover Agent A** (hardcoded address)
2. **Concurrent service requests** sent to Agent A
3. **Agent A handles both** without blocking:
   - Sends pricing quotes to both
   - Receives escrow confirmations from both
   - Processes both tasks
   - Submits proofs for both
4. **Both clients release payments** via Sanctum Gateway
5. **Agent A ready for more requests** (persistent)

## Key Observations

- ✅ **No conflicts**: Each client gets unique escrow PDA
- ✅ **Parallel Gateway calls**: Multiple transactions via Gateway simultaneously
- ✅ **Autonomous coordination**: No manual intervention needed
- ✅ **Persistent agents**: All agents keep running after transactions complete

## Scalability Proof

This demonstrates:
- **Horizontal scaling**: Add more clients → system handles them
- **Vertical scaling**: Single provider serves multiple clients
- **Gateway reliability**: All payments succeed regardless of concurrency
- **True autonomy**: Zero human intervention from start to finish

---

**Result**: A functioning autonomous agent economy powered by Sanctum Gateway! 🚀
