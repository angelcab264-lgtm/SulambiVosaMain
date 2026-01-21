from flask import g, request
from werkzeug.exceptions import BadRequest
from ..models.RequirementsModel import RequirementsModel
from ..models.ExternalEventModel import ExternalEventModel
from ..models.InternalEventModel import InternalEventModel
from ..models.EvaluationModel import EvaluationModel
from ..models.MembershipModel import MembershipModel
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
  import time
  start_time = time.time()
  
  try:
    print("[REQUIREMENTS_GET_ALL] ========================================")
    print("[REQUIREMENTS_GET_ALL] Fetching all requirements...")
    
    step_start = time.time()
    # Get all requirements - already sorted by ID DESC in Model.getAll() for requirements table
    requirements = RequirementsDb.getAll()
    
    step_time = time.time() - step_start
    print(f"[REQUIREMENTS_GET_ALL] Retrieved {len(requirements)} requirements from database (sorted by most recent first) ({step_time:.2f}s)")

    # OPTIMIZATION: Batch fetch all events to avoid opening hundreds of database connections
    # Collect all unique event IDs first
    external_event_ids = set()
    internal_event_ids = set()
    
    for requirement in requirements:
      eventType = requirement.get("type", "external")
      eventIdValue = requirement.get("eventId")
      
      if eventIdValue is not None:
        if eventType == "external":
          external_event_ids.add(eventIdValue)
        elif eventType == "internal":
          internal_event_ids.add(eventIdValue)
    
    print(f"[REQUIREMENTS_GET_ALL] Found {len(external_event_ids)} unique external events and {len(internal_event_ids)} unique internal events")
    
    # OPTIMIZATION: Batch fetch only needed events
    step_start = time.time()
    external_events_cache = {}
    if external_event_ids:
      try:
        all_external_events = ExternalEventDb.getAll()
        for event in all_external_events:
          if event and event.get("id") in external_event_ids:
            external_events_cache[event["id"]] = event
        step_time = time.time() - step_start
        print(f"[REQUIREMENTS_GET_ALL] Cached {len(external_events_cache)}/{len(external_event_ids)} external events ({step_time:.2f}s)")
      except Exception as e:
        print(f"[REQUIREMENTS_GET_ALL] Warning: Failed to batch fetch external events: {e}")
    
    # Batch fetch all internal events
    step_start = time.time()
    internal_events_cache = {}
    if internal_event_ids:
      try:
        all_internal_events = InternalEventDb.getAll()
        for event in all_internal_events:
          if event and event.get("id") in internal_event_ids:
            internal_events_cache[event["id"]] = event
        step_time = time.time() - step_start
        print(f"[REQUIREMENTS_GET_ALL] Cached {len(internal_events_cache)}/{len(internal_event_ids)} internal events ({step_time:.2f}s)")
      except Exception as e:
        print(f"[REQUIREMENTS_GET_ALL] Warning: Failed to batch fetch internal events: {e}")

    # OPTIMIZATION: Batch fetch members for backfilling to avoid individual queries
    step_start = time.time()
    emails_to_lookup = set()
    srcodes_to_lookup = set()
    requirements_needing_backfill = []
    
    for index, requirement in enumerate(requirements):
      if not requirement.get("fullname"):
        email = requirement.get("email")
        srcode = requirement.get("srcode")
        if email and str(email).strip():
          emails_to_lookup.add(str(email).strip())
        if srcode and str(srcode).strip():
          srcodes_to_lookup.add(str(srcode).strip())
        requirements_needing_backfill.append(index)
    
    # Batch fetch members by email and srcode
    members_by_email = {}
    members_by_srcode = {}
    
    if emails_to_lookup or srcodes_to_lookup:
      try:
        all_members = MembershipDb.getAll()
        for member in all_members:
          member_email = member.get("email")
          member_srcode = member.get("srcode")
          if member_email and str(member_email).strip() in emails_to_lookup:
            members_by_email[str(member_email).strip()] = member
          if member_srcode and str(member_srcode).strip() in srcodes_to_lookup:
            members_by_srcode[str(member_srcode).strip()] = member
        step_time = time.time() - step_start
        print(f"[REQUIREMENTS_GET_ALL] Cached {len(members_by_email)} members by email, {len(members_by_srcode)} by srcode ({step_time:.2f}s)")
      except Exception as e:
        print(f"[REQUIREMENTS_GET_ALL] Warning: Failed to batch fetch members: {e}")
    
    # Now process requirements using cached events and members (no additional DB connections)
    step_start = time.time()
    for index, requirement in enumerate(requirements):
      # Backfill participant details if missing using cached members
      if index in requirements_needing_backfill:
        try:
          email = requirements[index].get("email")
          srcode = requirements[index].get("srcode")
          
          member = None
          if email and str(email).strip() in members_by_email:
            member = members_by_email[str(email).strip()]
          elif srcode and str(srcode).strip() in members_by_srcode:
            member = members_by_srcode[str(srcode).strip()]
          
          if member:
            requirements[index]["fullname"] = member.get("fullname") or requirements[index].get("fullname")
            requirements[index]["email"] = member.get("email") or requirements[index].get("email")
            requirements[index]["srcode"] = member.get("srcode") or requirements[index].get("srcode")
            requirements[index]["collegeDept"] = member.get("collegeDept") or requirements[index].get("collegeDept")
        except Exception as e:
          # Non-fatal: still return requirements list
          print("[requirements] Warning: failed to backfill member details:", e)

      eventType = requirements[index].get("type", "external")
      eventIdValue = requirements[index].get("eventId")
      
      if (eventType == "external"):
        matchedEvent = external_events_cache.get(eventIdValue) if eventIdValue is not None else None
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
        matchedEvent = internal_events_cache.get(eventIdValue) if eventIdValue is not None else None
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
    
    processing_time = time.time() - step_start
    print(f"[REQUIREMENTS_GET_ALL] Processed {len(requirements)} requirements ({processing_time:.2f}s)")
    
    total_time = time.time() - start_time
    print(f"[REQUIREMENTS_GET_ALL] ✅ Successfully processed {len(requirements)} requirements")
    print(f"[REQUIREMENTS_GET_ALL] ⏱️ Total time: {total_time:.2f}s")
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

  # Determine when to send evaluation email:
  # - Prefer the later of event durationEnd and evaluationSendTime (both stored as epoch ms)
  # - This ensures emails are sent only after the event has finished
  try:
    duration_end_ms = int(eventDetails.get("durationEnd", 0) or 0)
  except (TypeError, ValueError):
    duration_end_ms = 0

  try:
    eval_send_ms = int(eventDetails.get("evaluationSendTime", 0) or 0)
  except (TypeError, ValueError):
    eval_send_ms = 0

  # If evaluationSendTime is not set or is earlier than event end, use event end time
  target_epoch_ms = max(duration_end_ms, eval_send_ms)

  # If still zero (no timing info), fall back to immediate execution
  if target_epoch_ms <= 0:
    print("[REQUIREMENTS_ACCEPT] Warning: No valid durationEnd/evaluationSendTime; sending evaluation email immediately")
    sendRenderedEvaluationMail(requirementDetails=existence, eventDetails=eventDetails)
  else:
    # Schedule email to be sent after target time (no execAnyway so past times are skipped)
    executeDelayedAction(
      target_epoch_ms,
      lambda: sendRenderedEvaluationMail(requirementDetails=existence, eventDetails=eventDetails),
      execAnyway=False
    )

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
    
    # Use Cloudinary for file uploads (validates PDF and images only)
    # IMPORTANT: All uploads MUST go to Cloudinary - local storage is disabled
    from app.utils.multipartFileWriter import cloudinaryFileWriter
    
    try:
      resultingPaths = cloudinaryFileWriter(["medCert", "waiver"], folder="requirements")
      print(f"[REQUIREMENTS_CREATE] ✅ Cloudinary uploads successful")
      print(f"[REQUIREMENTS_CREATE] Cloudinary URLs: {resultingPaths}")
      print(f"[REQUIREMENTS_CREATE] medCert URL: {resultingPaths.get('medCert', 'NOT FOUND')}")
      print(f"[REQUIREMENTS_CREATE] waiver URL: {resultingPaths.get('waiver', 'NOT FOUND')}")
      
      # Verify both files were uploaded to Cloudinary
      medCertUrl = resultingPaths.get("medCert", "")
      waiverUrl = resultingPaths.get("waiver", "")
      
      if not medCertUrl:
        error_msg = "Medical certificate file was not uploaded to Cloudinary"
        print(f"[REQUIREMENTS_CREATE] ❌ ERROR: {error_msg}")
        return ({ "message": error_msg }, 400)
      
      if not waiverUrl:
        error_msg = "Waiver file was not uploaded to Cloudinary"
        print(f"[REQUIREMENTS_CREATE] ❌ ERROR: {error_msg}")
        return ({ "message": error_msg }, 400)
      
      # Verify URLs are Cloudinary URLs (not local paths)
      if not medCertUrl.startswith(('http://', 'https://')):
        error_msg = f"Invalid medical certificate URL format. Expected Cloudinary URL, got: {medCertUrl[:50]}..."
        print(f"[REQUIREMENTS_CREATE] ❌ ERROR: {error_msg}")
        return ({ "message": "Medical certificate must be uploaded to Cloudinary" }, 400)
      
      if not waiverUrl.startswith(('http://', 'https://')):
        error_msg = f"Invalid waiver URL format. Expected Cloudinary URL, got: {waiverUrl[:50]}..."
        print(f"[REQUIREMENTS_CREATE] ❌ ERROR: {error_msg}")
        return ({ "message": "Waiver must be uploaded to Cloudinary" }, 400)
      
      print(f"[REQUIREMENTS_CREATE] ✅ Both files verified as Cloudinary URLs")
      
    except BadRequest as e:
      # Re-raise BadRequest from cloudinaryFileWriter (Cloudinary config issues, validation errors, etc.)
      print(f"[REQUIREMENTS_CREATE] ❌ BadRequest from Cloudinary upload: {str(e)}")
      return ({ "message": str(e) }, 400)
    except Exception as e:
      error_msg = f"Failed to upload files to Cloudinary: {str(e)}"
      print(f"[REQUIREMENTS_CREATE] ❌ ERROR: {error_msg}")
      return ({ "message": error_msg }, 500)
    
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
    
    # Get file URLs - both should already be Cloudinary URLs (verified above)
    medCertUrl = resultingPaths.get("medCert") or ""
    waiverUrl = resultingPaths.get("waiver") or ""
    
    print(f"[REQUIREMENTS_CREATE] Saving Cloudinary URLs to database:")
    print(f"  medCert: {medCertUrl[:80]}...")
    print(f"  waiver: {waiverUrl[:80]}...")
    
    createdRequirement = RequirementsDb.create(
      medCertUrl,  # Cloudinary URL
      waiverUrl,   # Cloudinary URL
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
  # Build evaluation link safely, even if FRONTEND_APP_URL is not configured
  base_url = FRONTEND_APP_URL or ""
  link = (base_url + "/evaluation/" + str(requirementDetails.get("id"))) if base_url else "/evaluation/" + str(requirementDetails.get("id"))
  templateHtml = templateHtml.replace("[link]", link)

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
