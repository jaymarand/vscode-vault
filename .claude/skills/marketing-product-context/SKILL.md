---
name: product-marketing-context
description: "When the user wants to create or update their product marketing context document. Also use when the user mentions 'product context,' 'marketing context,' 'set up context,' 'positioning,' 'who is my target audience,' 'describe my product,' 'ICP,' 'ideal customer profile,' or wants to avoid repeating foundational information across marketing tasks. Use this at the start of any new project before using other marketing skills — it creates `.agents/product-marketing-context.md` that all other skills reference for product, audience, and positioning context."
metadata:
  version: 1.1.0
  source: https://github.com/coreyhaines31/marketingskills
---

# Product Marketing Context

You help users create and maintain a product marketing context document. This captures foundational positioning and messaging information that other marketing skills reference, so users don't repeat themselves.

The document is stored at `.agents/product-marketing-context.md`.

## Workflow

### Step 1: Check for Existing Context

First, check if `.agents/product-marketing-context.md` already exists. Also check `.claude/product-marketing-context.md` for older setups — if found there but not in `.agents/`, offer to move it.

**If it exists:**
- Read it and summarize what's captured
- Ask which sections they want to update
- Only gather info for those sections

**If it doesn't exist, offer two options:**

1. **Auto-draft from codebase** (recommended): Study the repo—README, landing pages, marketing copy, package.json, etc.—and draft a V1. The user then reviews, corrects, and fills gaps.

2. **Start from scratch**: Walk through each section conversationally, gathering info one section at a time.

### Step 2: Gather Information

Walk through each section below conversationally, one at a time. Don't dump all questions at once.

## Sections to Capture

### 1. Product Overview
- One-line description
- What it does (2-3 sentences)
- Product category
- Product type (SaaS, marketplace, e-commerce, service, etc.)
- Business model and pricing

### 2. Target Audience
- Target company type (industry, size, stage)
- Target decision-makers (roles, departments)
- Primary use case
- Jobs to be done (2-3 things customers "hire" you for)
- Specific use cases or scenarios

### 3. Personas (B2B only)
- User, Champion, Decision Maker, Financial Buyer, Technical Influencer
- What each cares about, their challenge, and the value you promise them

### 4. Problems & Pain Points
- Core challenge customers face before finding you
- Why current solutions fall short
- What it costs them (time, money, opportunities)
- Emotional tension (stress, fear, doubt)

### 5. Competitive Landscape
- **Direct competitors**: Same solution, same problem
- **Secondary competitors**: Different solution, same problem
- **Indirect competitors**: Conflicting approach

### 6. Differentiation
- Key differentiators
- How you solve it differently
- Why that's better
- Why customers choose you over alternatives

### 7. Objections & Anti-Personas
- Top 3 objections and how to address them
- Who is NOT a good fit

### 8. Switching Dynamics (JTBD Four Forces)
- **Push**: Frustrations with current solution
- **Pull**: What attracts them to you
- **Habit**: What keeps them stuck
- **Anxiety**: What worries them about switching

### 9. Customer Language
- How customers describe the problem (verbatim)
- How they describe your solution (verbatim)
- Words/phrases to use and avoid

### 10. Brand Voice
- Tone, communication style, brand personality

### 11. Proof Points
- Key metrics, notable customers, testimonials

### 12. Goals
- Primary business goal
- Key conversion action
- Current metrics

## Step 3: Create the Document

Save to `.agents/product-marketing-context.md` with structured sections for each area above.

## Tips

- **Be specific**: Ask "What's the #1 frustration that brings them to you?"
- **Capture exact words**: Customer language beats polished descriptions
- **Ask for examples**: "Can you give me an example?" unlocks better answers
- **Validate as you go**: Summarize each section and confirm before moving on
- **Skip what doesn't apply**: Not every product needs all sections
