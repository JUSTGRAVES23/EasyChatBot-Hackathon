"""
World Repository Interface.

Defines the contract required by UAI
to retrieve learning worlds.

The domain/application layers must not
depend on:

- databases
- YAML files
- APIs
- external systems

Only this contract.
"""

from __future__ import annotations

from typing import Protocol


class WorldRepository(Protocol):
    """
    Repository contract for World retrieval.
    """

    def get_by_id(
        self,
        world_id: str,
    ):
        """
        Retrieve a world configuration.

        Parameters
        ----------
        world_id:
            Unique world identifier.

        Returns
        -------
        World configuration or None.
        """
        ...