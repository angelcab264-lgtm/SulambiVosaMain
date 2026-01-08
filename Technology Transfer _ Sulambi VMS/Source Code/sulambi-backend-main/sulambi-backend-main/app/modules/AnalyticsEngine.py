import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, mean_squared_error
import joblib
import os
from ..database.connection import cursorInstance, quote_identifier

class AnalyticsEngine:
    def __init__(self):
        self.conn, _ = cursorInstance()
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        
    def prepare_event_success_data(self):
        """Prepare data for event success prediction"""
        internal_events_table = quote_identifier('internalEvents')
        external_events_table = quote_identifier('externalEvents')
        requirements_table = quote_identifier('requirements')
        evaluation_table = quote_identifier('evaluation')
        feedback_table = quote_identifier('feedback')
        query = f"""
        SELECT 
            ie.id,
            ie.title,
            ie."durationStart",
            ie."durationEnd",
            ie.venue,
            ie."modeOfDelivery",
            ie."maleTotal",
            ie."femaleTotal",
            ie.status,
            ie."createdAt",
            COUNT(r.id) as registered_count,
            COUNT(CASE WHEN e.finalized = 1 AND e.criteria != '' THEN 1 END) as attended_count,
            AVG(CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END) as has_feedback
        FROM {internal_events_table} ie
        LEFT JOIN {requirements_table} r ON ie.id = r."eventId" AND r.type = 'internal'
        LEFT JOIN {evaluation_table} e ON r.id = e."requirementId"
        LEFT JOIN {feedback_table} f ON ie."feedback_id" = f.id
        WHERE ie.status IN ('accepted', 'completed', 'cancelled')
        GROUP BY ie.id
        
        UNION ALL
        
        SELECT 
            ee.id,
            ee.title,
            ee."durationStart",
            ee."durationEnd",
            ee.location as venue,
            'external' as modeOfDelivery,
            0 as maleTotal,
            0 as femaleTotal,
            ee.status,
            ee."createdAt",
            COUNT(r.id) as registered_count,
            COUNT(CASE WHEN e.finalized = 1 AND e.criteria != '' THEN 1 END) as attended_count,
            AVG(CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END) as has_feedback
        FROM {external_events_table} ee
        LEFT JOIN {requirements_table} r ON ee.id = r."eventId" AND r.type = 'external'
        LEFT JOIN {evaluation_table} e ON r.id = e."requirementId"
        LEFT JOIN {feedback_table} f ON ee."feedback_id" = f.id
        WHERE ee.status IN ('accepted', 'completed', 'cancelled')
        GROUP BY ee.id
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # Feature engineering
        df['duration_hours'] = (df['durationEnd'] - df['durationStart']) / (1000 * 60 * 60)
        df['attendance_rate'] = df['attended_count'] / (df['registered_count'] + 1e-6)
        df['total_participants'] = df['maleTotal'] + df['femaleTotal']
        df['is_weekend'] = pd.to_datetime(df['createdAt']).dt.dayofweek.isin([5, 6]).astype(int)
        
        # Success definition: attendance rate > 0.7 and status = 'completed'
        df['success'] = ((df['attendance_rate'] > 0.7) & (df['status'] == 'completed')).astype(int)
        
        return df
    
    def prepare_volunteer_dropout_data(self):
        """Prepare data for volunteer dropout risk prediction"""
        membership_table = quote_identifier('membership')
        requirements_table = quote_identifier('requirements')
        evaluation_table = quote_identifier('evaluation')
        query = f"""
        SELECT 
            m.id,
            m.age,
            m.sex,
            m.campus,
            m."collegeDept",
            m."yrlevelprogram",
            m."volunterismExperience",
            m."weekdaysTimeDevotion",
            m."weekendsTimeDevotion",
            m."areasOfInterest",
            m.accepted,
            m.active,
            COUNT(r.id) as total_registrations,
            COUNT(CASE WHEN e.finalized = 1 AND e.criteria != '' THEN 1 END) as attended_events,
            AVG(CASE WHEN e.finalized = 1 AND e.criteria != '' THEN 1 ELSE 0 END) as attendance_rate,
            MAX(r."createdAt") as last_participation,
            MIN(r."createdAt") as first_participation
        FROM {membership_table} m
        LEFT JOIN {requirements_table} r ON m.email = r.email
        LEFT JOIN {evaluation_table} e ON r.id = e."requirementId"
        WHERE m.accepted = true
        GROUP BY m.id
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # Feature engineering
        df['participation_span'] = (pd.to_datetime(df['last_participation']) - pd.to_datetime(df['first_participation'])).dt.days
        df['days_since_last_event'] = (datetime.now() - pd.to_datetime(df['last_participation'])).dt.days
        df['is_high_risk'] = ((df['attendance_rate'] < 0.5) | (df['days_since_last_event'] > 90)).astype(int)
        
        return df
    
    def train_event_success_model(self):
        """Train model to predict event success"""
        df = self.prepare_event_success_data()
        
        # Select features
        feature_columns = ['duration_hours', 'total_participants', 'is_weekend', 'has_feedback']
        X = df[feature_columns].fillna(0)
        y = df['success']
        
        # Encode categorical variables
        le = LabelEncoder()
        X['modeOfDelivery'] = le.fit_transform(df['modeOfDelivery'].fillna('unknown'))
        self.encoders['modeOfDelivery'] = le
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['event_success'] = scaler
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Event Success Model Accuracy: {accuracy:.3f}")
        
        self.models['event_success'] = model
        return model
    
    def train_volunteer_dropout_model(self):
        """Train model to predict volunteer dropout risk"""
        df = self.prepare_volunteer_dropout_data()
        
        # Select features
        feature_columns = ['age', 'volunterismExperience', 'total_registrations', 
                          'attendance_rate', 'participation_span', 'days_since_last_event']
        X = df[feature_columns].fillna(0)
        y = df['is_high_risk']
        
        # Encode categorical variables
        categorical_columns = ['sex', 'campus', 'collegeDept', 'yrlevelprogram']
        for col in categorical_columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(df[col].fillna('unknown'))
            self.encoders[col] = le
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['volunteer_dropout'] = scaler
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Volunteer Dropout Model Accuracy: {accuracy:.3f}")
        
        self.models['volunteer_dropout'] = model
        return model
    
    def predict_event_success(self, event_data):
        """Predict success probability for an event"""
        if 'event_success' not in self.models:
            self.train_event_success_model()
        
        # Prepare input data
        features = np.array([[
            event_data.get('duration_hours', 0),
            event_data.get('total_participants', 0),
            event_data.get('is_weekend', 0),
            event_data.get('has_feedback', 0)
        ]])
        
        # Scale features
        features_scaled = self.scalers['event_success'].transform(features)
        
        # Predict
        success_prob = self.models['event_success'].predict_proba(features_scaled)[0][1]
        return success_prob
    
    def predict_volunteer_dropout_risk(self, volunteer_data):
        """Predict dropout risk for a volunteer"""
        if 'volunteer_dropout' not in self.models:
            self.train_volunteer_dropout_model()
        
        # Prepare input data
        features = np.array([[
            volunteer_data.get('age', 0),
            volunteer_data.get('volunterismExperience', 0),
            volunteer_data.get('total_registrations', 0),
            volunteer_data.get('attendance_rate', 0),
            volunteer_data.get('participation_span', 0),
            volunteer_data.get('days_since_last_event', 0)
        ]])
        
        # Scale features
        features_scaled = self.scalers['volunteer_dropout'].transform(features)
        
        # Predict
        dropout_prob = self.models['volunteer_dropout'].predict_proba(features_scaled)[0][1]
        return dropout_prob
    
    def get_analytics_insights(self):
        """Get comprehensive analytics insights"""
        event_df = self.prepare_event_success_data()
        volunteer_df = self.prepare_volunteer_dropout_data()
        
        insights = {
            'event_analytics': {
                'total_events': len(event_df),
                'success_rate': event_df['success'].mean(),
                'avg_attendance_rate': event_df['attendance_rate'].mean(),
                'high_success_venues': event_df.groupby('venue')['success'].mean().sort_values(ascending=False).head(5).to_dict(),
                'best_event_times': event_df.groupby('is_weekend')['success'].mean().to_dict()
            },
            'volunteer_analytics': {
                'total_volunteers': len(volunteer_df),
                'high_risk_volunteers': volunteer_df['is_high_risk'].sum(),
                'avg_attendance_rate': volunteer_df['attendance_rate'].mean(),
                'dropout_risk_by_demographics': volunteer_df.groupby('campus')['is_high_risk'].mean().to_dict()
            }
        }
        
        return insights
    
    def save_models(self, model_dir='models'):
        """Save trained models to disk"""
        os.makedirs(model_dir, exist_ok=True)
        
        for name, model in self.models.items():
            joblib.dump(model, f"{model_dir}/{name}_model.pkl")
        
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, f"{model_dir}/{name}_scaler.pkl")
        
        for name, encoder in self.encoders.items():
            joblib.dump(encoder, f"{model_dir}/{name}_encoder.pkl")
    
    def load_models(self, model_dir='models'):
        """Load trained models from disk"""
        for name in ['event_success', 'volunteer_dropout']:
            model_path = f"{model_dir}/{name}_model.pkl"
            scaler_path = f"{model_dir}/{name}_scaler.pkl"
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                self.models[name] = joblib.load(model_path)
                self.scalers[name] = joblib.load(scaler_path)

