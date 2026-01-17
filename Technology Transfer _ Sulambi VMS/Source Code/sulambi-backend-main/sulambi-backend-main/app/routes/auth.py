from flask import Blueprint, request
from ..controllers import auth
from ..middlewares.requiredParams import authParams

AuthBlueprint = Blueprint('auth', __name__, url_prefix="/auth")

@AuthBlueprint.post('/login')
def authLoginRoute():
  return auth.login()

@AuthBlueprint.post('/register')
def authRegisterRoute():
  return auth.register()

@AuthBlueprint.delete('/logout/<usertoken>')
def authLogoutRoute(usertoken):
  return auth.logout(usertoken)

@AuthBlueprint.post('/check-status')
def checkApplicationStatusRoute():
  return auth.checkApplicationStatus()

@AuthBlueprint.get('/test-email')
def testEmailRoute():
  return auth.testEmail()

@AuthBlueprint.before_request
def authMiddleware():
  if (request.method not in ["OPTIONS", "GET", "DELETE"]):
    missingParam = None
    
    if (request.path == '/api/auth/login'):
      missingParam = authParams.loginParamCheck()

    if (request.path == '/api/auth/register'):
      missingParam = authParams.registerParamCheck()

    if (missingParam != None):
      return missingParam
