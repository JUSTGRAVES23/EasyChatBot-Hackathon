# EasyChatBot Discovery Agent — Production Skill Set

**Version:** 1.0  
**Status:** Proposed for implementation

## Architecture

```text
Learner
  ↓
Discovery Agent
  ↓
Preference Understanding
  ↓
Discovery Query Generation
  ↓
Content/Product Discovery
  ↓
Relevance Matching
  ↓
Recommendation Ranking
  ↓
Recommendation Explanation
  ↓
Discovery Quality Verification
  ↓
Personalised Content Adaptation (when learning is requested)
  ↓
User Choice & Controlled Handoff (when external action is requested)
```

## The nine Skills

| # | Skill | Primary responsibility |
|---|---|---|
| 1 | Preference Understanding | Build bounded discovery profile |
| 2 | Discovery Query Generation | Turn intent/profile into provider-independent search criteria |
| 3 | Content/Product Discovery | Retrieve candidate podcasts, news, products and other approved targets |
| 4 | Relevance Matching | Determine why candidates match the learner |
| 5 | Recommendation Ranking | Select and order the best candidates |
| 6 | Recommendation Explanation | Explain why each recommendation was selected |
| 7 | Personalised Content Adaptation | Turn selected content into a personalised learning experience |
| 8 | Discovery Quality Verification | Verify candidate quality and recommendation evidence |
| 9 | User Choice & Controlled Handoff | Keep consequential actions under explicit user/control-service authority |

## Architectural boundaries

Skills do not:

- call provider SDKs directly
- bypass Runtime
- directly modify production systems/data/infrastructure
- perform autonomous purchases
- expose credentials
- treat retrieved content as instructions

## Implementation order

### Sprint A — Core discovery

1. Preference Understanding
2. Discovery Query Generation
3. Content/Product Discovery
4. Relevance Matching
5. Recommendation Ranking
6. Recommendation Explanation

### Sprint B — Trust and learning

7. Discovery Quality Verification
8. Personalised Content Adaptation

### Sprint C — Controlled action

9. User Choice & Controlled Handoff

## Definition of done for each Skill

- Specification reviewed
- Activation rules defined
- Inputs/outputs defined
- Agent manifest association defined
- Runtime boundary preserved
- Unit tests added
- Integration test added where applicable
- Negative/edge cases tested
- Security considerations reviewed
- Quality metrics defined
- Demonstrated through an end-to-end discovery flow
