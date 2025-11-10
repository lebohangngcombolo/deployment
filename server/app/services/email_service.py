from flask import render_template, current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from threading import Thread
import logging

class EmailService:
    """Full-featured email service using SendGrid, compatible with your existing methods."""

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

        EmailService.send_async_email(subject, email, html)

    @staticmethod
    def send_password_reset_email(email, reset_token):
        subject = "Password Reset Request"
        reset_link = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        try:
            html = render_template(
                'email_templates/password_reset_email.html', 
                reset_link=reset_link
            )
        except Exception:
            logging.error(f"Failed to render password reset template for {email}", exc_info=True)
            html = f"Reset your password using this link: {reset_link}"

        EmailService.send_async_email(subject, email, html)

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

        EmailService.send_async_email(subject, email, html)

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

        EmailService.send_async_email(subject, email, html)

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

        EmailService.send_async_email(subject, email, html, text_body=text_body)

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
            text_body = f"Hi {candidate_name},\n\nYour {interview_type} interview scheduled on {interview_date} has been cancelled.\nReason: {reason_text}\n\nPlease contact us for rescheduling."
        except Exception:
            logging.error(f"Failed to render interview cancellation template for {email}", exc_info=True)
            html = text_body = f"Hi {candidate_name}, your {interview_type} interview scheduled on {interview_date} has been cancelled.\nReason: {reason_text}"

        EmailService.send_async_email(subject, email, html, text_body=text_body)

    @staticmethod
    def send_interview_reschedule_email(email, candidate_name, old_time, new_time, interview_type, meeting_link=None):
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
            logging.error(f"Failed to render reschedule email template for {email}", exc_info=True)
            html = f"Hi {candidate_name}, your {interview_type} interview has been rescheduled from {old_time} to {new_time}. Link: {meeting_link}"

        EmailService.send_async_email(subject, email, html)

    @staticmethod
    def send_async_email(subject, to_email, html_body, text_body=None):
        """Send email using SendGrid in a background thread."""
        def send_email_thread(subject, to_email, html_body, text_body):
            try:
                message = Mail(
                    from_email=current_app.config['MAIL_DEFAULT_SENDER'],
                    to_emails=to_email,
                    subject=str(subject),
                    html_content=html_body,
                    plain_text_content=text_body or ""
                )
                sg = SendGridAPIClient(current_app.config['SENDGRID_API_KEY'])
                response = sg.send(message)
                logging.info(f"Email sent to {to_email}, status: {response.status_code}")
            except Exception as e:
                logging.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)

        Thread(target=send_email_thread, args=(subject, to_email, html_body, text_body)).start()


