# Admin Panel - Complete Guide

## 🔐 How to Access Admin Panel

1. **Start the app**
   ```powershell
   python study_buddy.py
   ```

2. **Login as Admin**
   - Select **🛡️ Admin** role
   - Username: `admin`
   - Password: `password123`
   - Click **Login** or use **👤 Admin Quick Login** button

3. **Click "Admin Panel"** in the left sidebar

---

## 📍 Admin Panel Layout

```
┌─────────────────────────────────────────────────────────┐
│ Admin Management Panel                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Quick Actions:                                          │
│ [➕ Create New Admin]  [👨‍🎓 Register New Student]     │
│                                                         │
│ Content Review                                          │
│ [Files] [Posts] [Replies]                              │
│                                                         │
│ ┌───────────────────────────────────────────────────┐  │
│ │ Content Review Area                               │  │
│ │ (Shows files, posts, or replies based on tab)     │  │
│ │                                                   │  │
│ └───────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🟢 Button #1: Create New Admin

**Location:** Top-left area under "Quick Actions"
**Color:** Green button
**Full Text:** `➕ Create New Admin`

### What it does:
Creates a new administrator account with full access to the admin panel

### How to use:
1. Click the **green button** labeled "➕ Create New Admin"
2. A dialog window will open with these fields:
   - **Admin Username** (required, must be unique)
   - **Password** (required, minimum 6 characters)
   - **Confirm Password** (must match password)
   - **Security Question** (for password recovery)
   - **Security Answer** (for password recovery)

3. Fill in all fields
4. Click **"Create Admin"** button at the bottom
5. You'll see a success message
6. New admin can now login!

### Example:
```
Admin Username: newadmin
Password: admin12345
Confirm: admin12345
Security Question: What is your favorite color?
Security Answer: blue
```

---

## 🔵 Button #2: Register New Student

**Location:** Right next to "Create New Admin" button
**Color:** Blue button
**Full Text:** `👨‍🎓 Register New Student`

### What it does:
Registers a new student account so they can access the portal

### How to use:
1. Click the **blue button** labeled "👨‍🎓 Register New Student"
2. A dialog window will open with these fields:
   - **Student Number** (required, must be unique)
   - **Password** (required, minimum 6 characters)
   - **Confirm Password** (must match password)
   - **Security Question** (for password recovery)
   - **Security Answer** (for password recovery)

3. Fill in all fields
4. Click **"Register Student"** button at the bottom
5. You'll see a success message
6. New student can now login!

### Example:
```
Student Number: STU001
Password: student12345
Confirm: student12345
Security Question: What is your pet's name?
Security Answer: fluffy
```

---

## 📋 Content Review Tabs

Below the action buttons, you'll see three tabs:

### **Files Tab**
- Shows pending file uploads from students
- Actions: View, Approve, Reject, Delete

### **Posts Tab**
- Shows pending forum posts
- Actions: Approve, Reject

### **Replies Tab**
- Shows pending forum replies/comments
- Actions: Approve, Reject

---

## ✅ Testing the Features

### Test Creating Admin:
1. Login as `admin` / `password123`
2. Click **Admin Panel**
3. Click green **➕ Create New Admin** button
4. Fill the form:
   - Admin Username: `testadmin01`
   - Password: `testpass123`
   - Confirm: `testpass123`
   - Security Question: `Favorite color?`
   - Answer: `red`
5. Click **"Create Admin"**
6. Success! Log out and login with new credentials

### Test Registering Student:
1. Login as admin
2. Click **Admin Panel**
3. Click blue **👨‍🎓 Register New Student** button
4. Fill the form:
   - Student Number: `STU005`
   - Password: `student456`
   - Confirm: `student456`
   - Security Question: `Favorite movie?`
   - Answer: `avatar`
5. Click **"Register Student"**
6. Success! Log out and login with new credentials

---

## 🎯 Troubleshooting

### Buttons not visible?
- Make sure you're logged in as admin
- Make sure you're on the **Admin Panel** page
- Scroll up if needed - buttons are at the top

### Getting an error when creating admin/student?
- Make sure **username is unique** (not already taken)
- Make sure **password is at least 6 characters**
- Make sure passwords **match in both fields**
- Make sure security **question and answer are filled**

### Dialog won't close?
- Click "Cancel" or the X button to close without saving
- Or fill all required fields and click the action button

---

## 💡 Key Points

✅ Buttons are **large and clearly visible** at the top of Admin Panel
✅ **Green button** = Create Admin
✅ **Blue button** = Register Student
✅ Both buttons open **popup dialogs** to collect information
✅ All fields are **validated before saving**
✅ Success messages confirm when account is created
✅ New accounts can **immediately login** with provided credentials

---

## 🚀 Quick Command

```powershell
cd "C:\Users\Rochelle Lumibao\study buddy.py-orig"
python study_buddy.py
```

Then login and navigate to Admin Panel to see the buttons!

