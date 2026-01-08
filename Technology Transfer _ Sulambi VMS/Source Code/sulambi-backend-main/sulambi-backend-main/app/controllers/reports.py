from ..utils.multipartFileWriter import basicFileWriter
from ..models.ExternalEventModel import ExternalEventModel
from ..models.ExternalReportModel import ExternalReportModel
from ..models.InternalEventModel import InternalEventModel
from ..models.InternalReportModel import InternalReportModel
from ..models.RequirementsModel import RequirementsModel
from ..models.EvaluationModel import EvaluationModel
from ..models.SignatoriesModel import SignatoriesModel

from flask import request
import json

ExternalEventDb = ExternalEventModel()
ExternalReportDb = ExternalReportModel()
EvaluationDb = EvaluationModel()
InternalEventDb = InternalEventModel()
InternalReportDb = InternalReportModel()
RequirementsDb = RequirementsModel()
SignatoriesDb = SignatoriesModel()

def getAllReports():
  externalReports = ExternalReportDb.getAll()
  internalReports = InternalReportDb.getAll()

  returnableExternal = []
  returnableInternal = []

  # manual join the external event details
  for report in externalReports:
    matchedEvent = ExternalEventDb.get(report["eventId"])
    if (matchedEvent == None): continue
    report["eventId"] = matchedEvent
    report["signatoriesId"] = SignatoriesDb.get(report["signatoriesId"])
    report["photos"] = report["photos"].split(",") if report["photos"] else []
    report["photoCaptions"] = report["photoCaptions"].split(",") if report.get("photoCaptions") else []
    returnableExternal.append(report)

  # manual join the internal event details
  for report in internalReports:
    matchedEvent = InternalEventDb.get(report["eventId"])
    if (matchedEvent == None): continue
    report["eventId"] = matchedEvent
    report["signatoriesId"] = SignatoriesDb.get(report["signatoriesId"])
    report["photos"] = report["photos"].split(",") if report["photos"] else []
    report["photoCaptions"] = report["photoCaptions"].split(",") if report.get("photoCaptions") else []
    returnableInternal.append(report)

  return {
    "external": returnableExternal,
    "internal": returnableInternal,
    "message": "Successfully retrieved all reports"
  }

