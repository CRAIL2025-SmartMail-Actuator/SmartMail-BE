import imaplib
import email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import logging
import time
import threading
from datetime import datetime
from models import Email
from categorizer import EmailCategorizer
from db_sync import SyncSessionLocal  # Importing synchronous session

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, mailbox_config):
        self.host = "imap.gmail.com"
        self.port = 993
        self.username = mailbox_config.email
        self.password = mailbox_config.app_password
        self.use_ssl = True
        self.user_id = mailbox_config.user_id
        self.mailbox_config_id = mailbox_config.id

        self.categorizer = EmailCategorizer()
        self.monitoring = False
        self.monitor_thread = None

    def connect_imap(self):
        try:
            mail = imaplib.IMAP4_SSL(self.host, self.port)
            mail.login(self.username, self.password)
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {str(e)}")
            raise

    def decode_header_value(self, value):
        if value is None:
            return ""
        decoded_parts = decode_header(value)
        return "".join(
            part.decode(encoding or "utf-8") if isinstance(part, bytes) else part
            for part, encoding in decoded_parts
        )

    def extract_email_content(self, email_message):
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain" and "attachment" not in str(
                    part.get("Content-Disposition")
                ):
                    try:
                        body += part.get_payload(decode=True).decode(
                            "utf-8", errors="ignore"
                        )
                    except Exception as e:
                        pass
        else:
            try:
                body = email_message.get_payload(decode=True).decode(
                    "utf-8", errors="ignore"
                )
            except Exception as e:
                pass
        return body.strip()

    def send_email(self, to_email: str, subject: str, body_text: str):
        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body_text, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email} successfully")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")

    def process_email(self, email_message, message_id):
        try:
            with SyncSessionLocal() as session:
                sender = self.decode_header_value(email_message.get("From", ""))
                subject = self.decode_header_value(email_message.get("Subject", ""))
                body = self.extract_email_content(email_message)

                existing_email = (
                    session.query(Email).filter_by(thread_id=message_id).first()
                )
                if existing_email:
                    logger.info(f"Email {message_id} already processed")
                    return

                new_email = Email(
                    user_id=self.user_id,
                    from_email=sender,
                    from_name=None,  # Optional: Extract if needed from `sender`
                    to_email=self.username,
                    subject=subject,
                    body=body,
                    html_body=None,  # Optional: Extract from HTML parts if needed
                    timestamp=datetime.utcnow(),
                    is_read=False,
                    is_starred=False,
                    has_attachments=False,  # You can set based on email content inspection
                    priority="normal",
                    labels=[],  # You can customize this if labeling is added later
                    thread_id=message_id,
                    ai_analysis=None,
                    category_id=None,  # Will be set after categorization
                )
                session.add(new_email)
                session.commit()
                logger.info(f"Processed email from {sender} with subject '{subject}'")

        except Exception as e:
            logger.error(f"Error processing email {message_id}: {str(e)}")

    def fetch_unseen_emails(self):
        try:
            mail = self.connect_imap()
            mail.select("INBOX")
            status, messages = mail.search(None, "ALL")
            if status != "OK":
                logger.warning("No new emails found.")
                return

            for msg_id in messages[0].split()[-1:]:
                _, msg_data = mail.fetch(msg_id, "(RFC822)")
                email_message = email.message_from_bytes(msg_data[0][1])
                message_id = email_message.get("Message-ID", f"msg_{msg_id.decode()}")
                self.process_email(email_message, message_id)

            mail.close()
            mail.logout()
        except Exception as e:
            logger.error(f"Error fetching unseen emails: {str(e)}")

    def monitor_loop(self):
        while self.monitoring:
            try:
                self.fetch_unseen_emails()
                time.sleep(30)
            except Exception as e:
                logger.error(f"Monitoring error: {str(e)}")
                time.sleep(60)

    def start_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info(f"Started monitoring for {self.username}")

    def stop_monitoring(self):
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info(f"Stopped monitoring for {self.username}")
