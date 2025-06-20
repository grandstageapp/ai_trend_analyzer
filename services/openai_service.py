import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OpenAI API key not configured")
        
        self.client = OpenAI(api_key=self.api_key)
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-large",
                input=texts
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    def cluster_and_identify_trends(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use OpenAI to identify trends from clustered posts
        
        Args:
            posts: List of post dictionaries with content
            
        Returns:
            List of identified trends with descriptions
        """
        try:
            if not posts:
                return []
            
            # Prepare post content for analysis
            post_contents = [post.get('content', '') for post in posts]
            
            # Create prompt for trend identification
            prompt = self._create_trend_identification_prompt(post_contents)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI trend analyst. Analyze social media posts to identify trending topics in AI and technology. Respond with valid JSON only."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response from OpenAI")
                return []
            result = json.loads(content)
            trends = result.get('trends', [])
            
            logger.info(f"Identified {len(trends)} trends from {len(posts)} posts")
            return trends
            
        except Exception as e:
            logger.error(f"Error identifying trends: {e}")
            return []
    
    def generate_trend_description(self, trend_title: str, related_posts: List[str]) -> str:
        """
        Generate a detailed description for a trend
        
        Args:
            trend_title: The trend title/topic
            related_posts: List of post contents related to this trend
            
        Returns:
            Detailed trend description
        """
        try:
            prompt = f"""
            Generate a comprehensive description for the AI/technology trend: "{trend_title}"
            
            Based on these social media discussions:
            {chr(10).join(['- ' + post[:200] + '...' for post in related_posts[:10]])}
            
            Please provide:
            1. A clear explanation of what this trend is about
            2. Key developments or news driving the trend
            3. Why it's significant in the AI/tech space
            4. Potential implications or future directions
            
            Keep the description informative but accessible to non-technical readers.
            Aim for 200-400 words.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technology journalist who explains AI trends clearly and accurately."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4
            )
            
            content = response.choices[0].message.content
            description = content.strip() if content else ""
            logger.info(f"Generated description for trend: {trend_title}")
            return description
            
        except Exception as e:
            logger.error(f"Error generating trend description: {e}")
            return f"Trend related to {trend_title} based on recent social media discussions."
    
    def chat_about_trend(self, trend_context: str, user_message: str) -> str:
        """
        Handle chat interactions about a specific trend
        
        Args:
            trend_context: Context information about the trend
            user_message: User's question or message
            
        Returns:
            AI response
        """
        try:
            system_prompt = f"""
            You are an AI assistant helping content creators understand technology trends.
            
            Context about the current trend:
            {trend_context}
            
            Provide helpful, accurate, and engaging responses about this trend.
            Keep responses conversational but informative.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.6,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else "I apologize, but I'm having trouble processing your question right now. Please try again."
            
        except Exception as e:
            logger.error(f"Error in trend chat: {e}")
            return "I apologize, but I'm having trouble processing your question right now. Please try again."
    
    def generate_blog_content(self, trend_context: str) -> str:
        """
        Generate sample blog content for a trend
        
        Args:
            trend_context: Context about the trend and related posts
            
        Returns:
            Generated blog post content (500 words or less)
        """
        try:
            prompt = f"""
            Write a compelling blog post about this AI/technology trend:
            
            {trend_context}
            
            Requirements:
            - 400-500 words maximum
            - Engaging headline-style title
            - Clear introduction that hooks the reader
            - Explain the trend in accessible language
            - Include why it matters for businesses/professionals
            - End with actionable insights or future outlook
            - Professional but conversational tone
            - Structure with clear paragraphs
            
            Format as a complete blog post ready for publication.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content writer specializing in AI and technology topics for business audiences."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=700
            )
            
            response_content = response.choices[0].message.content
            if not response_content:
                logger.error("Empty response from OpenAI for blog content")
                return "Unable to generate content at this time. Please try again later."
            content = response_content.strip()
            logger.info("Generated blog content successfully")
            return content
            
        except Exception as e:
            logger.error(f"Error generating blog content: {e}")
            return "Unable to generate content at this time. Please try again later."
    
    def _create_trend_identification_prompt(self, post_contents: List[str]) -> str:
        """Create a prompt for trend identification"""
        posts_text = "\n\n".join([f"Post {i+1}: {content}" for i, content in enumerate(post_contents[:20])])
        
        return f"""
        Analyze these AI/technology-related social media posts and identify the main trending topics:

        {posts_text}

        Please identify 3-7 distinct trends and return them in this JSON format:
        {{
            "trends": [
                {{
                    "title": "Short descriptive title (2-5 words)",
                    "posts_count": number_of_posts_related_to_this_trend,
                    "relevance_score": score_from_1_to_10,
                    "post_indices": [list_of_post_numbers_that_relate_to_this_trend]
                }}
            ]
        }}

        Focus on:
        - AI model releases or updates
        - New AI tools or applications  
        - AI policy/regulation discussions
        - Technical breakthroughs
        - Industry partnerships/acquisitions
        - AI ethics and safety topics
        - Enterprise AI adoption

        Only include trends that appear in multiple posts or are particularly significant.
        """
