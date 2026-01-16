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
  
  def _normalize_column_name(self, column_name):
    """Normalize column name for PostgreSQL (lowercase if not quoted during creation)"""
    # Since columns were created without quotes, they're stored in lowercase in PostgreSQL
    # Convert to lowercase for PostgreSQL queries to match stored column names
    if is_postgresql:
      return column_name.lower()
    return column_name
  
  def _normalize_column_list(self, columns):
    """Normalize column names for PostgreSQL queries"""
    if is_postgresql:
      return [self._normalize_column_name(col) for col in columns]
    return columns
  
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
    # Normalize column names for PostgreSQL (lowercase to match unquoted column names)
    normalized_columns = self._normalize_column_list(columns_list)
    columnQuery = ", ".join(normalized_columns)
    table_name = self._get_table_name()
    normalized_primary_key = self._normalize_column_name(self.primaryKey)
    query = f"SELECT {columnQuery} FROM {table_name} WHERE {normalized_primary_key}=?"
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
    # Normalize column names for PostgreSQL (lowercase to match unquoted column names)
    normalized_columns = self._normalize_column_list(columns_list)
    columnQuery = ", ".join(normalized_columns)
    table_name = self._get_table_name()

    # For requirements table, order by ID descending to get most recent first
    # This assumes the table has an 'id' column (primary key)
    if self.table == "requirements":
      normalized_primary_key = self._normalize_column_name(self.primaryKey)
      query = f"SELECT {columnQuery} FROM {table_name} ORDER BY {normalized_primary_key} DESC"
    else:
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
    # Normalize column names for PostgreSQL (lowercase to match unquoted column names)
    normalized_columns = self._normalize_column_list(columns_list)
    columnQuery = ", ".join(normalized_columns)
    table_name = self._get_table_name()

    # Build query with proper NULL handling - only include non-None values
    conditions = []
    params = []
    for col, val in zip(columns, values):
      if val is not None:
        # Normalize column name for PostgreSQL
        normalized_col = self._normalize_column_name(col)
        conditions.append(f"{normalized_col}=?")
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
    # Normalize column names for PostgreSQL (lowercase to match unquoted column names)
    normalized_columns = self._normalize_column_list(columns_list)
    columnQuery = ", ".join(normalized_columns)
    table_name = self._get_table_name()

    # Normalize column names for PostgreSQL
    queryFormatter = [f"{self._normalize_column_name(col)}=?" for col in columns]
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
    import traceback
    try:
      conn, cursor = connection.cursorInstance()

      if (includePrimaryKey):
        columns_to_use = [self.primaryKey] + self.columns
        queryFormatter = ", ".join('?' * (len(self.columns) + 1))
      else:
        columns_to_use = self.columns
        queryFormatter = ", ".join('?' * len(self.columns))

      # Normalize column names for PostgreSQL (lowercase to match unquoted column names)
      normalized_columns = self._normalize_column_list(columns_to_use)
      columnFormatter = ", ".join(normalized_columns)

      table_name = self._get_table_name()
      query = f"INSERT INTO {table_name} ({columnFormatter}) VALUES ({queryFormatter})"
      query = connection.convert_placeholders(query)
      
      print(f"[MODEL.CREATE] Table: {table_name}")
      print(f"[MODEL.CREATE] Columns ({len(columns_to_use)}): {', '.join(columns_to_use[:5])}{'...' if len(columns_to_use) > 5 else ''}")
      print(f"[MODEL.CREATE] Data tuple length: {len(data)}")
      print(f"[MODEL.CREATE] Query: {query[:200]}{'...' if len(query) > 200 else ''}")
      
      if len(data) != len(columns_to_use):
        error_msg = f"Data tuple length ({len(data)}) does not match columns ({len(columns_to_use)})"
        print(f"[MODEL.CREATE] ERROR: {error_msg}")
        print(f"[MODEL.CREATE] Columns: {columns_to_use}")
        print(f"[MODEL.CREATE] Data: {data}")
        conn.close()
        raise ValueError(error_msg)
      
      # For PostgreSQL, use RETURNING from the start to get ID directly (avoids sequence issues)
      if is_postgresql:
        returning_query = f"INSERT INTO {table_name} ({columnFormatter}) VALUES ({queryFormatter}) RETURNING {self.primaryKey}"
        returning_query = connection.convert_placeholders(returning_query)
        cursor.execute(returning_query, data)
        lastRowId = cursor.fetchone()[0]
        conn.commit()
        print(f"[MODEL.CREATE] Insert successful with ID: {lastRowId}")
        insertedData = self.get(lastRowId)
      else:
        # SQLite: execute and get last row id
        cursor.execute(query, data)
        conn.commit()
        print(f"[MODEL.CREATE] Insert successful")
        lastRowId = self.getLastPrimaryKey()
        insertedData = self.get(lastRowId)

      conn.close()
      return insertedData
    except Exception as e:
      error_str = str(e)
      # Handle PostgreSQL sequence sync issues
      if is_postgresql and "duplicate key value violates unique constraint" in error_str and "_pkey" in error_str:
        print(f"[MODEL.CREATE] PostgreSQL sequence out of sync detected. Attempting to fix...")
        try:
          # CRITICAL: Rollback FIRST before any other operations
          conn.rollback()
          print(f"[MODEL.CREATE] Transaction rolled back")
          
          # Use pg_get_serial_sequence to get the actual sequence name (handles quoted table names correctly)
          # This is more reliable than assuming the naming convention
          sequence_query = "SELECT pg_get_serial_sequence(%s, %s)"
          cursor.execute(sequence_query, (table_name, self.primaryKey))
          seq_result = cursor.fetchone()
          
          if seq_result and seq_result[0]:
            sequence_name = seq_result[0]  # Already includes schema if needed
            print(f"[MODEL.CREATE] Found sequence: {sequence_name}")
          else:
            # Fallback: try standard naming convention (quoted)
            sequence_name = f'"{self.table}_{self.primaryKey}_seq"'
            print(f"[MODEL.CREATE] Using fallback sequence name: {sequence_name}")
          
          # Get max ID from table
          max_id_query = f"SELECT COALESCE(MAX({self.primaryKey}), 0) + 1 FROM {table_name}"
          cursor.execute(max_id_query)
          max_id_result = cursor.fetchone()
          next_id = max_id_result[0] if max_id_result else 1
          
          # Use setval with the sequence name (regclass type - handles quoted names automatically)
          # setval(sequence_name, value, is_called) - false means next value will be exactly 'value'
          cursor.execute("SELECT setval(%s, %s, false)", (sequence_name, next_id))
          conn.commit()
          print(f"[MODEL.CREATE] Sequence reset to {next_id}. Retrying insert...")
          
          # Retry the insert with RETURNING
          returning_query = f"INSERT INTO {table_name} ({columnFormatter}) VALUES ({queryFormatter}) RETURNING {self.primaryKey}"
          returning_query = connection.convert_placeholders(returning_query)
          cursor.execute(returning_query, data)
          lastRowId = cursor.fetchone()[0]
          conn.commit()
          print(f"[MODEL.CREATE] Retry successful with ID: {lastRowId}")
          insertedData = self.get(lastRowId)
          conn.close()
          return insertedData
        except Exception as retry_error:
          print(f"[MODEL.CREATE] Retry failed: {str(retry_error)}")
          traceback.print_exc()
          try:
            conn.rollback()
          except:
            pass
          if 'conn' in locals():
            conn.close()
          raise
      
      print(f"[MODEL.CREATE] ERROR: {error_str}")
      print(f"[MODEL.CREATE] Error type: {type(e).__name__}")
      print(f"[MODEL.CREATE] Table: {self.table}")
      if 'query' in locals():
        print(f"[MODEL.CREATE] Query was: {query[:500]}")
      if 'data' in locals():
        print(f"[MODEL.CREATE] Data length: {len(data)}")
        print(f"[MODEL.CREATE] Data sample: {str(data)[:200]}")
      traceback.print_exc()
      if 'conn' in locals():
        conn.close()
      raise

  # updates the data with the given primary key
  def update(self, key, data: tuple):
    conn, cursor = connection.cursorInstance()
    # Normalize column names for PostgreSQL (lowercase to match unquoted column names)
    normalized_columns = self._normalize_column_list(self.columns)
    queryFormatter = [f"{col}=?" for col in normalized_columns]
    queryFormatter = ", ".join(queryFormatter)

    table_name = self._get_table_name()
    normalized_primary_key = self._normalize_column_name(self.primaryKey)
    query = f"UPDATE {table_name} SET {queryFormatter} WHERE {normalized_primary_key}=?"
    query = connection.convert_placeholders(query)
    print("update query: ", query)
    cursor.execute(query, data + (key,))
    conn.commit()

    return self.get(key)

  # updates specific fields only
  def updateSpecific(self, key, fields: list[str], data: tuple):
    conn, cursor = connection.cursorInstance()
    # Normalize column names for PostgreSQL (lowercase to match unquoted column names)
    normalized_fields = self._normalize_column_list(fields)
    queryFormatter = [f"{col}=?" for col in normalized_fields]
    queryFormatter = ", ".join(queryFormatter)

    table_name = self._get_table_name()
    normalized_primary_key = self._normalize_column_name(self.primaryKey)
    query = f"UPDATE {table_name} SET {queryFormatter} WHERE {normalized_primary_key}=?"
    query = connection.convert_placeholders(query)
    cursor.execute(query, data + (key,))
    conn.commit()

  # deletes one data
  def delete(self, key):
    conn, cursor = connection.cursorInstance()
    tmpDeleted = self.get(key)

    table_name = self._get_table_name()
    # Normalize column name for PostgreSQL (lowercase to match unquoted column names)
    normalized_primary_key = self._normalize_column_name(self.primaryKey)
    query = f"DELETE FROM {table_name} WHERE {normalized_primary_key}=?"
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
    # Normalize column name for PostgreSQL (lowercase to match unquoted column names)
    normalized_key = self._normalize_column_name(overwritingKey)
    query = f"SELECT {normalized_key} FROM {table_name} ORDER BY {normalized_key} DESC LIMIT 1"
    cursor.execute(query)
    lastPrimary = cursor.fetchone()

    conn.close()
    if (lastPrimary == None): return None
    return lastPrimary[0]
