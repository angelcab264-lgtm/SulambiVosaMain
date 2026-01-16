
from ..models.EvaluationModel import EvaluationModel
from ..models.RequirementsModel import RequirementsModel
from ..models.AccountModel import AccountModel
from ..models.MembershipModel import MembershipModel
from ..models.ExternalEventModel import ExternalEventModel
from ..models.InternalEventModel import InternalEventModel
from flask import request, g

ExternalEventDb = ExternalEventModel()
InternalEventDb = InternalEventModel()
EvaluationDb = EvaluationModel()
RequirementDb = RequirementsModel()
MembershipDb = MembershipModel()
AccountDb = AccountModel()

def getAllEvaluation():
  return {
    "message": "Successfully retrieved all evaluation",
    "data": EvaluationDb.getAll()
  }

def getEvaluationByEvent(eventId: int, eventType: str):
  allEventRequirements = RequirementDb.getAndSearch(["eventId", "type"], [eventId, eventType])
  returnFormat = []

  for requirement in allEventRequirements:
    matchedEvaluation = EvaluationDb.getAndSearch(["requirementId"], [requirement["id"]])
    if (len(matchedEvaluation) == 0):
      continue

    returnFormat.append({
      "requirements": requirement,
      "evaluation": matchedEvaluation[0]
    })

  return {
    "data": returnFormat,
    "message": "Successfully retrieved evaluation data"
  }

def getPersonalEvaluationStatus():
  accountSessionInfo = g.get("accountSessionInfo")
  accountDetails = AccountDb.get(accountSessionInfo["id"])

  if (accountSessionInfo["accountType"] != "member"):
    return ({ "message": "Invalid account type" }, 403)

  if (accountDetails == None):
    return ({ "message": "Session expired" }, 403)

  # retrieve user requirement details
  membershipId = accountDetails["membershipId"]
  userDetails = MembershipDb.get(membershipId)
  userEmail = userDetails["email"]

  # requirements and evaluation has one-to-one relationship
  matchedReqs = RequirementDb.getOrSearch(["email"], [userEmail])

  formattedResponse = []
  for requirement in matchedReqs:
    evaluation = EvaluationDb.getOrSearch(["requirementId"], [requirement["id"]])
    if (len(evaluation) == 0):
      continue

    # user attendance status
    evaluation = evaluation[0]
    attendanceStatus = "registered"
    if (evaluation["finalized"] == 1 and (evaluation["criteria"] != "")):
      attendanceStatus = "attended"
    if (evaluation["finalized"] == 1 and (evaluation["criteria"] == "" or evaluation["criteria"] == None)):
      attendanceStatus = "not-attended"

    # event details extraction
    if (requirement["type"] == "external"):
      eventData = ExternalEventDb.get(requirement["eventId"])
    else:
      eventData = InternalEventDb.get(requirement["eventId"])

    formattedResponse.append({
      "evaluationId": evaluation["id"],
      "event": eventData,
      "requirement": requirement,
      "eventType": requirement["type"],
      "attendanceStatus": attendanceStatus,
    })
  
  return {
    "message": "Successfully retrieved personal evaluation status",
    "data": formattedResponse
  }

def evaluatable(requirementId):
  matchedRequirement = RequirementDb.get(requirementId)
  if (matchedRequirement == None):
    return False
  if (not matchedRequirement["accepted"]):
    return False

  # check if there's an existing evaluation template for the user
  # Allow access if evaluation exists (whether finalized or not)
  matchedEvaluation = EvaluationDb.getAndSearch(["requirementId"], [requirementId])
  if len(matchedEvaluation) == 0:
    return False
  
  # Only allow submission if not finalized yet
  evaluation = matchedEvaluation[0]
  return evaluation["finalized"] == 0 or evaluation["finalized"] == False

def isEvaluatable(requirementId):
  matchedRequirement = RequirementDb.get(requirementId)
  if (matchedRequirement == None):
    return ({"message": "The requirement ID does not exist"}, 404)
  
  if (not matchedRequirement["accepted"]):
    return ({"message": "Your requirement has not been accepted yet"}, 403)
  
  # Check if evaluation exists
  matchedEvaluation = EvaluationDb.getAndSearch(["requirementId"], [requirementId])
  if len(matchedEvaluation) == 0:
    return ({"message": "No evaluation form available for this requirement"}, 404)
  
  evaluation = matchedEvaluation[0]
  isAlreadySubmitted = evaluation["finalized"] == 1 or evaluation["finalized"] == True
  
  if (evaluatable(requirementId)):
    return {
      "message": "The requirement ID provided is valid",
      "data": RequirementDb.get(requirementId),
      "canSubmit": True,
      "alreadySubmitted": False
    }
  elif isAlreadySubmitted:
    return {
      "message": "Evaluation form has already been submitted",
      "data": RequirementDb.get(requirementId),
      "canSubmit": False,
      "alreadySubmitted": True
    }
  else:
    return ({"message": "The provided requirement is not evaluatable"}, 403)


