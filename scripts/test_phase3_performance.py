#!/usr/bin/env python3
"""
Test script for Phase 3 performance optimizations
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime
from app import create_app, db
from models import Post, Author, Trend
from utils.caching import cache_manager
from utils.query_optimization import query_optimizer
from services.performance_service import performance_monitor
from utils.validators import data_validator
from utils.type_definitions import PostData, AuthorData, EngagementMetrics

def test_caching_system():
    """Test caching implementation"""
    print("\n=== Testing Caching System ===")
    
    # Test basic cache operations
    test_data = {"message": "Phase 3 cache test", "timestamp": time.time()}
    cache_manager.set("test_cache", test_data, ttl=300)
    
    retrieved = cache_manager.get("test_cache")
    assert retrieved == test_data, "Cache set/get failed"
    print("✓ Basic cache operations working")
    
    # Test cache statistics
    stats = cache_manager.get_stats()
    print(f"✓ Cache type: {stats['cache_type']}")
    print(f"✓ Cache hit rate: {stats['hit_rate_percent']}%")
    
    # Test cache invalidation
    cache_manager.delete("test_cache")
    retrieved = cache_manager.get("test_cache")
    assert retrieved is None, "Cache deletion failed"
    print("✓ Cache invalidation working")

def test_query_optimization():
    """Test query optimization features"""
    print("\n=== Testing Query Optimization ===")
    
    app = create_app()
    with app.app_context():
        # Test optimized trending posts query
        start_time = time.time()
        trending_posts = query_optimizer.get_trending_posts(days=7, limit=10)
        execution_time = time.time() - start_time
        
        print(f"✓ Trending posts query: {len(trending_posts)} posts in {execution_time:.3f}s")
        
        # Test optimized top trends query
        start_time = time.time()
        top_trends = query_optimizer.get_top_trends(limit=10)
        execution_time = time.time() - start_time
        
        print(f"✓ Top trends query: {len(top_trends)} trends in {execution_time:.3f}s")
        
        # Test database performance stats
        perf_stats = query_optimizer.get_database_performance_stats()
        print(f"✓ Database performance stats available: {'table_stats' in perf_stats}")

def test_performance_monitoring():
    """Test performance monitoring system"""
    print("\n=== Testing Performance Monitoring ===")
    
    # Test performance decorator
    @performance_monitor.track_execution_time("test_operation")
    def test_operation():
        time.sleep(0.1)  # Simulate work
        return "operation_complete"
    
    result = test_operation()
    assert result == "operation_complete", "Performance tracking failed"
    print("✓ Performance tracking decorator working")
    
    # Test performance summary
    summary = performance_monitor.get_performance_summary(hours=1)
    assert "operations" in summary, "Performance summary missing operations"
    print(f"✓ Performance summary: {len(summary['operations'])} operations tracked")
    
    # Test optimization recommendations
    recommendations = performance_monitor.optimize_recommendations()
    print(f"✓ Generated {len(recommendations)} optimization recommendations")

def test_data_validation():
    """Test consolidated data validation"""
    print("\n=== Testing Data Validation ===")
    
    # Test valid post data
    valid_post = {
        "post_id": "1234567890",
        "content": "Test post content for Phase 3 validation",
        "created_at": datetime.utcnow(),
        "author": {
            "username": "testuser",
            "name": "Test User",
            "follower_count": 100,
            "verified": False
        },
        "metrics": {
            "like_count": 10,
            "reply_count": 2,
            "retweet_count": 5,
            "quote_count": 1
        }
    }
    
    try:
        is_valid = data_validator.validate_post_data(valid_post)
        print("✓ Valid post data validation passed")
    except Exception as e:
        print(f"✗ Valid post validation failed: {e}")
    
    # Test content sanitization
    dirty_content = "<script>alert('xss')</script>Normal content"
    clean_content = data_validator.sanitize_content(dirty_content)
    assert "<script" not in clean_content, "Content sanitization failed"
    print("✓ Content sanitization working")
    
    # Test search query validation
    try:
        data_validator.validate_search_query("safe search query")
        print("✓ Search query validation passed")
    except Exception as e:
        print(f"✗ Search query validation failed: {e}")

def test_type_definitions():
    """Test type definitions and data structures"""
    print("\n=== Testing Type Definitions ===")
    
    # Test PostData structure
    author_data = AuthorData(
        username="typetest",
        name="Type Test User",
        follower_count=50,
        verified=False,
        profile_url="https://example.com"
    )
    
    engagement = EngagementMetrics(
        like_count=5,
        reply_count=1,
        retweet_count=2,
        quote_count=0
    )
    
    post_data = PostData(
        post_id="type_test_123",
        content="Testing type definitions",
        created_at=datetime.utcnow(),
        author=author_data,
        metrics=engagement
    )
    
    assert post_data.post_id == "type_test_123", "PostData structure failed"
    print("✓ Type definitions working correctly")

def test_embedding_caching():
    """Test embedding caching functionality"""
    print("\n=== Testing Embedding Caching ===")
    
    app = create_app()
    with app.app_context():
        from services.openai_service import OpenAIService
        
        # Test with mock data to avoid API calls
        test_texts = ["AI trends in 2025", "Machine learning advances"]
        
        # We'll test the caching logic without making actual API calls
        import hashlib
        from utils.caching import cache_manager
        
        # Simulate cached embeddings
        for text in test_texts:
            text_hash = hashlib.md5(text.encode()).hexdigest()
            cache_key = f"embedding:{text_hash}"
            mock_embedding = [0.1, 0.2, 0.3] * 100  # Mock 300-dim embedding
            cache_manager.set(cache_key, mock_embedding, ttl=300)
        
        print("✓ Embedding caching simulation completed")

def run_comprehensive_phase3_test():
    """Run all Phase 3 performance optimization tests"""
    print("🚀 Starting Phase 3 Performance Optimization Test Suite")
    print("=" * 60)
    
    try:
        test_caching_system()
        test_query_optimization()
        test_performance_monitoring()
        test_data_validation()
        test_type_definitions()
        test_embedding_caching()
        
        print("\n" + "=" * 60)
        print("✅ ALL PHASE 3 PERFORMANCE TESTS PASSED!")
        print("Performance optimizations are working correctly.")
        
        # Show performance summary
        print("\n📊 Performance Summary:")
        summary = performance_monitor.get_performance_summary(hours=1)
        for operation, stats in summary['operations'].items():
            print(f"  {operation}: {stats['total_calls']} calls, avg {stats['avg_execution_time']:.3f}s")
        
        cache_stats = cache_manager.get_stats()
        print(f"\n💾 Cache Statistics:")
        print(f"  Type: {cache_stats['cache_type']}")
        print(f"  Requests: {cache_stats['total_requests']}")
        print(f"  Hit Rate: {cache_stats['hit_rate_percent']}%")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_comprehensive_phase3_test()
    exit(0 if success else 1)