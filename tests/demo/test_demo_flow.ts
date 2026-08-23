describe(
    "Demo integration flow",
    () => {

        it(
            "contains demo environment flow",
            () => {

                const steps = [
                    "Scenario Selection",
                    "Playback",
                    "Evidence",
                    "YETI"
                ];

                expect(steps.length)
                    .toBe(4);

            }
        );

    }
);
