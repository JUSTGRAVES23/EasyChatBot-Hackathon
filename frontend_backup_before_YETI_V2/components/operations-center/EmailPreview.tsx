export default function EmailPreview(
    {email}: {email:any}
) {

    return (
        <section>
            <h2>
                Email Preview
            </h2>

            <p>
                Subject:
                {email.subject}
            </p>

            <p>
                Status:
                {email.status}
            </p>
        </section>
    );
}
