import os
import smtplib
import random
import logging
import uuid
from email.mime.text import MIMEText
from flask import session, jsonify
from datetime import datetime, timedelta
from urllib.parse import urlparse


log = logging.getLogger(__name__)


class OTPManager:
    @staticmethod
    def generate_and_send_otp(email):
        """
        Generate a 4-digit OTP, store it in the session, and send it via email.
        """
        try:
            # Generate OTP
            otp = random.randint(1000, 9999)
            session['otp'] = otp
            session['otp_expiry'] = (
                datetime.now() + timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
            session['email'] = email

            # Load SMTP configuration
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 465))
            smtp_email = os.getenv('SMTP_EMAIL')
            smtp_password = os.getenv('SMTP_PASSWORD')

            if not all([smtp_server, smtp_port, smtp_email, smtp_password]):
                log.error(
                    "SMTP configuration is incomplete. Please check the environment variables.")
                return False

            log.debug(f"Preparing to send OTP to {email}. OTP: {otp}")

            # Prepare and send email
            msg = MIMEText(f"Your OTP is: {otp}\nThis OTP is valid for 5 minutes.")  # noqa
            msg['Subject'] = 'OTP Verification'
            msg['From'] = smtp_email
            msg['To'] = email

            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(smtp_email, smtp_password)
                server.sendmail(smtp_email, email, msg.as_string())

            log.info(f"OTP sent successfully to {email}.")
            return {"status": True, "message": "Otp Sent Successfully"}

        except smtplib.SMTPException as smtp_error:
            log.error(f"SMTP error while sending OTP to {email}: {smtp_error}")
            return {"status": False, "message": "SMTP error 550: Mailbox unavailable."}

        except Exception as e:
            log.error(f"Unexpected error while sending OTP to {email}: {e}")
            return False

    @staticmethod
    def verify_otp(entered_otp):
        """
        Verify the OTP entered by the user against the session-stored OTP.
        """
        try:
            stored_otp = session.get('otp')
            expiry_time = session.get('otp_expiry')

            if not stored_otp or not expiry_time:
                log.warning("OTP or expiry time is missing in the session.")
                return {"status": False, "message": "OTP not found. Please request a new OTP."}

            expiry_datetime = datetime.strptime(
                expiry_time, '%Y-%m-%d %H:%M:%S')
            if datetime.now() > expiry_datetime:
                log.warning("OTP expired.")
                session.pop('otp', None)
                session.pop('otp_expiry', None)
                return {"status": False, "message": "OTP expired. Please request a new OTP."}

            if str(stored_otp) == str(entered_otp):
                session.pop('otp', None)
                session.pop('otp_expiry', None)
                session['otp_verified'] = True
                log.info("OTP verified successfully. hai")
                return {"status": True, "message": "OTP verified successfully."}

            log.warning("Incorrect OTP entered.")
            return {"status": False, "message": "Invalid OTP. Please try again."}

        except Exception as e:
            log.error(f"Error during OTP verification: {e}")
            return {"status": False, "message": "An unexpected error occurred during verification."}

    @staticmethod
    def send_claim_request_email(recipient_email, company_name):
        try:
            # Load SMTP configuration
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 465))
            smtp_email = os.getenv('SMTP_EMAIL')
            smtp_password = os.getenv('SMTP_PASSWORD')

            if not all([smtp_server, smtp_port, smtp_email, smtp_password]):
                log.error(
                    "SMTP configuration is incomplete. Please check the environment variables.")
                return {"status": False, "message": "Email configuration error."}

            log.debug(
                f"Preparing to send claim request email to {recipient_email}.")

            # Email content
            subject = "Claim Request Notification"
            body = (
                f"Dear User,\n\n"
                f"Your request to claim the company profile for '{company_name}' has been received. \n\n"
                f"Best Regards,\nThe REGX Team"
            )

            # Create email message
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = smtp_email
            msg['To'] = recipient_email

            # Send email
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(smtp_email, smtp_password)
                server.sendmail(smtp_email, recipient_email, msg.as_string())

            log.info(
                f"Claim request email sent successfully to {recipient_email}.")
            return {"status": True, "message": "Claim request email sent successfully."}

        except smtplib.SMTPException as smtp_error:
            log.error(
                f"SMTP error while sending claim request email to {recipient_email}: {smtp_error}")
            return {"status": False, "message": "Failed to send email. SMTP error."}

        except Exception as e:
            log.error(
                f"Unexpected error while sending claim request email to {recipient_email}: {e}")
            return {"status": False, "message": "An unexpected error occurred while sending email."}

    @staticmethod
    def profile_approve_email(recipient_email, company_name):
        try:
            # Load SMTP configuration
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 465))
            smtp_email = os.getenv('SMTP_EMAIL')
            smtp_password = os.getenv('SMTP_PASSWORD')

            if not all([smtp_server, smtp_port, smtp_email, smtp_password]):
                log.error(
                    "SMTP configuration is incomplete. Please check the environment variables.")
                return {"status": False, "message": "Email configuration error."}

            log.debug(
                f"Preparing to send claim request email to {recipient_email}.")

            # Email content
            subject = "Claim Request Notification"
            body = (
                f"Dear User,\n\n"
                f"Congratualations your company profile '{company_name}' has been approved and live in our system. "
                f"Thanks for your patience\n\n"
                f"Best Regards,\nThe REGX Team"
            )

            # Create email message
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = smtp_email
            msg['To'] = recipient_email

            # Send email
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(smtp_email, smtp_password)
                server.sendmail(smtp_email, recipient_email, msg.as_string())

            log.info(
                f"Claim request email sent successfully to {recipient_email}.")
            return {"status": True, "message": "Claim request email sent successfully."}

        except smtplib.SMTPException as smtp_error:
            log.error(
                f"SMTP error while sending claim request email to {recipient_email}: {smtp_error}")
            return {"status": False, "message": "Failed to send email. SMTP error."}

        except Exception as e:
            log.error(
                f"Unexpected error while sending claim request email to {recipient_email}: {e}")
            return {"status": False, "message": "An unexpected error occurred while sending email."}

    @staticmethod
    def parsewebsite(url):
        # Parse the URL to break it down into components
        parsed = urlparse(url)

        domain = parsed.netloc   # Extract the domain name with possible subdomains

        # Remove 'www.' if it exists
        if domain.startswith('www.'):
            domain = domain[4:]

        # Also strip any port numbers
        domain = domain.split(':')[0]

        # Normalize to lower case to ensure consistency
        domain = domain.lower()

        # Strip trailing slash if it exists
        domain = domain.rstrip('/')
        return domain

    @staticmethod
    def generate_uuid():
        new_uuid = str(uuid.uuid4())
        return new_uuid
