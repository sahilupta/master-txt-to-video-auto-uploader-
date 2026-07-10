"""
master/database.py - Database module for MongoDB operations
Reconstructed from database.so analysis
"""
import motor.motor_asyncio
import pytz
from datetime import datetime
from config import Config

IST = pytz.timezone('Asia/Kolkata')


class Database:
    def __init__(self, uri, database_name):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[database_name]
        self.batches = self.db["batches"]
        self.batch_status = self.db["batch_status"]
        self.uploaded_files = self.db["uploaded_files"]
        self.topics = self.db["topics"]
        self.messages = self.db["messages"]

    async def add_batch(self, user_id, course_id, api, token, select, time, group_id, length, credit, filename, thumb):
        batch_data = {
            "user_id": user_id,
            "course_id": course_id,
            "api": api,
            "token": token,
            "select": select,
            "time": time,
            "group_id": group_id,
            "length": length,
            "credit": credit,
            "filename": filename,
            "thumb": thumb,
            "created_at": datetime.now(IST).isoformat()
        }
        await self.batches.update_one(
            {"user_id": user_id, "course_id": course_id},
            {"$set": batch_data},
            upsert=True
        )

    async def delete_batch(self, user_id, course_id):
        await self.batches.delete_one({"user_id": user_id, "course_id": course_id})

    async def delete_batch_status(self, user_id, course_id):
        await self.batch_status.delete_one({"user_id": user_id, "course_id": course_id})

    async def get_all_batches(self, user_id):
        cursor = self.batches.find({"user_id": user_id})
        return await cursor.to_list(length=None)

    async def get_all_batches_with_schedule(self):
        cursor = self.batches.find({"time": {"$ne": None}})
        return await cursor.to_list(length=None)

    async def get_batch(self, user_id, course_id):
        return await self.batches.find_one({"user_id": user_id, "course_id": course_id})

    async def get_batch_status(self, user_id, course_id):
        return await self.batch_status.find_one({"user_id": user_id, "course_id": course_id})

    async def get_incomplete_batches(self):
        cursor = self.batch_status.find({"status": {"$ne": "completed"}})
        return await cursor.to_list(length=None)

    async def get_msg_id(self, url):
        doc = await self.messages.find_one({"url": url})
        return doc.get("msg_id") if doc else None

    async def get_topic(self, group_id, subjectname):
        doc = await self.topics.find_one({"group_id": group_id, "subjectname": subjectname})
        return doc.get("forum_id") if doc else None

    async def is_batch_uptodate(self, user_id, course_id):
        status = await self.get_batch_status(user_id, course_id)
        if status:
            return status.get("status") == "completed"
        return False

    async def is_file_uploaded(self, course_id, url):
        doc = await self.uploaded_files.find_one({"course_id": course_id, "url": url})
        return doc is not None

    async def mark_file_uploaded(self, course_id, url, chat_id):
        await self.uploaded_files.update_one(
            {"course_id": course_id, "url": url},
            {"$set": {"course_id": course_id, "url": url, "chat_id": chat_id, "uploaded_at": datetime.now(IST).isoformat()}},
            upsert=True
        )

    async def save_batch_status(self, user_id, course_id, status):
        await self.batch_status.update_one(
            {"user_id": user_id, "course_id": course_id},
            {"$set": {"user_id": user_id, "course_id": course_id, "status": status, "updated_at": datetime.now(IST).isoformat()}},
            upsert=True
        )

    async def save_msg_id(self, url, msg_id):
        await self.messages.update_one(
            {"url": url},
            {"$set": {"url": url, "msg_id": msg_id}},
            upsert=True
        )

    async def save_topic(self, group_id, forum_id, subjectname):
        await self.topics.update_one(
            {"group_id": group_id, "subjectname": subjectname},
            {"$set": {"group_id": group_id, "forum_id": forum_id, "subjectname": subjectname}},
            upsert=True
        )

    async def update_batch_schedule(self, user_id, course_id, new_time):
        await self.batches.update_one(
            {"user_id": user_id, "course_id": course_id},
            {"$set": {"time": new_time}}
        )


db_instance = Database(Config.DB_URL, Config.DB_NAME)
