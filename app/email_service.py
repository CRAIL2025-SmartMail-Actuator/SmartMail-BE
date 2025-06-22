import imaplib
import email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import os
import logging
import time
import threading
from datetime import datetime
from app import db
from app.models import Email
from app.categorizer import EmailCategorizer

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.host = os.getenv("EMAIL_HOST")
        port_str = os.getenv("EMAIL_PORT", "")
        self.port = int(port_str) if port_str.strip() else 993
        self.username = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.use_ssl = os.getenv("EMAIL_USE_SSL", "true").lower() == "true"

        # Log configuration (without sensitive data)
        logger.info(
            f"Initializing EmailService with host={self.host}, port={self.port}, use_ssl={self.use_ssl}"
        )

        self.categorizer = EmailCategorizer()
        self.monitoring = False
        self.monitor_thread = None

    def connect_imap(self):
        """Connect to IMAP server"""
        try:
            if self.use_ssl:
                mail = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                mail = imaplib.IMAP4(self.host, self.port)

            mail.login(self.username, self.password)
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {str(e)}")
            raise

    def decode_header_value(self, value):
        """Decode email header value"""
        if value is None:
            return ""

        decoded_parts = decode_header(value)
        decoded_value = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_value += part.decode(encoding)
                else:
                    decoded_value += part.decode("utf-8", errors="ignore")
            else:
                decoded_value += part

        return decoded_value

    def extract_email_content(self, email_message):
        """Extract text content from email message"""
        body = ""

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if (
                    content_type == "text/plain"
                    and "attachment" not in content_disposition
                ):
                    try:
                        body += part.get_payload(decode=True).decode(
                            "utf-8", errors="ignore"
                        )
                    except:
                        pass
        else:
            try:
                body = email_message.get_payload(decode=True).decode(
                    "utf-8", errors="ignore"
                )
            except:
                pass

        return body.strip()

    def send_reply(self, to_email, subject, category):
        """Send automated reply with category"""
        try:
            # Create reply message
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = to_email
            msg["Subject"] = f"Re: {subject} - Categorized as {category}"

            # Email body
            body_text = f"""
            Hello,
            
            Thank you for your email. It has been automatically categorized as: {category}
            
            Your message has been received and will be processed accordingly:
            
            • Customer Support: Your inquiry will be forwarded to our support team
            • Marketing: Thank you for your interest in our services
            • Others: Your message has been noted and will be reviewed
            
            This is an automated response. If you need immediate assistance, please contact our support team directly.
            
            Best regards,
            Email Categorization System
            """

            msg.attach(MIMEText(body_text, "plain"))

            # Send email using SMTP
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Reply sent to {to_email} with category {category}")

        except Exception as e:
            logger.error(f"Failed to send reply to {to_email}: {str(e)}")

    def process_email(self, email_message, message_id):
        """Process a single email message"""
        from main import app

        try:
            # Extract email details
            with app.app_context():
                sender = self.decode_header_value(email_message.get("From", ""))
                subject = self.decode_header_value(email_message.get("Subject", ""))
                body = self.extract_email_content(email_message)

                # Categorize email (outside app context as it doesn't need db)
                category = self.categorizer.categorize_email(subject, body, sender)

                # Perform all database operations within app context
                # with app.app_context():
                # Check if email already exists
                existing_email = Email.query.filter_by(message_id=message_id).first()
                if existing_email:
                    logger.info(f"Email {message_id} already processed")
                    return

                # Save to database
                new_email = Email(
                    sender=sender,
                    subject=subject,
                    body=body,
                    category=category,
                    message_id=message_id,
                    processed_at=datetime.utcnow(),
                )

                db.session.add(new_email)
                db.session.commit()

                # Send automated reply
                sender_email = sender.split("<")[-1].strip(">")

                # TODO: Un comment when required to send emails
                # self.send_reply(sender_email, subject, category)

                logger.info(f"Processed email from {sender} - Category: {category}")

        except Exception as e:
            logger.error(f"Error processing email {message_id}: {str(e)}")
            db.session.rollback()

    def fetch_all_emails(self):
        """Fetch the latest 100 emails from inbox"""
        from main import app

        try:
            # IMAP operations outside app context
            with app.app_context():
                mail = self.connect_imap()
                mail.select("INBOX")

                # Search for all emails
                status, messages = mail.search(None, "ALL")
                if status != "OK" or not messages or not messages[0]:
                    logger.warning("No emails found in the inbox.")
                    mail.close()
                    mail.logout()
                    return

                message_ids = messages[0].split()

                # Get the latest 100 message IDs
                latest_message_ids = message_ids[-1:]
                logger.info(f"Found {len(latest_message_ids)} emails to process")

                for msg_id in latest_message_ids:
                    try:
                        # Fetch email
                        status, msg_data = mail.fetch(msg_id, "(RFC822)")
                        email_message = email.message_from_bytes(msg_data[0][1])

                        # Get unique message ID
                        message_id = email_message.get(
                            "Message-ID", f"msg_{msg_id.decode()}"
                        )

                        self.process_email(email_message, message_id)

                    except Exception as e:
                        logger.error(f"Error processing message 2 {msg_id}: {str(e)}")
                        continue

                mail.close()
                mail.logout()

                logger.info("Finished processing the latest 1 email")

        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")

    def monitor_new_emails(self):
        """Monitor inbox for new emails"""
        from main import app

        logger.info("Starting email monitoring...")

        while self.monitoring:
            try:
                # IMAP operations outside app context
                with app.app_context():
                    mail = self.connect_imap()
                    mail.select("INBOX")

                    # Search for unseen emails (IMAP operation)
                    status, messages = mail.search(None, "UNSEEN")
                    message_ids = messages[0].split()[-1:]

                    if message_ids:
                        logger.info(f"Found {len(message_ids)} new emails")

                        for msg_id in message_ids:
                            try:
                                # Fetch email
                                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                                email_message = email.message_from_bytes(msg_data[0][1])

                                # Get unique message ID
                                message_id = email_message.get(
                                    "Message-ID", f"msg_{msg_id.decode()}"
                                )

                                self.process_email(email_message, message_id)

                            except Exception as e:
                                logger.error(
                                    f"Error processing new message 1 {msg_id}: {str(e)}"
                                )
                                continue

                    mail.close()
                    mail.logout()

                # Wait before next check
                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in email monitoring: {str(e)}")
                time.sleep(60)  # Wait longer on error

    def start_monitoring(self):
        """Start monitoring emails in a separate thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_new_emails)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info("Email monitoring started")

    def stop_monitoring(self):
        """Stop monitoring emails"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            logger.info("Email monitoring stopped")
