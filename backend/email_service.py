import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

# SMTP Configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "") if os.getenv("SMTP_PASSWORD") else None
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
SMTP_TO_EMAIL = os.getenv("SMTP_TO_EMAIL")


async def send_contact_email(name: str, email: str, message: str, subject: str = None) -> bool:
    """
    Send a contact form submission via email using async SMTP.
    
    Args:
        name: Name of the person submitting the form
        email: Email address of the person submitting the form
        message: The message content
        subject: Optional subject line
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not all([SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_TO_EMAIL]):
        logger.error("SMTP configuration is incomplete. Check environment variables.")
        logger.error(f"SMTP_USERNAME: {SMTP_USERNAME is not None}")
        logger.error(f"SMTP_PASSWORD: {SMTP_PASSWORD is not None}")
        logger.error(f"SMTP_FROM_EMAIL: {SMTP_FROM_EMAIL is not None}")
        logger.error(f"SMTP_TO_EMAIL: {SMTP_TO_EMAIL is not None}")
        return False
    
    logger.info(f"Attempting to send email from {email} via {SMTP_HOST}:{SMTP_PORT}")
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject or f"Portfolio Contact: {name}"
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = SMTP_TO_EMAIL
        msg['Reply-To'] = email
        
        # Create email body
        text_content = f"""
New Contact Form Submission

Name: {name}
Email: {email}
Subject: {subject or 'N/A'}

Message:
{message}

---
This message was sent from your portfolio contact form.
Reply to this email to respond directly to {email}.
        """
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #0a192f; color: #64ffda; padding: 20px; border-radius: 5px; }}
        .content {{ background: #f4f4f4; padding: 20px; margin-top: 20px; border-radius: 5px; }}
        .label {{ font-weight: bold; color: #0a192f; }}
        .message {{ background: white; padding: 15px; margin-top: 10px; border-left: 4px solid #64ffda; }}
        .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #777; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>New Contact Form Submission</h2>
        </div>
        <div class="content">
            <p><span class="label">Name:</span> {name}</p>
            <p><span class="label">Email:</span> <a href="mailto:{email}">{email}</a></p>
            <p><span class="label">Subject:</span> {subject or 'N/A'}</p>
            <div class="message">
                <p><span class="label">Message:</span></p>
                <p>{message.replace(chr(10), '<br>')}</p>
            </div>
        </div>
        <div class="footer">
            <p>This message was sent from your portfolio contact form.</p>
            <p>Reply to this email to respond directly to {email}.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        logger.info(f"Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT}...")
        
        # Send email with timeout
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            start_tls=True,
            timeout=30,  # 30 second timeout
        )
        
        logger.info(f"Contact email sent successfully from {email} to {SMTP_TO_EMAIL}")
        return True
        
    except aiosmtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {str(e)}")
        logger.error("Check your Gmail App Password is correct")
        return False
    except aiosmtplib.SMTPException as e:
        logger.error(f"SMTP error sending email: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send contact email: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def send_test_email() -> bool:
    """Send a test email to verify SMTP configuration."""
    return await send_contact_email(
        name="Test User",
        email="test@example.com",
        message="This is a test email from your portfolio contact form.",
        subject="Test Email - Portfolio Contact Form"
    )
