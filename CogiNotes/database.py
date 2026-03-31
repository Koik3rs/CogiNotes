"""
SQLite Database Layer for Student Portal
Handles all data persistence for credentials, forum posts, and file metadata.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_portal.db")

class Database:
    def __init__(self):
        self.db_file = DB_FILE
        self._init_db()

    def _init_db(self):
        """Initialize database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Users/Credentials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                profile_picture_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migrate users table if needed
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'profile_picture_path' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_picture_path TEXT")

        # File metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                course TEXT,
                topic TEXT,
                program TEXT,
                uploader TEXT,
                upload_date TEXT,
                status TEXT DEFAULT 'pending',
                approved_by TEXT,
                rejection_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migrate file_metadata table if needed
        cursor.execute("PRAGMA table_info(file_metadata)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'status' not in columns:
            cursor.execute("ALTER TABLE file_metadata ADD COLUMN status TEXT DEFAULT 'pending'")
        if 'approved_by' not in columns:
            cursor.execute("ALTER TABLE file_metadata ADD COLUMN approved_by TEXT")
        if 'rejection_reason' not in columns:
            cursor.execute("ALTER TABLE file_metadata ADD COLUMN rejection_reason TEXT")

        # Forum posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forum_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT,
                post_date TEXT,
                status TEXT DEFAULT 'pending',
                approved_by TEXT,
                rejection_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migrate forum_posts table if needed
        cursor.execute("PRAGMA table_info(forum_posts)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'status' not in columns:
            cursor.execute("ALTER TABLE forum_posts ADD COLUMN status TEXT DEFAULT 'pending'")
        if 'approved_by' not in columns:
            cursor.execute("ALTER TABLE forum_posts ADD COLUMN approved_by TEXT")
        if 'rejection_reason' not in columns:
            cursor.execute("ALTER TABLE forum_posts ADD COLUMN rejection_reason TEXT")

        # Forum replies table (linked to posts)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forum_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                body TEXT,
                reply_date TEXT,
                status TEXT DEFAULT 'pending',
                approved_by TEXT,
                rejection_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES forum_posts(id) ON DELETE CASCADE
            )
        """)

        # Migrate forum_replies table if needed
        cursor.execute("PRAGMA table_info(forum_replies)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'status' not in columns:
            cursor.execute("ALTER TABLE forum_replies ADD COLUMN status TEXT DEFAULT 'pending'")
        if 'approved_by' not in columns:
            cursor.execute("ALTER TABLE forum_replies ADD COLUMN approved_by TEXT")
        if 'rejection_reason' not in columns:
            cursor.execute("ALTER TABLE forum_replies ADD COLUMN rejection_reason TEXT")

        # Downloads tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                filename TEXT NOT NULL,
                download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)

        conn.commit()
        conn.close()

        # Load default credentials if DB is empty
        self._load_default_credentials()

    def _load_default_credentials(self):
        """Load default credentials on first run."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            default_users = {
                "admin": "password123",
                "student001": "pass1234",
                "student002": "pass5678"
            }
            for username, password in default_users.items():
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, password)
                )
            conn.commit()
        conn.close()

    # ─── CREDENTIALS ─────────────────────────────────────────────
    def get_credentials(self):
        """Return dict of {username: password} for backward compatibility."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM users")
        creds = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return creds

    def verify_user(self, username, password):
        """Check if credentials are valid."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result and result[0] == password

    def add_user(self, username, password):
        """Add a new user."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    # ─── PROFILE PICTURES ───────────────────────────────────────
    def set_profile_picture(self, username, picture_path):
        """Set user's profile picture path."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET profile_picture_path = ? WHERE username = ?",
            (picture_path, username)
        )
        conn.commit()
        conn.close()

    def get_profile_picture(self, username):
        """Get user's profile picture path."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT profile_picture_path FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else None

    # ─── FILE METADATA ──────────────────────────────────────────
    def save_file_metadata(self, filename, course="", topic="", program="", uploader=""):
        """Save or update file metadata. New uploads are set to 'pending' status."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        upload_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            # Always set to pending for new uploads or re-uploads
            cursor.execute("""
                INSERT OR REPLACE INTO file_metadata 
                (filename, course, topic, program, uploader, upload_date, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (filename, course, topic, program, uploader, upload_date))
            conn.commit()
        finally:
            conn.close()

    def get_file_metadata(self, filename):
        """Get metadata for a specific file."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT course, topic, program, uploader, upload_date
            FROM file_metadata WHERE filename = ?
        """, (filename,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                "course": result[0],
                "topic": result[1],
                "program": result[2],
                "uploader": result[3],
                "date": result[4]
            }
        return {}

    def get_all_file_metadata(self):
        """Get metadata for all files as a dict."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT filename, course, topic, program, uploader, upload_date, status FROM file_metadata")
        meta = {}
        for row in cursor.fetchall():
            meta[row[0]] = {
                "course": row[1],
                "topic": row[2],
                "program": row[3],
                "uploader": row[4],
                "date": row[5],
                "status": row[6] if row[6] else "pending"
            }
        conn.close()
        return meta

    def delete_file_metadata(self, filename):
        """Delete metadata for a file."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM file_metadata WHERE filename = ?", (filename,))
        conn.commit()
        conn.close()

    def get_pending_files(self):
        """Get all pending file uploads for admin review."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT filename, course, topic, program, uploader, upload_date, rejection_reason
            FROM file_metadata WHERE status = 'pending'
        """)
        files = [dict(zip(['filename', 'course', 'topic', 'program', 'uploader', 'upload_date', 'rejection_reason'], row)) 
                 for row in cursor.fetchall()]
        conn.close()
        return files

    def approve_file(self, filename, admin_username):
        """Approve a pending file upload."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE file_metadata SET status = 'approved', approved_by = ? WHERE filename = ?",
            (admin_username, filename)
        )
        conn.commit()
        conn.close()

    def reject_file(self, filename, admin_username, reason=""):
        """Reject a pending file upload."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE file_metadata SET status = 'rejected', approved_by = ?, rejection_reason = ? WHERE filename = ?",
            (admin_username, reason, filename)
        )
        conn.commit()
        conn.close()

    def get_file_status(self, filename):
        """Get the approval status of a file."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM file_metadata WHERE filename = ?", (filename,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    # ─── FORUM POSTS ────────────────────────────────────────────
    def add_forum_post(self, author, title, body):
        """Add a new forum post."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        post_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("""
            INSERT INTO forum_posts (author, title, body, post_date)
            VALUES (?, ?, ?, ?)
        """, (author, title, body, post_date))
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return post_id

    def add_forum_reply(self, post_id, author, body):
        """Add a reply to a forum post."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        reply_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("""
            INSERT INTO forum_replies (post_id, author, body, reply_date)
            VALUES (?, ?, ?, ?)
        """, (post_id, author, body, reply_date))
        conn.commit()
        conn.close()

    def get_all_forum_posts(self):
        """Get all forum posts with their replies (JSON-compatible format)."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Get all approved posts
        cursor.execute("""
            SELECT id, author, title, body, post_date, status
            FROM forum_posts WHERE status = 'approved' ORDER BY created_at DESC
        """)
        posts = []
        for row in cursor.fetchall():
            post_id, author, title, body, post_date, status = row
            
            # Get approved replies for this post
            cursor.execute("""
                SELECT author, body, reply_date
                FROM forum_replies WHERE post_id = ? AND status = 'approved' ORDER BY created_at ASC
            """, (post_id,))
            replies = [
                {"author": r[0], "body": r[1], "date": r[2]}
                for r in cursor.fetchall()
            ]

            posts.append({
                "id": post_id,
                "author": author,
                "title": title,
                "body": body,
                "date": post_date,
                "status": status,
                "replies": replies
            })

        conn.close()
        return posts

    def delete_forum_post(self, post_id):
        """Delete a forum post (cascades to replies)."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM forum_posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()

    def get_pending_forum_content(self):
        """Get all pending forum posts and replies for admin review."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        result = {"posts": [], "replies": []}
        
        # Get pending posts
        cursor.execute("""
            SELECT id, author, title, body, post_date, rejection_reason
            FROM forum_posts WHERE status = 'pending' ORDER BY created_at ASC
        """)
        result["posts"] = [dict(zip(['id', 'author', 'title', 'body', 'post_date', 'rejection_reason'], row)) 
                          for row in cursor.fetchall()]
        
        # Get pending replies
        cursor.execute("""
            SELECT id, post_id, author, body, reply_date, rejection_reason
            FROM forum_replies WHERE status = 'pending' ORDER BY created_at ASC
        """)
        result["replies"] = [dict(zip(['id', 'post_id', 'author', 'body', 'reply_date', 'rejection_reason'], row)) 
                           for row in cursor.fetchall()]
        
        conn.close()
        return result

    def approve_forum_post(self, post_id, admin_username):
        """Approve a pending forum post."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE forum_posts SET status = 'approved', approved_by = ? WHERE id = ?",
            (admin_username, post_id)
        )
        conn.commit()
        conn.close()

    def reject_forum_post(self, post_id, admin_username, reason=""):
        """Reject a pending forum post."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE forum_posts SET status = 'rejected', approved_by = ?, rejection_reason = ? WHERE id = ?",
            (admin_username, reason, post_id)
        )
        conn.commit()
        conn.close()

    def approve_forum_reply(self, reply_id, admin_username):
        """Approve a pending forum reply."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE forum_replies SET status = 'approved', approved_by = ? WHERE id = ?",
            (admin_username, reply_id)
        )
        conn.commit()
        conn.close()

    def reject_forum_reply(self, reply_id, admin_username, reason=""):
        """Reject a pending forum reply."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE forum_replies SET status = 'rejected', approved_by = ?, rejection_reason = ? WHERE id = ?",
            (admin_username, reason, reply_id)
        )
        conn.commit()
        conn.close()

    # ─── UTILITY ─────────────────────────────────────────────────
    def clear_all(self):
        """Clear all data (use with caution)."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM forum_replies")
        cursor.execute("DELETE FROM forum_posts")
        cursor.execute("DELETE FROM file_metadata")
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()
        self._load_default_credentials()

    def get_db_stats(self):
        """Get database statistics."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM forum_posts")
        post_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM file_metadata")
        file_count = cursor.fetchone()[0]
        conn.close()
        return {
            "users": user_count,
            "posts": post_count,
            "files": file_count,
            "db_size_kb": os.path.getsize(self.db_file) / 1024 if os.path.exists(self.db_file) else 0
        }

    # ─── DOWNLOADS TRACKING ─────────────────────────────────────
    def record_download(self, username, filename):
        """Record that a user has downloaded a file."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_downloads (username, filename) VALUES (?, ?)",
            (username, filename)
        )
        conn.commit()
        conn.close()

    def get_user_downloads(self, username):
        """Get list of files downloaded by a user."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT filename FROM user_downloads WHERE username = ? ORDER BY download_date DESC",
            (username,)
        )
        downloads = [row[0] for row in cursor.fetchall()]
        conn.close()
        return downloads


# Global instance
db = Database()
