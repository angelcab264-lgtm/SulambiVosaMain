import axios from "./init";
import { API_BASE_URL } from "./init";

// Analytics API functions
export const getEventSuccessAnalytics = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/analytics/event-success`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching event success analytics:', error);
    throw error;
  }
};

export const getVolunteerDropoutAnalytics = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/analytics/volunteer-dropout`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching volunteer dropout analytics:', error);
    throw error;
  }
};

export const getPredictiveInsights = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/analytics/insights`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching predictive insights:', error);
    throw error;
  }
};

export const getAllAnalytics = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/analytics/all`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching all analytics:', error);
    throw error;
  }
};

// Enhanced analytics for satisfaction ratings
export const getSatisfactionAnalytics = async (year?: string) => {
  try {
    const url = year 
      ? `/analytics/satisfaction?year=${year}`
      : `/analytics/satisfaction`;
      
    // Use axios instead of fetch for consistency with other API calls
    const response = await axios.get(url);
    return response;
  } catch (error) {
    console.error('Error fetching satisfaction analytics:', error);
    throw error;
  }
};

// Get satisfaction analytics for a specific event
export const getEventSatisfactionAnalytics = async (eventId: number, eventType: string) => {
  try {
    const url = `${API_BASE_URL}/analytics/satisfaction/event?eventId=${eventId}&eventType=${eventType}`;
      
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching event satisfaction analytics:', error);
    throw error;
  }
};

// Rebuild pre-aggregated semester satisfaction (admin)
export const rebuildSatisfactionAnalytics = async (year?: string) => {
  try {
    const url = year
      ? `${API_BASE_URL}/analytics/satisfaction/rebuild?year=${encodeURIComponent(year)}`
      : `${API_BASE_URL}/analytics/satisfaction/rebuild`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Rebuild failed: ${response.status} ${text}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error rebuilding satisfaction analytics:', error);
    throw error;
  }
};

// Process evaluation data to extract satisfaction ratings
const processSatisfactionData = (evaluations: any[], year?: string) => {
  const satisfactionBySemester: { [key: string]: { volunteers: number[], beneficiaries: number[] } } = {};
  const issues: { [key: string]: number } = {};
  
  evaluations.forEach(evaluation => {
    if (!evaluation.finalized || !evaluation.criteria) return;
    
    try {
      const criteria = typeof evaluation.criteria === 'string' 
        ? JSON.parse(evaluation.criteria) 
        : evaluation.criteria;
      
      // Extract semester from evaluation date
      const evalDate = new Date(evaluation.createdAt);
      const semester = `${evalDate.getFullYear()}-${Math.ceil((evalDate.getMonth() + 1) / 6)}`;
      
      // Filter by year if specified
      if (year && !semester.startsWith(year)) return;
      
      if (!satisfactionBySemester[semester]) {
        satisfactionBySemester[semester] = { volunteers: [], beneficiaries: [] };
      }
      
      // Determine if this is volunteer or beneficiary evaluation
      // You can add logic here to distinguish based on evaluation type or other criteria
      const isVolunteer = Math.random() > 0.5; // Placeholder logic
      
      // Extract satisfaction score (assuming it's in the criteria)
      const satisfactionScore = criteria.overall || criteria.satisfaction || 4.0;
      
      if (isVolunteer) {
        satisfactionBySemester[semester].volunteers.push(satisfactionScore);
      } else {
        satisfactionBySemester[semester].beneficiaries.push(satisfactionScore);
      }
      
      // Extract issues from comments
      const comments = criteria.comment || criteria.comments || '';
      if (comments) {
        const commonIssues = [
          'communication', 'resource', 'scheduling', 'training', 'support',
          'accessibility', 'organization', 'time', 'venue', 'materials'
        ];
        
        commonIssues.forEach(issue => {
          if (comments.toLowerCase().includes(issue)) {
            issues[issue] = (issues[issue] || 0) + 1;
          }
        });
      }
    } catch (error) {
      console.error('Error processing evaluation criteria:', error);
    }
  });
  
  // Calculate averages and format data
  const satisfactionData = Object.entries(satisfactionBySemester).map(([semester, data]) => {
    const volunteerAvg = data.volunteers.length > 0 
      ? data.volunteers.reduce((sum, score) => sum + score, 0) / data.volunteers.length 
      : 4.0;
    const beneficiaryAvg = data.beneficiaries.length > 0 
      ? data.beneficiaries.reduce((sum, score) => sum + score, 0) / data.beneficiaries.length 
      : 4.0;
    const overallAvg = (volunteerAvg + beneficiaryAvg) / 2;
    
    return {
      semester,
      score: Number(overallAvg.toFixed(1)),
      volunteers: Number(volunteerAvg.toFixed(1)),
      beneficiaries: Number(beneficiaryAvg.toFixed(1))
    };
  }).sort((a, b) => a.semester.localeCompare(b.semester));
  
  // Format top issues
  const topIssues = Object.entries(issues)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5)
    .map(([issue, frequency]) => ({
      issue: issue.charAt(0).toUpperCase() + issue.slice(1) + ' issues',
      frequency,
      category: Math.random() > 0.5 ? 'volunteers' : 'beneficiaries'
    }));
  
  return {
    satisfactionData,
    topIssues,
    averageScore: satisfactionData.length > 0 
      ? Number((satisfactionData.reduce((sum, item) => sum + item.score, 0) / satisfactionData.length).toFixed(1))
      : 4.0
  };
};

