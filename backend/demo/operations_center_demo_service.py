class OperationsCenterDemoService:
    """
    Aggregates demo data for Operations Center.

    Read-only presentation boundary.
    """


    def build_view(
        self,
        demo_data: dict,
    ):

        return {
            "timeline": {
                "event": demo_data["event"],
                "component": demo_data["component"],
                "severity": demo_data["severity"],
            },

            "evidence": {
                "available": True,
                "reason": demo_data["reason"],
            },

            "email_preview": demo_data["email"],

            "yeti": demo_data["yeti_message"],
        }
