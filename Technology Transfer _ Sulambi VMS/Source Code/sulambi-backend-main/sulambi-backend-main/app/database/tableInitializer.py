from . import connection
from dotenv import load_dotenv
import os

load_dotenv()
DEBUG = os.getenv("DEBUG") == "True"
conn, cursor = connection.cursorInstance()

# Detect database type
DATABASE_URL = os.getenv("DATABASE_URL")
is_postgresql = DATABASE_URL and DATABASE_URL.startswith('postgresql://')

# Helper function to convert SQLite syntax to PostgreSQL
def convert_sql(sql):
    """Convert SQLite syntax to PostgreSQL if needed"""
    if not is_postgresql:
        return sql
    
    # Replace SQLite-specific syntax with PostgreSQL
    sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
    sql = sql.replace('STRING', 'VARCHAR(255)')
    sql = sql.replace('DATETIME DEFAULT CURRENT_TIMESTAMP', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    # Convert timestamp columns that store milliseconds to BIGINT (they exceed INTEGER range)
    # These columns store Unix timestamps in milliseconds
    import re
    timestamp_columns = [
        'durationStart', 'durationEnd', 'evaluationSendTime',  # Events tables
        'firstEventDate', 'lastEventDate', 'calculatedAt', 'lastUpdated'  # volunteerParticipationHistory
    ]
    for col in timestamp_columns:
        # Match: column_name INTEGER (with optional NOT NULL, etc.)
        pattern = rf'\b{col}\s+INTEGER\b'
        sql = re.sub(pattern, f'{col} BIGINT', sql, flags=re.IGNORECASE)
    
    # Quote table names in CREATE TABLE statements to preserve case in PostgreSQL
    # Match: CREATE TABLE IF NOT EXISTS tableName( or CREATE TABLE tableName(
    sql = re.sub(
        r'CREATE TABLE (IF NOT EXISTS )?(\w+)\s*\(',
        lambda m: f'CREATE TABLE {m.group(1) or ""}"{m.group(2)}"(',
        sql,
        flags=re.IGNORECASE
    )
    
    # PostgreSQL uses single quotes for string literals, not double quotes
    # Replace all double-quoted strings in DEFAULT clauses
    # Match DEFAULT "value" and replace with DEFAULT 'value'
    sql = re.sub(r'DEFAULT\s+"([^"]+)"', r"DEFAULT '\1'", sql)
    # Handle placeholders: SQLite uses ?, PostgreSQL uses %s
    # But we'll handle this in execute calls separately
    return sql

# Helper function to execute with correct placeholders
def execute_sql(sql, params=None):
    """Execute SQL with correct placeholder syntax"""
    sql = convert_sql(sql)
    if params:
        # Convert ? to %s for PostgreSQL
        if is_postgresql:
            sql = sql.replace('?', '%s')
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)

"""
NOTE: I will not add any relations to tables, but I will be doing these stuffs
on logic-level of the application for faster implementation
"""


####################
#  ACCOUNTS TABLE  #
####################
DEBUG and print("[*] Initializing accounts table...", end="")
execute_sql("""
  CREATE TABLE IF NOT EXISTS accounts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username STRING NOT NULL,
    password STRING NOT NULL,
    accountType STRING NOT NULL,
    membershipId INTEGER,
    active BOOLEAN DEFAULT TRUE
  )
""")

DEBUG and print("Done")

####################
#  SESSIONS TABLE  #
####################
DEBUG and print("[*] Initializing sessions table...", end="")
execute_sql("""
  CREATE TABLE IF NOT EXISTS sessions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token STRING UNIQUE,
    userid INTEGER NOT NULL,
    accountType STRING NOT NULL
  )
""")

DEBUG and print("Done")

