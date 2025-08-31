"""
SoulBridge AI - Relationship Profile Analyzer
AI-powered analysis and insights for relationship profiles
Future enhancement for relationship management
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

class ProfileAnalyzer:
    """Analyzer for relationship profiles with AI insights"""
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        self.analysis_types = [
            'connection_health',
            'communication_patterns', 
            'relationship_growth',
            'conflict_resolution',
            'emotional_support',
            'compatibility_assessment'
        ]
    
    def analyze_relationship(self, profile: Dict[str, Any], analysis_type: str = 'connection_health') -> Dict[str, Any]:
        """Analyze a relationship profile using AI"""
        try:
            if not self.openai_client:
                return {
                    'success': False,
                    'error': 'AI analysis not available - OpenAI client not configured'
                }
            
            if analysis_type not in self.analysis_types:
                return {
                    'success': False,
                    'error': f'Invalid analysis type. Available: {", ".join(self.analysis_types)}'
                }
            
            # Prepare analysis prompt
            analysis_prompt = self._create_analysis_prompt(profile, analysis_type)
            
            # Generate AI analysis
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a relationship counseling AI assistant. Provide thoughtful, constructive analysis of relationships based on the provided information. Be empathetic, professional, and focus on actionable insights."
                    },
                    {
                        "role": "user", 
                        "content": analysis_prompt
                    }
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            analysis_result = response.choices[0].message.content
            
            # Structure the analysis result
            structured_analysis = {
                'analysis_type': analysis_type,
                'profile_id': profile.get('id'),
                'profile_name': profile.get('name'),
                'generated_at': datetime.now().isoformat(),
                'analysis': analysis_result,
                'insights': self._extract_insights(analysis_result),
                'recommendations': self._extract_recommendations(analysis_result),
                'health_score': self._calculate_health_score(profile)
            }
            
            logger.info(f"🔍 Generated {analysis_type} analysis for profile: {profile.get('name')}")
            
            return {
                'success': True,
                'analysis': structured_analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze relationship: {e}")
            return {
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            }
    
    def analyze_relationship_network(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the overall relationship network"""
        try:
            if not profiles:
                return {
                    'success': True,
                    'network_analysis': {
                        'total_relationships': 0,
                        'network_health': 'unknown',
                        'diversity_score': 0,
                        'support_network_strength': 0,
                        'recommendations': ['Start building meaningful relationships to improve your social network.']
                    }
                }
            
            # Calculate network metrics
            network_metrics = self._calculate_network_metrics(profiles)
            
            # Generate AI insights if available
            network_insights = []
            if self.openai_client:
                network_insights = self._generate_network_insights(profiles, network_metrics)
            
            network_analysis = {
                'total_relationships': len(profiles),
                'network_health': network_metrics['overall_health'],
                'diversity_score': network_metrics['diversity_score'],
                'support_network_strength': network_metrics['support_strength'],
                'type_distribution': network_metrics['type_distribution'],
                'connection_distribution': network_metrics['connection_distribution'],
                'contact_frequency_analysis': network_metrics['contact_analysis'],
                'insights': network_insights,
                'recommendations': self._generate_network_recommendations(network_metrics),
                'analyzed_at': datetime.now().isoformat()
            }
            
            logger.info(f"🌐 Analyzed relationship network: {len(profiles)} relationships")
            
            return {
                'success': True,
                'network_analysis': network_analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze relationship network: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_relationship_insights(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Get quick insights about a relationship without full AI analysis"""
        try:
            insights = []
            warnings = []
            suggestions = []
            
            # Connection strength insights
            strength = profile.get('connection_strength', 'moderate')
            if strength in ['very_weak', 'weak']:
                warnings.append("This relationship shows weak connection strength")
                suggestions.append("Consider reaching out more frequently to strengthen the bond")
            elif strength in ['very_strong']:
                insights.append("This is a very strong relationship - a valuable part of your support network")
            
            # Meeting frequency insights
            frequency = profile.get('meeting_frequency', 'rarely')
            last_contact = profile.get('last_contact')
            
            if frequency in ['rarely', 'never']:
                if last_contact:
                    try:
                        last_date = datetime.fromisoformat(last_contact.replace('Z', '+00:00'))
                        days_since = (datetime.now() - last_date.replace(tzinfo=None)).days
                        if days_since > 90:
                            warnings.append(f"No contact in {days_since} days - relationship may be drifting")
                            suggestions.append("Schedule a catch-up call or meeting")
                    except:
                        pass
                else:
                    warnings.append("No recorded contact history")
            
            # Relationship type insights
            rel_type = profile.get('type', 'other')
            if rel_type == 'family':
                insights.append("Family relationships provide important emotional foundation")
            elif rel_type == 'romantic':
                insights.append("Romantic relationships require regular nurturing and communication")
            elif rel_type == 'mentor':
                insights.append("Mentoring relationships can provide valuable growth opportunities")
            
            # Notes analysis
            notes = profile.get('notes', '')
            if len(notes) < 50:
                suggestions.append("Add more detailed notes to track relationship patterns and important details")
            
            return {
                'success': True,
                'insights': {
                    'positive_aspects': insights,
                    'areas_of_concern': warnings,
                    'suggestions': suggestions,
                    'relationship_health': self._calculate_health_score(profile),
                    'last_analyzed': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get relationship insights: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_analysis_prompt(self, profile: Dict[str, Any], analysis_type: str) -> str:
        """Create analysis prompt for AI"""
        base_info = f"""
Relationship Profile Analysis Request:

Name: {profile.get('name', 'Anonymous')}
Type: {profile.get('type', 'Unknown')}
Connection Strength: {profile.get('connection_strength', 'Not specified')}
Meeting Frequency: {profile.get('meeting_frequency', 'Not specified')}
Last Contact: {profile.get('last_contact', 'Not specified')}
Notes: {profile.get('notes', 'No notes provided')}
"""
        
        analysis_prompts = {
            'connection_health': f"{base_info}\nPlease analyze the health of this relationship. Focus on connection strength, communication patterns, and overall relationship vitality. Provide specific insights and actionable recommendations.",
            
            'communication_patterns': f"{base_info}\nAnalyze the communication patterns in this relationship. Consider frequency, quality, and effectiveness of communication. What improvements could be made?",
            
            'relationship_growth': f"{base_info}\nEvaluate the growth potential and trajectory of this relationship. What opportunities exist for deeper connection and mutual development?",
            
            'conflict_resolution': f"{base_info}\nAssess how conflict and challenges might be handled in this relationship. What strategies would improve conflict resolution?",
            
            'emotional_support': f"{base_info}\nAnalyze the emotional support dynamics in this relationship. How well does this relationship provide and receive emotional support?",
            
            'compatibility_assessment': f"{base_info}\nEvaluate the compatibility and long-term sustainability of this relationship. What factors contribute to or detract from compatibility?"
        }
        
        return analysis_prompts.get(analysis_type, analysis_prompts['connection_health'])
    
    def _extract_insights(self, analysis_text: str) -> List[str]:
        """Extract key insights from AI analysis"""
        # Simple extraction - could be enhanced with NLP
        insights = []
        
        # Look for insight indicators
        insight_keywords = ['insight:', 'key point:', 'important:', 'notable:', 'strength:', 'opportunity:']
        
        lines = analysis_text.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in insight_keywords):
                insights.append(line)
            elif line.startswith('•') or line.startswith('-'):
                insights.append(line)
        
        return insights[:5]  # Limit to top 5 insights
    
    def _extract_recommendations(self, analysis_text: str) -> List[str]:
        """Extract recommendations from AI analysis"""
        recommendations = []
        
        # Look for recommendation indicators
        rec_keywords = ['recommend', 'suggest', 'consider', 'try', 'should', 'could', 'might']
        
        lines = analysis_text.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in rec_keywords):
                recommendations.append(line)
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def _calculate_health_score(self, profile: Dict[str, Any]) -> int:
        """Calculate a simple health score for the relationship (0-100)"""
        score = 50  # Base score
        
        # Connection strength contribution
        strength = profile.get('connection_strength', 'moderate')
        strength_scores = {
            'very_weak': -20,
            'weak': -10,
            'moderate': 0,
            'strong': 15,
            'very_strong': 25
        }
        score += strength_scores.get(strength, 0)
        
        # Meeting frequency contribution
        frequency = profile.get('meeting_frequency', 'rarely')
        frequency_scores = {
            'daily': 20,
            'weekly': 15,
            'bi_weekly': 10,
            'monthly': 5,
            'quarterly': 0,
            'bi_annually': -5,
            'annually': -10,
            'rarely': -15,
            'never': -25
        }
        score += frequency_scores.get(frequency, 0)
        
        # Recent contact bonus
        last_contact = profile.get('last_contact')
        if last_contact:
            try:
                last_date = datetime.fromisoformat(last_contact.replace('Z', '+00:00'))
                days_since = (datetime.now() - last_date.replace(tzinfo=None)).days
                if days_since <= 7:
                    score += 10
                elif days_since <= 30:
                    score += 5
                elif days_since > 90:
                    score -= 10
            except:
                pass
        
        # Notes quality bonus
        notes = profile.get('notes', '')
        if len(notes) > 100:
            score += 5
        
        return max(0, min(100, score))
    
    def _calculate_network_metrics(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics for the relationship network"""
        metrics = {
            'type_distribution': {},
            'connection_distribution': {},
            'contact_analysis': {},
            'diversity_score': 0,
            'support_strength': 0,
            'overall_health': 'unknown'
        }
        
        if not profiles:
            return metrics
        
        # Type distribution
        for profile in profiles:
            rel_type = profile.get('type', 'other')
            metrics['type_distribution'][rel_type] = metrics['type_distribution'].get(rel_type, 0) + 1
        
        # Connection strength distribution
        for profile in profiles:
            strength = profile.get('connection_strength', 'moderate')
            metrics['connection_distribution'][strength] = metrics['connection_distribution'].get(strength, 0) + 1
        
        # Contact frequency analysis
        for profile in profiles:
            frequency = profile.get('meeting_frequency', 'rarely')
            metrics['contact_analysis'][frequency] = metrics['contact_analysis'].get(frequency, 0) + 1
        
        # Calculate diversity score (0-100)
        type_count = len(metrics['type_distribution'])
        metrics['diversity_score'] = min(100, type_count * 20)  # Max score with 5+ types
        
        # Calculate support strength (average health scores)
        total_health = sum(self._calculate_health_score(profile) for profile in profiles)
        metrics['support_strength'] = total_health / len(profiles)
        
        # Overall health assessment
        if metrics['support_strength'] >= 80:
            metrics['overall_health'] = 'excellent'
        elif metrics['support_strength'] >= 60:
            metrics['overall_health'] = 'good'
        elif metrics['support_strength'] >= 40:
            metrics['overall_health'] = 'fair'
        else:
            metrics['overall_health'] = 'needs_attention'
        
        return metrics
    
    def _generate_network_insights(self, profiles: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[str]:
        """Generate AI insights about the relationship network"""
        try:
            if not self.openai_client:
                return []
            
            # Create network summary for AI analysis
            network_summary = f"""
Relationship Network Summary:
- Total relationships: {len(profiles)}
- Relationship types: {metrics['type_distribution']}
- Connection strengths: {metrics['connection_distribution']}
- Contact frequencies: {metrics['contact_analysis']}
- Diversity score: {metrics['diversity_score']}/100
- Support strength: {metrics['support_strength']:.1f}/100
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a relationship network analyst. Provide 2-3 key insights about this person's relationship network in a concise, helpful manner."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this relationship network and provide key insights:\n{network_summary}"
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            insights_text = response.choices[0].message.content
            return [insight.strip() for insight in insights_text.split('\n') if insight.strip()]
            
        except Exception as e:
            logger.error(f"Failed to generate network insights: {e}")
            return []
    
    def _generate_network_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on network metrics"""
        recommendations = []
        
        # Diversity recommendations
        if metrics['diversity_score'] < 40:
            recommendations.append("Consider expanding your relationship network to include different types of relationships (family, friends, colleagues, mentors)")
        
        # Support strength recommendations
        if metrics['support_strength'] < 50:
            recommendations.append("Focus on strengthening existing relationships through more frequent contact and deeper engagement")
        
        # Type-specific recommendations
        type_dist = metrics['type_distribution']
        if type_dist.get('mentor', 0) == 0:
            recommendations.append("Consider developing mentoring relationships for personal and professional growth")
        
        if type_dist.get('friend', 0) < 2:
            recommendations.append("Building more friendships can provide emotional support and social fulfillment")
        
        # Contact frequency recommendations
        contact_analysis = metrics['contact_analysis']
        rarely_or_never = contact_analysis.get('rarely', 0) + contact_analysis.get('never', 0)
        if rarely_or_never > len(contact_analysis) / 2:
            recommendations.append("Schedule regular check-ins with important people to maintain relationship health")
        
        return recommendations[:4]  # Limit to 4 recommendations