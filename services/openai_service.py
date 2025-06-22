import os
import json
import logging
import time
import functools
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config import Config
from utils.caching import cache_manager

logger = logging.getLogger(__name__)

def retry_with_exponential_backoff(max_retries=3, base_delay=1):
    """Decorator for retrying API calls with exponential backoff"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on certain errors
                    if hasattr(e, 'status_code') and e.status_code in [401, 403, 429]:
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        return wrapper
    return decorator

class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OpenAI API key not configured")
        
        self.client = OpenAI(api_key=self.api_key, timeout=60.0)
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        self.embedding_model = "text-embedding-3-large"
        
        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time = 0
        self.circuit_open = False
        self.failure_threshold = 5
        self.recovery_timeout = 300  # 5 minutes
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker should block requests"""
        if not self.circuit_open:
            return False
            
        # Check if recovery timeout has passed
        if time.time() - self.last_failure_time > self.recovery_timeout:
            self.circuit_open = False
            self.failure_count = 0
            logger.info("Circuit breaker reset - attempting API calls")
            return False
            
        return True
    
    def _record_failure(self):
        """Record API failure for circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _record_success(self):
        """Record API success for circuit breaker"""
        if self.failure_count > 0:
            self.failure_count = max(0, self.failure_count - 1)

    @retry_with_exponential_backoff(max_retries=3, base_delay=1)
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts with caching
        
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
    
    @retry_with_exponential_backoff(max_retries=2, base_delay=2)
    def cluster_and_identify_trends(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use OpenAI to identify trends from clustered posts with caching and retry logic
        
        Args:
            posts: List of post dictionaries with content
            
        Returns:
            List of identified trends with descriptions
        """
        try:
            if not posts:
                return []
            
            # Check circuit breaker
            if self._check_circuit_breaker():
                logger.warning("Circuit breaker open - using fallback trend identification")
                return self._fallback_trend_identification(posts)
            
            # Create cache key
            post_contents = [post.get('content', '') for post in posts]
            cache_key = f"trends_{hash(str(sorted(post_contents)))}"
            cached_result = cache_manager.get(cache_key)
            
            if cached_result:
                logger.info(f"Using cached trend identification for {len(posts)} posts")
                return cached_result
            
            # Create optimized prompt for trend identification
            prompt = self._create_optimized_trend_prompt(post_contents)
            
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI trend analyst. Analyze posts to identify trends. Respond with valid JSON only."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                timeout=45.0
            )
            
            execution_time = time.time() - start_time
            
            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response from OpenAI")
                return self._fallback_trend_identification(posts)
                
            result = json.loads(content)
            trends = result.get('trends', [])
            
            # Cache for 30 minutes
            cache_manager.set(cache_key, trends, 1800)
            
            self._record_success()
            logger.info(f"Identified {len(trends)} trends from {len(posts)} posts in {execution_time:.2f}s")
            return trends
            
        except Exception as e:
            self._record_failure()
            logger.error(f"Error identifying trends: {e}")
            if "timeout" in str(e).lower():
                logger.warning("Trend identification timed out, using fallback")
                return self._fallback_trend_identification(posts)
            return []
    
    def _create_optimized_trend_prompt(self, post_contents: List[str]) -> str:
        """Create an optimized prompt for trend identification"""
        
        posts_text = "\n".join([
            f"{i+1}. {content[:100]}..." if len(content) > 100 else f"{i+1}. {content}"
            for i, content in enumerate(post_contents[:8])  # Limit to 8 posts
        ])
        
        return f"""
        Identify trends from these AI posts:

        {posts_text}

        Return JSON:
        {{
            "trends": [
                {{
                    "title": "Brief title (2-4 words)",
                    "posts_count": count,
                    "relevance_score": 1-10
                }}
            ]
        }}

        Focus on: AI models, tools, policy, ethics, enterprise adoption.
        Only trends appearing in 2+ posts or highly significant.
        """

    def _fallback_trend_identification(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate basic trends when AI analysis fails"""
        post_contents = [post.get('content', '') for post in posts]
        
        # Simple keyword-based trend detection
        ai_keywords = {
            'AI Models': ['gpt', 'model', 'llm', 'transformer'],
            'AI Ethics': ['ethics', 'bias', 'fairness', 'responsibility'], 
            'Enterprise AI': ['enterprise', 'business', 'company', 'adoption'],
            'AI Tools': ['tool', 'platform', 'application', 'software'],
            'AI Research': ['research', 'breakthrough', 'study', 'discovery']
        }
        
        trends = []
        for trend_name, keywords in ai_keywords.items():
            matching_posts = 0
            for content in post_contents:
                content_lower = content.lower()
                if any(keyword in content_lower for keyword in keywords):
                    matching_posts += 1
            
            if matching_posts >= 2:
                trends.append({
                    'title': trend_name,
                    'posts_count': matching_posts,
                    'relevance_score': min(10, matching_posts * 2)
                })
        
        logger.info(f"Generated {len(trends)} fallback trends")
        return trends
    
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
            
            **IMPORTANT: Format your response in Markdown with:**
            - Use ## for section headers
            - Use **bold** for emphasis
            - Use bullet points (-) for lists
            - Use line breaks between paragraphs for better readability
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