def getReportCalculations(eventId: int, eventType: str):
  from ..database.connection import convert_boolean_value
  accepted_value = convert_boolean_value(1)
  registeredUsers = RequirementsDb.getAndSearch(
    ["eventId", "type", "accepted"],
    [eventId, eventType, accepted_value])

  # filter only the one who attended
  onlyAttendedUsers = []
  onlyAttendedEvals = []
  for requirement in registeredUsers:
    evaluationMatch = EvaluationDb.getAndSearch(["requirementId"], [requirement["id"]])
    if (len(evaluationMatch) == 0):
      continue

    evaluationMatch = evaluationMatch[0]
    if (evaluationMatch["finalized"] == 1):
      onlyAttendedUsers.append(requirement)
      onlyAttendedEvals.append(evaluationMatch)

  # get specific signatories for the event mentioned
  signatoriesData = {}
  if (eventType == "external"):
    matchedEvent = ExternalEventDb.get(eventId)
    signId = matchedEvent.get("signatoriesId")
    signatoriesData = SignatoriesDb.get(signId)
  else:
    matchedEvent = InternalEventDb.get(eventId)
    signId = matchedEvent.get("signatoriesId")
    signatoriesData = SignatoriesDb.get(signId)

  if (eventType == "external"):
    # users sex details
    attendedOutsiderMale = 0
    attendedOutsiderFemale = 0
    attendedBsuMale = 0
    attendedBsuFemale = 0

    # users overall experience details
    outsiderExcellent = 0
    outsiderVerySatisfactory = 0
    outsiderSatisfactory = 0
    outsiderFair = 0
    outsiderPoor = 0
    bsuExcellent = 0
    bsuVerySatisfactory = 0
    bsuSatisfactory = 0
    bsuFair = 0
    bsuPoor = 0

    # user overall experience with the timeline
    timelineoutsiderExcellent = 0
    timelineoutsiderVerySatisfactory = 0
    timelineoutsiderSatisfactory = 0
    timelineoutsiderFair = 0
    timelineoutsiderPoor = 0
    timelinebsuExcellent = 0
    timelinebsuVerySatisfactory = 0
    timelinebsuSatisfactory = 0
    timelinebsuFair = 0
    timelinebsuPoor = 0

    # im too tired to think of solution...
    for requirement, evaluation in zip(onlyAttendedUsers, onlyAttendedEvals):
      # count satisfactory of users outside campus
      evalCriteriaString = evaluation["criteria"]
      evalCriteriaDict: dict = safeJsonParser(evalCriteriaString)

      # safe parsable test
      if (not evalCriteriaDict):
        continue

      if (requirement["affiliation"] == "N/A"):
        # count sex outside of campus
        if (requirement["sex"].lower() == "male"):
          attendedOutsiderMale += 1
        else:
          attendedOutsiderFemale += 1

        if ((evalCriteriaDict.get("overall") or "").lower() == "excellent"):
          outsiderExcellent += 1
        if ((evalCriteriaDict.get("overall") or "").lower() == "very satisfactory"):
          outsiderVerySatisfactory += 1
        if ((evalCriteriaDict.get("overall") or "").lower() == "satisfactory"):
          outsiderSatisfactory += 1
        if ((evalCriteriaDict.get("overall") or "").lower() == "fair"):
          outsiderFair += 1
        if ((evalCriteriaDict.get("overall") or "").lower() == "poor"):
          outsiderPoor += 1

        # timeline calculation
        if ((evalCriteriaDict.get("time") or "").lower() == "excellent"):
          timelineoutsiderExcellent += 1
        if ((evalCriteriaDict.get("time") or "").lower() == "very satisfactory"):
          timelineoutsiderVerySatisfactory += 1
        if ((evalCriteriaDict.get("time") or "").lower() == "satisfactory"):
          timelineoutsiderSatisfactory += 1
        if ((evalCriteriaDict.get("time") or "").lower() == "fair"):
          timelineoutsiderFair += 1
        if ((evalCriteriaDict.get("time") or "").lower() == "poor"):
          timelineoutsiderPoor += 1
      else:
        # count bsu sex volunteer
        if ((requirement.get("sex") or "").lower() == "male"):
          attendedBsuMale += 1
        else:
          attendedBsuFemale += 1

        # overall performance
        if ((evalCriteriaDict.get("overall") or "").lower() == "excellent"):
          bsuExcellent += 1
        if ((evalCriteriaDict.get("overall") or "").lower() == "very satisfactory"):
          bsuVerySatisfactory += 1
        if ((evalCriteriaDict.get("overall") or "").lower() == "satisfactory"):
          bsuSatisfactory += 1
        if ((evalCriteriaDict.get("overall") or "").lower() == "fair"):
          bsuFair += 1
        if ((evalCriteriaDict.get("overall") or "").lower() == "poor"):
          bsuPoor += 1

        # timeline performance
        if ((evalCriteriaDict.get("time") or "").lower() == "excellent"):
          timelinebsuExcellent += 1
        if ((evalCriteriaDict.get("time") or "").lower() == "very satisfactory"):
          timelinebsuVerySatisfactory += 1
        if ((evalCriteriaDict.get("time") or "").lower() == "satisfactory"):
          timelinebsuSatisfactory += 1
        if ((evalCriteriaDict.get("time") or "").lower() == "fair"):
          timelinebsuFair += 1
        if ((evalCriteriaDict.get("time") or "").lower() == "poor"):
          timelinebsuPoor += 1

    return {
      "data": {
        "outsider": {
          "sex": {
            "male": attendedOutsiderMale,
            "female": attendedOutsiderFemale
          },
          "evaluation": {
            "overall": {
              "excellent": outsiderExcellent,
              "verySatisfactory": outsiderVerySatisfactory,
              "satisfactory": outsiderSatisfactory,
              "fair": outsiderFair,
              "poor": outsiderPoor
            },
            "timeline": {
              "excellent": timelineoutsiderExcellent,
              "verySatisfactory": timelineoutsiderVerySatisfactory,
              "satisfactory": timelineoutsiderSatisfactory,
              "fair": timelineoutsiderFair,
              "poor": timelineoutsiderPoor
            }
          }
        },
        "insider": {
          "sex": {
            "male": attendedBsuMale,
            "female": attendedBsuFemale
          },
          "evaluation": {
            "overall": {
              "excellent": bsuExcellent,
              "verySatisfactory": bsuVerySatisfactory,
              "satisfactory": bsuSatisfactory,
              "fair": bsuFair,
              "poor": bsuPoor
            },
            "timeline": {
              "excellent": timelinebsuExcellent,
              "verySatisfactory": timelinebsuVerySatisfactory,
              "satisfactory": timelinebsuSatisfactory,
              "fair": timelinebsuFair,
              "poor": timelinebsuPoor
            }
          }
        },
        "signatoriesData": signatoriesData
      },
      "message": "Successfully retrieved event report analytics"
    }
  
  responseFormat = {
    "sex": {
      "male": 0,
      "female": 0
    },
    "evalResult": {
      "male": {
        "excellent": 0,
        "verySatisfactory": 0,
        "satisfactory": 0,
        "fair": 0,
        "poor": 0
      },
      "female": {
        "excellent": 0,
        "verySatisfactory": 0,
        "satisfactory": 0,
        "fair": 0,
        "poor": 0
      }
    },
    "signatoriesData": signatoriesData
  }

  if (eventType == "internal"):
    for requirement, evaluation in zip(onlyAttendedUsers, onlyAttendedEvals):
      evalCriteriaString = evaluation["criteria"]
      evalCriteriaDict: dict = safeJsonParser(evalCriteriaString)

      if (requirement["sex"] == "male"):
        responseFormat["sex"]["male"] += 1
        if (evalCriteriaDict.get("overall").lower() == "excellent"):
          responseFormat["evalResult"]["male"]["excellent"] += 1
        if (evalCriteriaDict.get("overall").lower() == "very satisfactory"):
          responseFormat["evalResult"]["male"]["verySatisfactory"] += 1
        if (evalCriteriaDict.get("overall").lower() == "satisfactory"):
          responseFormat["evalResult"]["male"]["satisfactory"] += 1
        if (evalCriteriaDict.get("overall").lower() == "fair"):
          responseFormat["evalResult"]["male"]["fair"] += 1
        if (evalCriteriaDict.get("overall").lower() == "poor"):
          responseFormat["evalResult"]["male"]["poor"] += 1
      else:
        responseFormat["sex"]["female"] += 1
        if (evalCriteriaDict.get("overall").lower() == "excellent"):
          responseFormat["evalResult"]["female"]["excellent"] += 1
        if (evalCriteriaDict.get("overall").lower() == "very satisfactory"):
          responseFormat["evalResult"]["female"]["verySatisfactory"] += 1
        if (evalCriteriaDict.get("overall").lower() == "satisfactory"):
          responseFormat["evalResult"]["female"]["satisfactory"] += 1
        if (evalCriteriaDict.get("overall").lower() == "fair"):
          responseFormat["evalResult"]["female"]["fair"] += 1
        if (evalCriteriaDict.get("overall").lower() == "poor"):
          responseFormat["evalResult"]["female"]["poor"] += 1

    return {
      "data": responseFormat,
      "message": "Successfully retrieved report analytics"
    }


