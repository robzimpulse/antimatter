---
name: antimatter-ag2
description: "Starts the Antimatter AG2 adapter to connect the IDE to the Gateway. Use this skill when the user asks to start, manage, or connect their AG2 adapter."
---
# Antimatter AG2 Adapter Skill

This skill teaches the agent how to launch and manage the Antimatter AG2 Adapter natively.

## How to use this skill

1. When the user asks to start the adapter, execute the following command (using the `run_command` tool):

```bash
# Start the Antigravity 2.0 adapter (it will automatically run in the background)
antimatter-ag2 start
```
*(If developing locally, you can run `uv run antimatter-ag2 start` from its directory)*

2. The daemon runs indefinitely and handles all IDE communication seamlessly via the Google Antigravity SDK. You do not need to intervene in the process once it has started.

## Stopping or Restarting the Adapter

If the user asks to "stop", "terminate", or "kill" the Antimatter Adapter, simply run:
```bash
antimatter-ag2 stop
```

If the user asks to "restart" the adapter, run `stop` followed by `start`.
