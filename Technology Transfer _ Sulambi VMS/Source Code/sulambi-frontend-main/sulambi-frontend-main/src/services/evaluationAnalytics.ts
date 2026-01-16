import dayjs from "dayjs";

// Analytics service for evaluation forms
export interface EvaluationAnalytics {
  volunteerId?: string;
  beneficiaryId?: string;
  eventId: string;
  eventType: 'external' | 'internal';
  evaluationType: 'volunteer' | 'beneficiary';
  timestamp: number;
  responses: {
    [key: string]: any;
  };
  calculatedMetrics: {
    overallSatisfaction?: number;
    averageRating?: number;
    totalResponses: number;
    completionTime: number; // in seconds
  };
}

export interface VolunteerEvaluationData {
  overallSatisfaction: number;
  eventOrganization: number;
  communication: number;
  supportProvided: number;
  learningExperience: number;
  participationLevel: string;
  skillDevelopment: string;
  teamCollaboration: string;
  challenges: string;
  improvements: string;
  additionalComments: string;
}

export interface BeneficiaryEvaluationData {
  overallSatisfaction: number;
  serviceQuality: number;
  volunteerHelpfulness: number;
  impactOnCommunity: number;
  accessibility: number;
  culturalSensitivity: number;
  demographics: {
    age?: string;
    gender?: string;
    location?: string;
  };
  participationFrequency: string;
  additionalComments: string;
}

class EvaluationAnalyticsService {
  private analytics: EvaluationAnalytics[] = [];

  // Submit volunteer evaluation
  async submitVolunteerEvaluation(
    eventId: string,
    eventType: 'external' | 'internal',
    data: VolunteerEvaluationData,
    startTime: number
  ): Promise<EvaluationAnalytics> {
    const completionTime = Math.floor((Date.now() - startTime) / 1000);
    
    // Calculate average rating from numeric fields
    const numericFields = [
      data.overallSatisfaction,
      data.eventOrganization,
      data.communication,
      data.supportProvided,
      data.learningExperience
    ];
    
    const averageRating = numericFields.reduce((sum, rating) => sum + rating, 0) / numericFields.length;

    const analytics: EvaluationAnalytics = {
      volunteerId: `vol_${Date.now()}`, // In real app, this would be the actual volunteer ID
      eventId,
      eventType,
      evaluationType: 'volunteer',
      timestamp: Date.now(),
      responses: data,
      calculatedMetrics: {
        overallSatisfaction: data.overallSatisfaction,
        averageRating,
        totalResponses: Object.keys(data).length,
        completionTime
      }
    };

    this.analytics.push(analytics);
    
    // In a real application, this would send to your backend API
    console.log('Volunteer Evaluation Analytics:', analytics);
    
    return analytics;
  }