def getReportByEventId(eventId: int, eventType: str):
  if (eventType == "external"):
    matchedEvent = ExternalEventDb.get(eventId)
    if (matchedEvent == None):
      return ({"message": "Event ID does not exist"}, 404)

    matchedReport = ExternalReportDb.getAndSearch(["eventId"], [id])
    if (matchedReport == None):
      return ({"message": "No report submitted for this event"}, 404)

    return {
      "data": matchedReport,
      "message": "Successfully retrieved report"
    }

  if (eventType == "internal"):
    matchedEvent = InternalEventDb.get(eventId)
    if (matchedEvent == None):
      return ({"message": "Event ID does not exist"}, 404)

    matchedReport = InternalEventDb.getAndSearch(["eventId"], [id])
    if (matchedReport == None):
      return ({"message": "No report submitted for this event"}, 403)

    return {
      "data": matchedReport,
      "message": "Successfully retrieved report"
    }

def createReport(eventId: int, eventType: str):
  photoPath = basicFileWriter([])
  photoNames = ",".join([photoPath[key] for key in photoPath])
  
  # Extract photo captions from form data
  photoCaptions = []
  for key in photoPath:
    captionKey = f"photo_caption_{list(photoPath.keys()).index(key)}"
    caption = request.form.get(captionKey, "")
    photoCaptions.append(caption)
  photoCaptionsStr = ",".join(photoCaptions)

  # checks if report has been submitted to the event id
  if (eventType == "external"):
    matchedEvent = ExternalEventDb.get(eventId)

    if (matchedEvent == None):
      return ({"message": "Event ID does not exist"}, 404)

    matchedReport = ExternalReportDb.getAndSearch(["eventId"], [eventId])
    if (len(matchedReport) > 0):
      return ({"message": "A report for this event has already been submitted"}, 403)


    # creation of external report
    createdReport = ExternalReportDb.create(
      eventId=eventId,
      narrative=request.form.get("narrative"),
      photos=photoNames,
      photoCaptions=photoCaptionsStr,
      signatoriesId=matchedEvent.get("signatoriesId")
    )

    # assigning of signatories
    # ExternalReportDb.updateSpecific([])
    createdReport["eventId"] = matchedEvent
    return {
      "data": createdReport,
      "message": "Successfully submitted report"
    }

  # checks if report has been submitted to the event id
  if (eventType == "internal"):
    matchedEvent = InternalEventDb.get(eventId)

    if (matchedEvent == None):
      return ({"message": "Event ID does not exist"}, 404)

    matchedReport = InternalReportDb.getAndSearch(["eventId"], [eventId])
    if (len(matchedReport) > 0):
      return ({"message": "A report for this event has already been submitted"}, 403)

    createdReport = InternalReportDb.create(
      eventId=eventId,
      narrative=request.form.get("narrative"),
      budgetUtilized=request.form.get("budgetUtilized") or "",
      budgetUtilizedSrc=request.form.get("budgetUtilizedSrc") or "",
      psAttribution=request.form.get("psAttribution") or "",
      psAttributionSrc=request.form.get("psAttributionSrc") or "",
      photos=photoNames,
      photoCaptions=photoCaptionsStr,
      signatoriesId=matchedEvent.get("signatoriesId")
    )

    createdReport["eventId"] = matchedEvent
    return {
      "data": createdReport,
      "message": "Successfully submitted report"
    }