def evaluateByRequirement(requirementId):
  # condition for already existing evaluation
  if (not evaluatable(requirementId)):
    return ({ "message": "The provided requirement ID cannot be evaluated" }, 403)

  # retrieve evaluation template for the requirement-id
  evaluationTemplates = EvaluationDb.getAndSearch(["requirementId"], [requirementId])
  if (len(evaluationTemplates) == 0):
    return ({ "message": "No evaluation template found for this requirement" }, 404)
  
  evaluationTemplate = evaluationTemplates[0]

  # Get requirement details
  requirement = RequirementDb.get(requirementId)
  if requirement == None:
    return ({ "message": "Requirement not found" }, 404)

  # evaluation for the event (derived from requirement id)
  EvaluationDb.updateSpecific(evaluationTemplate["id"],
    ["criteria", "q13", "q14", "comment", "recommendations", "finalized"],
    (
      request.json["criteria"],
      request.json["q13"],
      request.json["q14"],
      request.json["comment"],
      request.json["recommendations"],
      True
    )
  )

  # Save to satisfactionSurveys table for analytics
  try:
    from ..database.connection import cursorInstance
    import json
    from datetime import datetime
    
    conn, cursor = cursorInstance()
    
    # Parse criteria to extract ratings
    criteria_data = request.json.get("criteria", {})
    if isinstance(criteria_data, str):
      try:
        criteria_data = json.loads(criteria_data) if criteria_data.startswith('{') else eval(criteria_data)
      except:
        criteria_data = {}
    
    # Map criteria ratings to 1-5 scale
    rating_map = {
      "Excellent": 5,
      "Very Satisfactory": 4,
      "Satisfactory": 3,
      "Fair": 2,
      "Poor": 1
    }
    
    # Extract ratings
    overall_satisfaction = 0
    organization_rating = 0
    communication_rating = 0
    venue_rating = 0
    materials_rating = 0
    support_rating = 0
    
    if isinstance(criteria_data, dict):
      overall_satisfaction = rating_map.get(criteria_data.get('overall', ''), 0)
      organization_rating = rating_map.get(criteria_data.get('appropriateness', ''), 0)
      communication_rating = rating_map.get(criteria_data.get('expectations', ''), 0)
      materials_rating = rating_map.get(criteria_data.get('materials', ''), 0)
      support_rating = rating_map.get(criteria_data.get('session', ''), 0)
    
    # Use q13/q14 as overall if criteria doesn't have it
    q13 = request.json.get("q13", "")
    q14 = request.json.get("q14", "")
    
    if overall_satisfaction == 0:
      if q13:
        try:
          overall_satisfaction = float(q13)
        except:
          pass
      elif q14:
        try:
          overall_satisfaction = float(q14)
        except:
          pass
    
    # Determine respondent type
    respondent_type = "Volunteer"
    if q14 and not q13:
      respondent_type = "Beneficiary"
    elif q13 and q14:
      respondent_type = "Both"
    
    # Convert q13 and q14 to numbers
    volunteer_rating = None
    beneficiary_rating = None
    
    if q13:
      try:
        volunteer_rating = float(q13)
      except:
        pass
    
    if q14:
      try:
        beneficiary_rating = float(q14)
      except:
        pass
    
    # Get event info
    event_id = requirement.get("eventId")
    event_type = requirement.get("type", "internal")
    
    # Get event title
    event_title = ""
    try:
      from ..database.connection import quote_identifier, convert_placeholders
      event_table = "internalEvents" if event_type == "internal" else "externalEvents"
      quoted_table = quote_identifier(event_table)
      query = f"SELECT title FROM {quoted_table} WHERE id = ?"
      query = convert_placeholders(query)
      cursor.execute(query, (event_id,))
      event_row = cursor.fetchone()
      if event_row:
        event_title = event_row[0]
    except:
      pass
    
    # Check if already exists
    cursor.execute("""
      SELECT id FROM satisfactionSurveys 
      WHERE requirementId = ? AND respondentEmail = ?
    """, (requirementId, requirement.get("email", "")))
    
    if not cursor.fetchone():
      # Insert into satisfactionSurveys
      submitted_at = int(datetime.now().timestamp() * 1000)
      
      cursor.execute("""
        INSERT INTO satisfactionSurveys (
          eventId, eventType, requirementId, respondentType, respondentEmail, respondentName,
          overallSatisfaction, volunteerRating, beneficiaryRating,
          organizationRating, communicationRating, venueRating, materialsRating, supportRating,
          q13, q14, comment, recommendations,
          wouldRecommend, areasForImprovement, positiveAspects,
          submittedAt, finalized
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """, (
        event_id, event_type, requirementId, respondent_type, 
        requirement.get("email", ""), requirement.get("fullname", ""),
        overall_satisfaction, volunteer_rating, beneficiary_rating,
        organization_rating, communication_rating, venue_rating, materials_rating, support_rating,
        q13, q14, request.json.get("comment", ""), request.json.get("recommendations", ""),
        overall_satisfaction >= 4 if overall_satisfaction > 0 else None,  # Would recommend if rating >= 4
        None,  # Areas for improvement
        request.json.get("comment", "") if overall_satisfaction >= 4 else None,  # Positive aspects
        submitted_at, True
      ))
      conn.commit()
    
    conn.close()
  except Exception as e:
    # Don't fail the evaluation if satisfaction survey save fails
    print(f"Error saving to satisfactionSurveys: {e}")

  return {
    "message": "Successfully evaluated event",
    "data": EvaluationDb.get(evaluationTemplate["id"])
  }

