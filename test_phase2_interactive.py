#!/usr/bin/env python3
"""
Interactive demonstration of Phase 2 architecture improvements
"""
from app import create_app, db
from tasks.background_tasks import BackgroundTasks
from services.service_manager import ServiceManager
from utils.monitoring import task_monitor
import time

def interactive_demo():
    """Interactive demonstration of Phase 2 features"""
    
    print("🔬 Phase 2 Architecture Interactive Demo")
    print("=" * 50)
    
    app = create_app()
    with app.app_context():
        
        # 1. Demonstrate Singleton Pattern
        print("\n1. Singleton Pattern Demo:")
        print("Creating multiple ServiceManager instances...")
        sm1 = ServiceManager()
        sm2 = ServiceManager()
        print(f"   Instance 1 ID: {id(sm1)}")
        print(f"   Instance 2 ID: {id(sm2)}")
        print(f"   Same instance? {sm1 is sm2}")
        
        # 2. Demonstrate Service Access
        print("\n2. Service Access Demo:")
        twitter_svc = sm1.twitter_service
        trend_svc = sm1.trend_service
        config = sm1.config
        print(f"   Twitter Service: {type(twitter_svc).__name__}")
        print(f"   Trend Service: {type(trend_svc).__name__}")
        print(f"   Config: {type(config).__name__}")
        
        # 3. Demonstrate Background Tasks with Correlation ID
        print("\n3. Background Tasks Demo:")
        bg_tasks = BackgroundTasks()
        print(f"   Correlation ID: {bg_tasks.correlation_id}")
        print(f"   Service Manager: {type(bg_tasks.service_manager).__name__}")
        
        # 4. Demonstrate Task Monitoring
        print("\n4. Task Monitoring Demo:")
        task_id = f"demo_task_{int(time.time())}"
        metrics = task_monitor.start_task(task_id, "demo_task", bg_tasks.correlation_id)
        print(f"   Started task: {task_id}")
        print(f"   Task status: {metrics.status.value}")
        
        time.sleep(1)  # Simulate work
        
        task_monitor.complete_task(task_id, posts_processed=5, trends_created=1)
        print(f"   Task completed successfully")
        
        # 5. Demonstrate Database Connection Pool
        print("\n5. Database Connection Pool Demo:")
        for i in range(3):
            result = db.session.execute(db.text("SELECT current_timestamp"))
            timestamp = result.scalar()
            print(f"   Connection {i+1}: {timestamp}")
        
        # 6. Demonstrate Exception Handling
        print("\n6. Exception Handling Demo:")
        from utils.exceptions import ProcessingException
        try:
            raise ProcessingException("Demo exception", bg_tasks.correlation_id)
        except ProcessingException as e:
            print(f"   Caught exception: [{e.correlation_id}] {e.message}")
        
        # 7. Show Database Indexes
        print("\n7. Database Performance Indexes:")
        index_query = """
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename IN ('posts', 'authors', 'engagement') 
        AND indexname LIKE 'idx_%'
        LIMIT 5
        """
        result = db.session.execute(db.text(index_query))
        indexes = result.fetchall()
        for idx in indexes:
            print(f"   ✓ {idx[0]}")
        
        print("\n" + "=" * 50)
        print("✅ Phase 2 Architecture Demo Complete!")
        print("\nKey improvements demonstrated:")
        print("• Singleton pattern for efficient service management")
        print("• Database connection pooling for better performance")
        print("• Task monitoring with correlation IDs for tracking")
        print("• Comprehensive exception handling hierarchy")
        print("• Batch processing capabilities")
        print("• Performance indexes for faster queries")

if __name__ == "__main__":
    interactive_demo()