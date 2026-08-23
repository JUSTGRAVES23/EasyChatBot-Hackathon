export default function DemoEventConsole(
    {response}: {response:any}
) {
    return (
        <section>
            <h2>Demo Event Console</h2>
            <pre>
                {JSON.stringify(response, null, 2)}
            </pre>
        </section>
    );
}
