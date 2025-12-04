# 👤 User Database Integration Guide

## Current Implementation

The HR Chatbot now includes user authentication with the following features:

### ✅ **Implemented Features**
- **User ID Input Screen**: After clicking "Press to Login", users are prompted to enter their Employee ID
- **User Validation**: Server validates user IDs and provides user information
- **Personalized Status Display**: Shows "User: [ID]" instead of "Enhanced Dataset: Ready"
- **User Context in Logs**: Server logs include user information for better tracking
- **Ticket Association**: Support tickets are linked to specific user IDs

### 🗃️ **Current User Database Structure**

**Location**: `enhanced_hr_server.py` - `UserDatabase` class

**Current Storage**: In-memory dictionary (for demo/development)

**Sample User Records**:
```python
{
    "EMP001234": {"name": "John Doe", "department": "Engineering", "grade": "L5"},
    "EMP005678": {"name": "Jane Smith", "department": "HR", "grade": "L4"},
    "EMP009999": {"name": "Admin User", "department": "IT", "grade": "L6"}
}
```

**Validation Logic**:
- Exact match: Returns full user info from database
- Pattern match: Accepts any ID starting with "EMP" + 6+ characters
- Invalid format: Rejects and provides format guidance

## 🚀 **Future Database Integration**

### **Recommended Database Options**

#### **Option 1: PostgreSQL (Recommended for Enterprise)**
```python
import psycopg2
from sqlalchemy import create_engine

class PostgreSQLUserDatabase:
    def __init__(self):
        self.engine = create_engine('postgresql://user:password@localhost/hr_db')
    
    def validate_user(self, user_id: str) -> dict:
        # Query actual employee database
        query = "SELECT name, department, grade FROM employees WHERE emp_id = %s"
        # Implementation here
```

#### **Option 2: MongoDB (Flexible Document Store)**
```python
from pymongo import MongoClient

class MongoUserDatabase:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client.hr_database
        self.users = self.db.employees
    
    def validate_user(self, user_id: str) -> dict:
        user = self.users.find_one({"emp_id": user_id})
        # Implementation here
```

#### **Option 3: LDAP/Active Directory Integration**
```python
import ldap

class LDAPUserDatabase:
    def __init__(self):
        self.ldap_server = "ldap://company.domain.com"
    
    def validate_user(self, user_id: str) -> dict:
        # Validate against company LDAP
        # Implementation here
```

### **Integration Steps**

1. **Install Database Dependencies**:
   ```bash
   pip install psycopg2-binary  # For PostgreSQL
   pip install pymongo          # For MongoDB
   pip install python-ldap      # For LDAP
   ```

2. **Update UserDatabase Class**:
   - Replace in-memory storage with database connection
   - Update `validate_user()` method to query real database
   - Add error handling for database connection issues

3. **Environment Configuration**:
   ```python
   import os
   
   DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/hr_db')
   LDAP_SERVER = os.getenv('LDAP_SERVER', 'ldap://company.com')
   ```

4. **Security Considerations**:
   - Add input sanitization for user IDs
   - Implement rate limiting for validation requests
   - Add logging for security audit trails
   - Use environment variables for sensitive configuration

### **Database Schema Recommendations**

#### **Employee Table Structure**:
```sql
CREATE TABLE employees (
    emp_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    department VARCHAR(50),
    grade VARCHAR(10),
    manager_id VARCHAR(20),
    hire_date DATE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **Chat Logs Table** (Optional):
```sql
CREATE TABLE chat_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(20) REFERENCES employees(emp_id),
    question TEXT,
    answer TEXT,
    confidence_score FLOAT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

## 🔧 **Configuration Updates Needed**

### **1. Update enhanced_hr_server.py**:
```python
# Replace UserDatabase class with your chosen implementation
from .database import PostgreSQLUserDatabase  # or your choice

# Initialize with real database
user_db = PostgreSQLUserDatabase()
```

### **2. Add Environment Variables**:
Create `.env` file:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/hr_database
LDAP_SERVER=ldap://company.domain.com
LDAP_BIND_DN=cn=admin,dc=company,dc=com
LDAP_PASSWORD=your_ldap_password
```

### **3. Update Docker Configuration** (if using):
```yaml
version: '3.8'
services:
  hr-chatbot:
    build: .
    environment:
      - DATABASE_URL=postgresql://hr_user:password@db:5432/hr_db
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: hr_db
      POSTGRES_USER: hr_user
      POSTGRES_PASSWORD: password
```

## 🎯 **Current User Experience**

1. **Login Flow**: Click "Press to Login" → Enter Employee ID → Continue
2. **Validation**: Server validates ID format and checks database
3. **Personalization**: Status shows "User: [ID]" instead of generic message
4. **Chat Context**: All queries are logged with user information
5. **Ticket Creation**: Support tickets include user ID for follow-up

## 📊 **Testing the System**

### **Demo User IDs** (currently accepted):
- `EMP001234` - John Doe (Engineering)
- `EMP005678` - Jane Smith (HR)  
- `EMP009999` - Admin User (IT)
- Any ID matching pattern `EMP######` (6+ digits)

### **Test Scenarios**:
1. Valid predefined user: Enter `EMP001234`
2. Valid pattern user: Enter `EMP123456`
3. Invalid format: Enter `ABC123` (should be rejected)
4. Empty input: Click Continue without entering ID

## 🚀 **Next Steps for Production**

1. **Choose and implement your preferred database solution**
2. **Set up proper authentication/authorization**
3. **Add user session management**
4. **Implement proper error handling and logging**
5. **Add user preference storage**
6. **Create admin interface for user management**

The current implementation provides a solid foundation that can be easily extended with your organization's specific user database requirements.
