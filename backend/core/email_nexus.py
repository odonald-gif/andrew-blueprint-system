import logging
import os
import imaplib
import smtplib
import email
from email.message import EmailMessage
import re
from typing import List, Dict, Any


logger = logging.getLogger(__name__)

class EmailNexus:
    """
    The Unified Inbox (Real SMTP/IMAP).
    Connects to an email provider to fetch unread messages and dispatch replies.
    Handles prioritization, filtering, and auto-drafting via Donna.
    """
    def __init__(self):
        self.email_user = os.getenv("EMAIL_USER")
        self.email_pass = os.getenv("EMAIL_APP_PASSWORD")
        self.imap_host = os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com")
        self.smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
        
        if not self.email_user or not self.email_pass:
            raise ValueError("MISSING EMAIL_USER or EMAIL_APP_PASSWORD - Email Nexus cannot boot.")

    def evaluate_priority(self, sender: str, subject: str, body: str) -> dict:
        """
        Scores the email from 1 to 10 based on keywords and sender identity.
        """
        score = 5 # default
        
        # Heuristic scoring
        if "unsubscribe" in body.lower() or "promo" in subject.lower():
            score = 1
        elif sender.endswith(".edu") or "assignment" in subject.lower():
            score = 8
        elif "upwork" in sender.lower() or "offer" in subject.lower() or "interview" in subject.lower():
            score = 10
            
        action = "ARCHIVE"
        if score > 7:
            action = "SUMMARIZE"
        if score > 8:
            action = "NOTIFY_AND_DRAFT"
            
        return {"score": score, "action": action}

    def fetch_unread_emails(self) -> List[Dict[str, Any]]:
        """
        Connects via IMAP to fetch unread emails.
        """
        logger.info("Connecting to IMAP to fetch unread emails...")
        emails_data = []
        try:
            mail = imaplib.IMAP4_SSL(self.imap_host)
            mail.login(self.email_user, self.email_pass)
            mail.select("inbox")

            status, messages = mail.search(None, '(UNSEEN)')
            if status == "OK" and messages[0]:
                for num in messages[0].split():
                    typ, data = mail.fetch(num, '(RFC822)')
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = str(msg.get("Subject", ""))
                            sender = str(msg.get("From", ""))
                            body = ""
                            
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    if content_type == "text/plain":
                                        body += part.get_payload(decode=True).decode()
                            else:
                                body = msg.get_payload(decode=True).decode()
                                
                            emails_data.append({
                                "id": num.decode(),
                                "sender": sender,
                                "subject": subject,
                                "body": body
                            })
            mail.close()
            mail.logout()
            return emails_data
        except Exception as e:
            logger.error(f"IMAP Error: {e}")
            raise RuntimeError(f"Failed to fetch emails via IMAP: {e}")

    def process_incoming_emails(self) -> List[Dict[str, Any]]:
        """
        Main pipeline for processing unread emails.
        """
        unread = self.fetch_unread_emails()
        results = []
        
        for email_data in unread:
            evaluation = self.evaluate_priority(email_data["sender"], email_data["subject"], email_data["body"])
            
            result = {
                "subject": email_data["subject"],
                "sender": email_data["sender"],
                "priority_score": evaluation["score"],
                "action_taken": evaluation["action"],
                "donna_draft": None
            }
            
            if evaluation["action"] == "NOTIFY_AND_DRAFT":
                # Pass to PersonaEngine for Shadow Mode drafting
                from core.persona import persona_engine
                donna_response = persona_engine.generate_twin_reply(email_data["sender"], "professional", email_data["body"])
                result["donna_draft"] = donna_response
                
            results.append(result)
            
        return results

    def send_email(self, to_address: str, subject: str, body: str):
        """
        Dispatches an email via SMTP.
        """
        logger.info(f"Dispatching email to {to_address}...")
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = to_address

            server = smtplib.SMTP_SSL(self.smtp_host, 465)
            server.login(self.email_user, self.email_pass)
            server.send_message(msg)
            server.quit()
            logger.info("Email dispatched successfully.")
        except Exception as e:
            logger.error(f"SMTP Error: {e}")
            raise RuntimeError(f"Failed to send email via SMTP: {e}")

    def extract_otp(self, email_body: str) -> str:
        """
        Searches an email payload for a 6-digit 2FA / OTP code using Regex.
        """
        logger.info("Scanning email for OTP...")
        # Looks for 6 consecutive digits that might be an OTP
        match = re.search(r'\b\d{6}\b', email_body)
        if match:
            return match.group(0)
        return ""

try:
    email_nexus = EmailNexus()
except ValueError as e:
    email_nexus = None
    logger.warning(f"Email Nexus disabled: {e}")
