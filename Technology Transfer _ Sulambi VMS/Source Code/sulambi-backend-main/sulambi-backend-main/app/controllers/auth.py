from ..models.AccountModel import AccountModel
from ..models.MembershipModel import MembershipModel
from ..models.SessionModel import SessionModel
from ..modules.Mailer import threadedHtmlMailer, isEmailConfigured, validateEmailConfig, htmlMailer
from flask import request
import traceback

AccountDb = AccountModel()
MembershipDb = MembershipModel()
SessionDb = SessionModel()

def login():
  try:
    print("[AUTH_LOGIN] ========================================")
    print("[AUTH_LOGIN] Login request received")
    
    # Check if request has JSON
    if not request.json:
      print("[AUTH_LOGIN] ❌ ERROR: No JSON data in request")
      return ({ "message": "No data provided" }, 400)
    
    username = request.json.get('username')
    password = request.json.get('password')
    
    print(f"[AUTH_LOGIN] Username: {username}")
    print(f"[AUTH_LOGIN] Password: {'*' * len(password) if password else 'None'}")
    
    if not username or not password:
      print("[AUTH_LOGIN] ❌ ERROR: Missing username or password")
      return ({ "message": "Username and password are required" }, 400)
    
    print("[AUTH_LOGIN] Attempting authentication...")
    sessionDetails = AccountDb.authenticate(username, password)
    
    if (sessionDetails == None):
      print("[AUTH_LOGIN] ❌ Authentication failed - Invalid credentials")
      print("[AUTH_LOGIN] ========================================")
      return ({ "message": "Invalid Credentials" }, 403)
    
    print(f"[AUTH_LOGIN] ✅ Authentication successful!")
    print(f"[AUTH_LOGIN] Account Type: {sessionDetails.get('accountType')}")
    print(f"[AUTH_LOGIN] User ID: {sessionDetails.get('userid')}")
    print(f"[AUTH_LOGIN] Token: {sessionDetails.get('token')[:20]}..." if sessionDetails.get('token') else "No token")
    print("[AUTH_LOGIN] ========================================")

    membershipData = None
    if (sessionDetails["accountType"] == "member"):
      print("[AUTH_LOGIN] Fetching member data...")
      accountData = AccountDb.get(sessionDetails["userid"])
      membershipData = MembershipDb.get(accountData["membershipId"])
      print(f"[AUTH_LOGIN] Member data retrieved: {membershipData is not None}")

    response = {
      "message": "Successfully logged in",
      "session": sessionDetails,
      "memberData": membershipData
    }
    
    print("[AUTH_LOGIN] ✅ Login successful, returning response")
    return response
    
  except KeyError as e:
    print(f"[AUTH_LOGIN] ❌ ERROR: Missing key in request: {e}")
    print(f"[AUTH_LOGIN] Traceback: {traceback.format_exc()}")
    return ({ "message": f"Missing required field: {str(e)}" }, 400)
  except Exception as e:
    print(f"[AUTH_LOGIN] ❌ ERROR: Unexpected error: {str(e)}")
    print(f"[AUTH_LOGIN] Traceback: {traceback.format_exc()}")
    return ({ "message": f"Server error: {str(e)}" }, 500)

def logout(usertoken):
  matchedToken = SessionDb.get(usertoken)
  if (matchedToken == None):
    return { "message": "Token does not exist (cannot logout)" }

  result = SessionDb.delete(matchedToken["id"])
  return { "message": "Successfully logged out token" }