  // Submit beneficiary evaluation
  async submitBeneficiaryEvaluation(
    eventId: string,
    eventType: 'external' | 'internal',
    data: BeneficiaryEvaluationData,
    startTime: number,
    eventWindow?: {
      durationEnd: string;
    }
  ): Promise<EvaluationAnalytics> {
    const completionTime = Math.floor((Date.now() - startTime) / 1000);

    // Beneficiary evaluations can be submitted for 1 week after event ends
    if (eventWindow) {
      const end = dayjs(eventWindow.durationEnd);
      const now = dayjs();
      if (end.isValid()) {
        // Check that event has ended
        if (now.isBefore(end)) {
          throw new Error(
            "Evaluations open after the event concludes. Please try again later."
          );
        }
        // Check that event ended within the last 7 days (1 week evaluation window)
        const daysSinceEnd = now.diff(end, 'day', true);
        if (daysSinceEnd > 7) {
          throw new Error(
            "The evaluation window for this event has closed. Evaluations are accepted within 7 days after the event ends."
          );
        }
      }
    }
    
    // Calculate average rating from numeric fields
    const numericFields = [
      data.overallSatisfaction,
      data.serviceQuality,
      data.volunteerHelpfulness,
      data.impactOnCommunity,
      data.accessibility,
      data.culturalSensitivity
    ];
    
    const averageRating = numericFields.reduce((sum, rating) => sum + rating, 0) / numericFields.length;

    // Convert numeric ratings back to text format for criteria
    const ratingToText = (rating: number): string => {
      if (rating >= 5) return "Excellent";
      if (rating >= 4) return "Very Satisfactory";
      if (rating >= 3) return "Satisfactory";
      if (rating >= 2) return "Fair";
      return "Poor";
    };

    // Prepare criteria object matching backend format
    const criteria = {
      overall: ratingToText(data.overallSatisfaction),
      appropriateness: ratingToText(data.serviceQuality),
      expectations: ratingToText(data.volunteerHelpfulness),
      session: ratingToText(data.impactOnCommunity),
      time: ratingToText(data.accessibility),
      materials: ratingToText(data.culturalSensitivity)
    };

    // Submit to backend API
    try {
      const axios = (await import('axios')).default;
      const response = await axios.post('/api/evaluation/beneficiary', {
        eventId: parseInt(eventId),
        eventType: eventType,
        criteria: criteria,
        comment: data.additionalComments || '',
        recommendations: '',
        q13: '', // Empty for beneficiaries
        q14: data.overallSatisfaction.toString(), // Beneficiary rating
        email: data.demographics?.location || '', // Use location or empty
        name: '' // Anonymous beneficiary
      });

      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to submit beneficiary evaluation');
      }
    } catch (error: any) {
      console.error('Error submitting beneficiary evaluation to backend:', error);
      throw new Error(
        error.response?.data?.message || 
        error.message || 
        'Failed to submit beneficiary evaluation. Please try again.'
      );
    }

    const analytics: EvaluationAnalytics = {
      beneficiaryId: `ben_${Date.now()}`,
      eventId,
      eventType,
      evaluationType: 'beneficiary',
      timestamp: Date.now(),
      responses: data,
      calculatedMetrics: {
        overallSatisfaction: data.overallSatisfaction,
        averageRating,
        totalResponses: Object.keys(data).length,
        completionTime
      }
    };

    this.analytics.push(analytics);
    
    return analytics;
  }

  // Get analytics data
  getAnalytics(): EvaluationAnalytics[] {
    return this.analytics;
  }

  // Get analytics by type
  getAnalyticsByType(type: 'volunteer' | 'beneficiary'): EvaluationAnalytics[] {
    return this.analytics.filter(analytic => analytic.evaluationType === type);
  }

  // Get analytics by event
  getAnalyticsByEvent(eventId: string): EvaluationAnalytics[] {
    return this.analytics.filter(analytic => analytic.eventId === eventId);
  }

  // Calculate overall metrics
  calculateOverallMetrics(): {
    totalEvaluations: number;
    volunteerEvaluations: number;
    beneficiaryEvaluations: number;
    averageVolunteerRating: number;
    averageBeneficiaryRating: number;
  } {
    const volunteerAnalytics = this.getAnalyticsByType('volunteer');
    const beneficiaryAnalytics = this.getAnalyticsByType('beneficiary');

    const averageVolunteerRating = volunteerAnalytics.length > 0 
      ? volunteerAnalytics.reduce((sum, analytic) => sum + (analytic.calculatedMetrics.averageRating || 0), 0) / volunteerAnalytics.length
      : 0;

    const averageBeneficiaryRating = beneficiaryAnalytics.length > 0 
      ? beneficiaryAnalytics.reduce((sum, analytic) => sum + (analytic.calculatedMetrics.averageRating || 0), 0) / beneficiaryAnalytics.length
      : 0;

    return {
      totalEvaluations: this.analytics.length,
      volunteerEvaluations: volunteerAnalytics.length,
      beneficiaryEvaluations: beneficiaryAnalytics.length,
      averageVolunteerRating,
      averageBeneficiaryRating
    };
  }
}

// Export singleton instance
export const evaluationAnalyticsService = new EvaluationAnalyticsService();






























