"""Clear old test conversations from database"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def clear_test_data():
    client = AsyncIOMotorClient('mongodb://admin:aura_admin_2024@localhost:27017/aura_healthcare?authSource=admin')
    db = client['aura_healthcare']
    
    # Delete the old test conversation
    result = await db.conversations.delete_many({
        "conversation_id": "conv_1761998049.335064_patient_test123"
    })
    print(f"Deleted {result.deleted_count} old conversations")
    
    # Also delete associated messages
    msg_result = await db.messages.delete_many({
        "conversation_id": "conv_1761998049.335064_patient_test123"
    })
    print(f"Deleted {msg_result.deleted_count} old messages")
    
    client.close()
    print("✅ Test data cleared!")

if __name__ == "__main__":
    asyncio.run(clear_test_data())
