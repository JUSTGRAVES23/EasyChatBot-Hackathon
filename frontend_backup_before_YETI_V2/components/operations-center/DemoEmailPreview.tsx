export default function DemoEmailPreview(
    {email}: {email:any}
) {

    return (
        <section>
            <h2>Email Preview</h2>

            <p>
                {email.subject}
            </p>

            <p>
                Status:
                {email.status}
            </p>
        </section>
    );
}
