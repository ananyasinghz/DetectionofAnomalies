import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_SETTINGS
import pandas as pd
import logging

# Add EmailSender class directly in this file
class EmailSender:
    @staticmethod
    def send_email(subject, body):
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SETTINGS['sender_email']
        msg['To'] = EMAIL_SETTINGS['receiver_email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        try:
            server = smtplib.SMTP(EMAIL_SETTINGS['smtp_server'], EMAIL_SETTINGS['smtp_port'])
            server.starttls()
            server.login(EMAIL_SETTINGS['sender_email'], EMAIL_SETTINGS['sender_password'])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            logging.error(f"Email failed: {str(e)}")

class ReportGenerator:
    @staticmethod
    def generate_report():
        try:
            # Read logs (simplified example - adjust parsing as needed)
            with open('anomalies.log', 'r') as f:
                anomalies = f.read()
            
            report = f"""
            <h2>System Health Report ({datetime.now().date()})</h2>
            <h3>Recent Anomalies</h3>
            <pre>{anomalies[-5000:]}</pre>  # Last ~5KB of logs
            """
            return report
        except Exception as e:
            logging.error(f"Report error: {str(e)}")
            return "Error generating report."

    @staticmethod
    def send_daily_report():
        report = ReportGenerator.generate_report()
        EmailSender.send_email("Daily System Report", report)

    @staticmethod
    def send_weekly_report():
        report = ReportGenerator.generate_report()
        EmailSender.send_email("Weekly System Report", report)

if __name__ == "__main__":
    ReportGenerator.send_daily_report()  # Test email