def submitBeneficiaryEvaluation():
  """
  Submit beneficiary evaluation directly to satisfactionSurveys table
  This allows beneficiaries to submit feedback without a requirementId
  """
  try:
    from ..database.connection import cursorInstance
    import json
    from datetime import datetime
    
    # Get data from request
    event_id = request.json.get("eventId")
    event_type = request.json.get("eventType", "external")
    criteria_data = request.json.get("criteria", {})
    comment = request.json.get("comment", "")
    recommendations = request.json.get("recommendations", "")
    q13 = request.json.get("q13", "")
    q14 = request.json.get("q14", "")
    
    # Beneficiary data
    overall_satisfaction = 0
    if isinstance(criteria_data, str):
      try:
        criteria_data = json.loads(criteria_data) if criteria_data.startswith('{') else eval(criteria_data)
      except:
        criteria_data = {}
    
    # Map criteria ratings to 1-5 scale
    rating_map = {
      "Excellent": 5,
      "Very Satisfactory": 4,
      "Satisfactory": 3,
      "Fair": 2,
      "Poor": 1
    }
    
    if isinstance(criteria_data, dict):
      overall_satisfaction = rating_map.get(criteria_data.get('overall', ''), 0)
      organization_rating = rating_map.get(criteria_data.get('appropriateness', ''), 0)
      communication_rating = rating_map.get(criteria_data.get('expectations', ''), 0)
      materials_rating = rating_map.get(criteria_data.get('materials', ''), 0)
      support_rating = rating_map.get(criteria_data.get('session', ''), 0)
      venue_rating = rating_map.get(criteria_data.get('venue', ''), 0)
    else:
      organization_rating = 0
      communication_rating = 0
      materials_rating = 0
      support_rating = 0
      venue_rating = 0
    
    # Use q14 or calculated overall satisfaction
    if not overall_satisfaction and q14:
      try:
        overall_satisfaction = float(q14)
      except:
        pass
    
    # For beneficiaries, q14 should contain the satisfaction rating
    # If q14 is a number, use it; otherwise use overall_satisfaction
    beneficiary_rating = None
    if q14:
      try:
        beneficiary_rating = float(q14)
        if not overall_satisfaction:
          overall_satisfaction = beneficiary_rating
      except:
        pass
    
    if not overall_satisfaction:
      overall_satisfaction = 0
    
    conn, cursor = cursorInstance()
    
    # Get event title
    event_title = ""
    try:
      from ..database.connection import quote_identifier, convert_placeholders
      event_table = "internalEvents" if event_type == "internal" else "externalEvents"
      quoted_table = quote_identifier(event_table)
      query = f"SELECT title FROM {quoted_table} WHERE id = ?"
      query = convert_placeholders(query)
      cursor.execute(query, (int(event_id),))
      event_row = cursor.fetchone()
      if event_row:
        event_title = event_row[0]
    except:
      pass
    
    # Insert directly into satisfactionSurveys table
    submitted_at = int(datetime.now().timestamp() * 1000)
    
    # Generate a unique requirementId for tracking (using negative ID or UUID)
    import uuid
    requirement_id = str(uuid.uuid4())
    
    cursor.execute("""
      INSERT INTO satisfactionSurveys (
        eventId, eventType, requirementId, respondentType, respondentEmail, respondentName,
        overallSatisfaction, volunteerRating, beneficiaryRating,
        organizationRating, communicationRating, venueRating, materialsRating, supportRating,
        q13, q14, comment, recommendations,
        wouldRecommend, areasForImprovement, positiveAspects,
        submittedAt, finalized
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
      int(event_id), event_type, requirement_id, "Beneficiary", 
      request.json.get("email", ""), request.json.get("name", ""),
      overall_satisfaction, None, beneficiary_rating or overall_satisfaction,
      organization_rating, communication_rating, venue_rating, materials_rating, support_rating,
      "", q14 or str(overall_satisfaction), comment, recommendations,
      overall_satisfaction >= 4 if overall_satisfaction > 0 else None,
      None,
      comment if overall_satisfaction >= 4 else None,
      submitted_at, True
    ))
    conn.commit()
    conn.close()
    
    return {
      "message": "Beneficiary evaluation submitted successfully",
      "success": True
    }, 200
    
  except Exception as e:
    print(f"Error submitting beneficiary evaluation: {e}")
    import traceback
    traceback.print_exc()
    return {
      "message": f"Error submitting beneficiary evaluation: {str(e)}",
      "success": False,
      "error": str(e)
    }, 500