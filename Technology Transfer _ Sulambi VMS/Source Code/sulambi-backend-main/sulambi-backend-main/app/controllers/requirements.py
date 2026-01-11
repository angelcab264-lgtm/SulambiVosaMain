from flask import g, request
from ..models.RequirementsModel import RequirementsModel
from ..models.ExternalEventModel import ExternalEventModel
from ..models.InternalEventModel import InternalEventModel
from ..models.EvaluationModel import EvaluationModel
from ..models.MembershipModel import MembershipModel
from ..utils.multipartFileWriter import basicFileWriter
from ..modules.CallbackTimer import executeDelayedAction
from ..modules.Mailer import threadedHtmlMailer, htmlMailer

from dotenv import load_dotenv
import os

load_dotenv()

FRONTEND_APP_URL = os.getenv("FRONTEND_APP_URL")

RequirementsDb = RequirementsModel()
ExternalEventDb = ExternalEventModel()
InternalEventDb = InternalEventModel()
EvaluationDb = EvaluationModel()
MembershipDb = MembershipModel()

def getAllRequirements():
  try:
    print("[REQUIREMENTS_GET_ALL] ========================================")
    print("[REQUIREMENTS_GET_ALL] Fetching all requirements...")
    
    requirements = RequirementsDb.getAll()
    print(f"[REQUIREMENTS_GET_ALL] Retrieved {len(requirements)} requirements from database")

    # manual joining of data (this implementation is just restarted, my bad...)
    for index, requirement in enumerate(requirements):
      # Backfill participant details if missing (common when older uploads only sent files)
      try:
        if (not requirements[index].get("fullname")):
          email = requirements[index].get("email")
          srcode = requirements[index].get("srcode")

          member = None
          if (email != None and str(email).strip() != ""):
            matches = MembershipDb.getAndSearch(["email"], (str(email).strip(),))
            if (len(matches) > 0):
              member = matches[0]
          if (member == None and srcode != None and str(srcode).strip() != ""):
            matches = MembershipDb.getAndSearch(["srcode"], (str(srcode).strip(),))
            if (len(matches) > 0):
              member = matches[0]

          if (member != None):
            requirements[index]["fullname"] = member.get("fullname") or requirements[index].get("fullname")
            requirements[index]["email"] = member.get("email") or requirements[index].get("email")
            requirements[index]["srcode"] = member.get("srcode") or requirements[index].get("srcode")
            requirements[index]["collegeDept"] = member.get("collegeDept") or requirements[index].get("collegeDept")
      except Exception as e:
        # Non-fatal: still return requirements list
        print("[requirements] Warning: failed to backfill member details:", e)

      eventType = requirements[index].get("type", "external")
      eventIdValue = requirements[index]["eventId"]
      
      if (eventType == "external"):
        matchedEvent = ExternalEventDb.get(eventIdValue)
        if (matchedEvent == None):
          # If event doesn't exist, provide a placeholder event object
          requirements[index]["eventId"] = {
            "id": eventIdValue,
            "title": "Event Not Found (Deleted or Missing)",
            "status": "unknown"
          }
        else:
          requirements[index]["eventId"] = matchedEvent
      elif (eventType == "internal"):
        matchedEvent = InternalEventDb.get(eventIdValue)
        if (matchedEvent == None):
          # If event doesn't exist, provide a placeholder event object
          requirements[index]["eventId"] = {
            "id": eventIdValue,
            "title": "Event Not Found (Deleted or Missing)",
            "status": "unknown"
          }
        else:
          requirements[index]["eventId"] = matchedEvent
      else:
        # Handle unknown event types - provide placeholder
        requirements[index]["eventId"] = {
          "id": eventIdValue,
          "title": f"Unknown Event Type: {eventType}",
          "status": "unknown"
        }

    print(f"[REQUIREMENTS_GET_ALL] ✅ Successfully processed {len(requirements)} requirements")
    print("[REQUIREMENTS_GET_ALL] ========================================")
    
    return {
      "message": "Successfully retrieved all requirements",
      "data": requirements
    }
  except Exception as e:
    print(f"[REQUIREMENTS_GET_ALL] ❌ ERROR: {str(e)}")
    import traceback
    print(f"[REQUIREMENTS_GET_ALL] Traceback: {traceback.format_exc()}")
    return ({ "message": f"Server error: {str(e)}" }, 500)

def acceptRequirements(id: int):
  existence = RequirementsDb.get(id)
  if (existence == None):
    return ({"message": "Requirement ID entered does not exist"}, 404)

  # get evaluation send time details to automate mailing
  if (existence["type"] == "external"):
    eventDetails = ExternalEventDb.get(existence["eventId"])
  else:
    eventDetails = InternalEventDb.get(existence["eventId"])

  if (eventDetails == None):
    return ({"message": "An error occured in automating mailing"}, 500)

  # create an evaluation template for user to answer
  createdEval = EvaluationDb.create(id, "", "", "", "", "", False)

  # automated mailing executed
  executeDelayedAction(int(eventDetails["evaluationSendTime"]), lambda: sendRenderedEvaluationMail(
    eventDetails=eventDetails,
    requirementDetails=existence
  ), execAnyway=True)

  RequirementsDb.updateSpecific(id, ["accepted"], (True,))
  updatedData = RequirementsDb.get(id)
  sendAcceptedRequirementsMail(existence, eventDetails)

  return {
    "message": "Successfully accepted requirement",
    "data": updatedData
  }

