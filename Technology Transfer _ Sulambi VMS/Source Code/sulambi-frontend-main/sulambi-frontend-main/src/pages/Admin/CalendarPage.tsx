import { useState, useEffect } from "react";
import { Box, Typography, Grid, Card, CardContent, Chip } from "@mui/material";
import { CalendarToday, LocationOn, AccessTime, People } from "@mui/icons-material";
import TextHeader from "../../components/Headers/TextHeader";
import TextSubHeader from "../../components/Headers/TextSubHeader";
import PageLayout from "../PageLayout";
import { getAllEvents } from "../../api/events";
import { ExternalEventProposalType, InternalEventProposalType } from "../../interface/types";
import dayjs from "dayjs";
import { useCachedFetch } from "../../hooks/useCachedFetch";
import { CACHE_TIMES } from "../../utils/apiCache";

const CalendarPage = () => {
  // Use cached fetch - data persists when navigating away and coming back!
  const { data: eventsResponse, loading } = useCachedFetch({
    cacheKey: 'calendar_events',
    fetchFn: () => getAllEvents(),
    cacheTime: CACHE_TIMES.MEDIUM, // Cache for 5 minutes
    useMemoryCache: true, // Fast memory cache for navigation
  });

  // Process events data
  const events = eventsResponse
    ? [...(eventsResponse.external || []), ...(eventsResponse.internal || [])]
        .filter(event => event.status === "accepted")
        .sort((a, b) => a.durationStart - b.durationStart)
    : [];

  const formatDate = (timestamp: number) => {
    return dayjs(timestamp).format("MMM DD, YYYY");
  };

  const formatTime = (timestamp: number) => {
    return dayjs(timestamp).format("h:mm A");
  };

  const getEventLocation = (event: ExternalEventProposalType | InternalEventProposalType) => {
    return 'location' in event ? event.location : event.venue;
  };

  const getEventType = (event: ExternalEventProposalType | InternalEventProposalType) => {
    return 'location' in event ? 'External' : 'Internal';
  };

  const getEventColor = (event: ExternalEventProposalType | InternalEventProposalType) => {
    return 'location' in event ? '#1976d2' : '#2e7d32';
  };

  if (loading) {
    return (
      <PageLayout page="calendar">
        <TextHeader>CALENDAR</TextHeader>
        <TextSubHeader>Loading events...</TextSubHeader>
      </PageLayout>
    );
  }

  return (
    <PageLayout page="calendar">
      <TextHeader>CALENDAR</TextHeader>
      <TextSubHeader gutterBottom>
        View all upcoming and past events in calendar format
      </TextSubHeader>
      
      <Box sx={{ marginTop: 3 }}>
        {events.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '400px',
              textAlign: 'center'
            }}
          >
            <CalendarToday sx={{ fontSize: 64, color: "#666" }} />
            <Typography variant="h6" color="text.secondary" sx={{ marginTop: 2 }}>
              No events scheduled
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Events will appear here once they are created and approved
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={3}>
            {events.map((event) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={event.id}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 8px 25px rgba(0,0,0,0.15)'
                    }
                  }}
                >
                  <CardContent sx={{ flexGrow: 1, padding: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 1 }}>
                      <Chip
                        label={getEventType(event)}
                        size="small"
                        sx={{
                          backgroundColor: getEventColor(event),
                          color: 'white',
                          fontWeight: 'bold'
                        }}
                      />
                    </Box>
                    
                    <Typography variant="h6" component="h3" sx={{ 
                      fontWeight: 'bold', 
                      marginBottom: 1,
                      fontSize: '1.1rem',
                      lineHeight: 1.3
                    }}>
                      {event.title}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', marginBottom: 1, color: 'text.secondary' }}>
                      <CalendarToday sx={{ fontSize: 16, marginRight: 1 }} />
                      <Typography variant="body2">
                        {formatDate(event.durationStart)}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', marginBottom: 1, color: 'text.secondary' }}>
                      <AccessTime sx={{ fontSize: 16, marginRight: 1 }} />
                      <Typography variant="body2">
                        {formatTime(event.durationStart)} - {formatTime(event.durationEnd)}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', marginBottom: 1, color: 'text.secondary' }}>
                      <LocationOn sx={{ fontSize: 16, marginRight: 1 }} />
                      <Typography variant="body2" sx={{ 
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {getEventLocation(event)}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', color: 'text.secondary' }}>
                      <People sx={{ fontSize: 16, marginRight: 1 }} />
                      <Typography variant="body2">
                        {event.status === 'accepted' ? 'Open for Registration' : event.status}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
    </PageLayout>
  );
};

export default CalendarPage;
