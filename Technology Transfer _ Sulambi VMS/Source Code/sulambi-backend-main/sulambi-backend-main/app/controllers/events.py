from ..models.ExternalEventModel import ExternalEventModel
from ..models.InternalEventModel import InternalEventModel
from ..models.ExternalReportModel import ExternalReportModel
from ..models.InternalReportModel import InternalReportModel
from ..models.SignatoriesModel import SignatoriesModel

from ..models.AccountModel import AccountModel
from ..models.RequirementsModel import RequirementsModel
from ..models.EvaluationModel import EvaluationModel

from ..modules.LSIAlgorithm import LSICosineSimilarityMatch

from flask import request, g
from datetime import datetime
from ..database import connection

ExternalEventDb = ExternalEventModel()
InternalEventDb = InternalEventModel()
ExternalReportDb = ExternalReportModel()
InternalReportDb = InternalReportModel()
RequirementsDb  = RequirementsModel()
SignatoriesDb = SignatoriesModel()
EvaluationDb = EvaluationModel()
AccountDb = AccountModel()

def getAll():
  try:
    # manual mapping of user details
    accountSessionInfo = g.get("accountSessionInfo")
    if not accountSessionInfo:
      return ({
        "message": "Authentication required"
      }, 401)
    
    externalEvents = ExternalEventDb.getAll()
    internalEvents = InternalEventDb.getAll()

    combinedEvents = []

    if (accountSessionInfo.get("accountType") == "admin"):
      externalEvents = [event for event in externalEvents if event.get("status") != "editing"]
      internalEvents = [event for event in internalEvents if event.get("status") != "editing"]

    if (accountSessionInfo.get("accountType") == "member"):
      timeNow = int(datetime.now().timestamp() * 1000)
      externalEvents = [event for event in externalEvents if event.get("status") == "accepted" and event.get("durationEnd", 0) - timeNow > 0]
      internalEvents = [event for event in internalEvents if event.get("status") == "accepted" and event.get("durationEnd", 0) - timeNow > 0]

    # Batch fetch all related data to avoid N+1 queries
    # Collect all unique IDs
    all_created_by_ids = set()
    all_signatory_ids = set()
    all_external_event_ids = []
    all_internal_event_ids = []
    
    for event in externalEvents:
      if event.get("createdBy"):
        all_created_by_ids.add(event["createdBy"])
      if event.get("signatoriesId"):
        all_signatory_ids.add(event["signatoriesId"])
      if event.get("id"):
        all_external_event_ids.append(event["id"])
    
    for event in internalEvents:
      if event.get("createdBy"):
        all_created_by_ids.add(event["createdBy"])
      if event.get("signatoriesId"):
        all_signatory_ids.add(event["signatoriesId"])
      if event.get("id"):
        all_internal_event_ids.append(event["id"])
    
    # Batch fetch accounts
    accounts_map = {}
    if all_created_by_ids:
      for account_id in all_created_by_ids:
        try:
          account = AccountDb.get(account_id)
          if account:
            accounts_map[account_id] = account
        except Exception as e:
          print(f"Error fetching account {account_id}: {e}")
    
    # Batch fetch signatories
    signatories_map = {}
    if all_signatory_ids:
      for signatory_id in all_signatory_ids:
        try:
          signatory = SignatoriesDb.get(signatory_id)
          if signatory:
            signatories_map[signatory_id] = signatory
        except Exception as e:
          print(f"Error fetching signatory {signatory_id}: {e}")
    
    # Batch check for reports
    external_reports_map = {}
    if all_external_event_ids:
      for event_id in all_external_event_ids:
        try:
          reports = ExternalReportDb.getAndSearch(["eventId"], [event_id])
          external_reports_map[event_id] = len(reports) > 0
        except Exception as e:
          print(f"Error checking external report for event {event_id}: {e}")
          external_reports_map[event_id] = False
    
    internal_reports_map = {}
    if all_internal_event_ids:
      for event_id in all_internal_event_ids:
        try:
          reports = InternalReportDb.getAndSearch(["eventId"], [event_id])
          internal_reports_map[event_id] = len(reports) > 0
        except Exception as e:
          print(f"Error checking internal report for event {event_id}: {e}")
          internal_reports_map[event_id] = False
    
    # external events formatting using cached data
    for i in range(len(externalEvents)):
      try:
        event_id = externalEvents[i].get("id")
        created_by_id = externalEvents[i].get("createdBy")
        signatory_id = externalEvents[i].get("signatoriesId")
        
        externalEvents[i]["createdBy"] = accounts_map.get(created_by_id) if created_by_id else None
        externalEvents[i]["hasReport"] = external_reports_map.get(event_id, False)
        externalEvents[i]["eventTypeIndicator"] = "external"
        externalEvents[i]["signatoriesId"] = signatories_map.get(signatory_id) if signatory_id else None
      except Exception as e:
        print(f"Error formatting external event {externalEvents[i].get('id', 'unknown')}: {e}")
        # Continue with next event

    # internal events formatting using cached data
    for i in range(len(internalEvents)):
      try:
        event_id = internalEvents[i].get("id")
        created_by_id = internalEvents[i].get("createdBy")
        signatory_id = internalEvents[i].get("signatoriesId")
        
        internalEvents[i]["createdBy"] = accounts_map.get(created_by_id) if created_by_id else None
        internalEvents[i]["hasReport"] = internal_reports_map.get(event_id, False)
        internalEvents[i]["eventTypeIndicator"] = "internal"
        internalEvents[i]["signatoriesId"] = signatories_map.get(signatory_id) if signatory_id else None
      except Exception as e:
        print(f"Error formatting internal event {internalEvents[i].get('id', 'unknown')}: {e}")
        # Continue with next event

    # sort combined events
    combinedEvents: list = externalEvents + internalEvents
    combinedEvents.sort(key=lambda x: x.get("createdAt", 0) or 0, reverse=True)

    return {
      "events": combinedEvents,
      "external": externalEvents,
      "internal": internalEvents,
      "message": "Successfully retrieved all events"
    }
  except Exception as e:
    print(f"Error in getAll events: {e}")
    import traceback
    traceback.print_exc()
    return ({
      "message": f"Error retrieving events: {str(e)}"
    }, 500)

