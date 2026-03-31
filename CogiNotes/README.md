# Student Portal with SQLite Database

## Overview
This is a complete Student Portal application with integrated SQLite database for data persistence. The application handles user authentication, file uploads with metadata, and forum discussions.

## Database Schema

### Tables Created Automatically:

1. **users** - User credentials
   - `id` (PRIMARY KEY)
   - `username` (UNIQUE)
   - `password`
   - `created_at` (TIMESTAMP)

2. **file_metadata** - File upload information
   - `id` (PRIMARY KEY)
   - `filename` (UNIQUE)
   - `course`, `topic`, `program` (metadata fields)
   - `uploader` (student who uploaded)
   - `upload_date`
   - `created_at` (TIMESTAMP)

3. **forum_posts** - Discussion forum posts
   - `id` (PRIMARY KEY)
   - `author`, `title`, `body`
   - `post_date`
   - `created_at` (TIMESTAMP)

4. **forum_replies** - Replies to forum posts
   - `id` (PRIMARY KEY)
   - `post_id` (FOREIGN KEY)
   - `author`, `body`
   - `reply_date`
   - `created_at` (TIMESTAMP)

## Features

✅ **User Authentication** - Login with database-backed credentials
✅ **File Management** - Upload, browse, download files with metadata
✅ **Forum Discussion** - Post topics and reply to discussions
✅ **Persistent Storage** - All data stored in SQLite database
✅ **Modern UI** - Rounded buttons, custom styling, responsive layout

## Default Credentials

| Username    | Password       |
|------------|----------------|
| admin      | password123    |
| student001 | pass1234       |
| student002 | pass5678       |

## Installation

1. **Prerequisites**
   ```bash
   pip install pillow  # Optional: for image preview in uploads
   ```

2. **Run the Application**
   ```bash
   python study_buddy.py
   ```

3. **Database Initialization**
   - First run automatically creates `student_portal.db`
   - Default credentials are loaded from the database module

## File Structure

```
study buddy.py/
├── study_buddy.py        # Main application
├── database.py           # Database module (one level up)
├── student_portal.db     # SQLite database (auto-created)
└── uploads/              # Uploaded files directory
```

## Database Features

### Data Integrity
- Foreign key constraints ensure forum replies can't reference deleted posts
- Cascading deletes maintain data consistency
- Unique constraints prevent duplicate usernames and filenames

### Backward Compatibility
- JSON-style API (`load_forum()`, `load_uploaded_files()`)
- Existing code continues to work without modification

### Database Utilities
Access database statistics:
```python
from database import db
stats = db.get_db_stats()
print(stats)  # {'users': 3, 'posts': 5, 'files': 12, 'db_size_kb': 256}
```

## Key Improvements Over JSON

1. **Transactions** - Atomic writes, no partial updates
2. **Scalability** - Efficiently handles thousands of records
3. **Search** - Native SQL queries for filtering and sorting
4. **Relationships** - Proper foreign keys for data integrity
5. **Querying** - Complex queries without loading entire files

## Running the Application

Simply execute:
```bash
python study_buddy.py
```

The database will be automatically created and initialized with the default schema and credentials on first run.

## Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'database'`
- **Solution**: Ensure `database.py` is in the parent directory of `study buddy.py/`

**Issue**: Permission denied when creating database
- **Solution**: Ensure write permissions in the application directory

**Issue**: Database locked error
- **Solution**: Close other instances of the application, or restart

## Project Structure

The application maintains a clean separation of concerns:
- **UI Layer** (`study_buddy.py`) - All tkinter GUI code
- **Database Layer** (`database.py`) - All SQLite operations
- **Data Storage** (`student_portal.db`) - Persistent SQLite database

## Security Notes

⚠️ **Development Only**: This application uses plaintext password storage for demonstration. 
For production use, implement password hashing (e.g., bcrypt, argon2).

## Future Enhancements

- Add password reset functionality
- Implement role-based access control (admin/student)
- Add search indexing for better forum performance
- Export data to CSV/PDF reports
