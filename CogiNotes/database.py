"""
SQLite Database Layer for Student Portal
Handles all data persistence for credentials, forum posts, and file metadata.
"""

import sqlite3
import json
import os
import time
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_portal.db")

class Database:
    def __init__(self):
        self.db_file = DB_FILE
        self._init_db()

    def _get_connection(self):
        """Get database connection with proper timeout and WAL mode."""
        conn = sqlite3.connect(self.db_file, timeout=20.0, check_same_thread=False)
        conn.isolation_level = None  # Autocommit mode
        return conn

    def _init_db(self):
        """Initialize database schema if it doesn't exist."""
        try:
            conn = self._get_connection()
            conn.isolation_level = None
            cursor = conn.cursor()

            # Users/Credentials table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'student',
                    profile_picture_path TEXT,
                    security_question TEXT,
                    security_answer TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migrate users table if needed
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'role' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student'")
            if 'profile_picture_path' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN profile_picture_path TEXT")
            if 'security_question' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN security_question TEXT")
            if 'security_answer' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN security_answer TEXT")

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
            time.sleep(0.1)  # Small delay to ensure WAL is initialized
            self._load_default_credentials()
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            import traceback
            traceback.print_exc()

    def _load_default_credentials(self):
        """Load default credentials on first run."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                default_users = [
                    ("admin", "password123", "admin", "What is your favorite color?", "blue"),
                    ("student001", "pass1234", "student", "What is your pet's name?", "fluffy"),
                    ("student002", "pass5678", "student", "What city were you born in?", "tokyo")
                ]
                for username, password, role, question, answer in default_users:
                    cursor.execute(
                        "INSERT INTO users (username, password, role, security_question, security_answer) VALUES (?, ?, ?, ?, ?)",
                        (username, password, role, question, answer)
                    )
                conn.commit()
            
            # Ensure admin user has admin role (migration for existing DBs)
            cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'admin'")
            conn.commit()
        finally:
            conn.close()

    # ─── CREDENTIALS ─────────────────────────────────────────────
    def get_credentials(self):
        """Return dict of {username: password} for backward compatibility."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM users")
        creds = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return creds

    def verify_user(self, username, password):
        """Check if credentials are valid."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result and result[0] == password

    def add_user(self, username, password, role="student", security_question="", security_answer=""):
        """Add a new user with role."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, role, security_question, security_answer) VALUES (?, ?, ?, ?, ?)",
                (username, password, role, security_question, security_answer)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user_role(self, username):
        """Get role for given user."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            conn.close()
            # Return role if exists, default to student for backward compat
            if row:
                return row[0] if row[0] else "student"
            return None
        except Exception as e:
            print(f"Error getting user role: {e}")
            return None

    def set_user_role(self, username, role):
        """Set role for existing user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
        conn.commit()
        conn.close()

    def get_all_users(self):
        """Return all users with role and metadata."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, role, profile_picture_path FROM users ORDER BY username")
        users = [{"username": u, "role": r, "profile_picture": p} for (u, r, p) in cursor.fetchall()]
        conn.close()
        return users

    # ─── PROFILE PICTURES ───────────────────────────────────────
    def set_profile_picture(self, username, picture_path):
        """Set user's profile picture path."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET profile_picture_path = ? WHERE username = ?",
            (picture_path, username)
        )
        conn.commit()
        conn.close()

    def get_profile_picture(self, username):
        """Get user's profile picture path."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT profile_picture_path FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else None

    def get_security_question(self, username):
        """Get security question for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT security_question FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else None

    def verify_security_answer(self, username, answer):
        """Verify security answer for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT security_answer FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result and result[0].lower() == answer.lower()

    def update_password(self, username, new_password):
        """Update user's password."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
        conn.commit()
        conn.close()

    # ─── FILE METADATA ──────────────────────────────────────────
    def save_file_metadata(self, filename, course="", topic="", program="", uploader=""):
        """Save or update file metadata. New uploads are set to 'pending' status."""
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM file_metadata WHERE filename = ?", (filename,))
        conn.commit()
        conn.close()

    def get_pending_files(self):
        """Get all pending file uploads for admin review."""
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE file_metadata SET status = 'approved', approved_by = ? WHERE filename = ?",
            (admin_username, filename)
        )
        conn.commit()
        conn.close()

    def reject_file(self, filename, admin_username, reason=""):
        """Reject a pending file upload."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE file_metadata SET status = 'rejected', approved_by = ?, rejection_reason = ? WHERE filename = ?",
            (admin_username, reason, filename)
        )
        conn.commit()
        conn.close()

    def get_file_status(self, filename):
        """Get the approval status of a file."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM file_metadata WHERE filename = ?", (filename,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    # ─── FORUM POSTS ────────────────────────────────────────────
    def add_forum_post(self, author, title, body):
        """Add a new forum post."""
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM forum_posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()

    def get_pending_forum_content(self):
        """Get all pending forum posts and replies for admin review."""
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE forum_posts SET status = 'approved', approved_by = ? WHERE id = ?",
            (admin_username, post_id)
        )
        conn.commit()
        conn.close()

    def reject_forum_post(self, post_id, admin_username, reason=""):
        """Reject a pending forum post."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE forum_posts SET status = 'rejected', approved_by = ?, rejection_reason = ? WHERE id = ?",
            (admin_username, reason, post_id)
        )
        conn.commit()
        conn.close()

    def approve_forum_reply(self, reply_id, admin_username):
        """Approve a pending forum reply."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE forum_replies SET status = 'approved', approved_by = ? WHERE id = ?",
            (admin_username, reply_id)
        )
        conn.commit()
        conn.close()

    def reject_forum_reply(self, reply_id, admin_username, reason=""):
        """Reject a pending forum reply."""
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_downloads (username, filename) VALUES (?, ?)",
            (username, filename)
        )
        conn.commit()
        conn.close()

    def get_user_downloads(self, username):
        """Get list of files downloaded by a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT filename FROM user_downloads WHERE username = ? ORDER BY download_date DESC",
            (username,)
        )
        downloads = [row[0] for row in cursor.fetchall()]
        conn.close()
        return downloads

    def delete_user(self, username):
        """Delete a user and all associated data."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Delete user's downloads
            cursor.execute("DELETE FROM user_downloads WHERE username = ?", (username,))
            
            # Delete user's forum replies
            cursor.execute("DELETE FROM forum_replies WHERE author = ?", (username,))
            
            # Delete user's forum posts (replies will be deleted via CASCADE if set up)
            cursor.execute("DELETE FROM forum_posts WHERE author = ?", (username,))
            
            # Delete user's file metadata (but keep files on disk)
            # Note: files remain in uploads/ directory
            
            # Finally delete the user
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting user {username}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


# Global instance
db = Database()