######################
#  MEMBERSHIP TABLE  #
######################
DEBUG and print("[*] Initializing membership table...", end="")
execute_sql("""
  CREATE TABLE IF NOT EXISTS membership(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    applyingAs VARCHAR NOT NULL,
    volunterismExperience BOOLEAN NOT NULL,
    weekdaysTimeDevotion VARCHAR NOT NULL,
    weekendsTimeDevotion VARCHAR NOT NULL,
    areasOfInterest TEXT NOT NULL,

    fullname STRING NOT NULL,
    email STRING NOT NULL,
    affiliation STRING DEFAULT 'N/A',
    srcode STRING NOT NULL,
    age INTEGER NOT NULL,
    birthday STRING NOT NULL,
    sex STRING NOT NULL,
    campus STRING NOT NULL,
    collegeDept STRING NOT NULL,
    yrlevelprogram STRING NOT NULL,
    address TEXT NOT NULL,
    contactNum STRING NOT NULL,
    fblink STRING NOT NULL,
    bloodType VARCHAR NOT NULL,
    bloodDonation STRING NOT NULL,

    medicalCondition TEXT NOT NULL,
    paymentOption TEXT NOT NULL,

    username STRING NOT NULL,
    password STRING NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    accepted BOOLEAN,

    volunteerExpQ1 TEXT,
    volunteerExpQ2 TEXT,
    volunteerExpProof STRING,

    reasonQ1 TEXT,
    reasonQ2 TEXT
  )
""")

DEBUG and print("Done")

########################
#  REQUIREMENTS TABLE  #
########################
# for passing requirements for helpdesk/events
DEBUG and print("[*] Initializing requirements table...", end="")
execute_sql("""
  CREATE TABLE IF NOT EXISTS requirements(
    id STRING UNIQUE,
    medCert STRING NOT NULL,
    waiver STRING NOT NULL,
    type STRING NOT NULL,

    eventId INTEGER NOT NULL,
    affiliation STRING DEFAULT 'N/A',
    curriculum STRING,
    destination STRING,
    firstAid STRING,
    fees STRING,
    personnelInCharge STRING,
    personnelRole STRING,

    fullname STRING,
    email STRING,
    srcode STRING,
    age INTEGER,
    birthday STRING,
    sex STRING,
    campus STRING,
    collegeDept STRING,
    yrlevelprogram STRING,
    address TEXT,
    contactNum STRING,
    fblink STRING,

    accepted BOOLEAN
  )
""")

DEBUG and print("Done")

###########################
#  INTERNAL EVENTS TABLE  #
###########################
# for events proposal
DEBUG and print("[*] Initializing internalEvents table...", end="")
execute_sql("""
  CREATE TABLE IF NOT EXISTS internalEvents(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title STRING NOT NULL,
    durationStart INTEGER NOT NULL,
    durationEnd INTEGER NOT NULL,
    venue STRING NOT NULL,
    modeOfDelivery STRING NOT NULL,
    projectTeam TEXT NOT NULL,
    partner STRING NOT NULL,
    participant STRING NOT NULL,
    maleTotal INTEGER NOT NULL,
    femaleTotal INTEGER NOT NULL,
    rationale TEXT NOT NULL,
    objectives TEXT NOT NULL,
    description TEXT NOT NULL,
    workPlan TEXT NOT NULL,
    financialRequirement TEXT NOT NULL,
    evaluationMechanicsPlan TEXT NOT NULL,
    sustainabilityPlan TEXT NOT NULL,
    createdBy INTEGER NOT NULL,
    status STRING NOT NULL,
    toPublic BOOLEAN NOT NULL,
    evaluationSendTime INTEGER NOT NULL,

    feedback_id INTEGER,
    eventProposalType STRING,
    signatoriesId INTEGER,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
  )
""")

DEBUG and print("Done")

