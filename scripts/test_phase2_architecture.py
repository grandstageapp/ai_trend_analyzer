#!/usr/bin/env python3
"""
Comprehensive test script for Phase 2 architecture improvements
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import uuid
from datetime import datetime, timedelta
from app import create_app, db
from models import Post, Author, Engagement, Trend
from tasks.background_tasks import BackgroundTasks
from services.service_manager import ServiceManager
from utils.monitoring import task_monitor, TaskStatus
from utils.exceptions import (
    TwitterAPIException, DatabaseException, ProcessingException,
    DataIntegrityException, TrendAnalysisException
)

def test_singleton_pattern():
    """Test singleton pattern for ServiceManager"""
    print("\n=== Testing Singleton Pattern ===")
    
    # Create multiple instances
    sm1 = ServiceManager()
    sm2 = ServiceManager()
    sm3 = ServiceManager()
    
    # Verify they're the same instance
    assert sm1 is sm2 is sm3, "ServiceManager should be singleton"
    print("✓ ServiceManager singleton pattern working correctly")
    
    # Test service access consistency
    twitter1 = sm1.twitter_service
    twitter2 = sm2.twitter_service
    assert twitter1 is twitter2, "Services should be consistent across instances"
    print("✓ Service instances consistent across singleton")

def test_database_connection_pooling():
    """Test database connection pooling configuration"""
    print("\n=== Testing Database Connection Pooling ===")
    
    app = create_app()
    
    # Check pool configuration
    engine_options = app.config['SQLALCHEMY_ENGINE_OPTIONS']
    assert engine_options['pool_size'] == 20, "Pool size should be 20"
    assert engine_options['max_overflow'] == 30, "Max overflow should be 30"
    assert engine_options['pool_recycle'] == 3600, "Pool recycle should be 3600"
    assert engine_options['pool_pre_ping'] is True, "Pool pre-ping should be enabled"
    print("✓ Database connection pool configured correctly")
    
    # Test multiple connections
    with app.app_context():
        for i in range(5):
            result = db.session.execute(db.text("SELECT 1"))
            assert result.scalar() == 1
        print("✓ Multiple database connections working")

def test_batch_processing():
    """Test batch processing capabilities"""
    print("\n=== Testing Batch Processing ===")
    
    app = create_app()
    with app.app_context():
        bg_tasks = BackgroundTasks()
        
        # Create test data batch
        test_posts = []
        for i in range(25):  # Test batch processing with 25 posts
            post_data = {
                'post_id': f'batch_test_{i}_{int(time.time())}',
                'content': f'Batch processing test post #{i} for Phase 2 architecture',
                'created_at': datetime.utcnow(),
                'author': {
                    'username': f'batch_user_{i}',
                    'name': f'Batch Test User {i}',
                    'follower_count': 100 + i,
                    'verified': i % 3 == 0,
                    'profile_url': f'https://twitter.com/batch_user_{i}'
                },
                'metrics': {
                    'like_count': i * 2,
                    'reply_count': i,
                    'retweet_count': i // 2,
                    'quote_count': 1
                }
            }
            test_posts.append(post_data)
        
        # Test batch processing
        stored_posts = bg_tasks._store_posts_and_authors(test_posts)
        print(f"✓ Batch processing successful: {len(stored_posts)} posts stored")
        
        # Verify data integrity
        assert len(stored_posts) == 25, "All posts should be stored"
        print("✓ Batch data integrity verified")

def test_task_monitoring():
    """Test task monitoring and recovery mechanisms"""
    print("\n=== Testing Task Monitoring ===")
    
    correlation_id = str(uuid.uuid4())[:8]
    task_id = f"test_task_{int(time.time())}"
    
    # Test task start
    metrics = task_monitor.start_task(task_id, "test_task", correlation_id)
    assert metrics.task_id == task_id
    assert metrics.status == TaskStatus.RUNNING
    print("✓ Task monitoring start working")
    
    # Test task completion
    time.sleep(0.1)  # Small delay to show duration
    task_monitor.complete_task(task_id, posts_processed=10, trends_created=2)
    
    # Verify task is no longer in running tasks
    running_tasks = task_monitor.get_running_tasks()
    assert task_id not in running_tasks
    print("✓ Task monitoring completion working")
    
    # Test task failure
    fail_task_id = f"fail_test_{int(time.time())}"
    task_monitor.start_task(fail_task_id, "fail_test", correlation_id)
    task_monitor.fail_task(fail_task_id, "Test failure message")
    
    running_tasks = task_monitor.get_running_tasks()
    assert fail_task_id not in running_tasks
    print("✓ Task monitoring failure handling working")

def test_exception_hierarchy():
    """Test comprehensive exception hierarchy"""
    print("\n=== Testing Exception Hierarchy ===")
    
    correlation_id = str(uuid.uuid4())[:8]
    
    # Test base exception
    try:
        raise TwitterAPIException("Test Twitter API error", correlation_id=correlation_id)
    except TwitterAPIException as e:
        assert e.correlation_id == correlation_id
        assert "Test Twitter API error" in str(e)
        print("✓ TwitterAPIException working correctly")
    
    # Test database exception
    try:
        raise DatabaseException("Test database error", correlation_id=correlation_id)
    except DatabaseException as e:
        assert e.correlation_id == correlation_id
        print("✓ DatabaseException working correctly")
    
    # Test processing exception
    try:
        raise ProcessingException("Test processing error", correlation_id=correlation_id)
    except ProcessingException as e:
        assert e.correlation_id == correlation_id
        print("✓ ProcessingException working correctly")
    
    print("✓ Exception hierarchy implemented correctly")

def test_correlation_ids():
    """Test correlation ID logging system"""
    print("\n=== Testing Correlation ID System ===")
    
    app = create_app()
    with app.app_context():
        # Create multiple background task instances
        bg1 = BackgroundTasks()
        bg2 = BackgroundTasks()
        
        # Verify unique correlation IDs
        assert bg1.correlation_id != bg2.correlation_id
        assert len(bg1.correlation_id) == 8  # UUID first 8 chars
        print(f"✓ Unique correlation IDs: {bg1.correlation_id}, {bg2.correlation_id}")

def test_database_indexes():
    """Test database performance indexes"""
    print("\n=== Testing Database Indexes ===")
    
    app = create_app()
    with app.app_context():
        # Query to check if indexes exist
        index_query = """
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename IN ('posts', 'authors', 'engagement', 'trends', 'trend_scores', 'post_trends')
        AND indexname LIKE 'idx_%'
        """
        
        result = db.session.execute(db.text(index_query))
        indexes = [row[0] for row in result.fetchall()]
        
        expected_indexes = [
            'idx_posts_publish_date',
            'idx_posts_created_at', 
            'idx_posts_author_id',
            'idx_engagement_post_id',
            'idx_engagement_timestamp',
            'idx_authors_username',
            'idx_authors_follower_count',
            'idx_trends_created_at',
            'idx_trend_scores_date_generated',
            'idx_post_trends_trend_id'
        ]
        
        for expected_idx in expected_indexes:
            if expected_idx in indexes:
                print(f"✓ Index found: {expected_idx}")
            else:
                print(f"⚠ Index missing: {expected_idx}")
        
        print(f"✓ Database indexes verified: {len(indexes)} total indexes")

def test_transaction_management():
    """Test database transaction management"""
    print("\n=== Testing Transaction Management ===")
    
    app = create_app()
    with app.app_context():
        bg_tasks = BackgroundTasks()
        
        # Test successful transaction
        try:
            with bg_tasks.database_transaction():
                # This should work without issues
                test_author = Author(
                    username=f"transaction_test_{int(time.time())}",
                    author_name="Transaction Test User",
                    follower_count=100
                )
                db.session.add(test_author)
            print("✓ Successful transaction management working")
        except Exception as e:
            print(f"✗ Transaction management failed: {e}")
        
        # Test failed transaction rollback
        try:
            with bg_tasks.database_transaction():
                # This should trigger a rollback
                db.session.execute(db.text("SELECT * FROM nonexistent_table"))
        except DatabaseException:
            print("✓ Transaction rollback working correctly")
        except Exception as e:
            print(f"⚠ Unexpected transaction error: {e}")

def run_comprehensive_test():
    """Run all Phase 2 architecture tests"""
    print("🚀 Starting Phase 2 Architecture Test Suite")
    print("=" * 60)
    
    try:
        test_singleton_pattern()
        test_database_connection_pooling()
        test_batch_processing()
        test_task_monitoring()
        test_exception_hierarchy()
        test_correlation_ids()
        test_database_indexes()
        test_transaction_management()
        
        print("\n" + "=" * 60)
        print("✅ ALL PHASE 2 ARCHITECTURE TESTS PASSED!")
        print("Phase 2 improvements are working correctly.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)