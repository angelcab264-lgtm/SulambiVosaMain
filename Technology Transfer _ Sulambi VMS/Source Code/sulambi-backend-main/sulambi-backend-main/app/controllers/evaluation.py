
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
    
    # Check if already exists - handle both SQLite and PostgreSQL
    from ..database.connection import DATABASE_URL, quote_identifier, convert_placeholders, convert_boolean_value
    is_postgresql = DATABASE_URL and DATABASE_URL.startswith('postgresql://')
    
    if is_postgresql:
      check_query = """
        SELECT id FROM "satisfactionSurveys" 
        WHERE requirementid = %s AND respondentemail = %s
      """
    else:
      check_query = """
        SELECT id FROM satisfactionSurveys 
        WHERE requirementId = ? AND respondentEmail = ?
      """
    
    cursor.execute(check_query, (requirementId, requirement.get("email", "")))
    
    if not cursor.fetchone():
      # Insert into satisfactionSurveys
      submitted_at = int(datetime.now().timestamp() * 1000)
      
      if is_postgresql:
        # PostgreSQL: Use quoted mixed-case column names to match what analytics.py uses
        # The table has mixed-case columns (eventId, submittedAt as BIGINT, etc.) based on analytics.py queries
        insert_query = """
          INSERT INTO "satisfactionSurveys" (
            "eventId", "eventType", "requirementId", "respondentType", "respondentEmail", "respondentName",
            "overallSatisfaction", "volunteerRating", "beneficiaryRating",
            "organizationRating", "communicationRating", "venueRating", "materialsRating", "supportRating",
            q13, q14, comment, recommendations,
            "wouldRecommend", "areasForImprovement", "positiveAspects",
            "submittedAt", finalized
          ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        finalized_val = convert_boolean_value(True)
        would_recommend_val = convert_boolean_value(overall_satisfaction >= 4 if overall_satisfaction > 0 else None)
      else:
        # SQLite: use unquoted identifiers and ? placeholders
        insert_query = """
          INSERT INTO satisfactionSurveys (
            eventId, eventType, requirementId, respondentType, respondentEmail, respondentName,
            overallSatisfaction, volunteerRating, beneficiaryRating,
            organizationRating, communicationRating, venueRating, materialsRating, supportRating,
            q13, q14, comment, recommendations,
            wouldRecommend, areasForImprovement, positiveAspects,
            submittedAt, finalized
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        finalized_val = True
        would_recommend_val = overall_satisfaction >= 4 if overall_satisfaction > 0 else None
      
      cursor.execute(insert_query, (
        event_id, event_type, requirementId, respondent_type, 
        requirement.get("email", ""), requirement.get("fullname", ""),
        overall_satisfaction, volunteer_rating, beneficiary_rating,
        organization_rating, communication_rating, venue_rating, materials_rating, support_rating,
        q13, q14, request.json.get("comment", ""), request.json.get("recommendations", ""),
        would_recommend_val,
        None,  # Areas for improvement
        request.json.get("comment", "") if overall_satisfaction >= 4 else None,  # Positive aspects
        submitted_at, finalized_val
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
    comment = request.json.get("comment", "") or ""
    recommendations = request.json.get("recommendations", "") or ""
    q13 = request.json.get("q13", "") or ""
    q14 = request.json.get("q14", "") or ""
    
    # Validate event_id - PostgreSQL INTEGER range: -2,147,483,648 to 2,147,483,647
    try:
      # Handle both string and int event_id
      if isinstance(event_id, str):
        event_id = int(event_id)
      elif event_id is not None:
        event_id = int(event_id)
      else:
        event_id = None
      
      if event_id is None or event_id <= 0:
        return {
          "message": "Invalid event ID",
          "success": False,
          "error": "eventId is required and must be a positive integer"
        }, 400
      
      # Check if event_id is within PostgreSQL INTEGER range
      INTEGER_MAX = 2147483647
      INTEGER_MIN = -2147483648
      if event_id > INTEGER_MAX or event_id < INTEGER_MIN:
        return {
          "message": "Invalid event ID",
          "success": False,
          "error": f"eventId {event_id} is out of range for PostgreSQL INTEGER type (must be between {INTEGER_MIN} and {INTEGER_MAX})"
        }, 400
    except (ValueError, TypeError) as e:
      return {
        "message": "Invalid event ID",
        "success": False,
        "error": f"eventId must be a valid integer: {str(e)}"
      }, 400
    
    # Beneficiary data
    overall_satisfaction = 0.0
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
      overall_satisfaction = float(rating_map.get(criteria_data.get('overall', ''), 0))
      organization_rating = float(rating_map.get(criteria_data.get('appropriateness', ''), 0))
      communication_rating = float(rating_map.get(criteria_data.get('expectations', ''), 0))
      materials_rating = float(rating_map.get(criteria_data.get('materials', ''), 0))
      support_rating = float(rating_map.get(criteria_data.get('session', ''), 0))
      venue_rating = float(rating_map.get(criteria_data.get('venue', ''), 0))
    else:
      organization_rating = 0.0
      communication_rating = 0.0
      materials_rating = 0.0
      support_rating = 0.0
      venue_rating = 0.0
    
    # Use q14 or calculated overall satisfaction
    if overall_satisfaction == 0.0 and q14:
      try:
        overall_satisfaction = float(q14)
      except (ValueError, TypeError):
        pass
    
    # For beneficiaries, q14 should contain the satisfaction rating
    # If q14 is a number, use it; otherwise use overall_satisfaction
    beneficiary_rating = None
    if q14:
      try:
        beneficiary_rating = float(q14)
        if overall_satisfaction == 0.0:
          overall_satisfaction = beneficiary_rating
      except (ValueError, TypeError):
        pass
    
    if overall_satisfaction == 0.0:
      overall_satisfaction = 0.0
    
    conn, cursor = cursorInstance()
    
    # Verify event exists and get event title
    event_title = ""
    try:
      from ..database.connection import quote_identifier, convert_placeholders
      import os
      DATABASE_URL = os.getenv("DATABASE_URL")
      is_postgresql = DATABASE_URL and DATABASE_URL.startswith('postgresql://')
      
      event_table = "internalEvents" if event_type == "internal" else "externalEvents"
      quoted_table = quote_identifier(event_table)
      
      # For PostgreSQL, quote column names if they might be mixed case
      # For SQLite, use unquoted column names
      if is_postgresql:
        # In PostgreSQL, unquoted identifiers are lowercased, but we'll use quoted to be safe
        # Since CREATE TABLE uses lowercase 'id' and 'title', we can use them unquoted
        query = f'SELECT title FROM {quoted_table} WHERE id = %s'
      else:
        query = f"SELECT title FROM {quoted_table} WHERE id = ?"
      
      cursor.execute(query, (event_id,))
      event_row = cursor.fetchone()
      if event_row:
        event_title = event_row[0]
      else:
        # Log the issue but don't fail - allow submission even if event lookup fails
        print(f"Warning: Event with ID {event_id} and type {event_type} not found in {event_table}, but continuing with submission")
        # Don't return 404 - allow the submission to proceed
        # The event might exist but the query might have issues, or it's a new event
    except Exception as e:
      print(f"Error checking event: {e}")
      import traceback
      traceback.print_exc()
      # Continue anyway - event check is not critical for submission
    
    # Insert directly into satisfactionSurveys table
    submitted_at = int(datetime.now().timestamp() * 1000)
    
    # Generate a unique requirementId for tracking (using negative ID or UUID)
    import uuid
    requirement_id = str(uuid.uuid4())
    
    # Check if PostgreSQL and use appropriate syntax
    from ..database.connection import DATABASE_URL, quote_identifier, convert_placeholders, convert_boolean_value
    is_postgresql = DATABASE_URL and DATABASE_URL.startswith('postgresql://')
    
    # Get table name with proper quoting
    table_name = quote_identifier('satisfactionSurveys')
    
    if is_postgresql:
      # PostgreSQL: Use quoted mixed-case column names - EXACT same as evaluateByRequirement
      insert_query = """
        INSERT INTO "satisfactionSurveys" (
          "eventId", "eventType", "requirementId", "respondentType", "respondentEmail", "respondentName",
          "overallSatisfaction", "volunteerRating", "beneficiaryRating",
          "organizationRating", "communicationRating", "venueRating", "materialsRating", "supportRating",
          q13, q14, comment, recommendations,
          "wouldRecommend", "areasForImprovement", "positiveAspects",
          "submittedAt", finalized
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
      """
    else:
      # SQLite: use unquoted identifiers and ? placeholders
      insert_query = f"""
        INSERT INTO {table_name} (
          eventId, eventType, requirementId, respondentType, respondentEmail, respondentName,
          overallSatisfaction, volunteerRating, beneficiaryRating,
          organizationRating, communicationRating, venueRating, materialsRating, supportRating,
          q13, q14, comment, recommendations,
          wouldRecommend, areasForImprovement, positiveAspects,
          submittedAt, finalized
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """
    
    # Convert boolean for database compatibility - SAME as evaluateByRequirement
    if is_postgresql:
      finalized_val = convert_boolean_value(True)
      would_recommend_val = convert_boolean_value(overall_satisfaction >= 4 if overall_satisfaction > 0 else None)
    else:
      finalized_val = True
      would_recommend_val = overall_satisfaction >= 4 if overall_satisfaction > 0 else None
    
    # Execute INSERT - SAME parameter order as evaluateByRequirement
    cursor.execute(insert_query, (
      event_id, event_type, requirement_id, "Beneficiary",
      request.json.get("email", "") or "", request.json.get("name", "") or "",
      overall_satisfaction, None, beneficiary_rating,
      organization_rating, communication_rating, venue_rating, materials_rating, support_rating,
      q13, q14, comment, recommendations,
      would_recommend_val,
      None,  # Areas for improvement
      comment if overall_satisfaction >= 4 else None,  # Positive aspects
      submitted_at, finalized_val
    ))
      conn.commit()
      conn.close()
      
      return {
        "message": "Beneficiary evaluation submitted successfully",
        "success": True
      }, 200
    except Exception as db_error:
      conn.rollback()
      conn.close()
      error_msg = str(db_error)
      print(f"Database error submitting beneficiary evaluation: {db_error}")
      import traceback
      traceback.print_exc()
      
      # Provide more specific error message
      param_details = {
        "event_id": event_id,
        "event_id_type": type(event_id).__name__ if event_id is not None else "None",
        "submitted_at": submitted_at,
        "submitted_at_type": type(submitted_at).__name__ if 'submitted_at' in locals() else "unknown",
        "overall_satisfaction": overall_satisfaction_val if 'overall_satisfaction_val' in locals() else "unknown",
        "beneficiary_rating": beneficiary_rating_val if 'beneficiary_rating_val' in locals() else "unknown",
      }
      
      if "integer out of range" in error_msg.lower():
        param_details["event_id_range_check"] = f"INTEGER range: -2147483648 to 2147483647, value: {event_id}"
        param_details["submitted_at_range_check"] = f"BIGINT range: -9223372036854775808 to 9223372036854775807, value: {submitted_at}"
        print(f"[DEBUG] Integer out of range error details: {param_details}")
        
        return {
          "message": f"Database error: {error_msg}",
          "success": False,
          "error": error_msg,
          "details": param_details
        }, 500
      
      return {
        "message": f"Error submitting beneficiary evaluation: {error_msg}",
        "success": False,
        "error": error_msg,
        "details": param_details
      }, 500
    
  except Exception as e:
    print(f"Error submitting beneficiary evaluation: {e}")
    import traceback
    traceback.print_exc()
    return {
      "message": f"Error submitting beneficiary evaluation: {str(e)}",
      "success": False,
      "error": str(e)
    }, 500