# PROMPTS.md — Delta Agent Gatekeeper

This file is a template to help document the prompts actually used with your coding agent.
Replace or edit these entries so they accurately describe your real session. Do not claim
that a prompt was used if it was not.

## Main build prompt (suggested)
"Build a small Flask web app called Delta Agent Gatekeeper. It should register customer AI agents,
accept a customer name, agent name, action, and amount, and decide ALLOW, ASK CUSTOMER, or BLOCK.
Use the airline actions view fares, book, change, and refund. Show the rule number and reason.
Persist agents, revocation timestamps, and a timestamped audit log in JSON files."

## Policy prompt (suggested)
"Use these rules: unknown agents BLOCK; revoked agents BLOCK; customer mismatch BLOCK;
registered active agents may view fares; booking up to USD 500 ALLOW; booking above USD 500
ASK CUSTOMER; change and refund ASK CUSTOMER. Show six test cases with expected and actual results."

## What I checked/changed myself
After running the app, write down one real check or change you personally performed here.
Example only: "I registered a test agent, revoked it, and checked that a later fare-view request
was blocked and that the revocation time appeared in the agent table."

## Session evidence
Add genuine screenshots of your coding-agent session in the `Screenshots/` folder.
Include visible date/time where available.
