from ..database import connection
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Detect if we're using PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")
is_postgresql = DATABASE_URL and DATABASE_URL.startswith('postgresql://')

class Model:
  def __init__(self):
    self.table = ""
    self.primaryKey = ""
    self.columns = []
    self.filteredColumns = []
    self.createdAtCol = ""
  
  def _quote_identifier(self, identifier):
    """Quote identifier for PostgreSQL, leave unquoted for SQLite"""
    if is_postgresql:
      return f'"{identifier}"'
    return identifier
  
  def _get_table_name(self):
    """Get properly quoted table name based on database type"""
    return self._quote_identifier(self.table)

  def parseResponse(self, response: tuple | None, overwriteColumns=[]):
    if (response == None): return None
    if (len(overwriteColumns) == 0):
      completeColumns = [self.primaryKey] + self.columns
    else:
      completeColumns = overwriteColumns

    if (len(response) != len(completeColumns)):
      raise Exception("Response not equal to specified column(s)")

    singleParsed = {}
    for index, coldata in enumerate(response):
      if (completeColumns[index] in self.filteredColumns):
        singleParsed[completeColumns[index]] = "**redacted**"
        continue

      if (self.createdAtCol != "" and completeColumns[index] == self.createdAtCol):
        try:
          if (coldata != None):
            if (isinstance(coldata, int)):
              # Handle different timestamp formats
              # If timestamp is very large (> year 2100 in seconds), it's likely in milliseconds
              # If timestamp is very small (< year 2000 in seconds), it might be in a different format
              timestamp_seconds = coldata
              
              # Check if it's in milliseconds (timestamp > year 2000 in milliseconds)
              if coldata > 946684800000:  # Jan 1, 2000 in milliseconds
                timestamp_seconds = coldata / 1000
              # Check if it's in microseconds (timestamp > year 2000 in microseconds)
              elif coldata > 946684800000000:  # Jan 1, 2000 in microseconds
                timestamp_seconds = coldata / 1000000
              # If it's already in seconds but very small, it might be a relative timestamp
              elif coldata < 0:
                # Invalid timestamp, use current time
                timestamp_seconds = datetime.now().timestamp()
              
              try:
                coldata: datetime = datetime.fromtimestamp(timestamp_seconds)
              except (ValueError, OSError):
                # If timestamp conversion fails, use current time
                coldata = datetime.now()
            elif isinstance(coldata, datetime):
              # Already a datetime object, use as-is
              pass
            elif isinstance(coldata, str):
              try:
                # Try parsing as datetime string first
                coldata: datetime = datetime.strptime(coldata, "%Y-%m-%d %H:%M:%S")
              except ValueError:
                # Try alternative format
                try:
                  coldata: datetime = datetime.fromisoformat(coldata.replace('Z', '+00:00'))
                except ValueError:
                  # If parsing fails, set to current time
                  coldata = datetime.now()
            else:
              # Unknown type, use current time
              coldata = datetime.now()
            
            # Convert to timestamp (in milliseconds)
            if coldata:
              try:
                singleParsed[completeColumns[index]] = int(coldata.timestamp() * 1000)
              except (ValueError, OSError):
                # If timestamp conversion fails, use current time
                singleParsed[completeColumns[index]] = int(datetime.now().timestamp() * 1000)
            else:
              singleParsed[completeColumns[index]] = int(datetime.now().timestamp() * 1000)
          else:
            singleParsed[completeColumns[index]] = int(datetime.now().timestamp() * 1000)
        except Exception as e:
          print(f"Error parsing datetime for column {completeColumns[index]}: {e}, value: {coldata}")
          # Default to current time if parsing fails
          try:
            singleParsed[completeColumns[index]] = int(datetime.now().timestamp() * 1000)
          except:
            singleParsed[completeColumns[index]] = 0
      else:
        singleParsed[completeColumns[index]] = coldata
    return singleParsed

  def parseManyResponse(self, response: list[tuple], overwriteColumns=[]):
    if (len(response) == 0): return []
    manyParsed = []
    for coldata in response:
      manyParsed.append(self.parseResponse(coldata, overwriteColumns))
    return manyParsed

  # gets a single data through the use of the primary key
  def get(self, key):
    conn, cursor = connection.cursorInstance()
    columns_list = [self.primaryKey] + self.columns
    columnQuery = ", ".join([self._quote_identifier(col) for col in columns_list])
    table_name = self._get_table_name()
    primary_key_quoted = self._quote_identifier(self.primaryKey)
    query = f"SELECT {columnQuery} FROM {table_name} WHERE {primary_key_quoted}=?"
    query = connection.convert_placeholders(query)

    cursor.execute(query, (key, ))
    dbResponse = cursor.fetchone()

    response = self.parseResponse(dbResponse)
    conn.close()
    return response

  # returns all the data in the table
  def getAll(self):
    conn, cursor = connection.cursorInstance()
    columns_list = [self.primaryKey] + self.columns
    columnQuery = ", ".join([self._quote_identifier(col) for col in columns_list])
    table_name = self._get_table_name()

    query = f"SELECT {columnQuery} FROM {table_name}"

    cursor.execute(query)
    dbResponse = cursor.fetchall()

    response = self.parseManyResponse(dbResponse)
    conn.close()
    return response

  # gets a specific value by matching its column values
  def getOrSearch(self, columns: list, values: list):
    conn, cursor = connection.cursorInstance()
    columns_list = [self.primaryKey] + self.columns
    columnQuery = ", ".join([self._quote_identifier(col) for col in columns_list])
    table_name = self._get_table_name()

    # Build query with proper NULL handling - only include non-None values
    conditions = []
    params = []
    for col, val in zip(columns, values):
      if val is not None:
        col_quoted = self._quote_identifier(col)
        conditions.append(f"{col_quoted}=?")
        params.append(val)
    
    # If no conditions, return all records
    if not conditions:
      query = f"SELECT {columnQuery} FROM {table_name}"
    else:
      queryFormatter = " OR ".join(conditions)
      query = f"SELECT {columnQuery} FROM {table_name} WHERE {queryFormatter}"
      query = connection.convert_placeholders(query)
      query = connection.convert_boolean_condition(query)

    if params:
      cursor.execute(query, params)
    else:
      cursor.execute(query)
    dbResponse = cursor.fetchall()

    response = self.parseManyResponse(dbResponse, [self.primaryKey] + self.columns)
    conn.close()
    return response

  # gets a specific value by matching its column values
  def getAndSearch(self, columns: list, values: list):
    conn, cursor = connection.cursorInstance()
    columns_list = [self.primaryKey] + self.columns
    columnQuery = ", ".join([self._quote_identifier(col) for col in columns_list])
    table_name = self._get_table_name()

    queryFormatter = [f"{self._quote_identifier(col)}=?" for col in columns]
    queryFormatter = " AND ".join(queryFormatter)
    query = f"SELECT {columnQuery} FROM {table_name} WHERE {queryFormatter}"
    query = connection.convert_placeholders(query)

    cursor.execute(query, values)
    dbResponse = cursor.fetchall()

    response = self.parseManyResponse(dbResponse, [self.primaryKey] + self.columns)
    conn.close()
    return response

  # creates a new data with the provided columns and data value
  def create(self, data: tuple, includePrimaryKey=False):
    conn, cursor = connection.cursorInstance()

    if (includePrimaryKey):
      columns_to_use = [self.primaryKey] + self.columns
      queryFormatter = ", ".join('?' * (len(self.columns) + 1))
    else:
      columns_to_use = self.columns
      queryFormatter = ", ".join('?' * len(self.columns))

    # Quote column names for PostgreSQL to preserve case
    columnFormatter = ", ".join([self._quote_identifier(col) for col in columns_to_use])

    table_name = self._get_table_name()
    query = f"INSERT INTO {table_name} ({columnFormatter}) VALUES ({queryFormatter})"
    query = connection.convert_placeholders(query)
    print(query)
    cursor.execute(query, data)
    conn.commit()

    lastRowId = self.getLastPrimaryKey()
    insertedData = self.get(lastRowId)

    conn.close()
    return insertedData

  # updates the data with the given primary key
  def update(self, key, data: tuple):
    conn, cursor = connection.cursorInstance()
    queryFormatter = [f"{self._quote_identifier(col)}=?" for col in self.columns]
    queryFormatter = ", ".join(queryFormatter)

    table_name = self._get_table_name()
    primary_key_quoted = self._quote_identifier(self.primaryKey)
    query = f"UPDATE {table_name} SET {queryFormatter} WHERE {primary_key_quoted}=?"
    query = connection.convert_placeholders(query)
    print("update query: ", query)
    cursor.execute(query, data + (key,))
    conn.commit()

    return self.get(key)

  # updates specific fields only
  def updateSpecific(self, key, fields: list[str], data: tuple):
    conn, cursor = connection.cursorInstance()
    queryFormatter = [f"{self._quote_identifier(col)}=?" for col in fields]
    queryFormatter = ", ".join(queryFormatter)

    table_name = self._get_table_name()
    primary_key_quoted = self._quote_identifier(self.primaryKey)
    query = f"UPDATE {table_name} SET {queryFormatter} WHERE {primary_key_quoted}=?"
    query = connection.convert_placeholders(query)
    cursor.execute(query, data + (key,))
    conn.commit()

  # deletes one data
  def delete(self, key):
    conn, cursor = connection.cursorInstance()
    tmpDeleted = self.get(key)

    table_name = self._get_table_name()
    primary_key_quoted = self._quote_identifier(self.primaryKey)
    query = f"DELETE FROM {table_name} WHERE {primary_key_quoted}=?"
    query = connection.convert_placeholders(query)
    cursor.execute(query, (key,))
    conn.commit()
    return tmpDeleted

  # last row primary key
  def getLastPrimaryKey(self, overwritingKey=""):
    if (overwritingKey == ""):
      overwritingKey = self.primaryKey

    conn, cursor = connection.cursorInstance()
    table_name = self._get_table_name()
    query = f"SELECT {overwritingKey} FROM {table_name} ORDER BY id DESC LIMIT 1"
    cursor.execute(query)
    lastPrimary = cursor.fetchone()

    conn.close()
    if (lastPrimary == None): return None
    return lastPrimary[0]
