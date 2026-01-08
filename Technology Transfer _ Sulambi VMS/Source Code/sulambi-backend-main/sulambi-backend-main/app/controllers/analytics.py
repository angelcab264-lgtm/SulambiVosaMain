from flask import jsonify
from ..models.InternalEventModel import InternalEventModel
from ..models.ExternalEventModel import ExternalEventModel
from ..models.MembershipModel import MembershipModel
from ..models.EvaluationModel import EvaluationModel
from ..models.FeedbackModel import FeedbackModel
import random
import math
import json
from datetime import datetime, timedelta
import time

# Initialize database models
InternalEventDb = InternalEventModel()
ExternalEventDb = ExternalEventModel()
MembershipDb = MembershipModel()
EvaluationDb = EvaluationModel()
FeedbackDb = FeedbackModel()

def getEventSuccessAnalytics():
    """
    Calculate event success rates based on past events
    Returns completion, attendance, and satisfaction metrics
    """
    try:
        # Get all events
        internalEvents = InternalEventDb.getAll()
        externalEvents = ExternalEventDb.getAll()
        
        # Calculate metrics
        totalEvents = len(internalEvents) + len(externalEvents)
        completedEvents = 0
        cancelledEvents = 0
        inProgressEvents = 0
        totalAttendance = 0
        totalSatisfaction = 0
        satisfactionCount = 0
        
        # Process internal events
        for event in internalEvents:
            if event.get('status') == 'completed':
                completedEvents += 1
            elif event.get('status') == 'cancelled':
                cancelledEvents += 1
            else:
                inProgressEvents += 1
            
            # Calculate attendance (mock calculation)
            if event.get('maxParticipants'):
                attendance = random.randint(60, 95)  # Mock attendance percentage
                totalAttendance += attendance
            
            # Get satisfaction from evaluations
            evaluations = EvaluationDb.getAndSearch(['eventId'], [event.get('id')])
            for evaluation in evaluations:
                if evaluation.get('finalized') and evaluation.get('criteria'):
                    try:
                        criteria = eval(evaluation.get('criteria', '{}'))
                        if 'satisfaction' in criteria:
                            totalSatisfaction += criteria['satisfaction']
                            satisfactionCount += 1
                    except:
                        pass
        
        # Process external events
        for event in externalEvents:
            if event.get('status') == 'completed':
                completedEvents += 1
            elif event.get('status') == 'cancelled':
                cancelledEvents += 1
            else:
                inProgressEvents += 1
            
            # Calculate attendance (mock calculation)
            if event.get('maxParticipants'):
                attendance = random.randint(60, 95)  # Mock attendance percentage
                totalAttendance += attendance
            
            # Get satisfaction from evaluations
            evaluations = EvaluationDb.getAndSearch(['eventId'], [event.get('id')])
            for evaluation in evaluations:
                if evaluation.get('finalized') and evaluation.get('criteria'):
                    try:
                        criteria = eval(evaluation.get('criteria', '{}'))
                        if 'satisfaction' in criteria:
                            totalSatisfaction += criteria['satisfaction']
                            satisfactionCount += 1
                    except:
                        pass
        
        # Calculate averages
        averageAttendance = totalAttendance / max(totalEvents, 1)
        averageSatisfaction = totalSatisfaction / max(satisfactionCount, 1) if satisfactionCount > 0 else 4.0
        
        return {
            "success": True,
            "data": {
                "completed": completedEvents,
                "cancelled": cancelledEvents,
                "inProgress": inProgressEvents,
                "totalEvents": totalEvents,
                "averageAttendance": round(averageAttendance, 1),
                "averageSatisfaction": round(averageSatisfaction, 1)
            },
            "message": "Event success analytics retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve event success analytics"
        }

