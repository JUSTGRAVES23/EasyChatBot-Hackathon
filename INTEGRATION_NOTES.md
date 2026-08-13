# Integration Notes

This slice is intentionally isolated from the already-green commerce and
Flash Deal flows.

Before changing the main judge demo:

1. Run `pytest tests/ai_runtime/podcast -v`
2. Run `python examples/podcast_personalisation_demo.py`
3. Review the language-filter tests
4. Only then integrate the podcast vertical slice into the judge demo.

The intended architecture is:

Memory -> Podcast Agent -> Search Intent -> Provider Layer
-> Normalised Results -> Recommendation Service -> Character -> User Choice

Do not let the Agent call Apple/Spotify directly.
Do not let providers access Memory.
Do not let the character perform search.
Do not add Spotify user-library OAuth in this MVP.