def register():
  try:
    print("[AUTH_REGISTER] ========================================")
    print("[AUTH_REGISTER] Registration request received")
    
    # Check if request has JSON
    if not request.json:
      print("[AUTH_REGISTER] ❌ ERROR: No JSON data in request")
      return ({ "message": "No data provided" }, 400)
    
    print(f"[AUTH_REGISTER] Request keys: {list(request.json.keys())}")
    
    applyingAs = request.json.get("applyingAs")
    volunterismExperience = request.json.get("volunterismExperience")
    weekdaysTimeDevotion = request.json.get("weekdaysTimeDevotion")
    weekendsTimeDevotion = request.json.get("weekendsTimeDevotion")
    fullname = request.json.get("fullname")
    email = request.json.get("email")
    affiliation = request.json.get("affiliation")
    srcode = request.json.get("srcode")
    age = request.json.get("age")
    birthday = request.json.get("birthday")
    sex = request.json.get("sex")
    campus = request.json.get("campus")
    collegeDept = request.json.get("collegeDept")
    yrlevelprogram = request.json.get("yrlevelprogram")
    address = request.json.get("address")
    contactNum = request.json.get("contactNum")
    fblink = request.json.get("fblink")
    bloodType = request.json.get("bloodType")
    bloodDonation = request.json.get("bloodDonation")
    paymentOption = request.json.get("paymentOption")
    username = request.json.get("username")
    password = request.json.get("password")

    # optional fields
    medicalCondition = request.json.get("medicalCondition") or ""
    areasOfInterest = request.json.get("areasOfInterest") or ""
    volunteerExpQ1 = request.json.get("volunteerExpQ1") or ""
    volunteerExpQ2 = request.json.get("volunteerExpQ2") or ""
    volunteerExpProof = request.json.get("volunteerExpProof") or ""
    reasonQ1 = request.json.get("reasonQ1") or ""
    reasonQ2 = request.json.get("reasonQ2") or ""

    # check for existence of member
    memberMatch = MembershipDb.getOrSearch(["username", "email", "srcode"], [username, email, srcode])
    if (len(memberMatch) > 0):
      fieldError = []
      for member in memberMatch:
        if (member["username"] == username and fieldError.count("username") == 0):
          fieldError.append("username")
        if (member["email"] == email and fieldError.count("email") == 0):
          fieldError.append("email")
        if (member["srcode"] == srcode and fieldError.count("email") == 0):
          fieldError.append("srcode")

      return ({
        "message": "Membership for your account already exists",
        "fieldError": fieldError
      }, 400)

    # register membership for approval
    # Explicitly set accepted=None to ensure it's pending (NULL in database)
    createdMember = MembershipDb.create(
      address=address,
      age=age,
      applyingAs=applyingAs,
      areasOfInterest=areasOfInterest,
      birthday=birthday,
      bloodDonation=bloodDonation,
      bloodType=bloodType,
      campus=campus,
      collegeDept=collegeDept,
      contactNum=contactNum,
      email=email,
      affiliation=affiliation,
      fblink=fblink,
      fullname=fullname,
      medicalCondition=medicalCondition,
      password=password,
      paymentOption=paymentOption,
      reasonQ1=reasonQ1,
      reasonQ2=reasonQ2,
      sex=sex,
      srcode=srcode,
      username=username,
      volunterismExperience=volunterismExperience,
      volunteerExpQ1=volunteerExpQ1,
      volunteerExpQ2=volunteerExpQ2,
      weekdaysTimeDevotion=weekdaysTimeDevotion,
      weekendsTimeDevotion=weekendsTimeDevotion,
      yrlevelprogram=yrlevelprogram,
      volunteerExpProof=volunteerExpProof,
      accepted=None,  # Explicitly set to None for pending status
      active=True     # Set active to True by default
    )
    
    print(f"[AUTH_REGISTER] Member created with ID: {createdMember.get('id')}")
    print(f"[AUTH_REGISTER] Member accepted status: {createdMember.get('accepted')} (should be None for pending)")
    print(f"[AUTH_REGISTER] Member active status: {createdMember.get('active')}")

    # Send pending verification email
    sendPendingVerificationMail(createdMember)

    print("[AUTH_REGISTER] ✅ Registration successful, returning response")
    print("[AUTH_REGISTER] ========================================")
    
    return {
      "member": createdMember,
      "message": "Member successfully created"
    }
    
  except KeyError as e:
    print(f"[AUTH_REGISTER] ❌ ERROR: Missing key in request: {e}")
    print(f"[AUTH_REGISTER] Traceback: {traceback.format_exc()}")
    return ({ "message": f"Missing required field: {str(e)}" }, 400)
  except Exception as e:
    print(f"[AUTH_REGISTER] ❌ ERROR: Unexpected error: {str(e)}")
    print(f"[AUTH_REGISTER] Traceback: {traceback.format_exc()}")
    return ({ "message": f"Server error: {str(e)}" }, 500)

