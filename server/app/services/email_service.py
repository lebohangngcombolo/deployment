import logging
from threading import Thread
from flask import render_template, current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class EmailService:
    """Async SendGrid-based email service mirroring your Flask-Mail implementation."""

    @staticmethod
    def send_verification_email(email, verification_code):
        subject = "Verify Your Email Address"
        try:
            html = render_template(
                'email_templates/verification_email.html',
                verification_code=verification_code
            )
        except Exception:
            logging.error(f"Failed to render verification email template for {email}", exc_info=True)
            html = f"Your verification code is: {verification_code}"

        EmailService.send_async_email(subject, [email], html)

    @staticmethod
    def send_password_reset_email(email, reset_token):
        subject = "Password Reset Request"
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        try:
            html = render_template(
                'email_templates/password_reset_email.html',
                reset_link=reset_link
            )
        except Exception:
            logging.error(f"Failed to render password reset template for {email}", exc_info=True)
            html = f"Reset your password using this link: {reset_link}"

        EmailService.send_async_email(subject, [email], html)

    @staticmethod
    def send_interview_invitation(email, candidate_name, interview_date, interview_type, meeting_link=None):
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
            logging.error(f"Failed to render interview invitation template for {email}", exc_info=True)
            html = f"Hi {candidate_name}, your {interview_type} interview is scheduled on {interview_date}. Link: {meeting_link}"

        EmailService.send_async_email(subject, [email], html)

    @staticmethod
    def send_application_status_update(email, candidate_name, status, position_title):
        subject = f"Application Update for {position_title or 'your position'}"
        try:
            html = render_template(
                'email_templates/application_status_update.html',
                candidate_name=candidate_name,
                status=status,
                position_title=position_title
            )
        except Exception:
            logging.error(f"Failed to render application status update template for {email}", exc_info=True)
            html = f"Hi {candidate_name}, your application for {position_title} status is: {status}"

        EmailService.send_async_email(subject, [email], html)

    @staticmethod
    def send_temporary_password(email, password, first_name=None):
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

        EmailService.send_async_email(subject, [email], html, text_body=text_body)

    @staticmethod
    def send_interview_cancellation(email, candidate_name, interview_date, interview_type, reason=None):
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
            text_body = (
                f"Hi {candidate_name},\n\nYour {interview_type} interview scheduled on "
                f"{interview_date} has been cancelled.\nReason: {reason_text}\n\nPlease contact us for rescheduling."
            )
        except Exception:
            logging.error(f"Failed to render interview cancellation template for {email}", exc_info=True)
            html = text_body = f"Hi {candidate_name}, your {interview_type} interview scheduled on {interview_date} has been cancelled.\nReason: {reason_text}"

        EmailService.send_async_email(subject, [email], html, text_body=text_body)

    @staticmethod
    def send_interview_reschedule_email(email, candidate_name, old_time, new_time, interview_type, meeting_link=None):
        subject = "Interview Rescheduled"
        try:
            html = render_template(
                "email_templates/interview_reschedule.html",
                candidate_name=candidate_name,
                old_time=old_time,
                new_time=new_time,
                interview_type=interview_type,
                meeting_link=meeting_link
            )
        except Exception:
            logging.error(f"Failed to render reschedule email template for {email}", exc_info=True)
            html = f"Hi {candidate_name}, your {interview_type} interview has been rescheduled from {old_time} to {new_time}. Link: {meeting_link}"

        EmailService.send_async_email(subject, [email], html)

    # ---------------- SEND EMAIL CORE (SendGrid) ----------------
    @staticmethod
    def send_async_email(subject, recipients, html_body, text_body=None):
        """Send email asynchronously using SendGrid."""
        from app import create_app
        app = create_app()

        def send_email(app, subject, recipients, html_body, text_body):
            with app.app_context():
                try:
                    api_key = app.config.get('SENDGRID_API_KEY')
                    sender = app.config.get('MAIL_DEFAULT_SENDER')

                    if not api_key:
                        raise ValueError("Missing SENDGRID_API_KEY in config.")
                    if not sender:
                        raise ValueError("Missing MAIL_DEFAULT_SENDER in config.")

                    sg = SendGridAPIClient(api_key)

                    for recipient in recipients:
                        message = Mail(
                            from_email=sender,
                            to_emails=recipient,
                            subject=str(subject),
                            html_content=html_body or "",
                            plain_text_content=text_body or ""
                        )

                        response = sg.send(message)

                        if response.status_code not in (200, 202):
                            logging.error(
                                f"Failed to send email to {recipient}, "
                                f"status={response.status_code}, body={response.body}"
                            )
                        else:
                            logging.info(f"✅ Email sent to {recipient} [{response.status_code}]")

                except Exception as e:
                    logging.error(f"❌ SendGrid error while sending to {recipients}: {e}", exc_info=True)

        Thread(target=send_email, args=[app, subject, recipients, html_body, text_body], daemon=True).start()
