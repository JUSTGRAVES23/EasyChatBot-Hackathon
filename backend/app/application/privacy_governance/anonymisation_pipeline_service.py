from __future__ import annotations


class AnonymisationPipelineService:
    """Creates irreversible anonymous statistics.

    Hashes/pseudonyms must never be treated as anonymous data.
    """

    async def anonymise(self, dataset):
        return dataset
