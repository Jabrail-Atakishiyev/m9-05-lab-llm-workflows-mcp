![logo_ironhack_blue 7](https://user-images.githubusercontent.com/23629340/40541063-a07a0a8a-601a-11e8-91b5-2f13e4e6b441.png)

# Lab | Build the Loop Yourself

## Overview

Yesterday the Gemini SDK ran the tool-use loop for you. Today you write it **by hand, in plain Python** — no agent framework — so you can see exactly what an agent secretly is before we hand the model the wheel tomorrow. You'll add the two things that turn a single tool call into a small working system: **short-term memory** (so the model remembers the conversation) and a **step limit** (so the loop can never run away).

This is the "workflow" mindset in practice: *you* hold the control flow, and the model fills in the steps.

## Learning Goals

- Hand-roll the model→tool→model loop with your own control flow
- Maintain short-term memory by resending the running conversation
- Bound the loop with a step limit so it can never loop forever

## Setup

Fork, clone, branch. Reuse your Gemini key and the two tools from yesterday (`lookup_order`, `calculate`); `orders.json` is included again.

```bash
pip install -r requirements.txt
export GOOGLE_API_KEY="your-free-gemini-key"
```

> **No starter code — you build it from scratch.** There's no template in this repo; create your own working file(s) and write the code yourself. This close to the end of the bootcamp, scaffolding your own project is part of the exercise.

## Your Task

**Write the tool-call loop yourself, with memory and a step limit.**

1. Keep a **`messages` list** as your short-term memory. Every model call sends the whole list; every reply and every tool result gets appended to it.
2. Write the loop in plain Python:
   - call the model with the messages and the tool definitions,
   - if it requests a tool, **run the tool yourself**, append the result, and loop again,
   - if it returns a final answer, stop.
3. Add a **step limit** (e.g. stop after 5 iterations). If the loop hits it, stop and report "couldn't finish in time" rather than looping forever.
4. Demonstrate that **memory works** with a two-turn conversation where the second turn depends on the first:
   - Turn 1: *"What did order A1001 cost?"*
   - Turn 2: *"And what about three of them?"* ← only answerable because the model remembers turn 1

   Show that the second answer is correct because the prior turn is still in `messages`.

Your deliverable should make the loop and the memory visible — print each step the loop takes.

### Optional stretch — taste of MCP

Connect **one MCP tool** to your loop instead of a hand-written function (for example, a filesystem or fetch MCP server). You don't need to build a server — use an existing one and call one of its tools through the loop. Note in a comment how the standard MCP interface differs from wiring a function by hand.

## Submission

Commit your code and a transcript showing the loop's steps and the two-turn memory demo. Open a PR and paste the link.

## Quality Bar

- The loop is written by hand in plain Python (no agent framework)
- Short-term memory is a running `messages` list, and the two-turn demo proves it works
- A step limit is present and stops the loop cleanly
- No API key is committed
