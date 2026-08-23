# EasyChatBot Beta 1 — DPO / GRC Sign-off Pack

**Version:** 1.0-DRAFT  
**Scope:** Beta 1 only  
**Status:** PENDING DPO / GRC / Legal review

## Purpose

This pack is designed for formal review and sign-off of the Beta 1 privacy
and data-governance operating model.

It is deliberately structured as a governance artifact rather than a runtime
component.

## Required reviewers

| Role | Responsibility | Decision |
|---|---|---|
| Head Engineer | Confirms implementation matches the documented data flows and controls | PENDING |
| DPO / Privacy Owner | Determines GDPR compliance, legal bases, rights, retention, DPIA and transparency requirements | PENDING |
| Head GRC | Confirms governance, control ownership, evidence and review cadence | PENDING |
| Legal reviewer | Confirms legal interpretation, contractual/transfer requirements where needed | PENDING |

## No implied approval

The inclusion of a legal article or a proposed control does not constitute
a legal opinion or DPO approval. The workbook intentionally leaves material
legal determinations as `TBD`/`PENDING` where project facts or legal review are
required.

## Mandatory pre-Beta approval questions

1. Who is the controller for each Beta 1 processing activity?
2. What is the Article 6 legal basis for each distinct purpose?
3. Could free-form learner messages contain Article 9 special-category data?
4. What retention period and deletion trigger apply to access and conversation
   records?
5. Which Telegram/AI/provider entities act as controller, processor or another
   role?
6. Are Article 28 contractual requirements satisfied where a processor is used?
7. Are any third-country transfers involved, and if so, what Article 44–49
   mechanism applies?
8. Is a DPIA required under Article 35?
9. Are Articles 12–14 transparency requirements satisfied?
10. Can data-subject rights be operationally fulfilled?
11. Are Article 25 and Article 32 controls implemented and evidenced?
12. Does the documented processing exactly match the production/Beta system?

## Sign-off

### DPO / Privacy Owner

Name: ______________________________  
Decision: ☐ Approved  ☐ Approved with conditions  ☐ Rejected  
Date: ______________________________  
Conditions / findings:

________________________________________________________________________

Signature: __________________________

### Head GRC

Name: ______________________________  
Decision: ☐ Approved  ☐ Approved with conditions  ☐ Rejected  
Date: ______________________________  
Conditions / findings:

________________________________________________________________________

Signature: __________________________

### Legal Reviewer

Name: ______________________________  
Decision: ☐ Approved  ☐ Approved with conditions  ☐ Rejected  
Date: ______________________________  
Conditions / findings:

________________________________________________________________________

Signature: __________________________

### Head Engineer

Name: ______________________________  
Decision: ☐ Implemented as documented  ☐ Remediation required  
Date: ______________________________  
Technical findings:

________________________________________________________________________

Signature: __________________________