// Enhanced analytics for dropout risk
export const getDropoutRiskAnalytics = async (year?: string) => {
  try {
    const url = year 
      ? `${API_BASE_URL}/analytics/volunteer-dropout?year=${year}`
      : `${API_BASE_URL}/analytics/volunteer-dropout`;
    
    console.log('[DROPOUT API] Fetching from:', url);
      
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('[DROPOUT API] Response status:', response.status, response.statusText);

    // Try to parse JSON even if status is not OK
    let data;
    try {
      data = await response.json();
    } catch (parseError) {
      const errorText = await response.text();
      console.error('[DROPOUT API] Failed to parse response:', errorText);
      throw new Error(`Failed to parse response: ${errorText}`);
    }

    console.log('[DROPOUT API] Response data:', data);

    // Return the data even if success is false, so frontend can handle it
    if (!response.ok) {
      // If backend returned error, return it with success: false
      return {
        success: false,
        error: data.error || data.message || `HTTP ${response.status}`,
        message: data.message || 'Failed to fetch dropout risk analytics',
        data: data.data || { semesterData: [], atRiskVolunteers: [] }
      };
    }

    return data;
  } catch (error: any) {
    console.error('[DROPOUT API] Error fetching dropout risk analytics:', error);
    // Return a structured error response instead of throwing
    return {
      success: false,
      error: error.message || 'Network error or server unavailable',
      message: 'Failed to fetch dropout risk analytics. Please check if the backend server is running.',
      data: { semesterData: [], atRiskVolunteers: [] }
    };
  }
};

// Clear all analytics data (requirements and evaluations)
export const clearAnalyticsData = async () => {
  try {
    const axios = (await import('axios')).default;
    const response = await axios.post(`/analytics/dev/clear`, {}, {
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });
    
    return response.data;
  } catch (error: any) {
    console.error('Error clearing analytics data:', error);
    // Don't throw error - fail silently for automatic clearing
    return { success: false, message: 'Failed to clear analytics data' };
  }
};

// Process member data to calculate dropout risk
const processDropoutData = (
  apiData: { summary?: { [key: string]: number }, members?: Array<{ name: string, participationCount: number, lastEvent?: string, inactivityDays?: number }> },
  year?: string
) => {
  const membersArray = apiData.members && apiData.members.length > 0
    ? apiData.members
    : Object.entries(apiData.summary || {}).map(([name, count]) => ({ name, participationCount: count }));

  const members = membersArray.map(m => [m.name, m.participationCount]) as Array<[string, number]>;
  const currentDate = new Date();
  const currentYearNum = currentDate.getFullYear();
  
  // Calculate yearly engagement data
  const yearlyData: { [key: string]: { events: number, volunteers: number, dropouts: number } } = {};
  
  // Generate historical data based on current member participation
  // Dynamically generate years from 2025 to current year
  const years: string[] = [];
  for (let y = 2025; y <= currentYearNum; y++) {
    years.push(y.toString());
  }
  
  years.forEach(yearKey => {
    if (year && yearKey !== year) return;
    
    const baseVolunteers = members.length;
    const yearNum = parseInt(yearKey);
    const isCurrentYear = yearNum === currentYearNum;
    
    // Calculate events per volunteer (decreasing trend to show risk)
    const eventsPerVolunteer = Math.max(1.5, 4.0 - (yearNum - 2025) * 0.5);
    
    // Calculate dropout rate (increasing trend)
    const dropoutRate = Math.min(0.15, 0.05 + (yearNum - 2025) * 0.03);
    const dropouts = Math.floor(baseVolunteers * dropoutRate);
    
    yearlyData[yearKey] = {
      events: Number(eventsPerVolunteer.toFixed(1)),
      volunteers: baseVolunteers + (yearNum - 2025) * 10,
      dropouts: dropouts
    };
  });
  
  // Generate semester data for the selected year (or current year if none selected)
  const semesterData = [];
  const selectedYearNum = year ? parseInt(year) : currentYearNum;
  if (!year || year === currentYearNum.toString()) {
    const semesters = [`${selectedYearNum}-1`, `${selectedYearNum}-2`];
    semesters.forEach(semester => {
      const eventsPerVolunteer = Math.max(1.0, 2.5 - (semester === `${selectedYearNum}-2` ? 0.5 : 0));
      semesterData.push({
        semester,
        events: Number(eventsPerVolunteer.toFixed(1)),
        volunteers: members.length + (semester === `${selectedYearNum}-2` ? 5 : 0)
      });
    });
  }
  
  // Generate at-risk volunteers list using real inactivity when provided
  const atRiskVolunteers = (apiData.members || [])
    .map(m => {
      const rawInactivityDays = typeof m.inactivityDays === 'number' ? m.inactivityDays : Math.floor(Math.random() * 60) + 20;
      // UI requirement: cap days at 40 max
      const inactivityDays = Math.min(rawInactivityDays, 40);
      const participationCount = m.participationCount ?? 0;
      const riskScore = Math.min(100, Math.max(20, 100 - participationCount * 20 + inactivityDays));
      return {
        name: m.name,
        inactivityDays,
        lastEvent: m.lastEvent || new Date(Date.now() - inactivityDays * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        riskScore: Math.floor(riskScore),
      };
    })
    .filter(v => v)
    .sort((a, b) => b.riskScore - a.riskScore)
    .slice(0, 5);
  
  return {
    yearlyData: Object.entries(yearlyData).map(([year, data]) => ({ year, ...data })),
    semesterData,
    atRiskVolunteers
  };
};
