from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from threading import Thread
import os

load_dotenv()

EMAIL = os.getenv("AUTOMAILER_EMAIL")
PASSW = os.getenv("AUTOMAILER_PASSW")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL") or EMAIL

# Try to import SendGrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    SendGridAPIClient = None
    Mail = None

def isEmailConfigured():
  """Check if email configuration is properly set up"""
  # Check SendGrid first (preferred for Render free tier)
  if SENDGRID_AVAILABLE and SENDGRID_API_KEY and SENDGRID_API_KEY != "":
    return True
  # Fall back to SMTP configuration
  return EMAIL is not None and PASSW is not None and EMAIL != "" and PASSW != ""

def isSendGridConfigured():
  """Check if SendGrid is configured"""
  return SENDGRID_AVAILABLE and SENDGRID_API_KEY and SENDGRID_API_KEY != "" and (SENDGRID_FROM_EMAIL or EMAIL)

def validateEmailConfig():
  """Validate email configuration and return status"""
  # Check SendGrid first (preferred for Render free tier)
  if isSendGridConfigured():
    try:
      # Test SendGrid API key by making a simple API call
      sg = SendGridAPIClient(SENDGRID_API_KEY)
      response = sg.client.api_keys.get()
      
      if response.status_code == 200:
        return {
          "configured": True,
          "message": "SendGrid email configuration is valid",
          "provider": "SendGrid"
        }
      else:
        return {
          "configured": False,
          "message": f"SendGrid API key validation failed with status {response.status_code}",
          "provider": "SendGrid"
        }
    except Exception as e:
      error_msg = str(e)
      return {
        "configured": False,
        "message": f"SendGrid configuration test failed: {error_msg}",
        "provider": "SendGrid"
      }
  
  # Fall back to SMTP validation
  if not isEmailConfigured():
    return {
      "configured": False,
      "message": "Email configuration missing. Please set SENDGRID_API_KEY and SENDGRID_FROM_EMAIL (or AUTOMAILER_EMAIL and AUTOMAILER_PASSW for SMTP) in .env file",
      "provider": "None"
    }
  
  try:
    # Test SMTP connection with timeout
    import socket
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(10)  # 10 second timeout
    
    try:
      smtp = SMTP("smtp.gmail.com", 587)
      smtp.set_debuglevel(0)  # Disable debug output
      smtp.ehlo()
      smtp.starttls()
      smtp.login(EMAIL, PASSW)
      smtp.close()
      
      return {
        "configured": True,
        "message": "SMTP email configuration is valid",
        "provider": "SMTP"
      }
    finally:
      # Always reset timeout
      socket.setdefaulttimeout(old_timeout)
    
  except (socket.timeout, TimeoutError, OSError) as e:
    import socket
    socket.setdefaulttimeout(None)  # Reset on timeout
    error_msg = str(e)
    if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
      return {
        "configured": False,
        "message": "Email configuration test timed out. SMTP connection to smtp.gmail.com:587 timed out after 10 seconds. Consider using SendGrid for Render free tier.",
        "provider": "SMTP"
      }
    else:
      return {
        "configured": False,
        "message": f"Email configuration test failed: {error_msg}",
        "provider": "SMTP"
      }
  except Exception as e:
    import socket
    socket.setdefaulttimeout(None)  # Reset on any error
    return {
      "configured": False,
      "message": f"Email configuration test failed: {str(e)}",
      "provider": "SMTP"
    }

def sendMail(mailTo: str, content):
  Smtp = SMTP("smtp.gmail.com", 587)
  Smtp.ehlo()
  Smtp.starttls()
  Smtp.login(EMAIL, PASSW)
  Smtp.sendmail(EMAIL, mailTo, content)
  Smtp.close()

def htmlMailer(mailTo: str, subject: str, htmlRendered: str):
  """Send HTML email with error handling - uses SendGrid if configured, otherwise SMTP"""
  if not isEmailConfigured():
    print(f"[EMAIL ERROR] Email not configured. Cannot send email to {mailTo}")
    return False
  
  # Use SendGrid if configured (preferred for Render free tier)
  if isSendGridConfigured():
    try:
      from_email = SENDGRID_FROM_EMAIL or EMAIL
      message = Mail(
        from_email=from_email,
        to_emails=mailTo,
        subject=subject,
        html_content=htmlRendered
      )
      
      sg = SendGridAPIClient(SENDGRID_API_KEY)
      response = sg.send(message)
      
      if response.status_code in [200, 201, 202]:
        print(f"[EMAIL SUCCESS] Email sent via SendGrid to {mailTo} (status: {response.status_code})")
        return True
      else:
        print(f"[EMAIL ERROR] SendGrid returned status {response.status_code}: {response.body}")
        return False
    except Exception as e:
      print(f"[EMAIL ERROR] Failed to send email via SendGrid to {mailTo}: {str(e)}")
      return False
  
  # Fall back to SMTP
  try:
    messageMime = MIMEMultipart()
    messageMime["from"] = EMAIL
    messageMime["to"] = mailTo
    messageMime["subject"] = subject

    messageMime.attach(MIMEText(htmlRendered, "html"))
    Smtp = SMTP("smtp.gmail.com", 587)
    Smtp.ehlo()
    Smtp.starttls()
    Smtp.login(EMAIL, PASSW)
    Smtp.sendmail(EMAIL, mailTo, messageMime.as_string())
    Smtp.close()
    print(f"[EMAIL SUCCESS] Email sent via SMTP to {mailTo}")
    return True
  except Exception as e:
    print(f"[EMAIL ERROR] Failed to send email via SMTP to {mailTo}: {str(e)}")
    return False

def threadedHtmlMailer(mailTo: str, subject: str, htmlRendered: str):
  """Send HTML email in background thread with error handling"""
  th = Thread(target=htmlMailer, args=(mailTo, subject, htmlRendered))
  th.daemon = True
  th.start()
