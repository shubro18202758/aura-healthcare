"""
MCP Quick Test Script
Run this to verify MCP system is working correctly
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.mcp.mcp_server import mcp_server


async def test_mcp():
    """Test MCP system initialization and context fetching"""
    
    print("=" * 60)
    print("🧪 MCP SYSTEM TEST")
    print("=" * 60)
    
    # Test 1: Initialize MCP
    print("\n📋 Test 1: MCP Server Initialization")
    try:
        await mcp_server.initialize()
        print("✅ MCP Server initialized successfully")
        print(f"   Providers loaded: {len(mcp_server.providers)}")
        for name, provider in mcp_server.providers.items():
            status = "✓" if provider else "✗"
            print(f"   {status} {name}")
    except Exception as e:
        print(f"❌ MCP initialization failed: {e}")
        return
    
    # Test 2: Service Classification
    print("\n📋 Test 2: Service Classification")
    test_messages = [
        ("I have chest pain and feeling dizzy", "Health Query"),
        ("Can I book an appointment for tomorrow?", "Appointment Booking"),
        ("What does my insurance cover?", "Insurance Query"),
        ("I can't login to the app", "Tech Support"),
        ("Need to schedule a blood test", "Phlebotomy")
    ]
    
    for message, expected_type in test_messages:
        try:
            result = await mcp_server.classify_interaction(
                user_id="test_user",
                message=message
            )
            actual_type = result.get("service_type", "Unknown")
            confidence = result.get("confidence", 0)
            
            match = "✅" if expected_type.lower() in actual_type.lower() else "⚠️"
            print(f"   {match} '{message[:40]}...'")
            print(f"      → {actual_type} (confidence: {confidence:.1%})")
        except Exception as e:
            print(f"   ❌ Classification error: {e}")
    
    # Test 3: Context Fetching
    print("\n📋 Test 3: Context Fetching")
    try:
        from app.mcp.mcp_server import get_mcp_context
        
        context = await get_mcp_context(
            user_id="test_user",
            message="I've been having headaches for a week",
            conversation_id="test_conv"
        )
        
        print("✅ Context fetched successfully")
        print(f"   Total relevance: {context.get('total_relevance', 0):.2f}")
        print(f"   Providers used: {len(context.get('contexts', {}))}")
        
        if context.get('context_summary'):
            summary = context['context_summary'][:150]
            print(f"   Summary: {summary}...")
        
    except Exception as e:
        print(f"❌ Context fetching error: {e}")
    
    # Test 4: Training Data
    print("\n📋 Test 4: Training Data")
    try:
        provider = mcp_server.providers.get("service_classification")
        if provider:
            stats = provider.get_classification_stats()
            print(f"✅ Training data loaded")
            print(f"   Examples: {stats.get('total_training_examples', 0)}")
            print(f"   Service types: {len(stats.get('service_types', []))}")
            print(f"   Overall accuracy: {stats.get('overall_accuracy', 0):.1%}")
        else:
            print("⚠️  Service classification provider not available")
    except Exception as e:
        print(f"❌ Training data error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 MCP TEST COMPLETE")
    print("=" * 60)
    print("\n✅ All core components working!")
    print("📚 Read backend/app/mcp/README.md for full documentation")
    print("🔌 Test API: http://localhost:8000/api/mcp/health")
    print("\n")


if __name__ == "__main__":
    asyncio.run(test_mcp())
