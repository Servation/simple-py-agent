# ADR 0004: Automatic Log Compaction with Archival

## Status
Proposed

## Context
As the agent writes log entries using `write_ships_log`, the size of `ships_log.txt` grows indefinitely. Reading the log via `read_ships_log` consumes an increasing number of context window tokens, raising latency and API costs. We need a way to manage log size while preserving historical records.

We considered:
1. Overwriting logs with an LLM summary directly (Strategy A only).
2. Manual compaction via an explicit tool.
3. Automatically archiving raw logs to `ships_log_archive.txt`, summarizing the active logs, and writing the summary as the new starting point of `ships_log.txt` once the active log hits 30 lines (Combination of Strategy A and Strategy B).

## Decision
We will implement automatic log compaction when the active log reaches 30 entries. The system will:
1. Append the active log to `ships_log_archive.txt`.
2. Invoke the LLM Client in the background to summarize the active log entries into a concise 5-bullet summary.
3. Overwrite the active `ships_log.txt` with this summary.

## Consequences
- **Pros**:
  - Context optimization: Keeps `ships_log.txt` under 35 lines at all times, making `read_ships_log` incredibly cheap and fast.
  - Zero data loss: All raw, original timestamped entries are permanently preserved in `ships_log_archive.txt`.
  - Self-maintaining: The agent handles its own memory scaling transparently without requiring user intervention.
- **Cons**:
  - Write latency: Every 30th log write will trigger an additional background LLM request to compute the summary, slightly increasing the duration of that specific tool execution.
  - Implementation complexity: The `write_ships_log` tool must be passed a reference to the active `LLMClient` to perform the summarization.
