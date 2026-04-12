---
name: research-agent
description: Spawn a fast, cheap Haiku subagent to research topics via web search. Use this skill whenever the user says "research this," "look into," "find out about," "what's the latest on," "compare options for," "what are people saying about," "is there a tool for," "find competitors," "market research," or any time current information from the web would help answer the question. Also use when the user needs to verify claims, find documentation, check pricing, or gather data before making a decision. Even if the user doesn't explicitly say "research," use this when answering well requires up-to-date information beyond training data.
---

# Research Agent

Spawn a lightweight Haiku subagent to do web research fast and cheap. Use this instead of doing research in the main conversation — it keeps context clean and runs faster.

## When to Use

- User asks you to research, investigate, or look into something
- You need current information to answer a question well
- Comparing tools, services, competitors, or pricing
- Checking what's new or trending in a space
- Verifying claims or finding sources
- Gathering data before making a recommendation

## How to Spawn

Use the Agent tool with these settings:

```
Agent({
  description: "Research: [brief topic]",
  model: "haiku",
  prompt: "<your research brief>"
})
```

**Always use `model: "haiku"`** — it's fast, cheap, and plenty capable for search and summarization.

## Writing the Research Brief

The subagent has no context from your conversation. Brief it like a colleague who just walked in:

1. **What to find out** — be specific about the question
2. **Why it matters** — context helps the agent make judgment calls
3. **What to return** — specify the output format
4. **Scope limits** — how deep to go, what to skip

### Example Briefs

**Market research:**
```
Research the current landscape of automated website design tools and services.
I'm building a business that scrapes Google Maps for businesses with poor websites,
redesigns them, and sells the redesign. I need to understand:
- Who are the main competitors doing something similar?
- What do they charge?
- What's their pitch to small businesses?
Return bullet points with source URLs. Keep it under 300 words.
```

**Tool comparison:**
```
Compare the top 3 email automation platforms suitable for cold outreach at scale.
I need: pricing, sending limits, deliverability reputation, and API access.
Format as a comparison table. Include source URLs.
```

**Quick fact-check:**
```
Find the current pricing for Vercel Pro and Team plans.
Just the prices and what's included at each tier. Under 100 words.
```

## Output Format

Tell the subagent what format you want. Good defaults:

- **Quick lookup**: "Under 100 words, just the facts"
- **Summary**: "Bullet points with source URLs, under 300 words"
- **Deep dive**: "Structured report with sections, include all sources"
- **Comparison**: "Table format comparing X, Y, Z on these dimensions"

## Parallel Research

When you need multiple things researched, spawn multiple agents in a single message:

```
Agent({ description: "Research: competitor A", model: "haiku", prompt: "..." })
Agent({ description: "Research: competitor B", model: "haiku", prompt: "..." })
Agent({ description: "Research: pricing models", model: "haiku", prompt: "..." })
```

They run concurrently. Use this liberally — Haiku is cheap.

## After Research

The subagent's results come back as a tool result (not visible to the user). You need to:

1. **Synthesize** — don't just dump the raw results. Pull out what matters.
2. **Relate to context** — connect findings to the user's situation
3. **Recommend** — if the research supports a decision, make one

## Guidelines

- **Haiku only** — don't use Sonnet or Opus for research. Haiku handles search and summarization well.
- **Be specific in briefs** — vague prompts get vague results
- **Cap the output** — tell the agent a word limit so it doesn't ramble
- **Include "source URLs"** — always ask for sources so findings are verifiable
- **Run in background** when the research isn't blocking your next step — use `run_in_background: true`
