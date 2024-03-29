from typing import Optional
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings

from gamedoodle.core.models import SentMail


def _replace_url_to_link(value):
    urls = re.compile(
        r"((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)",
        re.MULTILINE | re.UNICODE,
    )
    return urls.sub(r'<a href="\1" target="_blank">\1</a>', value)


def send_email_via_gmail(
    *,
    recipient: str,
    subject: str,
    body: str,
    html: Optional[str] = None,
    auto_break: bool = True,
    auto_links: bool = True,
    save_to_db: Optional[bool] = True,
):
    """Send email using the Google Mail SMTP server.

    Credentials are taken from the Django settings.

    Args:

        recipient (str|list[str]): One or more email addresses to send to.

        subject (str): Subject for the email to use.

        body (str): Message body of the email.

        html (str): Optional html string instead of creating one from body.

        auto_break (bool): If no html is provided, break newlines as <br>
            in body when creating html.

        auto_links (bool): If no html is provided, convert URLs to <a>
            elements when creating html.

        save_to_db (bool): Store emails to database for debugging.

    The email will contain a plain/text and an html version.

    """
    gmail_smtp_server = settings.EMAIL_NOTIFICATIONS["GMAIL_SMTP_SERVER"]
    gmail_smtp_port = settings.EMAIL_NOTIFICATIONS["GMAIL_SMTP_PORT"]
    gmail_user = settings.EMAIL_NOTIFICATIONS["GMAIL_USER"]
    gmail_pwd = settings.EMAIL_NOTIFICATIONS["GMAIL_PWD"]  # App-password.

    from_email = gmail_user
    to_emails = recipient if type(recipient) is list else [recipient]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = ", ".join(to_emails)

    if html is None:
        html_body = body
        if auto_links:
            html_body = _replace_url_to_link(html_body)
        if auto_break:
            html_body = html_body.replace("\n", "<br/>")
        html = f"""
        <html>
        <body style="font-family: sans-serif; margin: 20px">
            <h1>{subject}</h1>
            {html_body}
        </body>
        </html>
        """

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in
    # this case the HTML message, is best and preferred.
    part1 = MIMEText(body, "plain")
    part2 = MIMEText(html, "html")
    msg.attach(part1)
    msg.attach(part2)

    server = smtplib.SMTP(gmail_smtp_server, gmail_smtp_port)
    try:
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(from_email, to_emails, msg.as_string())

        if save_to_db:
            SentMail.objects.create(
                sender=msg["From"],
                recipient=msg["To"],
                subject=msg["Subject"],
                body=body,
                html=html,
            )
    finally:
        server.quit()