def getOne(id: int, eventType: str):
  try:
    if (eventType == "external"):
      eventData = ExternalEventDb.get(id)
      if not eventData:
        return ({
          "message": "External event not found"
        }, 404)
      return {
        "data": eventData,
        "message": "Successfully retrieved external event"
      }

    if (eventType == "internal"):
      eventData = InternalEventDb.get(id)
      
      if not eventData:
        return ({
          "message": "Internal event not found"
        }, 404)
      
      # Query activity_month_assignments table
      activities = []
      try:
        conn, cursor = connection.cursorInstance()
        from ..database.connection import quote_identifier, convert_placeholders
        table_name = quote_identifier('activity_month_assignments')
        query = f"""
          SELECT activity_name, month 
          FROM {table_name}
          WHERE "eventId" = ?
          ORDER BY activity_name, month
        """
        query = convert_placeholders(query)
        cursor.execute(query, (id,))
        
        assignments = cursor.fetchall()
        
        # Group assignments by activity name
        activities_dict = {}
        for activity_name, month in assignments:
          if activity_name not in activities_dict:
            activities_dict[activity_name] = []
          activities_dict[activity_name].append(month)
        
        # Convert to list format with months array
        activities = [
          {"activity_name": name, "months": sorted(months)}
          for name, months in activities_dict.items()
        ]
        
        conn.close()
      except Exception as e:
        print(f"Error fetching activity_month_assignments: {e}")
        import traceback
        traceback.print_exc()
        # If table doesn't exist or error occurs, activities will remain empty list
      
      # Add activities to event data
      if eventData:
        eventData["activities"] = activities
      
      return {
        "data": eventData,
        "message": "Successfully retrieved internal event"
      }
    
    return ({
      "message": "Invalid event type"
    }, 400)
  except Exception as e:
    print(f"Error in getOne event: {e}")
    import traceback
    traceback.print_exc()
    return ({
      "message": f"Error retrieving event: {str(e)}"
    }, 500)

