from flask import request
from ..models.ExternalEventModel import ExternalEventModel
from ..models.InternalEventModel import InternalEventModel
from ..models.MembershipModel import MembershipModel
from ..models.AccountModel import AccountModel
from ..models.RequirementsModel import RequirementsModel
from ..models.EvaluationModel import EvaluationModel
from ..database.connection import convert_boolean_value

from datetime import datetime

'''
Data needed:
 - total approved events
 - pending events
 - rejected events
 - done events
 - total accounts
 - total pending membership
 - total members
 - total active members
'''

def getSummary():
  externalEvents = ExternalEventModel().getAll()
  internalEvents = InternalEventModel().getAll()
  allMembers = MembershipModel().getAll()
  allAccounts = AccountModel().getAll()

  # event information
  totalApprovedEvents = 0
  pendingEvents = 0
  rejectedEvents = 0
  implementedEvent = 0

  # members information
  totalMembers = 0
  totalPendingMembers = 0
  totalActiveMembers = 0

  # already summarized
  totalAccounts = len(allAccounts)

  # convert current time to milliseconds format
  currentTime = int(datetime.now().timestamp()) * 1000

  # external event data extraction
  for external in externalEvents:
    if (external["status"] == "editing"):
      continue

    if (external["status"] == "accepted"):
      totalApprovedEvents += 1
    elif (external["status"] == "submitted"):
      pendingEvents += 1
    else:
      rejectedEvents += 1

    if (external["status"] == "accepted" and (external["durationEnd"] - currentTime) < 0):
      implementedEvent += 1

  # internal event data extraction
  for internal in internalEvents:
    if (internal["status"] == "editing"):
      continue

    if (internal["status"] == "accepted"):
      totalApprovedEvents += 1
    elif (internal["status"] == "submitted"):
      pendingEvents += 1
    else:
      rejectedEvents += 1

    if (internal["status"] == "accepted" and (internal["durationEnd"] - currentTime) < 0):
      implementedEvent += 1

  # membership data extraction
  totalAllMembers = len(allMembers)  # Total members uploaded (all statuses)
  
  for member in allMembers:
    accepted = member.get("accepted")
    active = member.get("active")
    
    # Handle both boolean and integer values for accepted
    if accepted == 1 or accepted == True:
      totalMembers += 1
      # Handle both boolean and integer values for active
      if active == 1 or active == True:
        totalActiveMembers += 1
    elif accepted is None or accepted == "":
      totalPendingMembers += 1

  return {
    "data": {
      "totalApprovedEvents": totalApprovedEvents,
      "pendingEvents": pendingEvents,
      "rejectedEvents": rejectedEvents,
      "implementedEvent": implementedEvent,
      "totalMembers": totalMembers,
      "totalPendingMembers": totalPendingMembers,
      "totalActiveMembers": totalActiveMembers,
      "totalAllMembers": totalAllMembers,  # Total members uploaded (all statuses)
      "totalAccounts": totalAccounts
    },
    "message": "Successfully retrieved system summary"
  }

def getAnalytics():
  # Get data from membership table (real members only)
  # Show ALL accepted and active members with age/sex data
  allMemberships = MembershipModel().getAll()
  ageGroup = {}
  sexGroup = {}

  # Count all accepted and active members with age/sex data
  for membership in allMemberships:
    # Only count accepted and active members
    accepted = membership.get("accepted")
    active = membership.get("active")
    if accepted is None or accepted == False or accepted == 0:
      continue
    if accepted != 1 and accepted != True:
      continue
    if active is None or active == False or active == 0:
      continue
    if active != 1 and active != True:
      continue

    # Get and normalize age from membership (real member data only)
    age_value = membership.get("age")
    if age_value is not None and age_value != "":
      try:
        age_int = int(age_value) if isinstance(age_value, str) else age_value
        # Skip age 0 (invalid data)
        if age_int > 0:
          age_key = str(age_int)
          if age_key not in ageGroup:
            ageGroup[age_key] = 0
          ageGroup[age_key] += 1
      except (ValueError, TypeError):
        pass

    # Get and normalize sex from membership (real member data only)
    sex_value = membership.get("sex")
    if sex_value is not None and sex_value != "":
      sex_normalized = sex_value.strip().title()
      # Only count valid sex values (Male, Female)
      if sex_normalized in ["Male", "Female"]:
        if sex_normalized not in sexGroup:
          sexGroup[sex_normalized] = 0
        sexGroup[sex_normalized] += 1

  return {
    "message": "Successfully retrieved analytics",
    "data": {
      "ageGroup": ageGroup,
      "sexGroup": sexGroup
    },
  }

