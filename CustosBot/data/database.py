import aiosqlite
import asyncio
from datetime import datetime
from typing import Optional, List, Dict

class Database:
    def __init__(self, db_path: str = "data/custos.db"):
        self.db_path = db_path
    
    async def init_db(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    nickname TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Chat members table with ranks
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chat_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    rank TEXT DEFAULT 'participant',
                    message_count INTEGER DEFAULT 0,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, chat_id)
                )
            """)
            
            # Warnings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    reason TEXT,
                    issued_by INTEGER,
                    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Chats table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY,
                    title TEXT,
                    type TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Message statistics
            await db.execute("""
                CREATE TABLE IF NOT EXISTS message_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    date TEXT,
                    count INTEGER DEFAULT 1,
                    UNIQUE(user_id, chat_id, date)
                )
            """)
            
            await db.commit()
    
    async def add_user(self, user_id: int, username: Optional[str] = None, first_name: Optional[str] = None, last_name: Optional[str] = None):
        """Add or update user in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, last_name))
            await db.commit()
    
    async def add_chat_member(self, user_id: int, chat_id: int, rank: str = 'participant'):
        """Add user to chat with specified rank"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO chat_members (user_id, chat_id, rank)
                VALUES (?, ?, ?)
            """, (user_id, chat_id, rank))
            await db.commit()
    
    async def update_user_rank(self, user_id: int, chat_id: int, new_rank: str):
        """Update user rank in specific chat"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE chat_members SET rank = ? WHERE user_id = ? AND chat_id = ?
            """, (new_rank, user_id, chat_id))
            await db.commit()
    
    async def get_user_rank(self, user_id: int, chat_id: int) -> Optional[str]:
        """Get user rank in specific chat"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT rank FROM chat_members WHERE user_id = ? AND chat_id = ?
            """, (user_id, chat_id))
            result = await cursor.fetchone()
            return result[0] if result else None
    
    async def add_warning(self, user_id: int, chat_id: int, reason: str, issued_by: int):
        """Add warning to user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO warnings (user_id, chat_id, reason, issued_by)
                VALUES (?, ?, ?, ?)
            """, (user_id, chat_id, reason, issued_by))
            await db.commit()
    
    async def get_warning_count(self, user_id: int, chat_id: int) -> int:
        """Get warning count for user in chat"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) FROM warnings WHERE user_id = ? AND chat_id = ?
            """, (user_id, chat_id))
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def set_user_nickname(self, user_id: int, nickname: str):
        """Set user nickname"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET nickname = ? WHERE user_id = ?
            """, (nickname, user_id))
            await db.commit()
    
    async def set_user_description(self, user_id: int, description: str):
        """Set user description"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET description = ? WHERE user_id = ?
            """, (description, user_id))
            await db.commit()
    
    async def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT username, first_name, last_name, nickname, description 
                FROM users WHERE user_id = ?
            """, (user_id,))
            result = await cursor.fetchone()
            if result:
                return {
                    'username': result[0],
                    'first_name': result[1],
                    'last_name': result[2],
                    'nickname': result[3],
                    'description': result[4]
                }
            return None
    
    async def get_staff_list(self, chat_id: int) -> Dict[str, List]:
        """Get staff list organized by rank"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT u.user_id, u.username, u.first_name, u.nickname, cm.rank
                FROM users u
                JOIN chat_members cm ON u.user_id = cm.user_id
                WHERE cm.chat_id = ? AND cm.rank != 'participant'
                ORDER BY 
                    CASE cm.rank 
                        WHEN 'owner' THEN 1
                        WHEN 'administrator' THEN 2
                        WHEN 'moderator' THEN 3
                        ELSE 4
                    END
            """, (chat_id,))
            results = await cursor.fetchall()
            
            staff = {'owner': [], 'administrator': [], 'moderator': []}
            for row in results:
                user_info = {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'nickname': row[3]
                }
                rank = row[4]
                if rank in staff:
                    staff[rank].append(user_info)
            
            return staff
    
    async def add_chat(self, chat_id: int, title: str, chat_type: str):
        """Add chat to database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO chats (chat_id, title, type)
                VALUES (?, ?, ?)
            """, (chat_id, title, chat_type))
            await db.commit()
    
    async def get_user_chats(self, user_id: int) -> List[Dict]:
        """Get list of chats where user is a member"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT c.chat_id, c.title, c.type, cm.rank
                FROM chats c
                JOIN chat_members cm ON c.chat_id = cm.chat_id
                WHERE cm.user_id = ?
            """, (user_id,))
            results = await cursor.fetchall()
            
            chats = []
            for row in results:
                chats.append({
                    'chat_id': row[0],
                    'title': row[1],
                    'type': row[2],
                    'rank': row[3]
                })
            
            return chats
    
    async def increment_message_count(self, user_id: int, chat_id: int):
        """Increment user message count for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO message_stats (user_id, chat_id, date, count)
                VALUES (?, ?, ?, 1)
            """, (user_id, chat_id, today))
            
            await db.execute("""
                UPDATE message_stats SET count = count + 1 
                WHERE user_id = ? AND chat_id = ? AND date = ?
            """, (user_id, chat_id, today))
            
            await db.execute("""
                UPDATE chat_members SET message_count = message_count + 1
                WHERE user_id = ? AND chat_id = ?
            """, (user_id, chat_id))
            
            await db.commit()
    
    async def get_user_message_count(self, user_id: int, chat_id: int) -> int:
        """Get total message count for user in chat"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT message_count FROM chat_members 
                WHERE user_id = ? AND chat_id = ?
            """, (user_id, chat_id))
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def get_chat_stats(self, chat_id: int, limit: int = 20):
        """Get chat statistics - top active users"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT 
                    u.user_id,
                    u.nickname,
                    u.first_name,
                    u.username,
                    cm.message_count
                FROM chat_members cm
                JOIN users u ON cm.user_id = u.user_id
                WHERE cm.chat_id = ? AND cm.message_count > 0
                ORDER BY cm.message_count DESC
                LIMIT ?
            """, (chat_id, limit))
            return await cursor.fetchall()
    
    async def find_user_by_username(self, username: str, chat_id: int) -> Optional[int]:
        """Find user ID by username in specific chat"""
        # Remove @ if present
        clean_username = username.lstrip('@')
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT u.user_id FROM users u
                JOIN chat_members cm ON u.user_id = cm.user_id
                WHERE u.username = ? AND cm.chat_id = ?
            """, (clean_username, chat_id))
            result = await cursor.fetchone()
            return result[0] if result else None
    
    async def find_user_by_nickname(self, nickname: str, chat_id: int) -> Optional[int]:
        """Find user ID by nickname in specific chat"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT u.user_id FROM users u
                JOIN chat_members cm ON u.user_id = cm.user_id
                WHERE u.nickname = ? AND cm.chat_id = ?
            """, (nickname, chat_id))
            result = await cursor.fetchone()
            return result[0] if result else None
    
    async def find_user_by_name(self, name: str, chat_id: int) -> Optional[int]:
        """Find user ID by first name in specific chat"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT u.user_id FROM users u
                JOIN chat_members cm ON u.user_id = cm.user_id
                WHERE u.first_name = ? AND cm.chat_id = ?
            """, (name, chat_id))
            result = await cursor.fetchone()
            return result[0] if result else None