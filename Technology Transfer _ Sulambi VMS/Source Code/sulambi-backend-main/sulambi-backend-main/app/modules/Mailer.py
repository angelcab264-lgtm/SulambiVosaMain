from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from threading import Thread
import os

load_dotenv()

EMAIL = os.getenv("AUTOMAILER_EMAIL")
PASSW = os.getenv("AUTOMAILER_PASSW")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL") or EMAIL

# Try to import Resend
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    resend = None

def isEmailConfigured():
  """Check if email configuration is properly set up"""
  # Check Resend first (preferred for Render free tier)
  if RESEND_AVAILABLE and RESEND_API_KEY and RESEND_API_KEY != "":
    return True
  # Fall back to SMTP configuration
  return EMAIL is not None and PASSW is not None and EMAIL != "" and PASSW != ""

def isResendConfigured():
  """Check if Resend is configured"""
  return RESEND_AVAILABLE and RESEND_API_KEY and RESEND_API_KEY != "" and (RESEND_FROM_EMAIL or EMAIL)

def validateEmailConfig():
  """Validate email configuration and return status"""
  # Check Resend first (preferred for Render free tier)
  if isResendConfigured():
    try:
      # Test Resend API key by attempting to list domains
      # This is a lightweight API call to validate the key
      resend.api_key = RESEND_API_KEY
      # Simple validation - just check if API key is set and format looks correct
      if RESEND_API_KEY.startswith("re_"):
        return {
          "configured": True,
          "message": "Resend email configuration is valid",
          "provider": "Resend"
        }
      else:
        return {
          "configured": False,
          "message": "Resend API key format is invalid. It should start with 're_'",
          "provider": "Resend"
        }
    except Exception as e:
      error_msg = str(e)
      return {
        "configured": False,
        "message": f"Resend configuration test failed: {error_msg}",
        "provider": "Resend"
      }
  
  # Fall back to SMTP validation
  if not isEmailConfigured():
    return {
      "configured": False,
      "message": "Email configuration missing. Please set RESEND_API_KEY and RESEND_FROM_EMAIL (or AUTOMAILER_EMAIL and AUTOMAILER_PASSW for SMTP) in .env file",
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
        "message": "Email configuration test timed out. SMTP connection to smtp.gmail.com:587 timed out after 10 seconds. Consider using Resend for Render free tier.",
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
  """Send HTML email with error handling - uses Resend if configured, otherwise SMTP"""
  if not isEmailConfigured():
    print(f"[EMAIL ERROR] Email not configured. Cannot send email to {mailTo}")
    return False
  
  # Use Resend if configured (preferred for Render free tier)
  if isResendConfigured():
    try:
      resend.api_key = RESEND_API_KEY
      from_email = RESEND_FROM_EMAIL or EMAIL
      
      params = {
        "from": from_email,
        "to": mailTo,
        "subject": subject,
        "html": htmlRendered
      }
      
      response = resend.Emails.send(params)
      
      # Resend returns the email data on success, raises exception on error
      if response and hasattr(response, "id"):
        print(f"[EMAIL SUCCESS] Email sent via Resend to {mailTo} (id: {response.id})")
        return True
      else:
        print(f"[EMAIL ERROR] Resend did not return expected response: {response}")
        return False
    except Exception as e:
      print(f"[EMAIL ERROR] Failed to send email via Resend to {mailTo}: {str(e)}")
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