######################
#  Helper Functions  #
######################
def sendPendingVerificationMail(memberDetails):
  """Send email notification to user that their application is under review"""
  templateHtml = open("templates/application-under-review.html", "r").read()
  templateHtml = templateHtml.replace("[name]", memberDetails.get("fullname").split(" ")[0])
  templateHtml = templateHtml.replace("[application_type]", "membership")
  templateHtml = templateHtml.replace("[timeframe]", "3-5 business days")

  threadedHtmlMailer(
    mailTo=memberDetails.get("email"),
    htmlRendered=templateHtml,
    subject="Application Received - Pending Officer Verification | Sulambi VOSA"
  )

def checkApplicationStatus():
  """Check membership application status by email"""
  email = request.json.get("email")
  
  if not email:
    return ({"message": "Email is required"}, 400)
  
  # Search for membership by email
  memberMatch = MembershipDb.getOrSearch(["email"], [email])
  
  if len(memberMatch) == 0:
    return ({"message": "No application found with this email address"}, 404)
  
  member = memberMatch[0]
  
  # Determine status
  status = "pending"
  if member["accepted"] is True:
    status = "approved"
  elif member["accepted"] is False:
    status = "rejected"
  
  return {
    "message": "Application status retrieved successfully",
    "data": {
      "fullname": member["fullname"],
      "email": member["email"],
      "srcode": member["srcode"],
      "status": status,
      "applyingAs": member["applyingAs"],
      "campus": member["campus"],
      "collegeDept": member["collegeDept"],
      "submittedDate": member.get("created_at", "Unknown")
    }
  }

def testEmail():
  """Test email system configuration and send a test email"""
  from flask import request
  
  try:
    # Check email configuration
    is_configured = isEmailConfigured()
    
    if not is_configured:
      return {
        "success": False,
        "configured": False,
        "message": "Email not configured. AUTOMAILER_EMAIL and AUTOMAILER_PASSW must be set.",
        "smtp_test": None
      }
    
    # Test SMTP connection
    validation = validateEmailConfig()
    
    # Get test email from query parameter or use the configured email
    test_email = request.args.get('email', None)
    
    result = {
      "success": True,
      "configured": True,
      "smtp_test": validation,
      "message": validation.get("message", "Email configuration check completed")
    }
    
    # If test email provided, try to send
    if test_email:
      test_html = """
      <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
          <h2 style="color: #c07f00;">Test Email from Sulambi VOSA</h2>
          <p>This is a test email to verify the email system is working correctly in deployment.</p>
          <p>If you received this email, the email system is configured and functioning properly!</p>
          <hr style="margin: 20px 0;">
          <p style="color: #666; font-size: 12px;">Sent from Sulambi VOSA System - Deployment Test</p>
        </body>
      </html>
      """
      
      email_sent = htmlMailer(test_email, "Test Email - Sulambi VOSA Email System", test_html)
      
      result["test_email_sent"] = email_sent
      result["test_email_address"] = test_email
      if email_sent:
        result["message"] = f"Email configuration is valid and test email sent to {test_email}"
      else:
        result["message"] = f"Email configuration check passed but failed to send test email to {test_email}"
    
    return result
    
  except Exception as e:
    import traceback
    traceback.print_exc()
    return {
      "success": False,
      "configured": False,
      "message": f"Error testing email system: {str(e)}",
      "smtp_test": None
    }