def getPublicEvents():
  # Public route - no authentication required
  # Get all events that are approved (status == "accepted")
  allExternalEvents = ExternalEventDb.getAll()
  allInternalEvents = InternalEventDb.getAll()
  
  # Debug: Log all events to see what statuses exist
  print("=== DEBUG: All External Events ===")
  for event in allExternalEvents:
    print(f"ID: {event['id']}, Title: {event['title']}, Status: {event['status']}")
  
  print("=== DEBUG: All Internal Events ===")
  for event in allInternalEvents:
    print(f"ID: {event['id']}, Title: {event['title']}, Status: {event['status']}")
  
  # Return ALL approved events (both ongoing and finished) for public access
  # This allows beneficiaries to evaluate finished events - no account/membership required
  # Show events with status "accepted" OR "submitted" (in case admin approved but status wasn't updated)
  # Also check for case-insensitive status matching
  # Filter out only "editing" and "rejected" statuses
  externalEvents = []
  for event in allExternalEvents:
    status_lower = str(event.get("status", "")).lower().strip()
    # Include events that are not in editing or rejected state
    if status_lower not in ["editing", "rejected"]:
      externalEvents.append(event)
      print(f"✅ Including External Event: ID={event['id']}, Title={event['title']}, Status='{event['status']}'")
    else:
      print(f"❌ Excluding External Event: ID={event['id']}, Title={event['title']}, Status='{event['status']}'")
  
  internalEvents = []
  for event in allInternalEvents:
    status_lower = str(event.get("status", "")).lower().strip()
    # Include events that are not in editing or rejected state
    if status_lower not in ["editing", "rejected"]:
      internalEvents.append(event)
      print(f"✅ Including Internal Event: ID={event['id']}, Title={event['title']}, Status='{event['status']}'")
    else:
      print(f"❌ Excluding Internal Event: ID={event['id']}, Title={event['title']}, Status='{event['status']}'")
  
  print(f"=== DEBUG: Filtered External Events (accepted/submitted): {len(externalEvents)} ===")
  print(f"=== DEBUG: Filtered Internal Events (accepted/submitted): {len(internalEvents)} ===")
  
  return {
    "external": externalEvents,
    "internal": internalEvents,
    "message": "Successfully retrieved all public events"
  }

def getAnalysis(id: int, eventType: str):
  eventDetails = None
  if (eventType == "external"):
    eventDetails = ExternalEventDb.get(id)

  if (eventType == "internal"):
    eventDetails = InternalEventDb.get(id)

  if (eventDetails == None):
    return ({ "message": "Cannot find event specified" }, 404)

  matchedRequirements = RequirementsDb.getAndSearch(["eventId", "type"], [id, eventType])
  if (len(matchedRequirements) == 0):
    return ({ "message": "No Requirements for the specified event found" }, 406)

  textToAnalyze = []
  for requirement in matchedRequirements:
    matchedEvaluation = EvaluationDb.getAndSearch(["requirementId"], [requirement["id"]])
    if (len(matchedEvaluation) == 0):
      continue

    matchedEvaluation = matchedEvaluation[0]
    textToAnalyze.append(matchedEvaluation["recommendations"])

  analysis = LSICosineSimilarityMatch(textToAnalyze)
  normalized = averageAnalysis(analysis)

  return {
    "analysis": normalized,
    "message": "Successfully returned analysis"
  }

