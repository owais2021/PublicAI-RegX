import os
import smtplib
import random
import logging
from email.mime.text import MIMEText
from flask import session
from datetime import datetime, timedelta

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
                datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
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
            return True

        except smtplib.SMTPException as smtp_error:
            log.error(f"SMTP error while sending OTP to {email}: {smtp_error}")
            return False

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
                log.info("OTP verified successfully. hai")
                return {"status": True, "message": "OTP verified successfully."}

            log.warning("Incorrect OTP entered.")
            return {"status": False, "message": "Invalid OTP. Please try again."}

        except Exception as e:
            log.error(f"Error during OTP verification: {e}")
            return {"status": False, "message": "An unexpected error occurred during verification."}
