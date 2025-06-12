import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
from dotenv import load_dotenv
from typing import Optional, Dict, Any

class Database:
    """Database connection and operations manager"""
    
    def __init__(self):
        """Initialize database connection"""
        load_dotenv()
        
        self.mongo_uri = os.getenv("MONGO_URI")
        if not self.mongo_uri:
            raise ValueError("MONGO_URI environment variable is not set")
            
        self.database_name = os.getenv("DATABASE_NAME", "backend")
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        
        # Collections
        self._news_collection = None
        self._posts_collection = None
        self._users_collection = None
        self._ideas_collection = None

    async def connect(self):
        """Establish database connection"""
        try:
            self.client = AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client[self.database_name]
            
            # Initialize collections
            self._news_collection = self.db["news"]
            self._posts_collection = self.db["posts"]
            self._users_collection = self.db["users"]
            self._ideas_collection = self.db["idea"]
            
            # Verify connection
            await self.client.admin.command('ping')
            print("✅ MongoDB connection successful!")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise e

    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

    @staticmethod
    def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to JSON serializable format"""
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def get_news_by_slug(self, news_slug: str) -> Optional[Dict[str, Any]]:
        """Fetch a single news item by slug"""
        try:
            news = await self._news_collection.find_one({"slug": news_slug})
            return self.serialize_document(news) if news else None
        except Exception as e:
            print(f"Error finding news: {e}")
            return None
# Create global database instance
db = Database()
