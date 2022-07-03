import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings


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
    auto_break: bool = True,
    auto_links: bool = True,
):
    """Send email using the Google Mail SMTP server.

    Credentials are taken from the Django settings. The pass

    Args:
        recipient (str|list[str]): One or more email addresses to send to.
        subject (str): Subject for the email to use.
        body (str): Message body of the email.

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
    finally:
        server.quit()