def createExternalEvent():
  accountSessionInfo = g.get("accountSessionInfo")
  createdSignatories = SignatoriesDb.create(
    approvedBy="NAME",
    preparedBy="NAME",
    recommendingApproval1="NAME",
    recommendingApproval2="NAME",
    reviewedBy="NAME"
  )

  createdExternalEvent = ExternalEventDb.create(
    request.json["extensionServiceType"],
    request.json["title"],
    request.json["location"],
    request.json["durationStart"],
    request.json["durationEnd"],
    request.json["sdg"],
    request.json["orgInvolved"],
    request.json["programInvolved"],
    request.json["projectLeader"],
    request.json["partners"],
    request.json["beneficiaries"],
    request.json["totalCost"],
    request.json["sourceOfFund"],
    request.json["rationale"],
    request.json["objectives"],
    request.json["expectedOutput"],
    request.json["description"],
    request.json["financialPlan"],
    request.json["dutiesOfPartner"],
    request.json["evaluationMechanicsPlan"],
    request.json["sustainabilityPlan"],
    accountSessionInfo["id"],
    "editing",
    request.json["evaluationSendTime"],
    signatoriesId=createdSignatories["id"],
    externalServiceType=request.json["externalServiceType"] or "[]",
    eventProposalType=request.json["eventProposalType"] or "[]"
  )

  return {
    "data": createdExternalEvent,
    "message": "Successfully created a new external event!"
  }

def createInternalEvent():
  accountSessionInfo = g.get("accountSessionInfo")

  createdSignatories = SignatoriesDb.create(
    approvedBy="NAME",
    preparedBy="NAME",
    recommendingApproval1="NAME",
    recommendingApproval2="NAME",
    reviewedBy="NAME"
  )

  createdInternalEvent = InternalEventDb.create(
    request.json["title"],
    request.json["durationStart"],
    request.json["durationEnd"],
    request.json["venue"],
    request.json["modeOfDelivery"],
    request.json["projectTeam"],
    request.json["partner"],
    request.json["participant"],
    request.json["maleTotal"],
    request.json["femaleTotal"],
    request.json["rationale"],
    request.json["objectives"],
    request.json["description"],
    request.json["workPlan"],
    request.json["financialRequirement"],
    request.json["evaluationMechanicsPlan"],
    request.json["sustainabilityPlan"],
    accountSessionInfo["id"],
    "editing",
    False,
    request.json["evaluationSendTime"],
    createdSignatories["id"],
    eventProposalType=request.json.get("eventProposalType") or "[]"
  )

  return {
    "data": createdInternalEvent,
    "message": "Successfully created a new external event!"
  }

def editExternalEventStatus(id, status: str):
  accountSessionInfo = g.get("accountSessionInfo")
  externalEvent = ExternalEventDb.get(id)

  if (externalEvent == None):
    return ({ "message": "The specified event does not exist" }, 404)

  if (externalEvent["createdBy"] != accountSessionInfo["id"] and status == "submitted"):
    return ({ "message": "You have no permission to submit this event" }, 403)

  ExternalEventDb.updateSpecific(id, ["status"], (status,))
  updatedData = ExternalEventDb.get(id)
  return {
    "data": updatedData,
    "message": "Event successfully submitted"
  }

def editInternalEventStatus(id, status: str):
  accountSessionInfo = g.get("accountSessionInfo")
  internalEvent = InternalEventDb.get(id)

  if (internalEvent == None):
    return ({ "message": "The specified event does not exist" }, 404)

  if (internalEvent["createdBy"] != accountSessionInfo["id"] and status == "submitted"):
    return ({ "message": "You have no permission to submit this event" }, 403)

  InternalEventDb.updateSpecific(id, ["status"], (status,))
  updatedData = InternalEventDb.get(id)
  return {
    "data": updatedData,
    "message": "Event successfully submitted"
  }

