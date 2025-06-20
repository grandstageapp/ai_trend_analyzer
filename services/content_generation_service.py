import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from models import Trend, Post, PostTrend
from app import db

logger = logging.getLogger(__name__)

class ContentGenerationService:
    """Service for AI-powered content generation"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OpenAI API key not configured")
        
        self.client = OpenAI(api_key=self.api_key)
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
    
    def generate_blog_content(self, trend_id: int) -> str:
        """
        Generate a complete blog post for a specific trend
        
        Args:
            trend_id: ID of the trend to generate content for
            
        Returns:
            Generated blog post content
        """
        try:
            trend = Trend.query.get(trend_id)
            if not trend:
                return "Trend not found. Unable to generate content."
            
            # Get related posts for context
            related_posts = db.session.query(Post).join(PostTrend).filter(
                PostTrend.trend_id == trend_id
            ).limit(10).all()
            
            # Build comprehensive context
            context = self._build_trend_context(trend, related_posts)
            
            # Generate blog content
            prompt = self._create_blog_prompt(context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content writer specializing in AI and technology topics for business audiences. Create engaging, informative, and actionable content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            response_content = response.choices[0].message.content
            if not response_content:
                logger.error("Empty response from OpenAI for blog content")
                return "Unable to generate content at this time. Please try again later."
            
            content = response_content.strip()
            logger.info(f"Generated blog content for trend: {trend.title}")
            return content
            
        except Exception as e:
            logger.error(f"Error generating blog content: {e}")
            return "Unable to generate content at this time. Please try again later."
    
    def generate_social_media_content(self, trend_id: int, platform: str = "general") -> Dict[str, str]:
        """
        Generate social media content for different platforms
        
        Args:
            trend_id: ID of the trend to generate content for
            platform: Target platform (twitter, linkedin, general)
            
        Returns:
            Dictionary with different content formats
        """
        try:
            trend = Trend.query.get(trend_id)
            if not trend:
                return {"error": "Trend not found"}
            
            # Get related posts for context
            related_posts = db.session.query(Post).join(PostTrend).filter(
                PostTrend.trend_id == trend_id
            ).limit(5).all()
            
            context = self._build_trend_context(trend, related_posts)
            
            # Platform-specific prompts
            prompts = {
                "twitter": self._create_twitter_prompt(context),
                "linkedin": self._create_linkedin_prompt(context),
                "general": self._create_general_social_prompt(context)
            }
            
            results = {}
            for content_type, prompt in prompts.items():
                if platform != "general" and content_type != platform:
                    continue
                    
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are a social media expert creating {content_type} content about AI trends."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.8,
                    max_tokens=300
                )
                
                response_content = response.choices[0].message.content
                if response_content:
                    results[content_type] = response_content.strip()
            
            logger.info(f"Generated social media content for trend: {trend.title}")
            return results
            
        except Exception as e:
            logger.error(f"Error generating social media content: {e}")
            return {"error": "Unable to generate content at this time"}
    
    def generate_email_newsletter_content(self, trend_id: int) -> str:
        """
        Generate email newsletter content for a trend
        
        Args:
            trend_id: ID of the trend to generate content for
            
        Returns:
            Generated newsletter content
        """
        try:
            trend = Trend.query.get(trend_id)
            if not trend:
                return "Trend not found. Unable to generate content."
            
            related_posts = db.session.query(Post).join(PostTrend).filter(
                PostTrend.trend_id == trend_id
            ).limit(8).all()
            
            context = self._build_trend_context(trend, related_posts)
            prompt = self._create_newsletter_prompt(context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert newsletter writer creating engaging email content about AI trends for business professionals."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.6,
                max_tokens=600
            )
            
            response_content = response.choices[0].message.content
            if not response_content:
                logger.error("Empty response from OpenAI for newsletter content")
                return "Unable to generate content at this time. Please try again later."
            
            content = response_content.strip()
            logger.info(f"Generated newsletter content for trend: {trend.title}")
            return content
            
        except Exception as e:
            logger.error(f"Error generating newsletter content: {e}")
            return "Unable to generate content at this time. Please try again later."
    
    def generate_content_outline(self, trend_id: int) -> str:
        """
        Generate a content outline/structure for a trend
        
        Args:
            trend_id: ID of the trend to generate outline for
            
        Returns:
            Generated content outline
        """
        try:
            trend = Trend.query.get(trend_id)
            if not trend:
                return "Trend not found. Unable to generate outline."
            
            related_posts = db.session.query(Post).join(PostTrend).filter(
                PostTrend.trend_id == trend_id
            ).limit(10).all()
            
            context = self._build_trend_context(trend, related_posts)
            prompt = self._create_outline_prompt(context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a content strategist creating detailed outlines for AI and technology content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            response_content = response.choices[0].message.content
            if not response_content:
                logger.error("Empty response from OpenAI for content outline")
                return "Unable to generate outline at this time. Please try again later."
            
            content = response_content.strip()
            logger.info(f"Generated content outline for trend: {trend.title}")
            return content
            
        except Exception as e:
            logger.error(f"Error generating content outline: {e}")
            return "Unable to generate outline at this time. Please try again later."
    
    def _build_trend_context(self, trend: Trend, related_posts: List[Post]) -> str:
        """Build comprehensive context for content generation"""
        context = f"Trend: {trend.title}\n"
        context += f"Description: {trend.description}\n"
        context += f"Total Posts: {trend.total_posts}\n"
        context += f"Trend Score: {trend.get_latest_score()}\n\n"
        
        context += "Key insights from social media discussions:\n"
        for i, post in enumerate(related_posts[:5], 1):
            context += f"{i}. {post.content[:150]}...\n"
        
        return context
    
    def _create_blog_prompt(self, context: str) -> str:
        """Create prompt for blog content generation"""
        return f"""
        Write a compelling blog post about this AI/technology trend:
        
        {context}
        
        Requirements:
        - 400-600 words
        - Engaging headline that captures attention
        - Clear introduction that hooks the reader
        - Explain the trend in accessible language
        - Include why it matters for businesses and professionals
        - Provide specific examples or use cases
        - End with actionable insights or future outlook
        - Professional but conversational tone
        - Structure with clear paragraphs and smooth transitions
        
        Format as a complete blog post ready for publication.
        """
    
    def _create_twitter_prompt(self, context: str) -> str:
        """Create prompt for Twitter content generation"""
        return f"""
        Create Twitter content about this AI trend:
        
        {context}
        
        Generate 3 different tweet options:
        1. A thread starter (under 280 characters) that introduces the trend
        2. A single informative tweet with key insights
        3. A question tweet to engage followers
        
        Use relevant hashtags and keep content engaging and shareable.
        """
    
    def _create_linkedin_prompt(self, context: str) -> str:
        """Create prompt for LinkedIn content generation"""
        return f"""
        Create LinkedIn content about this AI trend:
        
        {context}
        
        Write a professional LinkedIn post (300-500 words) that:
        - Starts with a compelling hook
        - Explains the business implications
        - Provides actionable insights
        - Includes a call-to-action for engagement
        - Uses a professional but engaging tone
        """
    
    def _create_general_social_prompt(self, context: str) -> str:
        """Create prompt for general social media content"""
        return f"""
        Create general social media content about this AI trend:
        
        {context}
        
        Generate:
        1. A short, engaging post (150-200 words)
        2. 3-5 relevant hashtags
        3. A discussion question to boost engagement
        
        Keep tone informative but accessible to a general audience.
        """
    
    def _create_newsletter_prompt(self, context: str) -> str:
        """Create prompt for newsletter content generation"""
        return f"""
        Write an email newsletter section about this AI trend:
        
        {context}
        
        Requirements:
        - Compelling subject line suggestion
        - 250-400 word article
        - Clear structure with subheadings
        - Business-focused insights
        - Call-to-action at the end
        - Professional email tone
        
        Format for email newsletter inclusion.
        """
    
    def _create_outline_prompt(self, context: str) -> str:
        """Create prompt for content outline generation"""
        return f"""
        Create a detailed content outline for this AI trend:
        
        {context}
        
        Generate a comprehensive outline including:
        1. Main headline options (3 variations)
        2. Introduction key points
        3. Main sections with subsections
        4. Key statistics or data to include
        5. Expert quotes or perspectives to research
        6. Conclusion and call-to-action ideas
        7. SEO keywords and phrases
        
        Structure as a detailed content brief for writers.
        """