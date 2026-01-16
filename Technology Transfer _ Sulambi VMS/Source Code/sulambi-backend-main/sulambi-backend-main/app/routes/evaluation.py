from flask import Blueprint, request
from ..middlewares import tokenCheck
from ..middlewares.requiredParams import evaluationParams
from ..controllers import evaluation

EvaluationBlueprint = Blueprint('evaluation', __name__, url_prefix="/evaluation")

@EvaluationBlueprint.get("/")
def getAllEvaluationRoute():
  return evaluation.getAllEvaluation()

@EvaluationBlueprint.get("/personal")
def getPersonalEvaluationRoute():
  return evaluation.getPersonalEvaluationStatus()

@EvaluationBlueprint.get("/event/external/<id>")
def getExternalEventEvaluationsRoute(id):
  return evaluation.getEvaluationByEvent(id, "external")

@EvaluationBlueprint.get("/event/internal/<id>")
def getInternalEventEvaluationsRoute(id):
  return evaluation.getEvaluationByEvent(id, "internal")

@EvaluationBlueprint.get("/validity/<requirementId>")
def getEvaluatable(requirementId):
  return evaluation.isEvaluatable(requirementId)

@EvaluationBlueprint.post("/<requirementId>")
def createEvaluation(requirementId):
  return evaluation.evaluateByRequirement(requirementId)

@EvaluationBlueprint.post("/beneficiary")
def createBeneficiaryEvaluation():
  return evaluation.submitBeneficiaryEvaluation()

@EvaluationBlueprint.before_request
def evaluationMiddleware():
  if (request.method != "OPTIONS"):

    # token check for account session purposes
    if (request.path == '/api/evaluation/personal'):
      userCheck = tokenCheck.authCheckMiddleware()
      if (userCheck != None):
        return userCheck

    if (request.method not in ["GET", "DELETE", "PATCH"]):
      # Skip param check for beneficiary endpoint (public submission)
      if "/api/evaluation/beneficiary" in request.path:
        return None
        
      missingParams = None
      if (("/api/evaluation" in request.path) and (request.view_args and request.view_args.get("requirementId") != None)):
        missingParams = evaluationParams.evaluationParamCheck()

      if (missingParams != None):
        return missingParams
