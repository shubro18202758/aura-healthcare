"""
Test script to populate RAG knowledge base with medical knowledge from internet
Run this after starting the backend server
"""

import asyncio
import aiohttp
import json

async def populate_rag():
    """Trigger RAG population with medical knowledge"""
    
    base_url = "http://localhost:8000"
    
    # First, you need an admin token
    print("📝 Step 1: Login as admin to get token")
    print("Please run this command first:")
    print(f"curl -X POST {base_url}/api/auth/login -H 'Content-Type: application/json' -d '{{\"username\": \"admin\", \"password\": \"your_admin_password\"}}'")
    print()
    
    # Get admin token from user input
    admin_token = input("Enter your admin access token: ").strip()
    
    if not admin_token:
        print("❌ No token provided. Exiting.")
        return
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        
        # Check current document count
        print("\n📊 Checking current document count...")
        try:
            async with session.get(
                f"{base_url}/api/admin/rag/documents/count",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Current documents in RAG: {data.get('total_documents', 0)}")
                else:
                    print(f"⚠️  Could not get document count: {response.status}")
        except Exception as e:
            print(f"⚠️  Error checking document count: {e}")
        
        # Trigger comprehensive knowledge fetch
        print("\n🚀 Triggering comprehensive knowledge fetch...")
        print("⏳ This will fetch 100+ medical documents from:")
        print("   - PubMed: 80 research articles (8 medical topics)")
        print("   - WHO: 3 guideline pages")
        print("   - CDC: 4 guideline pages")
        print("   - RxNorm: 10 drug information entries")
        print("   - MedlinePlus: 8 medical condition entries")
        print("\n⏱️  Estimated time: 5-10 minutes (running in background)")
        
        try:
            async with session.post(
                f"{base_url}/api/admin/rag/populate/comprehensive",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"\n✅ {data['message']}")
                    print(f"📚 Sources: {', '.join(data['sources'])}")
                    print(f"⏱️  Estimated time: {data['estimated_time']}")
                    print("\n💡 The fetch is running in the background.")
                    print("   You can check the status with:")
                    print(f"   curl {base_url}/api/admin/rag/populate/status -H 'Authorization: Bearer YOUR_TOKEN'")
                else:
                    error_text = await response.text()
                    print(f"\n❌ Failed to trigger fetch: {response.status}")
                    print(f"   Error: {error_text}")
                    return
        except Exception as e:
            print(f"\n❌ Error triggering fetch: {e}")
            return
        
        # Poll for completion
        print("\n⏳ Monitoring fetch status (checking every 30 seconds)...")
        print("   Press Ctrl+C to stop monitoring (fetch continues in background)")
        
        try:
            while True:
                await asyncio.sleep(30)
                
                try:
                    async with session.get(
                        f"{base_url}/api/admin/rag/populate/status",
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('is_fetching'):
                                print("⏳ Still fetching documents...")
                            elif data.get('last_fetch'):
                                last_fetch = data['last_fetch']
                                if last_fetch.get('status') == 'completed':
                                    print("\n✅ Fetch completed!")
                                    print(f"   Documents fetched: {last_fetch.get('documents_fetched', 0)}")
                                    print(f"   Documents added to RAG: {last_fetch.get('documents_added', 0)}")
                                    print(f"   Duration: {last_fetch.get('duration_seconds', 0):.2f}s")
                                    break
                                elif last_fetch.get('status') == 'failed':
                                    print("\n❌ Fetch failed!")
                                    print(f"   Error: {last_fetch.get('error', 'Unknown error')}")
                                    break
                except Exception as e:
                    print(f"⚠️  Error checking status: {e}")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Stopped monitoring, but fetch continues in background.")
            print("   Check status later with the API endpoint.")
        
        # Final document count
        print("\n📊 Checking final document count...")
        try:
            async with session.get(
                f"{base_url}/api/admin/rag/documents/count",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Total documents in RAG: {data.get('total_documents', 0)}")
        except Exception as e:
            print(f"⚠️  Error checking document count: {e}")
        
        # Test search
        print("\n🔍 Testing RAG search with medical query...")
        test_query = "What are the symptoms of diabetes?"
        
        try:
            async with session.post(
                f"{base_url}/api/admin/rag/documents/search",
                headers=headers,
                params={"query": test_query, "limit": 3}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"\n✅ Search successful! Found {data.get('count', 0)} results")
                    
                    results = data.get('results', [])
                    if results:
                        print(f"\n📄 Top result:")
                        result = results[0]
                        content = result.get('content', '')[:200]
                        metadata = result.get('metadata', {})
                        print(f"   Content: {content}...")
                        print(f"   Source: {metadata.get('source', 'Unknown')}")
                        print(f"   Category: {metadata.get('category', 'Unknown')}")
                else:
                    print(f"⚠️  Search failed: {response.status}")
        except Exception as e:
            print(f"⚠️  Error testing search: {e}")
        
        print("\n🎉 RAG knowledge base populated successfully!")
        print("\n💡 Next steps:")
        print("   1. Try asking medical questions in the chat")
        print("   2. The RAG will use this knowledge to provide accurate answers")
        print("   3. You can add more documents using the custom endpoint")

if __name__ == "__main__":
    print("🏥 AURA Healthcare - RAG Knowledge Population")
    print("=" * 60)
    asyncio.run(populate_rag())