def rejectRequirements(id: int):
  existence = RequirementsDb.get(id)
  if (existence == None):
    return ({"message": "Requirement ID entered does not exist"}, 404)

  RequirementsDb.updateSpecific(id, ["accepted"], (False,))
  updatedData = RequirementsDb.get(id)

  if (existence["type"] == "external"):
    eventDetails = ExternalEventDb.get(existence["eventId"])
  else:
    eventDetails = InternalEventDb.get(existence["eventId"])

  if (eventDetails == None):
    return ({"message": "An error occured in automating mailing"}, 500)

  sendRejectedRequirementsMail(existence, eventDetails)

  return {
    "message": "Successfully rejected requirement",
    "data": updatedData
  }

def createNewRequirement(eventId: int):
  try:
    print("[REQUIREMENTS_CREATE] ========================================")
    print(f"[REQUIREMENTS_CREATE] Creating requirement for eventId: {eventId}")
    print(f"[REQUIREMENTS_CREATE] Request form keys: {list(request.form.keys())}")
    print(f"[REQUIREMENTS_CREATE] Request files keys: {list(request.files.keys())}")
    
    resultingPaths = basicFileWriter(["medCert", "waiver"])
    print(f"[REQUIREMENTS_CREATE] File paths: {resultingPaths}")
    
    # Only check for duplicates if email is provided
    email = request.form.get("email")
    if email and email.strip():
      matchedUserRequirement = RequirementsDb.getAndSearch(
        ["eventId", "type", "email"],
        [eventId, request.form.get("type") or "external", email]
      )

      if (len(matchedUserRequirement) > 0):
        print(f"[REQUIREMENTS_CREATE] ❌ Duplicate requirement found for email: {email}")
        return ({ "message": "Your email has already been registered to this event" }, 403)

    print("[REQUIREMENTS_CREATE] Creating requirement in database...")
    
    # Convert empty strings to None for integer fields (PostgreSQL requirement)
    # age column in requirements table is INTEGER (nullable), so empty strings must be None
    age_str = request.form.get("age") or ""
    age_value = None
    if age_str and age_str.strip():
      try:
        age_value = int(age_str.strip())
      except ValueError:
        age_value = None
    
    createdRequirement = RequirementsDb.create(
      resultingPaths.get("medCert") or "",
      resultingPaths.get("waiver") or "",
      eventId,
      request.form.get("type") or "external",
      request.form.get("curriculum") or "",
      request.form.get("destination") or "",
      request.form.get("firstAid") or "",
      request.form.get("fees") or "",
      request.form.get("personnelInCharge") or "",
      request.form.get("personnelRole") or "",
      request.form.get("fullname") or "",
      request.form.get("email") or "",
      request.form.get("srcode") or "",
      age_value,  # This will be an integer or None, not a string
      request.form.get("birthday") or "",
      request.form.get("sex") or "",
      request.form.get("campus") or "",
      request.form.get("collegeDept") or "",
      request.form.get("yrlevelprogram") or "",
      request.form.get("address") or "",
      request.form.get("contactNum") or "",
      request.form.get("fblink") or "",
      None,
      request.form.get("affiliation") or "N/A"
    )

    print(f"[REQUIREMENTS_CREATE] ✅ Requirement created successfully with ID: {createdRequirement.get('id')}")
    print("[REQUIREMENTS_CREATE] ========================================")

    return {
      "message": "Successfully uploaded requirements",
      "data": createdRequirement
    }
  except Exception as e:
    print(f"[REQUIREMENTS_CREATE] ❌ ERROR: {str(e)}")
    import traceback
    print(f"[REQUIREMENTS_CREATE] Traceback: {traceback.format_exc()}")
    return ({ "message": f"Server error: {str(e)}" }, 500)

######################
#  Helper Functions  #
######################
def sendRenderedEvaluationMail(requirementDetails: dict, eventDetails: dict):
  templateHtml = open("templates/evaluation-mail-template.html", "r").read()
  templateHtml = templateHtml.replace("[name]", requirementDetails.get("fullname"))
  templateHtml = templateHtml.replace("[token]", requirementDetails.get("id"))
  templateHtml = templateHtml.replace("[event-title]", eventDetails.get("title"))
  templateHtml = templateHtml.replace("[link]", FRONTEND_APP_URL + "/evaluation/" + requirementDetails.get("id"))

  htmlMailer(
    mailTo=requirementDetails.get("email"),
    htmlRendered=templateHtml,
    subject="Evaluation Attendance"
  )

def sendRejectedRequirementsMail(requirementDetails: dict, eventDetails: dict):
  templateHtml = open("templates/we-reject-to-inform-requirements.html", "r").read()
  templateHtml = templateHtml.replace("[name]", requirementDetails.get("fullname"))
  templateHtml = templateHtml.replace("[event]", eventDetails.get("title"))

  threadedHtmlMailer(
    mailTo=requirementDetails.get("email"),
    htmlRendered=templateHtml,
    subject="Requirement Evaluation: Sulambi - VOSA"
  )

def sendAcceptedRequirementsMail(requirementDetails: dict, eventDetails: dict):
  templateHtml = open("templates/we-are-pleased-to-inform-requirements.html", "r").read()
  templateHtml = templateHtml.replace("[name]", requirementDetails.get("fullname"))
  templateHtml = templateHtml.replace("[event]", eventDetails.get("title"))

  threadedHtmlMailer(
    mailTo=requirementDetails.get("email"),
    htmlRendered=templateHtml,
    subject="Requirement Evaluation: Sulambi - VOSA"
  )
