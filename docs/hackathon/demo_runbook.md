# EasyChatBot Hackathon Demo Runbook

## Purpose

Internal execution guide for the EasyChatBot hackathon demonstration.

This document is not part of the judge presentation.

---

# Official Demo Selection

## Judge Presentation Demo

File:

examples/hackathon_judge_demo.py


## Regression Validation Demo

File:

examples/hackathon_demo.py


---

# Pre-Demo Checklist

## Environment

Verify:

- Python environment activated
- Dependencies installed
- Repository clean
- Tests passing


Command:

pytest ".\tests" -q --tb=short


---

# Demo Execution

## Judge Demo

Command:

python ".\examples\hackathon_judge_demo.py"


Expected:

- Demo completes successfully
- No exceptions
- Final success message displayed


---

# Demo Story Order

## 0:00 - Opening

Problem:

Information overload prevents personalised learning.


## 0:30 - Governance

Explain:

The Runtime controls capability execution.


## 1:00 - Live Intelligence

Explain:

Real-world information is transformed into structured intelligence.


## 1:30 - Learning Transformation

Explain:

Information becomes learning content.


## 2:00 - Discovery

Explain:

Content is discovered, ranked and personalised.


## 2:30 - Controlled Actions

Explain:

The system keeps humans in control.


---

# Backup Procedure

If live demo fails:

1. Do not debug during presentation.
2. Show validated test results.
3. Show architecture.
4. Explain the working flow.


---

# Troubleshooting

## Demo does not start

Run:

pytest ".\tests" -q --tb=short


## Runtime issue

Verify:

- capability registration
- Runtime composition
- provider boundaries


---

# Final Validation

Before submission:

- [ ] Judge demo executed successfully
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Repository committed