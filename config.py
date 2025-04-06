# Email Configuration (for alerts and reports)
EMAIL_SETTINGS = {
    "smtp_server": "smtp.gmail.com",  # For Gmail
    "smtp_port": 587,
    "sender_email": "ananyasinghz2301@gmail.com",
    "sender_password": "hrkg nbmv fovg pmnq",  # Use App Password for Gmail
    "receiver_email": "khushiisinghzzz@gmail.com",
    "daily_report_time": "21:20",  # 8 AM daily
    "weekly_report_day": "Thursday"   # Weekly on Monday
}

# Anomaly Detection Settings
DETECTION_SETTINGS = {
    "contamination": 0.01,
    "monitoring_interval": 1  
}