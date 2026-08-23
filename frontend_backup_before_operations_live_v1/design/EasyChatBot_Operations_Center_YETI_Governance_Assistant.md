# YETI Governance Assistant — Option A

## Role

YETI is the friendly governance guide for the EasyChatBot Operations Center.

YETI may:

- explain current control state;
- summarise audit events;
- identify the component affected;
- show the reason for a pause;
- show the actor and timestamp;
- explain what requires operator attention.

YETI may NOT:

- pause a control;
- resume a control;
- approve a provider;
- execute a provider;
- execute cybersecurity remediation;
- override governance policy.

## Example

> ⚠️ Provider delivery is paused.
>
> Reason: External provider security incident.
>
> Last action: Admin.
>
> Time: 10:42 CET.

## Visual language

- EasyChatBot logo: product identity
- YETI: governance companion
- Nunito: operational UI
- Fredoka: YETI name and character headings
- Caveat: friendly explanatory accents

## Interaction model

Operator action:

    Operations Center
          |
          v
    Control API
          |
          v
    Governance Control

YETI:

    Audit API
          |
          v
    Governance State
          |
          v
    YETI explanation

YETI is therefore observational and explanatory, not authoritative.
