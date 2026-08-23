describe(
    "Cybersecurity to Governance navigation",
    () => {

        it(
            "creates governance center route",
            () => {

                const route =
                    "/operations-center/governance";

                expect(route)
                    .toContain(
                        "governance"
                    );
            }
        );
    }
);
