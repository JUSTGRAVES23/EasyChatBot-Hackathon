# EasyChatBot — Personalised Podcast Discovery MVP

## Canonical flow

```text
Memory + Learning World
        |
        v
PodcastDiscoveryAgent
        |
        v
PodcastSearchIntent
        |
        v
Apple / Spotify Provider Layer
        |
        v
Normalised PodcastSearchResult
        |
        v
PodcastRecommendationService
        |
        +--> HARD TARGET-LANGUAGE FILTER
        +--> USER-PREFERENCE MATCHING
        +--> LEARNING-WORLD RELEVANCE
        |
        v
PodcastRecommendation
        |
        v
Character
        |
        v
LISTEN / MORE INFORMATION
```

## Critical product rule

EasyChatBot is a language-learning platform. Therefore the target
language is a **hard eligibility constraint**, not merely a search term.

A French World learner must not receive an English podcast simply because
the topic matches.

Unknown-language candidates are also rejected when `language_required=True`.

## Provider independence

The Agent does not know whether Apple or Spotify is used. It produces
`PodcastSearchIntent`; providers translate that intent into their own
API syntax and return normalised `PodcastSearchResult` objects.

## Memory

Only explicit `MemoryType.PREFERENCE` memories are treated as preferences,
consistent with the existing discovery implementation. Optional metadata:

```text
topics=artificial intelligence, European regulation
keywords=technology,current affairs
```

Agents do not write persistent memory.

## Apple

The Apple adapter uses the iTunes Search API with `media=podcast`.

Apple documents approximately 20 Search API calls/minute and recommends
limiting results and caching.

## Spotify

The MVP searches Spotify **episodes**, because episode metadata exposes
`languages`. User-specific Spotify library/playback access is out of scope.

Use an injected access token. Credential acquisition belongs outside this
adapter. Spotify documents Client Credentials for server-to-server access
when user information is not required.

## Security / governance

The podcast capability is read-only. It does not:

- subscribe to podcasts
- download audio
- modify Spotify libraries
- start playback
- write memory
- execute purchases

The user remains responsible for the final LISTEN action.

## Validation

```powershell
pytest tests/ai_runtime/podcast -v
python examples/podcast_personalisation_demo.py
```

The tests and demo are deterministic and do not require network access.
