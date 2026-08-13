# EasyChatBot — Podcast Learning Challenge MVP

## User experience

```text
Memory + Learning World
        |
        v
Podcast Agent
        |
        v
Apple / Spotify
        |
        v
Language + preference filtering
        |
        v
Character recommendation
        |
        v
+-----------------------------+
| 🎧 PODCAST FIND             |
|                             |
| [ LISTEN ]                  |
| [ START CHALLENGE ]         |
+-----------------------------+
        |
        v
PodcastLearningChallenge
        |
        +--> Vocabulary
        +--> Comprehension
        +--> Discussion
        |
        v
ChallengeResult
```

## Scope

This is a hackathon MVP. The challenge is created from **verified podcast
metadata** and the learner's explicit language/level context.

It does not claim to have listened to or transcribed the podcast.

Out of scope:

- audio download
- transcription
- transcript semantic search
- autonomous playback
- Spotify user history
- subscriptions
- persistent memory writes

## Validation

Run:

```powershell
pytest tests/ai_runtime/podcast -v
```

Then:

```powershell
python src/ai_runtime/podcast/challenge_demo.py
```

The demo is deterministic and does not require network access.
