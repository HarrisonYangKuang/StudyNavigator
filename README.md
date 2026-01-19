# StudyNavigator

StudyNavigator is a small personal decision-making tool built to help me think more clearly before making study-related choices.

## What is this?
This project records decisions in a structured way and gives a simple recommendation based on self-rated factors like impact, cost, risk, and reversibility.

It is not meant to replace thinking.  
It is meant to slow down impulsive decisions.

## Why I built it
I often make study decisions quickly (competitions, time allocation, projects) and later realize I did not fully think through the trade-offs.

I built this tool to force myself to:
- clearly state my goal
- list my options
- think about risks before committing

## How it works (current version)
The current version is rule-based.

For each decision, the program:
1. asks for the decision, options, goal, and concern
2. asks the user to rate impact, cost, risk, and reversibility (1–5)
3. calculates a simple score (0–100)
4. outputs a recommendation and saves the result locally

This version focuses on transparency and explainability instead of complexity.

## Example use
Example decisions in the log file are for testing purposes only.

The tool is intended for everyday academic decisions, such as whether to join an activity or how to allocate time.

## Project status
This project is under active development.

Planned next steps include:
- adding a reflection mode to evaluate past decisions
- improving scoring logic
- optionally integrating AI in later stages

### Development notes
This project is intentionally developed in small steps.
Early versions focus on clarity and reflection rather than technical complexity.