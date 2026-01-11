from ..database import connection
from .Model import Model
import uuid

class SessionModel(Model):
  def __init__(self):
    super().__init__()
    self.table = "sessions"
    self.primaryKey = "id"
    self.columns = ["token", "userid", "accountType"]

  # overwrite search by token (or ID)
  def get(self, token_or_id):
    # SessionModel.get() can be called with either:
    # 1. A token (string UUID) - for looking up by token
    # 2. An ID (int) - for looking up by primary key (used by Model.create())
    # If it's an integer, use the base class get() method (primary key lookup)
    if isinstance(token_or_id, int):
      return super().get(token_or_id)
    # Otherwise, assume it's a token string and use getOrSearch
    matches = super().getOrSearch([self.primaryKey] + self.columns, [None, token_or_id, None, None])
    if (len(matches)== 0):
      return None
    return matches[0]

  # overwrite last row retrieval
  def getLastPrimaryKey(self):
    return super().getLastPrimaryKey("token")

  # generates new token for logged in
  def create(self, userid: int, accountType: str):
    return super().create((str(uuid.uuid4()), userid, accountType))

  # clears all user token
  def clearUserToken(self, userId):
    conn, cursor = connection.cursorInstance()
    table_name = self._get_table_name()
    query = f"DELETE FROM {table_name} WHERE userid=?"
    query = connection.convert_placeholders(query)
    cursor.execute(query, (userId,))
    conn.close()