def getEventInformation(eventId: int, eventType: str):
  try:
    if (eventType == "external"):
      event = ExternalEventModel().get(eventId)
      if not event:
        return ({
          "message": "External event not found"
        }, 404)
    else:
      event = InternalEventModel().get(eventId)
      if not event:
        return ({
          "message": "Internal event not found"
        }, 404)

    # Use database-appropriate boolean value for "accepted"
    accepted_val = convert_boolean_value(1)
    allrequirements = RequirementsModel().getAndSearch(
      ["eventId", "type", "accepted"],
      [eventId, eventType, accepted_val]
    )
    answered = 0

    for requirement in allrequirements:
      try:
        evaluation = EvaluationModel().getAndSearch(["requirementId"], [requirement["id"]])
        if (len(evaluation) > 0):
          evaluation = evaluation[0]
          # Check if evaluation is a dictionary and has the required keys
          if isinstance(evaluation, dict) and evaluation.get("finalized") and evaluation.get("recommendations", "") != "":
            answered += 1
      except Exception as e:
        # Log error but continue processing other requirements
        print(f"Error processing evaluation for requirement {requirement.get('id', 'unknown')}: {e}")
        continue

    return {
      "data": {
        "event": event,
        "registered": len(allrequirements),
        "attended": answered
      },
      "message": "Successfully retrieved event details"
    }
  except Exception as e:
    print(f"Error in getEventInformation: {e}")
    import traceback
    traceback.print_exc()
    return ({
      "message": f"Error retrieving event information: {str(e)}"
    }, 500)

def getActiveMemberData():
  responseSummary = {}
  detailedMembers = []

  # Use database-appropriate boolean values for active/accepted
  active_val = convert_boolean_value(1)
  accepted_val = convert_boolean_value(1)
  activeMembers = MembershipModel().getAndSearch(["active", "accepted"], [active_val, accepted_val])
  current_time_ms = int(datetime.now().timestamp()) * 1000
  ms_per_day = 1000 * 60 * 60 * 24

  for activeMember in activeMembers:
    userEmailIndicator = activeMember["email"]
    userFullname = activeMember["fullname"]
    
    # Only get accepted requirements (real volunteer registrations)
    matchedRequirements = RequirementsModel().getAndSearch(["email", "accepted"], [userEmailIndicator, accepted_val])
    
    # Skip members who haven't actually volunteered (no accepted requirements)
    if len(matchedRequirements) == 0:
      continue

    participation_count = 0
    last_event_ms = 0

    # count attended evaluations and compute last participation date
    for requirement in matchedRequirements:
      matchedEvaluation = EvaluationModel().getAndSearch(["requirementId", "finalized"], [requirement["id"], 1])
      if (len(matchedEvaluation) == 0):
        continue

      matchedEvaluation = matchedEvaluation[0]
      # treat finalized with non-empty recommendations as attended
      if (matchedEvaluation["recommendations"] != ""):
        participation_count += 1

        # fetch event end time for inactivity calculation
        try:
          if (requirement["type"] == "external"):
            event = ExternalEventModel().get(requirement["eventId"])
          else:
            event = InternalEventModel().get(requirement["eventId"])

          if event and event.get("durationEnd"):
            last_event_ms = max(last_event_ms, int(event["durationEnd"]))
        except Exception:
          pass

    responseSummary[userFullname] = participation_count

    inactivity_days = None
    last_event_iso = None
    if last_event_ms and last_event_ms > 0:
      inactivity_days = int((current_time_ms - last_event_ms) / ms_per_day)
      # convert ms to ISO date string (YYYY-MM-DD)
      last_event_iso = datetime.fromtimestamp(last_event_ms / 1000).strftime("%Y-%m-%d")

    detailedMembers.append({
      "name": userFullname,
      "participationCount": participation_count,
      "lastEvent": last_event_iso,
      "inactivityDays": inactivity_days if inactivity_days is not None else None
    })

  return {
    "data": {
      "summary": responseSummary,
      "members": detailedMembers
    },
    "message": "Successfully retrieved member details for event participation"
  }