def deleteReport(reportId: int, reportType: str):
  """Delete a report by ID and type"""
  try:
    print(f"Attempting to delete {reportType} report with ID: {reportId}")
    
    if reportType == "external":
      # Check if report exists
      existingReport = ExternalReportDb.get(reportId)
      if not existingReport:
        print(f"External report with ID {reportId} not found")
        return ({"message": "External report not found"}, 404)
      
      print(f"Found external report: {existingReport}")
      # Delete the report
      deletedReport = ExternalReportDb.delete(reportId)
      print(f"Successfully deleted external report: {deletedReport}")
      return {
        "message": "External report deleted successfully",
        "deletedReport": deletedReport
      }
    
    elif reportType == "internal":
      # Check if report exists
      existingReport = InternalReportDb.get(reportId)
      if not existingReport:
        print(f"Internal report with ID {reportId} not found")
        return ({"message": "Internal report not found"}, 404)
      
      print(f"Found internal report: {existingReport}")
      # Delete the report
      deletedReport = InternalReportDb.delete(reportId)
      print(f"Successfully deleted internal report: {deletedReport}")
      return {
        "message": "Internal report deleted successfully",
        "deletedReport": deletedReport
      }
    
    else:
      print(f"Invalid report type: {reportType}")
      return ({"message": "Invalid report type"}, 400)
      
  except Exception as e:
    print(f"Error deleting {reportType} report with ID {reportId}: {str(e)}")
    return ({"message": f"Error deleting report: {str(e)}"}, 500)


def safeJsonParser(jsonStr: str) -> dict:
  try:
    return json.loads(jsonStr)
  except:
    return False