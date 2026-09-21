import asyncio
import resend

from cybersecurity.email.email_configuration import RESEND_API_KEY


async def main():
    resend.api_key = RESEND_API_KEY

    email_id = "01a0c039-54c0-715f-8c7f-183ef37a8f49"

    print("EMAIL_ID =", email_id)

    try:
        result = await resend.Emails.get_async(email_id)

        print()
        print("RESEND_EMAIL_RESULT =")
        print(result)

    except Exception as exc:
        print()
        print("RESEND_EMAIL_EXCEPTION =", type(exc).__name__)
        print("RESEND_EMAIL_EXCEPTION_MESSAGE =", str(exc))


asyncio.run(main())
