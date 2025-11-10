import logging
from threading import Thread
from flask import render_template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class EmailService:
    """Full-featured SendGrid email service, fully async and app-context safe."""

    _app = None  # Will hold Flask app instance

    @classmethod
    def init_app(cls, app):
        """Initialize the EmailService with your Flask app."""
        cls._app = app

    @classmethod
    def send_verification_email(cls, email, verification_code):
        subject = "Verify Your Email Address"
        try:
            html = render_template(
                'email_templates/verification_email.html',
                verification_code=verification_code
            )
        except Exception:
            logging.error(f"Failed to render verification template for {email}", exc_info=True)
            html = f"Your verification code is: {verification_code}"

        cls.send_async_email(subject, email, html)

    @classmethod
    def send_password_reset_email(cls, email, reset_token):
        subject = "Password Reset Request"
        try:
            frontend_url = cls._app.config.get('FRONTEND_URL', 'http://localhost:3000')
            reset_link = f"{frontend_url}/reset-password?token={reset_token}"

            html = render_template(
                'email_templates/password_reset_email.html',
                reset_link=reset_link
            )
        except Exception:
            logging.error(f"Failed to render password reset template for {email}", exc_info=True)
            html = f"Reset your password using this link: {reset_link}"

        cls.send_async_email(subject, email, html)

    @classmethod
    def send_async_email(cls, subject, to_email, html_body, text_body=None):
        """Send email using SendGrid in a background thread."""

        if cls._app is None:
            raise RuntimeError("EmailService not initialized. Call EmailService.init_app(app) first.")

        def send_email_thread(subject, to_email, html_body, text_body):
            """Actual thread that sends the email with app context."""
            with cls._app.app_context():
                try:
                    message = Mail(
                        from_email=cls._app.config['MAIL_DEFAULT_SENDER'],
                        to_emails=to_email,
                        subject=str(subject),
                        html_content=html_body,
                        plain_text_content=text_body or ""
                    )
                    sg = SendGridAPIClient(cls._app.config['SENDGRID_API_KEY'])
                    response = sg.send(message)
                    logging.info(f"Email sent to {to_email}, status: {response.status_code}")
                except Exception as e:
                    logging.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)

        Thread(
            target=send_email_thread,
            args=(subject, to_email, html_body, text_body),
            daemon=True  # optional: allows Python to exit without waiting for thread
        ).start()

    # Additional email types
    @classmethod
    def send_interview_invitation(cls, email, candidate_name, interview_date, interview_type, meeting_link=None):
        subject = "Interview Invitation"
        try:
            html = render_template(
                'email_templates/interview_invitation.html',
                candidate_name=candidate_name,
                interview_date=interview_date,
                interview_type=interview_type,
                meeting_link=meeting_link
            )
        except Exception:
            logging.error(f"Failed to render invitation template for {email}", exc_info=True)
            html = f"Hi {candidate_name}, your {interview_type} interview is scheduled on {interview_date}. Link: {meeting_link}"

        cls.send_async_email(subject, email, html)

    @classmethod
    def send_application_status_update(cls, email, candidate_name, status, position_title):
        subject = f"Application Update for {position_title or 'your position'}"
        try:
            html = render_template(
                'email_templates/application_status_update.html',
                candidate_name=candidate_name,
                status=status,
                position_title=position_title
            )
        except Exception:
            logging.error(f"Failed to render application update template for {email}", exc_info=True)
            html = f"Hi {candidate_name}, your application for {position_title} status is: {status}"

        cls.send_async_email(subject, email, html)

    @classmethod
    def send_temporary_password(cls, email, password, first_name=None):
        subject = "Your Temporary Password"
        try:
            html = render_template(
                'email_templates/temporary_password.html',
                password=password,
                first_name=first_name,
                current_year=2025
            )
            text_body = f"Hello {first_name or ''},\n\nYour temporary password is: {password}"
        except Exception:
            logging.error(f"Failed to render temporary password template for {email}", exc_info=True)
            html = text_body = f"Your temporary password is: {password}"

        cls.send_async_email(subject, email, html, text_body=text_body)

    @classmethod
    def send_interview_cancellation(cls, email, candidate_name, interview_date, interview_type, reason=None):
        subject = "Interview Cancellation Notice"
        reason_text = reason or "No specific reason provided."
        try:
            html = render_template(
                'email_templates/interview_cancellation.html',
                candidate_name=candidate_name,
                interview_date=interview_date,
                interview_type=interview_type,
                reason=reason_text
            )
            text_body = f"Hi {candidate_name},\n\nYour {interview_type} interview scheduled on {interview_date} has been cancelled.\nReason: {reason_text}"
        except Exception:
            logging.error(f"Failed to render cancellation template for {email}", exc_info=True)
            html = text_body = f"Hi {candidate_name}, your {interview_type} interview scheduled on {interview_date} has been cancelled.\nReason: {reason_text}"

        cls.send_async_email(subject, email, html, text_body=text_body)

    @classmethod
    def send_interview_reschedule_email(cls, email, candidate_name, old_time, new_time, interview_type, meeting_link=None):
        subject = "Interview Rescheduled"
        try:
            html = render_template(
                'email_templates/interview_reschedule.html',
                candidate_name=candidate_name,
                old_time=old_time,
                new_time=new_time,
                interview_type=interview_type,
                meeting_link=meeting_link
            )
        except Exception:
            logging.error(f"Failed to render reschedule template for {email}", exc_info=True)
            html = f"Hi {candidate_name}, your {interview_type} interview has been rescheduled from {old_time} to {new_time}. Link: {meeting_link}"

        cls.send_async_email(subject, email, html)
