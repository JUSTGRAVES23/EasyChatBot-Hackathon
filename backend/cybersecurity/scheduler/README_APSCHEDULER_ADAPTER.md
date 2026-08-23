# APScheduler Integration Boundary


Architecture:

FastAPI lifespan

        |

        v

CybersecuritySchedulerRuntime

        |

        v

CybersecurityAPSchedulerAdapter

        |

        +----------------+

        |                |

        v                v

Daily 08:00       Weekly Monday 08:00


        |

        v

Critical Immediate Event


        |

        v

Reporting + Email Workflow


Design:

- Runtime does not depend on APScheduler.
- Adapter hides infrastructure details.
- Celery can replace APScheduler later.