def makeEventPublic(id, eventType: str):
  accountSessionInfo = g.get("accountSessionInfo")

  # make external event public
  if (eventType == "external"):
    if (ExternalEventDb.get(id) != None):
      ExternalEventDb.updateSpecific(id, ["toPublic"], (True,))
      return { "message": "Successfully made to public" }
    else:
      return ({ "message": "Specified event ID does not exist" }, 404)

  # make internal event public
  if (eventType == "internal"):
    if (InternalEventDb.get(id) != None):
      InternalEventDb.updateSpecific(id, ["toPublic"], (True,))
      return { "message": "Successfully made to public" }
    else:
      return ({ "message": "Specified event ID does not exist" }, 404)

def updateEvent(id, eventType: str):
  accountSessionInfo = g.get("accountSessionInfo")

  if (eventType == "internal"):
      try:
        matchedEvent = InternalEventDb.get(id)
        if (matchedEvent == None): return ({
          "message": "Internal Event provided does not exist"
        }, 404)

        import json
        
        # Ensure workPlan is a string (JSON stringified)
        workPlan = request.json.get("workPlan")
        if workPlan is None:
          workPlan = matchedEvent.get("workPlan", "{}")
        elif isinstance(workPlan, dict):
          workPlan = json.dumps(workPlan)
        elif not isinstance(workPlan, str):
          workPlan = json.dumps(workPlan) if workPlan else "{}"
        # If it's already a string, use as-is

        # Ensure financialRequirement and evaluationMechanicsPlan are strings
        financialRequirement = request.json.get("financialRequirement")
        if financialRequirement is None:
          financialRequirement = matchedEvent.get("financialRequirement", "{}")
        elif isinstance(financialRequirement, dict):
          financialRequirement = json.dumps(financialRequirement)
        elif not isinstance(financialRequirement, str):
          financialRequirement = json.dumps(financialRequirement) if financialRequirement else "{}"

        evaluationMechanicsPlan = request.json.get("evaluationMechanicsPlan")
        if evaluationMechanicsPlan is None:
          evaluationMechanicsPlan = matchedEvent.get("evaluationMechanicsPlan", "{}")
        elif isinstance(evaluationMechanicsPlan, dict):
          evaluationMechanicsPlan = json.dumps(evaluationMechanicsPlan)
        elif not isinstance(evaluationMechanicsPlan, str):
          evaluationMechanicsPlan = json.dumps(evaluationMechanicsPlan) if evaluationMechanicsPlan else "{}"

        # Use request values if provided, otherwise fallback to existing event values
        title = request.json.get("title")
        if title is None:
          title = matchedEvent.get("title", "")
        
        durationStart = request.json.get("durationStart")
        if durationStart is None:
          durationStart = matchedEvent.get("durationStart", 0)
        
        durationEnd = request.json.get("durationEnd")
        if durationEnd is None:
          durationEnd = matchedEvent.get("durationEnd", 0)
        
        venue = request.json.get("venue")
        if venue is None:
          venue = matchedEvent.get("venue", "")
        
        modeOfDelivery = request.json.get("modeOfDelivery")
        if modeOfDelivery is None:
          modeOfDelivery = matchedEvent.get("modeOfDelivery", "")
        
        projectTeam = request.json.get("projectTeam")
        if projectTeam is None:
          projectTeam = matchedEvent.get("projectTeam", "")
        
        partner = request.json.get("partner")
        if partner is None:
          partner = matchedEvent.get("partner", "")
        
        participant = request.json.get("participant")
        if participant is None:
          participant = matchedEvent.get("participant", "")
        
        maleTotal = request.json.get("maleTotal")
        if maleTotal is None:
          maleTotal = matchedEvent.get("maleTotal", "")
        
        femaleTotal = request.json.get("femaleTotal")
        if femaleTotal is None:
          femaleTotal = matchedEvent.get("femaleTotal", "")
        
        rationale = request.json.get("rationale")
        if rationale is None:
          rationale = matchedEvent.get("rationale", "")
        
        objectives = request.json.get("objectives")
        if objectives is None:
          objectives = matchedEvent.get("objectives", "")
        
        description = request.json.get("description")
        if description is None:
          description = matchedEvent.get("description", "")
        
        sustainabilityPlan = request.json.get("sustainabilityPlan")
        if sustainabilityPlan is None:
          sustainabilityPlan = matchedEvent.get("sustainabilityPlan", "")
        
        evaluationSendTime = request.json.get("evaluationSendTime")
        if evaluationSendTime is None:
          evaluationSendTime = matchedEvent.get("evaluationSendTime", 0)
        
        eventProposalType = request.json.get("eventProposalType")
        if eventProposalType is None:
          eventProposalType = matchedEvent.get("eventProposalType", "[]")

        updatedEvent = InternalEventDb.update(id, (
          title,
          durationStart,
          durationEnd,
          venue,
          modeOfDelivery,
          projectTeam,
          partner,
          participant,
          maleTotal,
          femaleTotal,
          rationale,
          objectives,
          description,
          workPlan,
          financialRequirement,
          evaluationMechanicsPlan,
          sustainabilityPlan,
          accountSessionInfo["id"],
          "editing",
          False,
          evaluationSendTime,
          matchedEvent.get("signatoriesId"),
          matchedEvent.get("createdAt"),
          matchedEvent.get("feedback_id"),
          eventProposalType
        ))
        
        return {
          "data": updatedEvent,
          "message": "Successfully updated internal event"
        }
      except Exception as e:
        print(f"Error updating internal event: {e}")
        import traceback
        traceback.print_exc()
        return ({
          "message": f"Error updating event: {str(e)}"
        }, 500)

  if (eventType == "external"):
    matchedEvent = ExternalEventDb.get(id)
    if (matchedEvent == None): return ({
      "message": "External Event provided does not exist"
    }, 404)

    print("created at", matchedEvent.get("createdAt"))

    updatedEvent = ExternalEventDb.update( id, (
      request.json["extensionServiceType"],
      request.json["title"],
      request.json["location"],
      request.json["durationStart"],
      request.json["durationEnd"],
      request.json["sdg"],
      request.json["orgInvolved"],
      request.json["programInvolved"],
      request.json["projectLeader"],
      request.json["partners"],
      request.json["beneficiaries"],
      request.json["totalCost"],
      request.json["sourceOfFund"],
      request.json["rationale"],
      request.json["objectives"],
      request.json["expectedOutput"],
      request.json["description"],
      request.json["financialPlan"],
      request.json["dutiesOfPartner"],
      request.json["evaluationMechanicsPlan"],
      request.json["sustainabilityPlan"],
      accountSessionInfo["id"],
      "editing",
      request.json["evaluationSendTime"],
      False,
      matchedEvent.get("signatoriesId"),
      matchedEvent.get("createdAt"),
      matchedEvent.get("feedback_id"),
      request.json.get("externalServiceType") or "[]",
      request.json.get("eventProposalType") or "[]"
    ))

  return {
    "message": "Successfully updated event",
    "data": updatedEvent
  }

def averageAnalysis(data):
  avg_data = {}
  for key in data:
      for sub_key, value in data[key].items():
          if sub_key not in avg_data:
              avg_data[sub_key] = {"sum": 0, "count": 0}
          avg_data[sub_key]["sum"] += value
          avg_data[sub_key]["count"] += 1

  for sub_key, stats in avg_data.items():
      avg_data[sub_key] = stats["sum"] / stats["count"]

  return avg_data

def normalizeOutput(data):
  total = 0
  data = averageAnalysis(data)
  normalizedValue = {}

  for keys in data:
    total += data[keys]
  for keys in data:
    normalizedValue[keys] = data[keys] / total

  return normalizedValue