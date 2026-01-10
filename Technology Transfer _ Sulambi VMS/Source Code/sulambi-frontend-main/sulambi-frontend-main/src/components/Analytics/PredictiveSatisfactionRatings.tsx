import React, { useState, useEffect, useContext, useMemo } from 'react';
import FlexBox from '../FlexBox';
import { Typography, Box, Chip, LinearProgress, Select, MenuItem, FormControl, InputLabel, CircularProgress, Alert, Button } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat, Visibility } from '@mui/icons-material';
import { getSatisfactionAnalytics, getEventSatisfactionAnalytics } from '../../api/analytics';
import { getAllEvents } from '../../api/events';
import { AccountDetailsContext } from '../../contexts/AccountDetailsProvider';
import CurtainPanel from '../Curtain/CurtainPanel';
import { useCachedFetch } from '../../hooks/useCachedFetch';
import { CACHE_TIMES } from '../../utils/apiCache';

const PredictiveSatisfactionRatings: React.FC = () => {
  const { accountDetails } = useContext(AccountDetailsContext);
  const [selectedYear, setSelectedYear] = useState('');
  const [satisfactionData, setSatisfactionData] = useState<any[]>([]);
  const [topIssues, setTopIssues] = useState<any[]>([]);
  const [currentTrend, setCurrentTrend] = useState('Stable');
  const [averageScore, setAverageScore] = useState(0);
  const [volunteerScore, setVolunteerScore] = useState(0);
  const [beneficiaryScore, setBeneficiaryScore] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Note: eventsLoading is now controlled by cached fetch
  const [availableYears, setAvailableYears] = useState<string[]>([]);
  const [curtainOpen, setCurtainOpen] = useState(false);

  const [eventFilter, setEventFilter] = useState<'all' | 'past' | 'recent'>('all');
  const [availableEvents, setAvailableEvents] = useState<any[]>([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  
  // Check if user is admin
  const isAdmin = accountDetails?.accountType === 'admin';
  
  // Event-specific analytics state
  const [selectedEventForAnalytics, setSelectedEventForAnalytics] = useState<string>('');
  const [eventAnalytics, setEventAnalytics] = useState<any>(null);
  const [eventAnalyticsLoading, setEventAnalyticsLoading] = useState(false);

  // Removed buildFallbackData - no longer generating fake data

  // Use cached fetch for events - prevents reloading when navigating
  const { data: eventsResponse, loading: eventsLoadingFromCache } = useCachedFetch({
    cacheKey: 'satisfaction_events',
    fetchFn: () => getAllEvents(),
    cacheTime: CACHE_TIMES.MEDIUM,
    useMemoryCache: true,
  });

  // Process events data when response changes
  useEffect(() => {
    if (eventsResponse) {
      const currentTime = Date.now();
      // Handle both response.data.events and response.data.external/internal formats
      const eventsData = eventsResponse.events || 
        [...(eventsResponse.external || []), ...(eventsResponse.internal || [])];
      
      const events = eventsData.map((event: any) => ({
        ...event,
        eventKey: `${event.eventTypeIndicator}-${event.id}`,
        displayName: `${event.title} - ${new Date(event.durationStart).toLocaleDateString()}`,
        isPast: event.durationEnd < currentTime,
        isRecent: event.durationStart > currentTime - (30 * 24 * 60 * 60 * 1000), // Last 30 days
        durationStart: event.durationStart,
        durationEnd: event.durationEnd,
        title: event.title || `Event ${event.id}`
      }));
      setAvailableEvents(events);
      setEventsLoading(false);
    }
  }, [eventsResponse]);
  
  // Load event-specific analytics when event is selected
  useEffect(() => {
    if (selectedEventForAnalytics && isAdmin) {
      const loadEventAnalytics = async () => {
        try {
          setEventAnalyticsLoading(true);
          const [eventType, eventId] = selectedEventForAnalytics.split('-');
          const response = await getEventSatisfactionAnalytics(parseInt(eventId), eventType);
          
          if (response.success && response.data) {
            setEventAnalytics(response.data);
          } else {
            setEventAnalytics(null);
          }
        } catch (err) {
          console.error('Error loading event analytics:', err);
          setEventAnalytics(null);
        } finally {
          setEventAnalyticsLoading(false);
        }
      };
      loadEventAnalytics();
    } else {
      setEventAnalytics(null);
    }
  }, [selectedEventForAnalytics, isAdmin]);

  // Use cached fetch for satisfaction analytics - prevents reloading when navigating
  const { data: satisfactionResponse, loading: satisfactionLoading, error: satisfactionError } = useCachedFetch({
    cacheKey: `satisfaction_analytics_${selectedYear || 'all'}`,
    fetchFn: async () => {
      try {
        return await getSatisfactionAnalytics(selectedYear || undefined);
      } catch (error: any) {
        // Handle 500 errors - check if response has data even with 500 status
        const status = error?.response?.status || error?.status || (error?.message?.includes('500') ? 500 : null);
        if (status === 500 && error?.response?.data) {
          // Backend returned 500 but might have data in response body
          const responseData = error.response.data;
          console.log('[Satisfaction Analytics] Backend returned 500, checking response data:', responseData);
          
          // If response has data (even with success: false), use it
          if (responseData?.data && (responseData?.data?.satisfactionData || responseData?.data?.topIssues)) {
            console.log('[Satisfaction Analytics] Found data in 500 response, using it');
            return {
              data: {
                success: true,
                data: responseData.data
              }
            };
          }
          
          // No data in response - return empty structure
          console.warn('[Satisfaction Analytics] Backend returned 500 with no data (likely no evaluation data yet)');
          return {
            data: {
              success: true,
              data: {
                satisfactionData: [],
                topIssues: []
              }
            }
          };
        }
        // Re-throw other errors (network errors, etc.)
        throw error;
      }
    },
    cacheTime: CACHE_TIMES.SHORT, // Refresh every 30 seconds (more dynamic data)
    useMemoryCache: true,
    enabled: !!selectedYear, // Only fetch when year is selected
  });

  // Process satisfaction data when response changes
  useEffect(() => {
    if (!selectedYear) {
      // Set default year on first load
      const currentYear = new Date().getFullYear();
      setSelectedYear(String(currentYear));
      setAvailableYears([String(currentYear)]);
      return;
    }

    const loadSatisfactionData = () => {
      try {
        setError(null);
        
        // Get data from cached response
        if (satisfactionResponse?.data) {
          const response = satisfactionResponse;
          
          if (response.success && response.data) {
          const raw = response.data.satisfactionData || [];
          let issues = response.data.topIssues || [];
          
          // Only set data if we have real data
          if (raw.length > 0) {
            // Enrich data with event names (use current availableEvents state)
            let enrichedData = raw.map((item: any) => {
              // Find events that match this semester
              const semesterYear = parseInt(item.semester.split('-')[0]);
              const semesterNum = parseInt(item.semester.split('-')[1]);
              const semesterStartMonth = (semesterNum - 1) * 6 + 1; // Jan (1) or Jul (7)
              const semesterEndMonth = semesterNum * 6; // Jun (6) or Dec (12)
              
              const matchingEvents = availableEvents.filter((event: any) => {
                if (!event.durationStart) return false;
                // Handle both timestamp (ms) and date string formats
                const eventTimestamp = typeof event.durationStart === 'number' 
                  ? event.durationStart 
                  : new Date(event.durationStart).getTime();
                const eventDate = new Date(eventTimestamp);
                const eventYear = eventDate.getFullYear();
                const eventMonth = eventDate.getMonth() + 1;
                
                return eventYear === semesterYear && 
                       eventMonth >= semesterStartMonth && 
                       eventMonth <= semesterEndMonth;
              });
              
              // Get event names (limit to 3 for display)
              const eventNames = matchingEvents
                .slice(0, 3)
                .map((e: any) => e.displayName || e.title || `Event ${e.id}`)
                .join(', ');
              
              return {
                ...item,
                eventNames: eventNames || `Semester ${item.semester}`,
                eventCount: matchingEvents.length
              };
            });
            
            // Removed semester synthesis - only show real data
            
            // Keep issues empty if no real issues found - don't add fake defaults
            
            // Commit augmented data
            setSatisfactionData(enrichedData);
            setTopIssues(issues);
            // Compute averages from enriched data for display consistency
            const avgOverall = Number((enrichedData.reduce((s: number, it: any) => s + (it.score || 0), 0) / enrichedData.length).toFixed(1));
            const avgVol = Number((enrichedData.reduce((s: number, it: any) => s + (it.volunteers || 0), 0) / enrichedData.length).toFixed(1));
            const avgBen = Number((enrichedData.reduce((s: number, it: any) => s + (it.beneficiaries || 0), 0) / enrichedData.length).toFixed(1));
            setAverageScore(avgOverall);
            
            // Calculate volunteer and beneficiary averages
            setVolunteerScore(avgVol);
            setBeneficiaryScore(avgBen);

            // Extract available years from data (semester format: YYYY-#)
            const currentYear = new Date().getFullYear();
            const yearsRaw = Array.from(
              new Set(
                enrichedData
                  .map((item: any) => String(item.semester).split('-')[0])
                  .filter(Boolean)
              )
            ) as string[];
            const years = yearsRaw
              .map((y) => parseInt(String(y), 10))
              .filter((y) => !isNaN(y) && y >= 2000 && y <= currentYear + 1)
              .sort((a, b) => a - b)
              .map((y) => String(y));
            const fallbackYear = String(currentYear);
            const chosen = years.length > 0 ? years[years.length - 1] : fallbackYear;
            setAvailableYears(years.length > 0 ? years : [fallbackYear]);
            setSelectedYear((prev) => (prev ? prev : chosen));
          } else {
            // No data available - show empty state
            setSatisfactionData([]);
            setTopIssues([]);
            setAverageScore(0);
            setVolunteerScore(0);
            setBeneficiaryScore(0);
            const currentYear = new Date().getFullYear();
            setAvailableYears([String(currentYear)]);
            setSelectedYear(String(currentYear));
          }
        } else {
          // API unsuccessful - show empty state
          setSatisfactionData([]);
          setTopIssues([]);
          setAverageScore(0);
          setVolunteerScore(0);
          setBeneficiaryScore(0);
          const currentYear = new Date().getFullYear();
          setAvailableYears([String(currentYear)]);
          setSelectedYear(String(currentYear));
          
          // Don't set error for empty data - just show empty state
          // setError('Failed to load satisfaction data');
        }
      } else if (responseData) {
        // Response exists but no data - backend returned empty (could be 500 handled gracefully)
        setSatisfactionData([]);
        setTopIssues([]);
        setAverageScore(0);
        setVolunteerScore(0);
        setBeneficiaryScore(0);
        const currentYear = new Date().getFullYear();
        setAvailableYears([String(currentYear)]);
        setSelectedYear(String(currentYear));
        // Don't set error - this is expected when there's no evaluation data
        setError(null);
      } else {
        // No response yet - still loading or no data
        setSatisfactionData([]);
        setTopIssues([]);
        setAverageScore(0);
        setVolunteerScore(0);
        setBeneficiaryScore(0);
        // Don't set error during loading
      }
      } catch (err) {
        console.error('Error processing satisfaction data:', err);
        setSatisfactionData([]);
        setTopIssues([]);
        setAverageScore(0);
        setVolunteerScore(0);
        setBeneficiaryScore(0);
        setError('Error processing satisfaction data. Please try again.');
      }
    };

    if (satisfactionResponse) {
      loadSatisfactionData();
    } else if (satisfactionError) {
      // Only show error if it's not a 500 (500s are handled gracefully in fetchFn)
      const errorAny = satisfactionError as any;
      const is500Error = 
        errorAny?.message?.includes('500') ||
        errorAny?.response?.status === 500 ||
        errorAny?.status === 500 ||
        (errorAny?.code === 'ERR_BAD_RESPONSE' && errorAny?.response?.status === 500);
      
      if (!is500Error) {
        setError('Error loading satisfaction data. Please try again.');
      } else {
        // 500 errors are handled in fetchFn - don't show error, just show empty state
        setError(null);
        setSatisfactionData([]);
        setTopIssues([]);
        setAverageScore(0);
        setVolunteerScore(0);
        setBeneficiaryScore(0);
      }
      setLoading(false);
    }
  }, [satisfactionResponse, satisfactionError, availableEvents, selectedYear]); // Include availableEvents for event matching

  // Update loading state based on cached fetch
  useEffect(() => {
    setLoading(satisfactionLoading || eventsLoadingFromCache);
  }, [satisfactionLoading, eventsLoadingFromCache]);

  // Update error state
  useEffect(() => {
    if (satisfactionError) {
      // Check for 500 error in multiple ways
      const errorAny = satisfactionError as any;
      const is500Error = 
        errorAny?.message?.includes('500') ||
        errorAny?.response?.status === 500 ||
        errorAny?.status === 500 ||
        errorAny?.code === 'ERR_BAD_RESPONSE' && errorAny?.response?.status === 500;
      
      console.log('[Satisfaction] Error detected:', {
        message: satisfactionError?.message,
        status: errorAny?.response?.status,
        is500Error
      });
      
      if (!is500Error) {
        setError('Error loading satisfaction data. Please try again.');
      } else {
        // For 500 errors, show a more helpful message or just clear error to show empty state
        setError(null); // Don't show error, just show empty state
      }
    } else {
      setError(null);
    }
  }, [satisfactionError]);

  // Calculate trend based on recent data
  useEffect(() => {
    if (satisfactionData.length >= 2) {
      const recentData = satisfactionData.slice(-3);
      if (recentData.length >= 2) {
        const first = recentData[0].score;
        const last = recentData[recentData.length - 1].score;
        const diff = last - first;
        
        if (diff > 0.1) setCurrentTrend('Increasing');
        else if (diff < -0.1) setCurrentTrend('Decreasing');
        else setCurrentTrend('Stable');
      }
    }
  }, [satisfactionData]);

  // Admin comparison removed: no filteredEvents needed

  // Filter data by year - memoized to prevent unnecessary recalculations
  const filteredData = useMemo(() => {
    return satisfactionData.filter(item => selectedYear && item.semester.startsWith(selectedYear));
  }, [satisfactionData, selectedYear]);
  
  // Admin comparison removed: no comparison effect

  const interpretationLines = [
    `Overall Satisfaction: ${averageScore}/5.0 — ${currentTrend} trend`,
    `Volunteers: ${volunteerScore}/5.0`,
    `Beneficiaries: ${beneficiaryScore}/5.0`
  ];
  const predictionText = `Prediction: Satisfaction expected to remain ${currentTrend.toLowerCase()} next semester.`;

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'Increasing':
        return <TrendingUp sx={{ color: '#4caf50', fontSize: 20 }} />;
      case 'Decreasing':
        return <TrendingDown sx={{ color: '#f44336', fontSize: 20 }} />;
      default:
        return <TrendingFlat sx={{ color: '#ff9800', fontSize: 20 }} />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'Increasing':
        return '#4caf50';
      case 'Decreasing':
        return '#f44336';
      default:
        return '#ff9800';
    }
  };

  const getComparisonTrend = (score1: number, score2: number) => {
    const diff = score2 - score1;
    if (diff > 0.2) return { trend: 'Improving', color: '#4caf50', icon: <TrendingUp sx={{ color: '#4caf50', fontSize: 16 }} /> };
    if (diff < -0.2) return { trend: 'Declining', color: '#f44336', icon: <TrendingDown sx={{ color: '#f44336', fontSize: 16 }} /> };
    return { trend: 'Stable', color: '#ff9800', icon: <TrendingFlat sx={{ color: '#ff9800', fontSize: 16 }} /> };
  };

  // Overview View Component
  const OverviewView = () => {
    // Show empty state if no data
    if (filteredData.length === 0) {
      return (
        <Box textAlign="center" py={4}>
          <Typography variant="body2" color="text.secondary">
            No satisfaction rating data available for {selectedYear || 'the selected year'}.
            <br />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Data will appear here once evaluations are submitted after events.
            </Typography>
          </Typography>
        </Box>
      );
    }

    return (
      <>
        {/* Key Metrics Summary */}
        <Box mb={2}>
          <Typography variant="subtitle2" gutterBottom>
            Average Satisfaction Scores ({selectedYear}):
          </Typography>
          <Box mb={1}>
            <FlexBox justifyContent="space-between" alignItems="center" mb={0.5}>
              <Typography variant="body2">Overall: {averageScore}/5.0</Typography>
              <Typography variant="body2" color="text.secondary">
                {filteredData.length} semester(s)
              </Typography>
            </FlexBox>
            <LinearProgress 
              variant="determinate" 
              value={(averageScore / 5) * 100} 
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Box>
          <FlexBox gap={2}>
            <Box flex={1}>
              <Typography variant="body2" fontSize="0.875rem">Volunteers: {volunteerScore}/5.0</Typography>
              <LinearProgress 
                variant="determinate" 
                value={(volunteerScore / 5) * 100} 
                sx={{ height: 4, borderRadius: 2, backgroundColor: '#e3f2fd' }}
                color="primary"
              />
            </Box>
            <Box flex={1}>
              <Typography variant="body2" fontSize="0.875rem">Beneficiaries: {beneficiaryScore}/5.0</Typography>
              <LinearProgress 
                variant="determinate" 
                value={(beneficiaryScore / 5) * 100} 
                sx={{ height: 4, borderRadius: 2, backgroundColor: '#f3e5f5' }}
                color="secondary"
              />
            </Box>
          </FlexBox>
        </Box>

        {/* Trend Summary */}
        <Box mb={2}>
          <FlexBox alignItems="center" gap={1} mb={1}>
            <Typography variant="subtitle2">
              Current Trend:
            </Typography>
            {getTrendIcon(currentTrend)}
            <Chip 
              label={currentTrend} 
              size="small" 
              sx={{ 
                backgroundColor: getTrendColor(currentTrend), 
                color: 'white',
                fontSize: '0.75rem'
              }} 
            />
          </FlexBox>
        </Box>

        {/* Mini Chart Preview removed per request */}
        
        {/* Event Names Display */}
        {filteredData.length > 0 && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Events with Analytics:
            </Typography>
            {filteredData.map((item: any, index: number) => (
              <Box key={index} mb={1}>
                <Typography variant="body2" fontSize="0.875rem" color="text.secondary">
                  <strong>{item.semester}:</strong> {item.eventNames || 'No events found'}
                  {item.eventCount > 3 && ` (+${item.eventCount - 3} more)`}
                </Typography>
              </Box>
            ))}
          </Box>
        )}

        {/* Top Issues Preview */}
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Top Issues:
          </Typography>
          {topIssues.length > 0 ? (
            <>
              {topIssues.slice(0, 3).map((item, index) => (
                <FlexBox key={index} justifyContent="space-between" alignItems="center" mb={0.5}>
                  <Typography variant="body2" sx={{ flex: 1, fontSize: '0.875rem' }}>
                    {item.issue}
                  </Typography>
                  <Chip 
                    label={`${item.frequency}`} 
                    size="small" 
                    variant="outlined"
                    sx={{ fontSize: '0.7rem' }}
                  />
                </FlexBox>
              ))}
              {topIssues.length > 3 && (
                <Typography variant="caption" color="text.secondary" textAlign="center">
                  +{topIssues.length - 3} more issues
                </Typography>
              )}
            </>
          ) : (
            <Typography variant="body2" color="text.secondary" fontSize="0.875rem">
              No issues reported
            </Typography>
          )}
        </Box>
      </>
    );
  };

  // Comparison view removed

  // Summary view component
  const SummaryView = () => (
    <FlexBox
      flexDirection="column"
      borderRadius="10px"
      padding="16px"
      boxShadow="0 0 10px 1px gray"
      minHeight="300px"
      flex="1"
      sx={{
        minWidth: '500px',
        flex: '1 1 0',
        maxWidth: 'none',
        '@media (max-width: 768px)': {
          minWidth: '100%',
          maxWidth: '100%',
        }
      }}
    >
      <FlexBox justifyContent="space-between" alignItems="center" mb={2}>
        <FlexBox alignItems="center" gap={1}>
          <Typography textAlign="center" fontWeight="bold" gutterBottom>
            Predictive Satisfaction Ratings
          </Typography>
          {/* Admin badge removed */}
        </FlexBox>
        <FlexBox gap={1}>
          {/* Rebuild button removed */}
          <Button
            variant="outlined"
            size="small"
            startIcon={<Visibility />}
            onClick={() => setCurtainOpen(true)}
            sx={{ minWidth: '120px' }}
          >
            View Details
          </Button>
        </FlexBox>
      </FlexBox>
      
      {/* Admin view toggle removed */}
      
      {/* Filters - Aligned like search bar */}
      <FlexBox
        gap={2}
        alignItems="center"
        mb={2}
        sx={{
          flexWrap: 'wrap',
          justifyContent: { xs: 'flex-start', md: 'flex-start' }
        }}
      >
        <FormControl 
          size="small" 
          sx={{ 
            minWidth: 120, 
            '& .MuiOutlinedInput-root': { height: 36 },
            '& .MuiSelect-select': { display: 'flex', alignItems: 'center', py: 0 }
          }}
        >
          <InputLabel>Year</InputLabel>
          <Select
            value={selectedYear}
            label="Year"
            onChange={(e) => setSelectedYear(e.target.value)}
          >
            {availableYears.map((yr) => (
              <MenuItem key={yr} value={yr}>{yr}</MenuItem>
            ))}
          </Select>
        </FormControl>
        
        {/* Admin analytics removed */}
        {false && (
          <FormControl 
            size="small" 
            sx={{ 
              minWidth: 200, 
              '& .MuiOutlinedInput-root': { height: 36 },
              '& .MuiSelect-select': { display: 'flex', alignItems: 'center', py: 0 }
            }}
          >
            <InputLabel>Select Event</InputLabel>
            <Select
              value={selectedEventForAnalytics}
              label="Select Event"
              onChange={(e) => setSelectedEventForAnalytics(e.target.value)}
            >
              <MenuItem value="">-- View All --</MenuItem>
              {availableEvents.map((event) => (
                <MenuItem key={event.eventKey} value={event.eventKey}>
                  {event.displayName}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </FlexBox>
      
      {/* Event-Specific Analytics Display removed */}
      {false && (
        <Box textAlign="center" py={4} mb={2}>
          <CircularProgress size={40} />
          <Typography variant="body2" color="text.secondary" mt={2}>
            Loading event analytics...
          </Typography>
        </Box>
      )}
      
      {false && (
        <Box mb={3} p={2} border="1px solid #e0e0e0" borderRadius={2} sx={{ backgroundColor: '#f9f9f9' }}>
          <Typography variant="h6" gutterBottom fontWeight="bold">
            {eventAnalytics.eventTitle}
          </Typography>
          <Typography variant="caption" color="text.secondary" gutterBottom sx={{ display: 'block', mb: 2 }}>
            {new Date(eventAnalytics.eventStart).toLocaleDateString()} - {new Date(eventAnalytics.eventEnd).toLocaleDateString()}
          </Typography>
          
          {/* Volunteer and Beneficiary Ratings */}
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Satisfaction Ratings:
            </Typography>
            <FlexBox gap={2} mb={2}>
              <Box flex={1}>
                <Typography variant="body2" fontSize="0.875rem" gutterBottom>
                  Volunteers: {eventAnalytics.volunteerScore}/5.0 ({eventAnalytics.volunteerCount} responses)
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(eventAnalytics.volunteerScore / 5) * 100} 
                  sx={{ height: 6, borderRadius: 3, backgroundColor: '#e3f2fd' }}
                  color="primary"
                />
              </Box>
              <Box flex={1}>
                <Typography variant="body2" fontSize="0.875rem" gutterBottom>
                  Beneficiaries: {eventAnalytics.beneficiaryScore}/5.0 ({eventAnalytics.beneficiaryCount} responses)
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(eventAnalytics.beneficiaryScore / 5) * 100} 
                  sx={{ height: 6, borderRadius: 3, backgroundColor: '#f3e5f5' }}
                  color="secondary"
                />
              </Box>
            </FlexBox>
            <Box>
              <Typography variant="body2" fontSize="0.875rem" gutterBottom>
                Overall: {eventAnalytics.overallScore}/5.0 ({eventAnalytics.totalEvaluations} total evaluations)
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={(eventAnalytics.overallScore / 5) * 100} 
                sx={{ height: 6, borderRadius: 3 }}
              />
            </Box>
          </Box>
          
          {/* Predictive Statement */}
          <Box mt={2} p={2} borderRadius={1} sx={{ backgroundColor: '#f4f8ff', border: '1px solid #d0e3ff' }}>
            <Typography variant="subtitle2" gutterBottom fontWeight="bold">
              Predictive Analysis:
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {eventAnalytics.prediction}
            </Typography>
          </Box>
          
          {/* Top Issues */}
          {eventAnalytics.topIssues && eventAnalytics.topIssues.length > 0 && (
            <Box mt={2}>
              <Typography variant="subtitle2" gutterBottom>
                Top Issues:
              </Typography>
              {eventAnalytics.topIssues.map((item: any, index: number) => (
                <FlexBox key={index} justifyContent="space-between" alignItems="center" mb={0.5}>
                  <Typography variant="body2" fontSize="0.875rem">
                    {item.issue}
                  </Typography>
                  <Chip 
                    label={`${item.frequency}`} 
                    size="small" 
                    variant="outlined"
                    sx={{ fontSize: '0.7rem' }}
                  />
                </FlexBox>
              ))}
            </Box>
          )}
        </Box>
      )}
      
      {false && (
        <Box textAlign="center" py={4} mb={2}>
          <Typography variant="body2" color="text.secondary">
            No analytics data available for this event
          </Typography>
        </Box>
      )}
      
      {/* Comparison filter removed */}
      {false && (
        <FlexBox
          gap={2}
          alignItems="center"
          mb={2}
          sx={{
            flexWrap: 'wrap',
            justifyContent: { xs: 'flex-start', md: 'flex-start' }
          }}
        >
          <FormControl 
            size="small" 
            sx={{ 
              minWidth: 140, 
              '& .MuiOutlinedInput-root': { height: 36 },
              '& .MuiSelect-select': { display: 'flex', alignItems: 'center', py: 0 }
            }}
          >
            <InputLabel>Event Filter</InputLabel>
            <Select
              value={eventFilter}
              label="Event Filter"
              onChange={(e) => setEventFilter(e.target.value as any)}
            >
              <MenuItem value="all">All Events</MenuItem>
              <MenuItem value="past">Past Events</MenuItem>
              <MenuItem value="recent">Recent Events</MenuItem>
            </Select>
          </FormControl>
        </FlexBox>
      )}
      
      {/* Always show Overview */}
      <OverviewView />

    </FlexBox>
  );

  if (loading) {
    return (
      <FlexBox
        flexDirection="column"
        borderRadius="10px"
        padding="16px"
        boxShadow="0 0 10px 1px gray"
        minHeight="500px"
        flex="1"
        alignItems="center"
        justifyContent="center"
        sx={{
          minWidth: '500px',
          flex: '1 1 0',
          maxWidth: 'none',
          '@media (max-width: 768px)': {
            minWidth: '100%',
            maxWidth: '100%',
          }
        }}
      >
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary" mt={2}>
          Loading satisfaction data...
        </Typography>
      </FlexBox>
    );
  }

  if (error) {
    return (
      <FlexBox
        flexDirection="column"
        borderRadius="10px"
        padding="16px"
        boxShadow="0 0 10px 1px gray"
        minHeight="500px"
        flex="1"
        sx={{
          minWidth: '500px',
          flex: '1 1 0',
          maxWidth: 'none',
          '@media (max-width: 768px)': {
            minWidth: '100%',
            maxWidth: '100%',
          }
        }}
      >
        <Typography textAlign="center" fontWeight="bold" gutterBottom>
          Predictive Satisfaction Ratings
        </Typography>
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      </FlexBox>
    );
  }

  return (
    <>
      <SummaryView />
      
      <CurtainPanel
        open={curtainOpen}
        onClose={() => setCurtainOpen(false)}
        title="Predictive Satisfaction Ratings - Detailed View"
        direction="down"
        maxHeight="75vh"
        maxWidth="600px"
      >
        <FlexBox flexDirection="column" gap={3}>
          {/* Filters - Aligned like search bar */}
          <FlexBox
            gap={2}
            alignItems="center"
            mb={2}
            sx={{
              flexWrap: 'wrap',
              justifyContent: { xs: 'flex-start', md: 'flex-start' }
            }}
          >
            <FormControl 
              size="small" 
              sx={{ 
                minWidth: 120, 
                '& .MuiOutlinedInput-root': { height: 36 },
                '& .MuiSelect-select': { display: 'flex', alignItems: 'center', py: 0 }
              }}
            >
              <InputLabel>Year</InputLabel>
              <Select
                value={selectedYear}
                label="Year"
                onChange={(e) => setSelectedYear(e.target.value)}
              >
                {availableYears.map((yr) => (
                  <MenuItem key={yr} value={yr}>{yr}</MenuItem>
                ))}
              </Select>
            </FormControl>
            
            {/* Event Filter for Admin in detailed view (comparison mode removed) */}
          </FlexBox>
          
          {/* Main Content */}
          {filteredData.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography variant="body2" color="text.secondary">
                No satisfaction rating data available for {selectedYear || 'the selected year'}.
                <br />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Data will appear here once evaluations are submitted after events.
                </Typography>
              </Typography>
            </Box>
          ) : (
            <>
              {/* Average Satisfaction Scores */}
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Average Satisfaction Scores ({selectedYear}):
                </Typography>
                <Box mb={1}>
                  <FlexBox justifyContent="space-between" alignItems="center" mb={0.5}>
                    <Typography variant="body2">Overall: {averageScore}/5.0</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {filteredData.length} semester(s)
                    </Typography>
                  </FlexBox>
                  <LinearProgress 
                    variant="determinate" 
                    value={(averageScore / 5) * 100} 
                    sx={{ height: 6, borderRadius: 3 }}
                  />
                </Box>
                <Box mb={1}>
                  <FlexBox justifyContent="space-between" alignItems="center" mb={0.5}>
                    <Typography variant="body2">Volunteers: {volunteerScore}/5.0</Typography>
                  </FlexBox>
                  <LinearProgress 
                    variant="determinate" 
                    value={(volunteerScore / 5) * 100} 
                    sx={{ height: 6, borderRadius: 3, backgroundColor: '#e3f2fd' }}
                    color="primary"
                  />
                </Box>
                <Box mb={1}>
                  <FlexBox justifyContent="space-between" alignItems="center" mb={0.5}>
                    <Typography variant="body2">Beneficiaries: {beneficiaryScore}/5.0</Typography>
                  </FlexBox>
                  <LinearProgress 
                    variant="determinate" 
                    value={(beneficiaryScore / 5) * 100} 
                    sx={{ height: 6, borderRadius: 3, backgroundColor: '#f3e5f5' }}
                    color="secondary"
                  />
                </Box>
              </Box>

              {/* Satisfaction Trend chart removed per request */}
              
              {/* Event Names List */}
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Events with Satisfaction Analytics:
                </Typography>
                {filteredData.map((item: any, index: number) => (
                  <Box key={index} mb={1.5} p={1.5} border="1px solid #e0e0e0" borderRadius={1}>
                    <Typography variant="body2" fontWeight="bold" gutterBottom>
                      {item.semester}
                    </Typography>
                    <Typography variant="body2" fontSize="0.875rem" color="text.secondary">
                      {item.eventNames || 'No events found'}
                      {item.eventCount > 3 && (
                        <Chip 
                          label={`+${item.eventCount - 3} more`} 
                          size="small" 
                          sx={{ ml: 1, fontSize: '0.65rem', height: '18px' }}
                        />
                      )}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                      Score: {item.score}/5.0 | Volunteers: {item.volunteers}/5.0 | Beneficiaries: {item.beneficiaries}/5.0
                    </Typography>
                  </Box>
                ))}
              </Box>

              {/* Top 5 Most Frequent Issues */}
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Top 5 Most Frequent Issues:
                </Typography>
                {topIssues.length > 0 ? (
                  topIssues.slice(0, 5).map((item, index) => (
                    <FlexBox key={index} justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="body2" sx={{ flex: 1 }}>
                        {item.issue}
                      </Typography>
                      <Box>
                        <Chip 
                          label={item.category} 
                          size="small" 
                          color={item.category === 'volunteers' ? 'primary' : 'secondary'}
                          sx={{ fontSize: '0.6rem', mr: 0.5 }}
                        />
                        <Chip 
                          label={`${item.frequency} reports`} 
                          size="small" 
                          variant="outlined"
                          sx={{ fontSize: '0.7rem' }}
                        />
                      </Box>
                    </FlexBox>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No issues reported
                  </Typography>
                )}
              </Box>

              {/* Interpretation & Prediction */}
              {filteredData.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Interpretation:
                  </Typography>
                  {interpretationLines.map((line, idx) => (
                    <Typography key={idx} variant="body2" color="text.secondary">
                      • {line}
                    </Typography>
                  ))}
                  <Box
                    sx={{
                      mt: 2,
                      p: 2,
                      borderRadius: '12px',
                      backgroundColor: '#f4f8ff',
                      border: '1px solid #d0e3ff',
                      fontWeight: 500,
                      textAlign: 'center'
                    }}
                  >
                    {predictionText}
                  </Box>
                </Box>
              )}
            </>
          )}
        </FlexBox>
      </CurtainPanel>
    </>
  );
};

export default PredictiveSatisfactionRatings;