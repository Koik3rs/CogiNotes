# Study Buddy Portal - Features Guide

## ✅ All Features Implemented and Functional

---

## 🔐 Login Credentials

### Student Accounts
- **Username:** `student001` | **Password:** `pass1234`
- **Username:** `student002` | **Password:** `pass5678`

### Admin Account
- **Username:** `admin` | **Password:** `password123`

---

## 🎯 Login Screen Features

### 1. **Role-Based Login**
- Select between **🧑‍🎓 Student** or **🛡️ Admin** before logging in
- Different placeholders for student number vs admin username
- Role-specific validation and error messages

### 2. **Quick Admin Login Button**
- Click **👤 Admin Quick Login** to auto-fill admin credentials
- Instantly logs in without manually entering credentials
- Saves time for admin testing

### 3. **Forgot Password Feature**
- Click **🔑 Forgot Password?** button on login page
- Answer your security question
- Set a new password
- Works for both student and admin accounts

### 4. **Create New Account**
- Click **📝 Create new account** to register as a student
- Fill in username, password, security question/answer
- Account created with "student" role by default

---

## 👑 Admin Panel Features

Access admin panel by:
1. Login as admin (`admin` / `password123`)
2. Select **Admin Panel** from navigation sidebar

### Top Control Bar Buttons

#### 1. **➕ Create Admin Button**
- **Location:** Top-right of Admin Panel
- **Function:** Create a new admin account
- **What you need:**
  - Admin Username (unique)
  - Password (min 6 characters)
  - Confirm Password
  - Security Question
  - Security Answer
- **Click:** "Create Admin" to save

#### 2. **👨‍🎓 Register Student Button**
- **Location:** Top-right of Admin Panel (next to Create Admin)
- **Function:** Register a new student account
- **What you need:**
  - Student Number (unique)
  - Password (min 6 characters)
  - Confirm Password
  - Security Question
  - Security Answer
- **Click:** "Register Student" to save

### Admin Review Tabs

After buttons, there are 3 review tabs:

1. **Files** - Approve/Reject uploaded files
   - View pending file uploads
   - Approve files to make them visible to students
   - Reject files if they don't meet guidelines
   - View file metadata (course, topic, uploader)

2. **Posts** - Approve/Reject forum posts
   - Review pending forum posts
   - Approve posts to publish them
   - Reject posts for community guideline violations

3. **Replies** - Approve/Reject forum replies
   - Review pending forum replies to posts
   - Approve to publish replies
   - Reject inappropriate replies

---

## 📚 Student Features

### Main Menu Options (Sidebar)
1. **Home** - Dashboard with welcome message and recent files
2. **Browse** - Search and filter uploaded files
3. **Forums** - Discuss with other students
4. **Downloads** - View downloaded files history
5. **Upload** - Upload study materials

### Student Capabilities
- Upload files (PDF, DOC/DOCX, JPEG, PNG, CSV)
- Add metadata to files (course, topic, program)
- Browse approved files
- Download files
- Create and reply to forum posts
- Change profile picture
- Reset password if forgotten

---

## 🚀 How to Test All Features

### Test Admin Registration
1. Login as admin
2. Go to Admin Panel
3. Click **👨‍🎓 Register Student**
4. Fill in all fields:
   - Student Number: `teststudent01`
   - Password: `testpass123`
   - Confirm: `testpass123`
   - Security Question: `What is your favorite color?`
   - Answer: `blue`
5. Click "Register Student"
6. Logout and login with new credentials

### Test Admin Creation
1. Login as admin
2. Go to Admin Panel
3. Click **➕ Create Admin**
4. Fill in all fields:
   - Admin Username: `testadmin01`
   - Password: `adminpass123`
   - Confirm: `adminpass123`
   - Security Question: `What is your pet's name?`
   - Answer: `fluffy`
5. Click "Create Admin"
6. Logout and login with new admin credentials

### Test Forgot Password
1. Go to login screen
2. Click **🔑 Forgot Password?**
3. Enter username: `student001`
4. Type security answer: `fluffy`
5. Enter new password: `newpass456`
6. Click "Reset Password"
7. Login with new password

---

## 💡 Key Features Summary

✅ **Dual Login System** - Separate student and admin workflows
✅ **Admin Management** - Create new admin accounts
✅ **Student Registration** - Admin can register students
✅ **Password Reset** - Security question-based recovery
✅ **File Approval System** - Admin reviews and approves uploads
✅ **Forum Moderation** - Admin reviews and approves posts
✅ **Role-Based Access** - Different features for students vs admins
✅ **Profile Pictures** - Students can upload profile images
✅ **Download Tracking** - System tracks what students download

---

## 📱 Running the Application

```powershell
cd "C:\Users\Rochelle Lumibao\study buddy.py-orig"
python study_buddy.py
```

The application will start with a login screen. All buttons are fully functional and visible!

---

## ⚙️ Technical Details

- **Database:** SQLite (auto-created on first run)
- **Frontend:** Tkinter GUI
- **Role System:** Student vs Admin with separate workflows
- **Security:** Password-based with security questions
- **File Storage:** Local uploads folder with metadata tracking

