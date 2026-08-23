export default function YetiConversationCard(
    {message}: {message:string}
) {

    return (
        <section>
            <h2>
                🧊 YETI Governance Assistant
            </h2>

            <p>
                {message}
            </p>
        </section>
    );
}