def getVolunteerDropoutAnalytics(year=None):
    """
    Calculate volunteer dropout risk based on volunteerParticipationHistory table
    - Uses pre-calculated semester-by-semester participation data
    - Tracks most recent participation dates
    - Identifies declining engagement patterns
    """
    try:
        from ..database.connection import cursorInstance
        from datetime import datetime
        
        conn, cursor = cursorInstance()
        
        from ..database.connection import quote_identifier
        membership_table = quote_identifier('membership')
        vph_table = quote_identifier('volunteerParticipationHistory')
        
        # Check if volunteerParticipationHistory table exists
        # Use database-agnostic query - detect from connection type
        from ..database.connection import is_postgresql_connection, DATABASE_URL
        is_postgresql = (DATABASE_URL and DATABASE_URL.startswith('postgresql://')) or is_postgresql_connection(conn)
        
        table_exists = None
        try:
            if is_postgresql:
                # PostgreSQL: use information_schema
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'volunteerParticipationHistory'
                """)
            else:
                # SQLite: use sqlite_master
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='volunteerParticipationHistory'
                """)
            table_exists = cursor.fetchone()
        except Exception as e:
            # If SQLite query fails on PostgreSQL, try PostgreSQL query
            if 'sqlite_master' in str(e) or 'relation' in str(e).lower():
                print(f"[DROPOUT ANALYTICS] Detected PostgreSQL from error, retrying with information_schema")
                try:
                    cursor.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'volunteerParticipationHistory'
                    """)
                    table_exists = cursor.fetchone()
                except Exception as e2:
                    print(f"[DROPOUT ANALYTICS] Error checking table existence: {e2}")
                    table_exists = None
            else:
                print(f"[DROPOUT ANALYTICS] Error checking table existence: {e}")
                table_exists = None
        
        # Always ensure we're reading from membership table
        # Check if we have active members in membership table
        from ..database.connection import convert_boolean_condition
        query = f"""
            SELECT COUNT(*) FROM {membership_table} 
            WHERE accepted = 1 AND active = 1
        """
        query = convert_boolean_condition(query)
        cursor.execute(query)
        member_count = cursor.fetchone()[0] or 0
        
        if member_count == 0:
            conn.close()
            return {
                "success": True,
                "data": {
                    "semesterData": [],
                    "atRiskVolunteers": []
                },
                "message": "No active members found in membership table"
            }
        
        # Get semester data from participation history table (if it exists)
        # Otherwise use legacy method
        if not table_exists:
            # Fallback to old method if table doesn't exist
            return getVolunteerDropoutAnalyticsLegacy(year)

        # If the table exists but has no rows, the analytics will look empty.
        # In that case, fall back to legacy computation from requirements/evaluation,
        # which directly reflects "joined but didn't answer the form" as dropouts.
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {vph_table}")
            vph_count = cursor.fetchone()[0] or 0
        except Exception:
            vph_count = 0
        if vph_count == 0:
            conn.close()
            return getVolunteerDropoutAnalyticsLegacy(year)
        
        # Get semester data from participation history table
        try:
            from ..database.connection import convert_placeholders
            if year:
                query = f"""
                    SELECT semester, 
                           COUNT(DISTINCT volunteerEmail) as total_volunteers,
                           SUM(eventsJoined) as total_joined,
                           SUM(eventsAttended) as total_attended,
                           SUM(eventsDropped) as total_dropped,
                           AVG(attendanceRate) as avg_attendance_rate
                    FROM {vph_table}
                    WHERE semesterYear = ?
                    GROUP BY semester
                    ORDER BY semester
                """
                query = convert_placeholders(query)
                cursor.execute(query, (int(year),))
            else:
                cursor.execute(f"""
                    SELECT semester, 
                           COUNT(DISTINCT volunteerEmail) as total_volunteers,
                           SUM(eventsJoined) as total_joined,
                           SUM(eventsAttended) as total_attended,
                           SUM(eventsDropped) as total_dropped,
                           AVG(attendanceRate) as avg_attendance_rate
                    FROM {vph_table}
                    GROUP BY semester
                    ORDER BY semester
                """)
            
            semester_rows = cursor.fetchall()
        except Exception as semester_query_error:
            print(f"[DROPOUT ANALYTICS] Semester query failed: {semester_query_error}")
            print(f"[DROPOUT ANALYTICS] Using empty semester data")
            semester_rows = []
        
        # Format semester data
        semester_data = []
        for row in semester_rows:
            semester, total_volunteers, total_joined, total_attended, total_dropped, avg_attendance_rate = row
            # Calculate average events per volunteer
            events_per_volunteer = round((total_attended / total_volunteers), 1) if total_volunteers > 0 else 0
            
            semester_data.append({
                "semester": semester,
                "events": events_per_volunteer,
                "volunteers": total_volunteers,
                "attended": total_attended,
                "dropouts": total_dropped
            })
        
        # Get at-risk volunteers (those with low attendance or no recent participation)
        current_time_ms = int(datetime.now().timestamp() * 1000)
        ms_per_day = 1000 * 60 * 60 * 24
        
        # First, get all active and accepted members from membership table
        # This ensures we're reading from the membership table as the source of truth
        try:
            from ..database.connection import convert_boolean_condition
            query = f"""
                SELECT 
                    m.email,
                    m.fullname,
                    COALESCE(MAX(vph.lastEventDate), 0) as most_recent_date,
                    COALESCE(SUM(vph.eventsJoined), 0) as total_joined,
                    COALESCE(SUM(vph.eventsAttended), 0) as total_attended,
                    COALESCE(AVG(vph.attendanceRate), 0) as avg_attendance_rate,
                    COALESCE(COUNT(DISTINCT vph.semester), 0) as semesters_active
                FROM {membership_table} m
                LEFT JOIN {vph_table} vph ON m.email = vph.volunteerEmail
                WHERE m.accepted = 1 AND m.active = 1
                GROUP BY m.email, m.fullname
            """
            query = convert_boolean_condition(query)
            cursor.execute(query)
            
            volunteer_rows = cursor.fetchall()
        except Exception as query_error:
            # If the JOIN fails (e.g., table doesn't exist or column mismatch), 
            # fall back to getting members without participation history
            print(f"[DROPOUT ANALYTICS] Query with JOIN failed: {query_error}")
            print(f"[DROPOUT ANALYTICS] Falling back to membership-only query")
            from ..database.connection import convert_boolean_condition
            query = f"""
                SELECT 
                    email,
                    fullname,
                    0 as most_recent_date,
                    0 as total_joined,
                    0 as total_attended,
                    0 as avg_attendance_rate,
                    0 as semesters_active
                FROM {membership_table}
                WHERE accepted = 1 AND active = 1
            """
            query = convert_boolean_condition(query)
            cursor.execute(query)
            volunteer_rows = cursor.fetchall()
        
        # Calculate at-risk volunteers from participation history
        at_risk_volunteers = []
        for row in volunteer_rows:
            email, name, most_recent_date, total_joined, total_attended, avg_attendance_rate, semesters_active = row
            
            # Calculate attendance rate
            attendance_rate = float(avg_attendance_rate) if avg_attendance_rate else 0
            
            # Calculate days since last event
            inactivity_days = 0
            if most_recent_date and most_recent_date > 0:
                inactivity_days = int((current_time_ms - most_recent_date) / ms_per_day)
            elif total_joined == 0 and total_attended == 0:
                # If member has never participated, use a high inactivity days value
                # This ensures members with no participation are flagged as high risk
                inactivity_days = 365  # Assume 1 year of inactivity if never participated
            
            # Calculate risk score (0-100)
            risk_score = 0
            
            # High risk for members with no participation at all
            if total_joined == 0 and total_attended == 0:
                risk_score += 50  # Never participated - high risk
            else:
                # Attendance rate factor (0-40 points)
                if attendance_rate < 50:
                    risk_score += 40
                elif attendance_rate < 70:
                    risk_score += 25
                elif attendance_rate < 85:
                    risk_score += 10
                
                # Participation factor (0-20 points)
                # IMPORTANT: If they joined but never submitted a finalized evaluation form,
                # we treat them as high dropout risk (joined but did not "participate" in our system).
                if total_attended == 0 and total_joined > 0:
                    risk_score += 50  # Joined but never attended (no finalized form) - high risk
                elif total_attended < 2:
                    risk_score += 10
            
            # Inactivity factor (0-40 points)
            if inactivity_days > 90:
                risk_score += 40
            elif inactivity_days > 60:
                risk_score += 25
            elif inactivity_days > 30:
                risk_score += 15
            
            # Consistency factor - fewer semesters active = higher risk
            if semesters_active == 1:
                risk_score += 10
            elif semesters_active == 0:
                risk_score += 20  # Never active in any semester
            
            risk_score = min(100, risk_score)
            
            # Only include volunteers with risk score >= 50
            if risk_score >= 50:
                last_event_str = None
                if most_recent_date and most_recent_date > 0:
                    last_event_str = datetime.fromtimestamp(most_recent_date / 1000).strftime('%Y-%m-%d')
                
                at_risk_volunteers.append({
                    "name": name,
                    "inactivityDays": inactivity_days,
                    "lastEvent": last_event_str or "Never",
                    "riskScore": int(risk_score),
                    "joinedEvents": total_joined,
                    "attendedEvents": total_attended,
                    "attendanceRate": round(attendance_rate, 1),
                    "semestersActive": semesters_active
                })
        
        # Sort by risk score (highest first)
        at_risk_volunteers.sort(key=lambda x: x["riskScore"], reverse=True)
        
        conn.close()
        
        return {
            "success": True,
            "data": {
                "semesterData": semester_data,
                "atRiskVolunteers": at_risk_volunteers[:10]  # Top 10 at-risk
            },
            "message": "Volunteer dropout analytics retrieved successfully"
        }
        
    except Exception as e:
        import traceback
        # Ensure connection is closed even on error
        try:
            if 'conn' in locals():
                conn.close()
        except:
            pass
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"[DROPOUT ANALYTICS ERROR] {error_msg}")
        print(f"[DROPOUT ANALYTICS TRACEBACK] {traceback_str}")
        return {
            "success": False,
            "error": error_msg,
            "message": "Failed to retrieve volunteer dropout analytics. Please check if membership table has active members.",
            "traceback": traceback_str
        }

def getVolunteerDropoutAnalyticsLegacy(year=None):
    """
    Legacy method - calculates from requirements/evaluations directly
    Used as fallback if volunteerParticipationHistory table doesn't exist
    """
    try:
        from ..database.connection import cursorInstance
        import math
        from datetime import datetime
        
        conn, cursor = cursorInstance()
        
        # Get all events with their dates to calculate semesters
        from ..database.connection import quote_identifier
        internal_events_table = quote_identifier("internalEvents")
        external_events_table = quote_identifier("externalEvents")
        cursor.execute(f"""
            SELECT id, title, durationStart, durationEnd, 'internal' as type
            FROM {internal_events_table}
            WHERE status IN ('accepted', 'completed')
            UNION ALL
            SELECT id, title, durationStart, durationEnd, 'external' as type
            FROM {external_events_table}
            WHERE status IN ('accepted', 'completed')
            ORDER BY durationStart
        """)
        all_events = cursor.fetchall()
        
        if not all_events:
            conn.close()
            return {
                "success": True,
                "data": {
                    "semesterData": [],
                    "atRiskVolunteers": []
                },
                "message": "No events found"
            }
        
        # Group events by semester
        semester_events = {}
        for event_id, event_title, event_start, event_end, event_type in all_events:
            if event_start:
                event_date = datetime.fromtimestamp(event_start / 1000)
                semester_year = event_date.year
                semester_num = math.ceil(event_date.month / 6)  # 1 for Jan-Jun, 2 for Jul-Dec
                semester_key = f"{semester_year}-{semester_num}"
                
                if semester_key not in semester_events:
                    semester_events[semester_key] = []
                semester_events[semester_key].append((event_id, event_type))
        
        # Filter by year if specified
        if year:
            semester_events = {k: v for k, v in semester_events.items() if k.startswith(str(year))}
        
        # Calculate semester engagement data
        semester_data = []
        all_volunteer_stats = {}  # Track per-volunteer stats across all semesters
        
        for semester, events in sorted(semester_events.items()):
            event_ids_internal = [e[0] for e in events if e[1] == 'internal']
            event_ids_external = [e[0] for e in events if e[1] == 'external']
            
            # Count volunteers who JOINED (submitted requirements) for events in this semester.
            # Include accepted OR pending, exclude rejected.
            # Use a robust volunteer key: email -> srcode -> fullname
            from ..database.connection import quote_identifier
            requirements_table = quote_identifier('requirements')
            evaluation_table = quote_identifier('evaluation')
            from ..database.connection import convert_placeholders, convert_boolean_condition
            joined_query = f"""
                SELECT COUNT(DISTINCT COALESCE(NULLIF(r.email, ''), NULLIF(r.srcode, ''), r.fullname)) as joined_count
                FROM {requirements_table} r
                WHERE (r.accepted = 1 OR r.accepted IS NULL)
            """
            joined_params = []
            
            if event_ids_internal and event_ids_external:
                joined_query += " AND ((r.type = 'internal' AND r.eventId IN ({}) OR (r.type = 'external' AND r.eventId IN ({}))))".format(
                    ','.join(['?' for _ in event_ids_internal]),
                    ','.join(['?' for _ in event_ids_external])
                )
                joined_params = event_ids_internal + event_ids_external
            elif event_ids_internal:
                joined_query += " AND r.type = 'internal' AND r.eventId IN ({})".format(','.join(['?' for _ in event_ids_internal]))
                joined_params = event_ids_internal
            elif event_ids_external:
                joined_query += " AND r.type = 'external' AND r.eventId IN ({})".format(','.join(['?' for _ in event_ids_external]))
                joined_params = event_ids_external
            else:
                continue
            
            joined_query = convert_boolean_condition(joined_query)
            joined_query = convert_placeholders(joined_query)
            cursor.execute(joined_query, joined_params)
            joined_count = cursor.fetchone()[0] or 0
            
            # Count volunteers who ATTENDED (participated) in this semester
            from ..database.connection import convert_placeholders, convert_boolean_condition
            attended_query = f"""
                SELECT COUNT(DISTINCT COALESCE(NULLIF(r.email, ''), NULLIF(r.srcode, ''), r.fullname)) as attended_count
                FROM {requirements_table} r
                INNER JOIN {evaluation_table} e ON r.id = e.requirementId
                WHERE r.accepted = 1 
                AND e.finalized = 1 
                AND e.criteria IS NOT NULL 
                AND e.criteria != ''
            """
            attended_params = []
            
            if event_ids_internal and event_ids_external:
                attended_query += " AND ((r.type = 'internal' AND r.eventId IN ({}) OR (r.type = 'external' AND r.eventId IN ({}))))".format(
                    ','.join(['?' for _ in event_ids_internal]),
                    ','.join(['?' for _ in event_ids_external])
                )
                attended_params = event_ids_internal + event_ids_external
            elif event_ids_internal:
                attended_query += " AND r.type = 'internal' AND r.eventId IN ({})".format(','.join(['?' for _ in event_ids_internal]))
                attended_params = event_ids_internal
            elif event_ids_external:
                attended_query += " AND r.type = 'external' AND r.eventId IN ({})".format(','.join(['?' for _ in event_ids_external]))
                attended_params = event_ids_external
            
            attended_query = convert_boolean_condition(attended_query)
            attended_query = convert_placeholders(attended_query)
            cursor.execute(attended_query, attended_params)
            attended_count = cursor.fetchone()[0] or 0
            
            # Calculate dropouts (joined but didn't attend)
            dropouts = max(0, joined_count - attended_count)
            
            # Calculate average events per volunteer
            events_per_volunteer = 0
            if attended_count > 0:
                from ..database.connection import convert_placeholders, convert_boolean_condition
                total_attendances_query = f"""
                    SELECT COUNT(*) as total_attendances
                    FROM {requirements_table} r
                    INNER JOIN {evaluation_table} e ON r.id = e.requirementId
                    WHERE r.accepted = 1 
                    AND e.finalized = 1 
                    AND e.criteria IS NOT NULL 
                    AND e.criteria != ''
                """
                total_attendances_params = []
                
                if event_ids_internal and event_ids_external:
                    total_attendances_query += " AND ((r.type = 'internal' AND r.eventId IN ({}) OR (r.type = 'external' AND r.eventId IN ({}))))".format(
                        ','.join(['?' for _ in event_ids_internal]),
                        ','.join(['?' for _ in event_ids_external])
                    )
                    total_attendances_params = event_ids_internal + event_ids_external
                elif event_ids_internal:
                    total_attendances_query += " AND r.type = 'internal' AND r.eventId IN ({})".format(','.join(['?' for _ in event_ids_internal]))
                    total_attendances_params = event_ids_internal
                elif event_ids_external:
                    total_attendances_query += " AND r.type = 'external' AND r.eventId IN ({})".format(','.join(['?' for _ in event_ids_external]))
                    total_attendances_params = event_ids_external
                
                total_attendances_query = convert_boolean_condition(total_attendances_query)
                total_attendances_query = convert_placeholders(total_attendances_query)
                cursor.execute(total_attendances_query, total_attendances_params)
                total_attendances = cursor.fetchone()[0] or 0
                events_per_volunteer = round(total_attendances / attended_count, 1) if attended_count > 0 else 0
            
            semester_data.append({
                "semester": semester,
                "events": events_per_volunteer,
                "volunteers": joined_count,  # Total who joined
                "attended": attended_count,  # Total who attended
                "dropouts": dropouts
            })
            
            # Track individual volunteer stats for at-risk calculation
            from ..database.connection import quote_identifier
            internal_events_table = quote_identifier('internalEvents')
            external_events_table = quote_identifier('externalEvents')
            from ..database.connection import convert_boolean_condition, convert_placeholders
            volunteer_query = f"""
                SELECT
                       COALESCE(NULLIF(r.email, ''), NULLIF(r.srcode, ''), r.fullname) as volunteerKey,
                       MAX(NULLIF(r.email, '')) as email,
                       MAX(NULLIF(r.fullname, '')) as fullname,
                       COUNT(DISTINCT r.id) as joined_events,
                       COUNT(DISTINCT CASE WHEN e.finalized = 1 AND e.criteria IS NOT NULL AND e.criteria != '' THEN r.id END) as attended_events,
                       MAX(CASE 
                           WHEN r.type = 'internal' THEN ei.durationEnd
                           ELSE ee.durationEnd
                       END) as last_event_date
                FROM {requirements_table} r
                LEFT JOIN {evaluation_table} e ON r.id = e.requirementId
                LEFT JOIN {internal_events_table} ei ON r.eventId = ei.id AND r.type = 'internal'
                LEFT JOIN {external_events_table} ee ON r.eventId = ee.id AND r.type = 'external'
                WHERE (r.accepted = 1 OR r.accepted IS NULL)
            """
            from ..database.connection import convert_placeholders, convert_boolean_condition
            volunteer_query = convert_boolean_condition(volunteer_query)
            volunteer_params = []
            
            if event_ids_internal and event_ids_external:
                volunteer_query += " AND ((r.type = 'internal' AND r.eventId IN ({}) OR (r.type = 'external' AND r.eventId IN ({}))))".format(
                    ','.join(['?' for _ in event_ids_internal]),
                    ','.join(['?' for _ in event_ids_external])
                )
                volunteer_params = event_ids_internal + event_ids_external
            elif event_ids_internal:
                volunteer_query += " AND r.type = 'internal' AND r.eventId IN ({})".format(','.join(['?' for _ in event_ids_internal]))
                volunteer_params = event_ids_internal
            elif event_ids_external:
                volunteer_query += " AND r.type = 'external' AND r.eventId IN ({})".format(','.join(['?' for _ in event_ids_external]))
                volunteer_params = event_ids_external
            
            volunteer_query += " GROUP BY volunteerKey"
            
            from ..database.connection import convert_placeholders
            volunteer_query = convert_placeholders(volunteer_query)
            cursor.execute(volunteer_query, volunteer_params)
            volunteer_rows = cursor.fetchall()
            
            for volunteer_key, email, fullname, joined_events, attended_events, last_event_date in volunteer_rows:
                key = volunteer_key or email or fullname
                if key not in all_volunteer_stats:
                    all_volunteer_stats[key] = {
                        "name": fullname or email or volunteer_key,
                        "totalJoined": 0,
                        "totalAttended": 0,
                        "lastEventDate": 0
                    }
                
                all_volunteer_stats[key]["totalJoined"] += joined_events
                all_volunteer_stats[key]["totalAttended"] += attended_events
                if last_event_date and last_event_date > all_volunteer_stats[key]["lastEventDate"]:
                    all_volunteer_stats[key]["lastEventDate"] = last_event_date
        
        # Calculate at-risk volunteers (across all semesters)
        current_time_ms = int(datetime.now().timestamp() * 1000)
        ms_per_day = 1000 * 60 * 60 * 24
        
        at_risk_volunteers = []
        for email, stats in all_volunteer_stats.items():
            totalJoined = stats["totalJoined"]
            totalAttended = stats["totalAttended"]
            last_event_date = stats["lastEventDate"]
            
            # Calculate attendance rate
            attendance_rate = (totalAttended / totalJoined * 100) if totalJoined > 0 else 0
            
            # Calculate days since last event
            inactivity_days = 0
            if last_event_date and last_event_date > 0:
                inactivity_days = int((current_time_ms - last_event_date) / ms_per_day)
            
            # Calculate risk score (0-100)
            # Factors: low attendance rate, high inactivity, low total participation
            risk_score = 0
            
            # Attendance rate factor (0-40 points)
            if attendance_rate < 50:
                risk_score += 40
            elif attendance_rate < 70:
                risk_score += 25
            elif attendance_rate < 85:
                risk_score += 10
            
            # Inactivity factor (0-40 points)
            if inactivity_days > 90:
                risk_score += 40
            elif inactivity_days > 60:
                risk_score += 25
            elif inactivity_days > 30:
                risk_score += 15
            
            # Participation factor
            # IMPORTANT: If they joined but never submitted a finalized evaluation form,
            # we treat them as high dropout risk.
            if totalAttended == 0 and totalJoined > 0:
                risk_score += 50  # Joined but never attended (no finalized form) - high risk
            elif totalAttended < 2:
                risk_score += 10
            
            risk_score = min(100, risk_score)
            
            # Only include volunteers with risk score >= 50
            if risk_score >= 50:
                last_event_str = None
                if last_event_date and last_event_date > 0:
                    last_event_str = datetime.fromtimestamp(last_event_date / 1000).strftime('%Y-%m-%d')
                
                at_risk_volunteers.append({
                    "name": stats["name"],
                    "inactivityDays": inactivity_days,
                    "lastEvent": last_event_str or "Never",
                    "riskScore": int(risk_score),
                    "joinedEvents": totalJoined,
                    "attendedEvents": totalAttended,
                    "attendanceRate": round(attendance_rate, 1)
                })
        
        # Sort by risk score (highest first)
        at_risk_volunteers.sort(key=lambda x: x["riskScore"], reverse=True)
        
        conn.close()
        
        return {
            "success": True,
            "data": {
                "semesterData": semester_data,
                "atRiskVolunteers": at_risk_volunteers[:10]  # Top 10 at-risk
            },
            "message": "Volunteer dropout analytics retrieved successfully"
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve volunteer dropout analytics",
            "traceback": traceback.format_exc()
        }

def getPredictiveInsights():
    """
    Generate predictive insights and recommendations
    """
    try:
        # Get basic analytics
        eventSuccess = getEventSuccessAnalytics()
        dropoutRisk = getVolunteerDropoutAnalytics()
        
        insights = []
        recommendations = []
        
        if eventSuccess.get('success'):
            eventData = eventSuccess['data']
            successRate = (eventData['completed'] / max(eventData['totalEvents'], 1)) * 100
            
            if successRate < 70:
                insights.append("Event success rate is below optimal level")
                recommendations.append("Review event planning process and improve pre-event preparation")
            
            if eventData['averageAttendance'] < 75:
                insights.append("Average attendance is lower than expected")
                recommendations.append("Enhance event marketing and engagement strategies")
        
        if dropoutRisk.get('success'):
            dropoutData = dropoutRisk['data']
            currentRisk = dropoutData[-1]['riskLevel'] if dropoutData else 0
            
            if currentRisk > 30:
                insights.append("High volunteer dropout risk detected")
                recommendations.append("Implement volunteer retention programs and improve engagement")
            elif currentRisk > 20:
                insights.append("Moderate volunteer dropout risk")
                recommendations.append("Monitor volunteer satisfaction and address concerns proactively")
        
        return {
            "success": True,
            "data": {
                "insights": insights,
                "recommendations": recommendations,
                "lastUpdated": datetime.now().isoformat()
            },
            "message": "Predictive insights generated successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate predictive insights"
        }

def getSatisfactionAnalytics(year=None):
    """
    Get satisfaction analytics from QR evaluations
    Processes evaluation data to extract satisfaction ratings and trends
    """
    try:
        # 0) Prefer pre-aggregated semester_satisfaction if available
        try:
            from ..database.connection import cursorInstance
            conn, cursor = cursorInstance()
            from ..database.connection import quote_identifier
            semester_satisfaction_table = quote_identifier('semester_satisfaction')
            from ..database.connection import convert_placeholders
            if year:
                query = f"""
                    SELECT year, semester, overall, volunteers, beneficiaries, topIssues
                    FROM {semester_satisfaction_table}
                    WHERE year=?
                    ORDER BY semester ASC
                """
                query = convert_placeholders(query)
                cursor.execute(query, (int(year),))
            else:
                cursor.execute(f"""
                    SELECT year, semester, overall, volunteers, beneficiaries, topIssues
                    FROM {semester_satisfaction_table}
                    ORDER BY year ASC, semester ASC
                """)
            rows = cursor.fetchall()
            conn.close()
            if rows and len(rows) > 0:
                satisfactionData = []
                issues_counter = {}
                for y, sem, ov, vol, ben, topIssues in rows:
                    satisfactionData.append({
                        "semester": f"{y}-{sem}",
                        "score": round(float(ov or 0), 1),
                        "volunteers": round(float(vol or 0), 1),
                        "beneficiaries": round(float(ben or 0), 1),
                    })
                    # Accumulate issues
                    try:
                        if isinstance(topIssues, str):
                            parsed = eval(topIssues) if topIssues.strip().startswith("[") else []
                        else:
                            parsed = topIssues or []
                        for it in parsed:
                            issues_counter[it.get("issue", "Issue")] = issues_counter.get(it.get("issue", "Issue"), 0) + int(it.get("frequency", 1))
                    except Exception:
                        pass

                overall_avg = sum([item["score"] for item in satisfactionData]) / len(satisfactionData) if satisfactionData else 4.0
                volunteer_avg = sum([item["volunteers"] for item in satisfactionData]) / len(satisfactionData) if satisfactionData else 4.0
                beneficiary_avg = sum([item["beneficiaries"] for item in satisfactionData]) / len(satisfactionData) if satisfactionData else 4.0
                top_issues = [{"issue": k, "frequency": v, "category": "volunteers"} for k, v in sorted(issues_counter.items(), key=lambda x: x[1], reverse=True)[:5]]
                return {
                    "success": True,
                    "data": {
                        "satisfactionData": satisfactionData,
                        "topIssues": top_issues,
                        "averageScore": round(overall_avg, 1),
                        "volunteerScore": round(volunteer_avg, 1),
                        "beneficiaryScore": round(beneficiary_avg, 1),
                        "totalEvaluations": 0,
                        "processedEvaluations": 0
                    },
                    "message": "Satisfaction analytics retrieved from pre-aggregated store"
                }
        except Exception as _:
            # If the table doesn't exist or any error, fall back to live computation below
            pass

        # Get all evaluations with their requirement and event info
        from ..database.connection import cursorInstance
        conn, cursor = cursorInstance()
        
        # Get evaluations with event dates
        from ..database.connection import quote_identifier
        internal_events_table = quote_identifier('internalEvents')
        external_events_table = quote_identifier('externalEvents')
        evaluation_table = quote_identifier('evaluation')
        requirements_table = quote_identifier('requirements')
        query = f"""
            SELECT e.id, e."requirementId", e.criteria, e.finalized, e.q13, e.q14, e.comment, e.recommendations,
                   r."eventId", r.type,
                   CASE 
                       WHEN r.type = 'internal' THEN ei."durationStart"
                       ELSE ee."durationStart"
                   END as eventDate
            FROM {evaluation_table} e
            INNER JOIN {requirements_table} r ON e."requirementId" = r.id
            LEFT JOIN {internal_events_table} ei ON r."eventId" = ei.id AND r.type = 'internal'
            LEFT JOIN {external_events_table} ee ON r."eventId" = ee.id AND r.type = 'external'
            WHERE e.finalized = 1 AND e.criteria IS NOT NULL AND e.criteria != ''
        """
        cursor.execute(query)
        
        evaluation_rows = cursor.fetchall()
        conn.close()
        
        satisfactionBySemester = {}
        issues = {}
        volunteerSatisfaction = []
        beneficiarySatisfaction = []
        
        for row in evaluation_rows:
            eval_id, req_id, criteria_str, finalized, q13, q14, comment, recommendations, event_id, event_type, event_date = row
            
            if not finalized or not criteria_str:
                continue
                
            try:
                # Parse criteria (handle both string and dict formats)
                criteria = criteria_str
                if isinstance(criteria, str):
                    try:
                        criteria = eval(criteria) if criteria.startswith('{') else json.loads(criteria)
                    except:
                        criteria = {}
                
                # Extract semester from event date (use event date since evaluation has no createdAt)
                if event_date:
                    evalDate = datetime.fromtimestamp(event_date / 1000)
                else:
                    evalDate = datetime.now()  # Fallback to current date
                semester = f"{evalDate.year}-{math.ceil(evalDate.month / 6)}"
                
                # Filter by year if specified
                if year and not semester.startswith(year):
                    continue
                
                if semester not in satisfactionBySemester:
                    satisfactionBySemester[semester] = {
                        'volunteers': [],
                        'beneficiaries': [],
                        'overall': []
                    }
                
                # Extract satisfaction scores from criteria
                # Look for various satisfaction indicators
                satisfaction_score = 4.0  # Default score
                
                # Check for overall satisfaction
                if 'overall' in criteria:
                    satisfaction_score = criteria['overall']
                elif 'satisfaction' in criteria:
                    satisfaction_score = criteria['satisfaction']
                elif 'rating' in criteria:
                    satisfaction_score = criteria['rating']
                else:
                    # Calculate average from available ratings
                    rating_keys = ['excellent', 'very_satisfactory', 'satisfactory', 'fair', 'poor']
                    ratings = [criteria.get(key, 0) for key in rating_keys]
                    if any(ratings):
                        # Convert to numeric score (1-5 scale)
                        score_map = {'excellent': 5, 'very_satisfactory': 4, 'satisfactory': 3, 'fair': 2, 'poor': 1}
                        for i, rating in enumerate(ratings):
                            if rating:
                                satisfaction_score = score_map[rating_keys[i]]
                                break
                
                # Determine if this is volunteer or beneficiary evaluation
                # Default to volunteer (most evaluations are from volunteers)
                is_volunteer = True  # Can be enhanced with evaluation type field if needed
                
                if is_volunteer:
                    satisfactionBySemester[semester]['volunteers'].append(satisfaction_score)
                    volunteerSatisfaction.append(satisfaction_score)
                else:
                    satisfactionBySemester[semester]['beneficiaries'].append(satisfaction_score)
                    beneficiarySatisfaction.append(satisfaction_score)
                
                satisfactionBySemester[semester]['overall'].append(satisfaction_score)
                
                # Extract issues from comments
                eval_comment = comment or criteria.get('comment', '') or criteria.get('comments', '') or ''
                if eval_comment:
                    common_issues = [
                        'communication', 'resource', 'scheduling', 'training', 'support',
                        'accessibility', 'organization', 'time', 'venue', 'materials',
                        'follow-up', 'feedback', 'coordination', 'preparation'
                    ]
                    
                    for issue in common_issues:
                        if issue.lower() in eval_comment.lower():
                            issues[issue] = issues.get(issue, 0) + 1
                            
            except Exception as e:
                print(f"Error processing evaluation {eval_id}: {e}")
                continue
        
        # Calculate semester averages
        satisfactionData = []
        for semester, data in satisfactionBySemester.items():
            if data['overall']:
                overall_avg = sum(data['overall']) / len(data['overall'])
                volunteer_avg = sum(data['volunteers']) / len(data['volunteers']) if data['volunteers'] else overall_avg
                beneficiary_avg = sum(data['beneficiaries']) / len(data['beneficiaries']) if data['beneficiaries'] else overall_avg
                
                satisfactionData.append({
                    'semester': semester,
                    'score': round(overall_avg, 1),
                    'volunteers': round(volunteer_avg, 1),
                    'beneficiaries': round(beneficiary_avg, 1)
                })
        
        # Sort by semester
        satisfactionData.sort(key=lambda x: x['semester'])
        
        # Calculate overall averages
        overall_avg = sum([item['score'] for item in satisfactionData]) / len(satisfactionData) if satisfactionData else 4.0
        volunteer_avg = sum(volunteerSatisfaction) / len(volunteerSatisfaction) if volunteerSatisfaction else 4.0
        beneficiary_avg = sum(beneficiarySatisfaction) / len(beneficiarySatisfaction) if beneficiarySatisfaction else 4.0
        
        # Format top issues
        top_issues = []
        for issue, frequency in sorted(issues.items(), key=lambda x: x[1], reverse=True)[:5]:
            top_issues.append({
                'issue': issue.replace('_', ' ').title() + ' Issues',
                'frequency': frequency,
                'category': 'volunteers' if random.random() > 0.5 else 'beneficiaries'  # Random assignment for demo
            })
        
        return {
            "success": True,
            "data": {
                "satisfactionData": satisfactionData,
                "topIssues": top_issues,
                "averageScore": round(overall_avg, 1),
                "volunteerScore": round(volunteer_avg, 1),
                "beneficiaryScore": round(beneficiary_avg, 1),
                "totalEvaluations": len(evaluation_rows),
                "processedEvaluations": len([row for row in evaluation_rows if row[3] == 1])  # row[3] is finalized
            },
            "message": "Satisfaction analytics retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve satisfaction analytics"
        }

def getEventSatisfactionAnalytics(eventId: int, eventType: str):
    """
    Get satisfaction analytics for a specific event
    Returns volunteer and beneficiary ratings separately
    """
    try:
        from ..database.connection import cursorInstance
        conn, cursor = cursorInstance()
        
        # Get event title
        from ..database.connection import quote_identifier, convert_placeholders
        event_table = "internalEvents" if eventType == "internal" else "externalEvents"
        quoted_table = quote_identifier(event_table)
        query = f"SELECT title, durationStart, durationEnd FROM {quoted_table} WHERE id = ?"
        query = convert_placeholders(query)
        cursor.execute(query, (eventId,))
        event_row = cursor.fetchone()
        
        if not event_row:
            conn.close()
            return {
                "success": False,
                "error": "Event not found",
                "message": "Event not found"
            }
        
        event_title, event_start, event_end = event_row
        
        # Get satisfaction surveys for this specific event (primary source)
        from ..database.connection import quote_identifier
        satisfaction_surveys_table = quote_identifier('satisfactionSurveys')
        evaluation_table = quote_identifier('evaluation')
        requirements_table = quote_identifier('requirements')
        from ..database.connection import convert_placeholders
        query1 = f"""
            SELECT id, respondentType, overallSatisfaction, volunteerRating, beneficiaryRating,
                   q13, q14, comment, recommendations, finalized
            FROM {satisfaction_surveys_table}
            WHERE eventId = ? AND eventType = ? AND finalized = 1
        """
        query1 = convert_placeholders(query1)
        cursor.execute(query1, (eventId, eventType))
        
        survey_rows = cursor.fetchall()
        
        # Also get evaluations as fallback (for backward compatibility)
        query2 = f"""
            SELECT e.id, e.requirementId, e.criteria, e.finalized, e.q13, e.q14, e.comment, e.recommendations,
                   r.eventId, r.type
            FROM {evaluation_table} e
            INNER JOIN {requirements_table} r ON e.requirementId = r.id
            WHERE r.eventId = ? AND r.type = ? AND e.finalized = 1 AND e.criteria IS NOT NULL AND e.criteria != ''
        """
        query2 = convert_placeholders(query2)
        cursor.execute(query2, (eventId, eventType))
        
        evaluation_rows = cursor.fetchall()
        conn.close()
        
        volunteerScores = []
        beneficiaryScores = []
        allScores = []
        issues = {}
        
        # Process satisfaction surveys (primary source)
        for row in survey_rows:
            survey_id, respondent_type, overall, vol_rating, ben_rating, q13, q14, comment, recommendations, finalized = row
            
            if not finalized:
                continue
            
            try:
                # Use overall satisfaction as primary score
                satisfaction_score = float(overall) if overall else 0
                
                if satisfaction_score > 0:
                    # Determine if volunteer or beneficiary based on respondentType
                    if respondent_type and "volunteer" in respondent_type.lower():
                        # Use volunteerRating if available, otherwise overall
                        vol_score = float(vol_rating) if vol_rating else satisfaction_score
                        volunteerScores.append(vol_score)
                        allScores.append(vol_score)
                    elif respondent_type and "beneficiary" in respondent_type.lower():
                        # Use beneficiaryRating if available, otherwise overall
                        ben_score = float(ben_rating) if ben_rating else satisfaction_score
                        beneficiaryScores.append(ben_score)
                        allScores.append(ben_score)
                    else:
                        # If type is unclear, use q13/q14 to determine
                        if q13:
                            try:
                                vol_score = float(q13)
                                volunteerScores.append(vol_score)
                                allScores.append(vol_score)
                            except:
                                allScores.append(satisfaction_score)
                        elif q14:
                            try:
                                ben_score = float(q14)
                                beneficiaryScores.append(ben_score)
                                allScores.append(ben_score)
                            except:
                                allScores.append(satisfaction_score)
                        else:
                            # Default to volunteer if unclear
                            volunteerScores.append(satisfaction_score)
                            allScores.append(satisfaction_score)
                    
                    # Extract issues from comments
                    if comment:
                        common_issues = [
                            'communication', 'resource', 'scheduling', 'training', 'support',
                            'accessibility', 'organization', 'time', 'venue', 'materials',
                            'follow-up', 'feedback', 'coordination', 'preparation'
                        ]
                        for issue in common_issues:
                            if issue.lower() in comment.lower():
                                issues[issue] = issues.get(issue, 0) + 1
                                
            except Exception as e:
                print(f"Error processing satisfaction survey {survey_id}: {e}")
                continue
        
        # Process evaluations as fallback (for backward compatibility)
        for row in evaluation_rows:
            eval_id, req_id, criteria_str, finalized, q13, q14, comment, recommendations, req_event_id, req_event_type = row
            
            try:
                # Parse criteria
                criteria = criteria_str
                if isinstance(criteria, str):
                    try:
                        criteria = eval(criteria) if criteria.startswith('{') else json.loads(criteria)
                    except:
                        criteria = {}
                
                # Extract satisfaction score
                satisfaction_score = 4.0
                if 'overall' in criteria:
                    satisfaction_score = criteria['overall']
                elif 'satisfaction' in criteria:
                    satisfaction_score = criteria['satisfaction']
                elif 'rating' in criteria:
                    satisfaction_score = criteria['rating']
                else:
                    rating_keys = ['excellent', 'very_satisfactory', 'satisfactory', 'fair', 'poor']
                    ratings = [criteria.get(key, 0) for key in rating_keys]
                    if any(ratings):
                        score_map = {'excellent': 5, 'very_satisfactory': 4, 'satisfactory': 3, 'fair': 2, 'poor': 1}
                        for i, rating in enumerate(ratings):
                            if rating:
                                satisfaction_score = score_map[rating_keys[i]]
                                break
                
                # Use q13 and q14 to determine if volunteer or beneficiary
                if q13:
                    try:
                        vol_score = float(q13) if q13 else satisfaction_score
                        volunteerScores.append(vol_score)
                        allScores.append(vol_score)
                    except:
                        volunteerScores.append(satisfaction_score)
                        allScores.append(satisfaction_score)
                
                if q14:
                    try:
                        ben_score = float(q14) if q14 else satisfaction_score
                        beneficiaryScores.append(ben_score)
                        allScores.append(ben_score)
                    except:
                        beneficiaryScores.append(satisfaction_score)
                        allScores.append(satisfaction_score)
                
                # If neither q13 nor q14, assume volunteer (default)
                if not q13 and not q14:
                    volunteerScores.append(satisfaction_score)
                    allScores.append(satisfaction_score)
                
                # Extract issues from comments
                eval_comment = comment or criteria.get('comment', '') or criteria.get('comments', '') or ''
                if eval_comment:
                    common_issues = [
                        'communication', 'resource', 'scheduling', 'training', 'support',
                        'accessibility', 'organization', 'time', 'venue', 'materials',
                        'follow-up', 'feedback', 'coordination', 'preparation'
                    ]
                    for issue in common_issues:
                        if issue.lower() in eval_comment.lower():
                            issues[issue] = issues.get(issue, 0) + 1
                            
            except Exception as e:
                print(f"Error processing evaluation {eval_id}: {e}")
                continue
        
        # Calculate averages
        volunteer_avg = sum(volunteerScores) / len(volunteerScores) if volunteerScores else 0
        beneficiary_avg = sum(beneficiaryScores) / len(beneficiaryScores) if beneficiaryScores else 0
        overall_avg = sum(allScores) / len(allScores) if allScores else 0
        
        # Generate predictive statement
        def generatePrediction(vol_avg, ben_avg, overall):
            if overall >= 4.5:
                prediction = "Excellent satisfaction ratings indicate strong event success. Future similar events are likely to maintain high satisfaction levels."
            elif overall >= 4.0:
                prediction = "Good satisfaction ratings suggest the event met expectations. With minor improvements, future events can achieve even higher satisfaction."
            elif overall >= 3.5:
                prediction = "Moderate satisfaction indicates areas for improvement. Addressing feedback can enhance future event satisfaction."
            else:
                prediction = "Lower satisfaction ratings highlight key areas needing attention. Strategic improvements are recommended for future events."
            
            if vol_avg > ben_avg + 0.3:
                prediction += " Volunteers showed notably higher satisfaction than beneficiaries, suggesting beneficiary experience could be enhanced."
            elif ben_avg > vol_avg + 0.3:
                prediction += " Beneficiaries showed notably higher satisfaction than volunteers, indicating strong impact despite volunteer challenges."
            
            return prediction
        
        prediction = generatePrediction(volunteer_avg, beneficiary_avg, overall_avg)
        
        # Format top issues
        top_issues = []
        for issue, frequency in sorted(issues.items(), key=lambda x: x[1], reverse=True)[:5]:
            top_issues.append({
                'issue': issue.replace('_', ' ').title() + ' Issues',
                'frequency': frequency
            })
        
        return {
            "success": True,
            "data": {
                "eventId": eventId,
                "eventType": eventType,
                "eventTitle": event_title,
                "eventStart": event_start,
                "eventEnd": event_end,
                "volunteerScore": round(volunteer_avg, 1),
                "beneficiaryScore": round(beneficiary_avg, 1),
                "overallScore": round(overall_avg, 1),
                "volunteerCount": len(volunteerScores),
                "beneficiaryCount": len(beneficiaryScores),
                "totalEvaluations": len(survey_rows) + len(evaluation_rows),
                "topIssues": top_issues,
                "prediction": prediction
            },
            "message": "Event satisfaction analytics retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve event satisfaction analytics"
        }

def clearAnalyticsData():
    """
    Clear all analytics-related data:
    - Deletes all requirements (clears age/sex analytics)
    - Deletes all evaluations (clears satisfaction ratings and dropout risk)
    """
    from ..database import connection
    
    conn, cursor = connection.cursorInstance()
    
    try:
        # Start transaction
        conn.execute("BEGIN TRANSACTION")
        
        from ..database.connection import quote_identifier
        evaluation_table = quote_identifier('evaluation')
        requirements_table = quote_identifier('requirements')
        
        # Delete all evaluations first (they reference requirements)
        cursor.execute(f"DELETE FROM {evaluation_table}")
        deleted_evaluations = cursor.rowcount
        
        # Delete all requirements
        cursor.execute(f"DELETE FROM {requirements_table}")
        deleted_requirements = cursor.rowcount
        
        # Commit transaction
        conn.commit()
        
        return {
            'success': True,
            'message': f'Successfully cleared analytics data: {deleted_requirements} requirements and {deleted_evaluations} evaluations deleted',
            'data': {
                'requirements_deleted': deleted_requirements,
                'evaluations_deleted': deleted_evaluations
            }
        }
        
    except Exception as e:
        # Rollback transaction on error
        conn.rollback()
        import traceback
        return {
            'success': False,
            'message': f'Failed to clear analytics data: {str(e)}',
            'error': traceback.format_exc()
        }
    finally:
        conn.close()

def deleteDummyVolunteersData():
    """
    Delete all analytics data for dummy volunteers including:
    - Age analytics (from requirements and membership)
    - Sex analytics (from requirements and membership)
    - Event participation (requirements)
    - Satisfaction predictions (evaluations)
    - Dropout-risk records (calculated from membership/requirements)
    - Aggregates (all analytics derived from dummy data)
    - The dummy users themselves (membership, accounts, sessions)
    
    Dummy users are identified by:
    - Emails starting with 'dummy' (case-insensitive)
    - Common test patterns: 'example', 'test', 'demo', 'fake'
    """
    from ..database import connection
    
    conn, cursor = connection.cursorInstance()
    
    try:
        # Start transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Step 1: Identify dummy user emails
        # Find all dummy members by email pattern
        # Only match obvious dummy/test patterns - be conservative to avoid deleting real users
        from ..database.connection import quote_identifier
        membership_table = quote_identifier('membership')
        requirements_table = quote_identifier('requirements')
        evaluation_table = quote_identifier('evaluation')
        print("[DELETE DUMMY] Step 1: Identifying dummy members...")
        cursor.execute(f"""
            SELECT id, email FROM {membership_table} 
            WHERE LOWER(email) LIKE 'dummy%@%' 
               OR LOWER(email) LIKE 'test%@%'
               OR LOWER(email) LIKE 'demo%@%'
               OR LOWER(email) LIKE 'fake%@%'
               OR (LOWER(email) LIKE 'example%@%' AND LOWER(email) NOT LIKE '%batstate%')
               OR LOWER(fullname) = 'dummy'
               OR LOWER(fullname) = 'test'
               OR LOWER(fullname) = 'demo'
               OR LOWER(fullname) = 'fake'
               OR LOWER(fullname) LIKE 'dummy %'
               OR LOWER(fullname) LIKE 'test %'
               OR LOWER(fullname) LIKE 'demo %'
               OR LOWER(fullname) LIKE 'fake %'
        """)
        dummy_members = cursor.fetchall()
        dummy_member_ids = [row[0] for row in dummy_members]
        dummy_emails = [row[1].lower() for row in dummy_members if row[1]]
        print(f"[DELETE DUMMY] Found {len(dummy_member_ids)} dummy members, {len(dummy_emails)} unique emails")
        
        deleted_counts = {
            'evaluations': 0,
            'requirements': 0,
            'sessions': 0,
            'accounts': 0,
            'memberships': 0
        }
        
        if len(dummy_member_ids) > 0 or len(dummy_emails) > 0:
            # Step 2: Delete evaluations linked to dummy requirements
            # First, get requirement IDs for dummy emails
            if len(dummy_emails) > 0:
                print(f"[DELETE DUMMY] Step 2: Finding requirements for {len(dummy_emails)} dummy emails...")
                from ..database.connection import convert_placeholders
                placeholders = ','.join(['?' for _ in dummy_emails])
                query = f"""
                    SELECT id FROM {requirements_table} 
                    WHERE LOWER(email) IN ({placeholders})
                """
                query = convert_placeholders(query)
                cursor.execute(query, dummy_emails)
                dummy_requirement_ids = [row[0] for row in cursor.fetchall()]
                print(f"[DELETE DUMMY] Found {len(dummy_requirement_ids)} dummy requirements")
                
                if len(dummy_requirement_ids) > 0:
                    # Delete evaluations for dummy requirements
                    print(f"[DELETE DUMMY] Step 2a: Deleting evaluations for dummy requirements...")
                    from ..database.connection import convert_placeholders
                    req_placeholders = ','.join(['?' for _ in dummy_requirement_ids])
                    query = f"""
                        DELETE FROM {evaluation_table} 
                        WHERE requirementId IN ({req_placeholders})
                    """
                    query = convert_placeholders(query)
                    cursor.execute(query, dummy_requirement_ids)
                    deleted_counts['evaluations'] = cursor.rowcount
                    print(f"[DELETE DUMMY] Deleted {deleted_counts['evaluations']} evaluations")
            
            # Step 3: Delete requirements for dummy emails
            if len(dummy_emails) > 0:
                print(f"[DELETE DUMMY] Step 3: Deleting requirements for dummy emails...")
                from ..database.connection import convert_placeholders
                placeholders = ','.join(['?' for _ in dummy_emails])
                query = f"""
                    DELETE FROM {requirements_table} 
                    WHERE LOWER(email) IN ({placeholders})
                """
                query = convert_placeholders(query)
                cursor.execute(query, dummy_emails)
                deleted_counts['requirements'] = cursor.rowcount
                print(f"[DELETE DUMMY] Deleted {deleted_counts['requirements']} requirements")
            
            # Step 4: Delete accounts linked to dummy members
            if len(dummy_member_ids) > 0:
                print(f"[DELETE DUMMY] Step 4: Finding accounts for {len(dummy_member_ids)} dummy members...")
                # Get account IDs linked to dummy members
                from ..database.connection import convert_placeholders
                member_placeholders = ','.join(['?' for _ in dummy_member_ids])
                query = f"""
                    SELECT id FROM accounts 
                    WHERE membershipId IN ({member_placeholders})
                """
                query = convert_placeholders(query)
                cursor.execute(query, dummy_member_ids)
                dummy_account_ids = [row[0] for row in cursor.fetchall()]
                print(f"[DELETE DUMMY] Found {len(dummy_account_ids)} dummy accounts")
                
                if len(dummy_account_ids) > 0:
                    # Step 5: Delete sessions for dummy accounts
                    print(f"[DELETE DUMMY] Step 5: Deleting sessions for dummy accounts...")
                    from ..database.connection import convert_placeholders
                    account_placeholders = ','.join(['?' for _ in dummy_account_ids])
                    query = f"""
                        DELETE FROM sessions 
                        WHERE userid IN ({account_placeholders})
                    """
                    query = convert_placeholders(query)
                    cursor.execute(query, dummy_account_ids)
                    deleted_counts['sessions'] = cursor.rowcount
                    print(f"[DELETE DUMMY] Deleted {deleted_counts['sessions']} sessions")
                    
                    # Delete accounts
                    print(f"[DELETE DUMMY] Step 5a: Deleting dummy accounts...")
                    from ..database.connection import convert_placeholders
                    query = f"""
                        DELETE FROM accounts 
                        WHERE id IN ({account_placeholders})
                    """
                    query = convert_placeholders(query)
                    cursor.execute(query, dummy_account_ids)
                    deleted_counts['accounts'] = cursor.rowcount
                    print(f"[DELETE DUMMY] Deleted {deleted_counts['accounts']} accounts")
            
            # Step 6: Delete dummy memberships (the dummy users themselves)
            if len(dummy_member_ids) > 0:
                print(f"[DELETE DUMMY] Step 6: Deleting {len(dummy_member_ids)} dummy memberships...")
                member_placeholders = ','.join(['?' for _ in dummy_member_ids])
                query = f"""
                    DELETE FROM {membership_table} 
                    WHERE id IN ({member_placeholders})
                """
                from ..database.connection import convert_placeholders
                query = convert_placeholders(query)
                cursor.execute(query, dummy_member_ids)
                deleted_counts['memberships'] = cursor.rowcount
                print(f"[DELETE DUMMY] Deleted {deleted_counts['memberships']} memberships")
        else:
            print("[DELETE DUMMY] No dummy members found to delete")
        
        # Commit transaction
        print("[DELETE DUMMY] Committing transaction...")
        conn.commit()
        print("[DELETE DUMMY] Transaction committed successfully!")
        
        total_deleted = sum(deleted_counts.values())
        
        return {
            'success': True,
            'message': f'Successfully deleted all dummy volunteer data: {total_deleted} total records deleted',
            'data': {
                'dummy_members_found': len(dummy_member_ids),
                'deleted_counts': deleted_counts,
                'total_deleted': total_deleted
            }
        }
        
    except Exception as e:
        # Rollback transaction on error
        conn.rollback()
        import traceback
        return {
            'success': False,
            'message': f'Failed to delete dummy volunteer data: {str(e)}',
            'error': traceback.format_exc()
        }
    finally:
        conn.close()

def seedDemoEvaluations(count: int = 100):
    """
    Insert demo evaluation records to drive analytics visuals.
    Note: evaluation table has no createdAt/type columns; satisfaction analytics will still compute averages.
    """
    try:
        seeded = 0
        issue_pool = [
            'communication', 'resource', 'scheduling', 'training', 'support',
            'accessibility', 'organization', 'time', 'venue', 'materials',
            'feedback', 'coordination', 'preparation'
        ]

        for i in range(count):
            # Simulate a satisfaction score 1-5 with a realistic distribution around 4.0
            base = random.gauss(4.0, 0.7)
            overall = max(1.0, min(5.0, round(base, 1)))

            # Randomly compose a comment with some issues sprinkled in
            issues_in_comment = random.sample(issue_pool, k=random.randint(0, 2))
            comment_text = "Great event overall. "
            if issues_in_comment:
                comment_text += "Some concerns: " + ", ".join(issues_in_comment) + "."

            # Build criteria payload expected by analytics
            criteria = {
                'overall': overall,
                'comment': comment_text,
                # include some alternate keys analytics may look for
                'satisfaction': overall,
            }

            # Required evaluation fields
            q13 = 'N/A'
            q14 = 'N/A'
            recommendations = 'Keep improving community engagement.'

            # Link to a pseudo requirement id (no FK constraint)
            requirement_id = f"demo_req_{int(time.time()*1000)}_{i}"

            # Persist
            # EvaluationModel.create signature: (requirementId, criteria, q13, q14, comment, recommendations, finalized)
            # But current model's create order differs from table (criteria first). We'll insert via updateSpecific-compatible order.
            inserted = EvaluationDb.create((
                # columns from EvaluationModel.columns ordering
                requirement_id,                    # requirementId
                str(criteria),                     # criteria (store as string)
                q13,                               # q13
                q14,                               # q14
                comment_text,                      # comment
                recommendations,                   # recommendations
                True                               # finalized
            ))

            if inserted:
                seeded += 1

        return {
            'success': True,
            'message': f'Seeded {seeded} demo evaluations',
            'data': { 'seeded': seeded }
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to seed demo evaluations: {str(e)}'
        }