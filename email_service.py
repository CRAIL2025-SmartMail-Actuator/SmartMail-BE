from email.utils import formatdate, make_msgid, parseaddr
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
from models import Category, Email, SentEmail
from categorizer import EmailCategorizer
from db_sync import SyncSessionLocal
import models
from routers.ai_service import ai_reponse  # Importing synchronous session

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
        self.auto_reply_enabled = mailbox_config.auto_reply_enabled
        self.confidence_threshold = mailbox_config.confidence_threshold
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

    def send_reply_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        in_reply_to: str = None,
        references: str = None,
    ):
        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = to_email
            msg["Subject"] = subject
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid()

            if in_reply_to:
                msg["In-Reply-To"] = in_reply_to
            if references:
                msg["References"] = references

            msg.attach(MIMEText(body_text, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Reply sent to {to_email} successfully")
            return msg["Message-ID"]
        except Exception as e:
            logger.error(f"Failed to send reply email: {str(e)}")
            raise

    def process_email(self, email_message, message_id, mailbox_type):
        try:
            with SyncSessionLocal() as session:
                sender = self.decode_header_value(email_message.get("From", ""))
                recipients = self.decode_header_value(email_message.get("To", ""))
                subject = self.decode_header_value(email_message.get("Subject", ""))
                body = self.extract_email_content(email_message)
                html_body = body
                raw_from = email_message.get("From")
                from_name, from_email = parseaddr(raw_from)

                # Check if already processed (both tables)
                if mailbox_type == "INBOX":
                    existing_email = (
                        session.query(Email).filter_by(thread_id=message_id).first()
                    )
                else:
                    existing_email = (
                        session.query(SentEmail)
                        .filter_by(message_id=message_id)
                        .first()
                    )

                if existing_email:
                    logger.info(f"Email {message_id} already processed")
                    return

                if mailbox_type == "INBOX":
                    new_email = Email(
                        user_id=self.user_id,
                        from_email=sender if sender else from_email,
                        from_name=from_name if from_name else None,
                        to_email=self.username,
                        subject=subject,
                        body=body,
                        html_body=html_body,
                        timestamp=datetime.utcnow(),
                        is_read=False,
                        is_starred=False,
                        has_attachments=False,
                        priority="normal",
                        labels=[],
                        thread_id=message_id,
                        ai_analysis=None,
                        category_id=None,
                    )
                    session.add(new_email)
                    # Categorize email
                    try:
                        categories = (
                            session.query(Category)
                            .filter_by(user_id=self.user_id)
                            .all()
                        )
                        category = self.categorizer.categorize_email(
                            subject, body, sender, self.user_id, categories
                        )
                        new_email.category_id = category if category else None
                        session.commit()
                        logger.info(
                            f"Processed email from {sender} with subject '{subject}'"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to categorize email {message_id}: {str(e)}"
                        )
                        new_email.category_id = None
                    if self.auto_reply_enabled:
                        try:
                            ai_res = ai_reponse(
                                self.user_id,
                                "",
                                self.username,
                                new_email.subject,
                                new_email.body,
                            )
                            if (
                                ai_res
                                and "subject" in ai_res
                                and "email_body" in ai_res
                                and "confidence_score" in ai_res
                            ):
                                subject = ai_res["subject"]
                                confidence_score = ai_res["confidence_score"]
                                body = ai_res["email_body"]
                                print(f"AI Response: {ai_res}")
                                print(f"Confidence Score: {confidence_score}")
                                print(f"Email Subject: {new_email.subject}")
                                print(f"Email Body: {new_email.body}")
                                print(
                                    self.auto_reply_enabled,
                                    self.confidence_threshold,
                                    "config",
                                )
                                if confidence_score >= self.confidence_threshold:
                                    new_message_id = self.send_reply_email(
                                        to_email=new_email.from_email,
                                        subject=subject,
                                        body_text=body,
                                        in_reply_to=message_id,
                                        references=message_id,
                                    )
                                    new_sent_email = models.SentEmail(
                                        message_id=new_message_id,
                                        original_email_id=new_email.id,
                                        sent_at=datetime.utcnow(),
                                        status="sent",
                                        recipients=[new_email.from_email],
                                        delivery_status="success",
                                        content=body,
                                        html_content=body,
                                        user_id=self.user_id,
                                    )
                                    session.add(new_sent_email)
                                    session.commit()
                                    session.refresh(new_sent_email)
                        except Exception as e:
                            logger.error(f"Failed to send auto-reply: {str(e)}")
                elif mailbox_type == "[Gmail]/Sent Mail" or mailbox_type == "SENT":
                    sent_email = SentEmail(
                        message_id=message_id,
                        original_email_id=None,  # Can be linked later via logic if needed
                        sent_at=datetime.utcnow(),
                        status="sent",
                        recipients=[r.strip() for r in recipients.split(",")]
                        if recipients
                        else [],
                        delivery_status="success",
                        content=body,
                        html_content=html_body,
                        user_id=self.user_id,
                    )
                    session.add(sent_email)

                session.commit()
                logger.info(f"Processed {mailbox_type} email with subject '{subject}'")

        except Exception as e:
            logger.error(f"Error processing email {message_id}: {str(e)}")

    def fetch_emails(self, mailbox_type="INBOX", search_type="ALL"):
        try:
            mail = self.connect_imap()
            mail.select(f'"{mailbox_type}"')
            status, messages = mail.search(None, search_type)
            if status != "OK":
                logger.warning(f"No emails found in {mailbox_type}.")
                return

            for msg_id in messages[0].split()[-1:]:
                _, msg_data = mail.fetch(msg_id, "(RFC822)")
                email_message = email.message_from_bytes(msg_data[0][1])
                message_id = email_message.get("Message-ID", f"msg_{msg_id.decode()}")
                self.process_email(email_message, message_id, mailbox_type)

            mail.close()
            mail.logout()
        except Exception as e:
            logger.error(f"Error fetching emails from {mailbox_type}: {str(e)}")

    def monitor_loop(self):
        while self.monitoring:
            try:
                self.fetch_emails("INBOX", "ALL")
                self.fetch_emails(
                    "[Gmail]/Sent Mail", "ALL"
                )  # Or use "SENT" depending on provider
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