###########################
#  EXTERNAL EVENTS TABLE  #
###########################
# internal events
DEBUG and print("[*] Initializing externalEvents table...", end="")
execute_sql("""
  CREATE TABLE IF NOT EXISTS externalEvents(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    extensionServiceType STRING NOT NULL,
    title STRING NOT NULL,
    location STRING NOT NULL,
    durationStart INTEGER NOT NULL,
    durationEnd INTEGER NOT NULL,
    sdg STRING NOT NULL,
    orgInvolved STRING NOT NULL,
    programInvolved STRING NOT NULL,
    projectLeader STRING NOT NULL,
    partners STRING NOT NULL,
    beneficiaries STRING NOT NULL,
    totalCost REAL NOT NULL,
    sourceOfFund STRING NOT NULL,
    rationale TEXT NOT NULL,
    objectives TEXT NOT NULL,
    expectedOutput TEXT NOT NULL,
    description TEXT NOT NULL,
    financialPlan TEXT NOT NULL,
    dutiesOfPartner TEXT NOT NULL,
    evaluationMechanicsPlan TEXT NOT NULL,
    sustainabilityPlan TEXT NOT NULL,
    createdBy INTEGER NOT NULL,
    status STRING NOT NULL,
    evaluationSendTime INTEGER NOT NULL,
    toPublic BOOLEAN DEFAULT FALSE,

    feedback_id INTEGER,
    externalServiceType STRING,
    eventProposalType STRING,

    signatoriesId INTEGER,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
  )
""")

DEBUG and print("Done")

###########################
#  EXTERNAL REPORT TABLE  #
###########################
# for external event proposal
DEBUG and print("[*] Initializing externalReport table...", end="")
execute_sql("""
  CREATE TABLE IF NOT EXISTS externalReport(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eventId INTEGER NOT NULL,
    narrative TEXT NOT NULL,
    photos TEXT NOT NULL,
    photoCaptions TEXT,
    signatoriesId INTEGER
  )
""")
DEBUG and print("Done")

###########################
#  INTERNAL REPORT TABLE  #
###########################
# internal events report
DEBUG and print("[*] Initializing internalReport table...", end="")
execute_sql("""
  CREATE TABLE IF NOT EXISTS internalReport(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eventId INTEGER NOT NULL,
    narrative TEXT NOT NULL,
    budgetUtilized INTEGER NOT NULL,
    budgetUtilizedSrc STRING NOT NULL,
    psAttribution INTEGER NOT NULL,
    psAttributionSrc STRING NOT NULL,
    photos TEXT NOT NULL,
    photoCaptions TEXT,
    signatoriesId INTEGER
  )
""")

DEBUG and print("Done")

####################
#  HELPDESK TABLE  #
####################
DEBUG and print("[*] Initializing helpdesk table...", end="")
execute_sql("""
  CREATE TABLE IF NOT EXISTS helpdesk(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email STRING NOT NULL,
    nameOfRequestee STRING NOT NULL,
    addressOfRequestee STRING NOT NULL,
    contactOfRequestee STRING NOT NULL,
    fblinkOfRequestee STRING NOT NULL,
    donationType INTEGER NOT NULL,

    nameOfMoneyRecipient STRING NOT NULL,
    addressOfRecipient STRING NOT NULL,
    contactOfRecipient STRING NOT NULL,
    gcashOrBankOfRecipient STRING,
    reason STRING NOT NULL,
    bloodTypeOfRecipient STRING,
    necessaryFiles TEXT NOT NULL,

    donationNeeded TEXT NOT NULL
  )
""")

DEBUG and print("Done")


###########################
#  EVENT EVALUATION FORM  #
###########################
DEBUG and print("[*] Initializing evaluation table...", end="")
execute_sql("""
  CREATE TABLE IF NOT EXISTS evaluation(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criteria TEXT NOT NULL,
    q13 TEXT NOT NULL,
    q14 TEXT NOT NULL,
    comment TEXT NOT NULL,
    recommendations TEXT NOT NULL,
    requirementId TEXT NOT NULL,
    finalized BOOLEAN DEFAULT FALSE
  )
""")

