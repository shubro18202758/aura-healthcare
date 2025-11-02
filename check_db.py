from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['aura_healthcare']

print('Total conversations:', db.conversations.count_documents({}))
print('\nConversations:')
for c in db.conversations.find({}, {'conversation_id': 1, 'patient_id': 1, 'status': 1, 'created_at': 1}):
    print(f"ID: {c.get('conversation_id', 'N/A')}")
    print(f"  Patient ID: {c.get('patient_id', 'N/A')}")
    print(f"  Status: {c.get('status', 'N/A')}")
    print(f"  Created: {c.get('created_at', 'N/A')}")
    print()
