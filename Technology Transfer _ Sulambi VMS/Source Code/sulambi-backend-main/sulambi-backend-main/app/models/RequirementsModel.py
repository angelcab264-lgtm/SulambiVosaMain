from .Model import Model
from uuid import uuid4

class RequirementsModel(Model):
  def __init__(self):
    super().__init__()

    self.table = "requirements"
    self.primaryKey = "id"
    self.columns = [
      "medCert",
      "waiver",
      "eventId",
      "affiliation",
      "type",
      "curriculum",
      "destination",
      "firstAid",
      "fees",
      "personnelInCharge",
      "personnelRole",
      "fullname",
      "email",
      "srcode",
      "age",
      "birthday",
      "sex",
      "campus",
      "collegeDept",
      "yrlevelprogram",
      "address",
      "contactNum",
      "fblink",
      "accepted"
    ]

  # overwrite search by token
  def get(self, token: str) -> dict | None:
    matches = super().getOrSearch([self.primaryKey] + self.columns, [token] + ([None] * len(self.columns)))
    if (len(matches)== 0):
      return None
    return matches[0]

  def create(self,
      # required info (filenames)
      medCert: str, waiver: str, eventId: int,
      eventType: str,

      # optional info
      curriculum: str, destination: str,
      firstAid: str, fees: str,
      personnelInCharge: str,
      personnelRole: str,

      # personal info
      fullname: str,
      email: str, srcode: str, age: int | None,  # Changed from str to int | None for PostgreSQL INTEGER column
      birthday: str, sex: str, campus: str,
      collegeDept: str, yrlevelprogram: str,
      address: str, contactNum: str, fblink: str,

      # requirement status
      accepted: bool=None,
      affiliation: str="N/A"):

    requirementToken = str(uuid4())
    return super().create((
      requirementToken,
      medCert, waiver,
      eventId, affiliation, eventType,
      curriculum, destination,
      firstAid, fees,
      personnelInCharge,
      personnelRole, fullname,
      email, srcode, age,  # This is now int | None, which PostgreSQL can handle
      birthday, sex, campus,
      collegeDept, yrlevelprogram,
      address, contactNum, fblink,
      accepted
    ), True)