DEBUG and print("Done")

#######################
#  SIGNATORIES TABLE  #
#######################
DEBUG and print("[*] Initializing eventSignatories table...")
execute_sql("""
  CREATE TABLE IF NOT EXISTS eventSignatories(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    preparedBy STRING DEFAULT "NAME",
    reviewedBy STRING DEFAULT "NAME",
    recommendingApproval1 STRING DEFAULT "NAME",
    recommendingApproval2 STRING DEFAULT "NAME",
    approvedBy STRING DEFAULT "NAME",

    preparedTitle STRING DEFAULT "Asst. Director, GAD Advocacies/GAD Head Secretariat/Coordinator",
    reviewedTitle STRING DEFAULT "Director, Extension Services/Head, Extension Services",
    approvedTitle STRING DEFAULT "University President/Chancellor",
    recommendingSignatory1 STRING DEFAULT "Vice President/Vice Chancellor for Research, Development and Extension Services",
    recommendingSignatory2 STRING DEFAULT "Vice President/Vice Chancellor for Administration and Finance"
  )
""")
DEBUG and print("Done")

####################
#  FEEDBACK TABLE  #
####################
DEBUG and print("[*] Initializing feedback table...")
execute_sql("""
  CREATE TABLE IF NOT EXISTS feedback(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    state STRING
  )
""")

####################
#  ACTIVITY MONTH ASSIGNMENTS TABLE  #
####################
DEBUG and print("[*] Initializing activity_month_assignments table...")
execute_sql("""
  CREATE TABLE IF NOT EXISTS activity_month_assignments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eventId INTEGER NOT NULL,
    activity_name TEXT NOT NULL,
    month INTEGER NOT NULL,
    FOREIGN KEY (eventId) REFERENCES internalEvents(id)
  )
""")
DEBUG and print("Done")

###########################
#  SATISFACTION SURVEYS TABLE  #
###########################
# For storing satisfaction survey responses from volunteers and beneficiaries
DEBUG and print("[*] Initializing satisfactionSurveys table...")
execute_sql("""
  CREATE TABLE IF NOT EXISTS satisfactionSurveys(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eventId INTEGER NOT NULL,
    eventType STRING NOT NULL,
    requirementId STRING,
    respondentType STRING NOT NULL,
    respondentEmail STRING NOT NULL,
    respondentName STRING,
    
    -- Satisfaction Ratings (1-5 scale)
    overallSatisfaction REAL NOT NULL,
    volunteerRating REAL,
    beneficiaryRating REAL,
    
    -- Detailed Ratings
    organizationRating REAL,
    communicationRating REAL,
    venueRating REAL,
    materialsRating REAL,
    supportRating REAL,
    
    -- Survey Questions
    q13 TEXT,
    q14 TEXT,
    comment TEXT,
    recommendations TEXT,
    
    -- Additional Feedback
    wouldRecommend BOOLEAN,
    areasForImprovement TEXT,
    positiveAspects TEXT,
    
    -- Metadata
    submittedAt INTEGER NOT NULL,
    finalized BOOLEAN DEFAULT FALSE
  )
""")
DEBUG and print("Done")

###########################
#  DROPOUT RISK ASSESSMENT TABLE  #
###########################
# For tracking volunteer engagement and dropout risk metrics
DEBUG and print("[*] Initializing dropoutRiskAssessment table...")
execute_sql("""
  CREATE TABLE IF NOT EXISTS dropoutRiskAssessment(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    membershipId INTEGER NOT NULL,
    volunteerEmail STRING NOT NULL,
    volunteerName STRING NOT NULL,
    
    -- Engagement Metrics
    totalEventsAttended INTEGER DEFAULT 0,
    eventsLastSemester INTEGER DEFAULT 0,
    eventsLastMonth INTEGER DEFAULT 0,
    averageEventsPerSemester REAL DEFAULT 0,
    
    -- Inactivity Tracking
    lastEventDate INTEGER,
    daysSinceLastEvent INTEGER DEFAULT 0,
    longestInactivityPeriod INTEGER DEFAULT 0,
    
    -- Risk Assessment
    riskScore INTEGER DEFAULT 0,
    riskLevel STRING DEFAULT 'Low',
    riskFactors TEXT,
    
    -- Engagement Trends
    engagementTrend STRING DEFAULT 'Stable',
    participationRate REAL DEFAULT 0,
    retentionProbability REAL DEFAULT 100,
    
    -- Semester Data
    semester STRING,
    calculatedAt INTEGER NOT NULL,
    
    -- Flags
    isAtRisk BOOLEAN DEFAULT FALSE,
    interventionNeeded BOOLEAN DEFAULT FALSE,
    notes TEXT
  )
""")
DEBUG and print("Done")

###########################
#  VOLUNTEER PARTICIPATION HISTORY TABLE  #
###########################
# For tracking volunteer participation history by semester
# Tracks events joined vs attended per semester for consistency monitoring
DEBUG and print("[*] Initializing volunteerParticipationHistory table...")
execute_sql("""
  CREATE TABLE IF NOT EXISTS volunteerParticipationHistory(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    volunteerEmail STRING NOT NULL,
    volunteerName STRING NOT NULL,
    membershipId INTEGER,
    
    -- Semester Information
    semester STRING NOT NULL,
    semesterYear INTEGER NOT NULL,
    semesterNumber INTEGER NOT NULL,
    
    -- Participation Metrics
    eventsJoined INTEGER DEFAULT 0,
    eventsAttended INTEGER DEFAULT 0,
    eventsDropped INTEGER DEFAULT 0,
    attendanceRate REAL DEFAULT 0,
    
    -- Event Details
    firstEventDate INTEGER,
    lastEventDate INTEGER,
    daysActiveInSemester INTEGER DEFAULT 0,
    
    -- Consistency Metrics
    participationConsistency STRING DEFAULT 'Regular',
    engagementLevel STRING DEFAULT 'Active',
    
    -- Timestamps
    calculatedAt INTEGER NOT NULL,
    lastUpdated INTEGER NOT NULL,
    
    -- Indexes for faster queries
    UNIQUE(volunteerEmail, semester)
  )
""")
DEBUG and print("Done")

# Create index for faster semester-based queries
DEBUG and print("[*] Creating indexes for volunteerParticipationHistory...")
execute_sql("CREATE INDEX IF NOT EXISTS idx_volunteer_email ON volunteerParticipationHistory(volunteerEmail)")
execute_sql("CREATE INDEX IF NOT EXISTS idx_semester ON volunteerParticipationHistory(semester)")
execute_sql("CREATE INDEX IF NOT EXISTS idx_last_event_date ON volunteerParticipationHistory(lastEventDate)")
DEBUG and print("Done")


# Insert the initial account values here
initialAccounts = [
  ("Admin", "sulambi@2024", "admin"),
  ("Sulambi-Officer", "password@2024", "officer"),
]

# DEBUG and print("[*] Inserting accounts...")
for account in initialAccounts:
  # Check if account already exists before inserting
  query = "SELECT COUNT(*) FROM accounts WHERE username = ?" if not is_postgresql else "SELECT COUNT(*) FROM accounts WHERE username = %s"
  cursor.execute(query, (account[0],))
  if cursor.fetchone()[0] == 0:
    DEBUG and print("[+] Account:", account[0])
    insert_query = "INSERT INTO accounts (username, password, accountType) VALUES (?, ?, ?)" if not is_postgresql else "INSERT INTO accounts (username, password, accountType) VALUES (%s, %s, %s)"
    cursor.execute(insert_query, account)
  else:
    DEBUG and print("[!] Account already exists:", account[0])

# DEBUG and print("[+] Done")
conn.commit()
conn.close()
