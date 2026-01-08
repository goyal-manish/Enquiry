import streamlit as st
import mysql.connector
import bcrypt
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client

# ---------------- CONFIG ----------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "tuition_db"
}

EMAIL_CONFIG = {
    "email": "yourgmail@gmail.com",
    "password": "GMAIL_APP_PASSWORD",
    "admin_email": "admin@gmail.com"
}

TWILIO_SID = "TWILIO_ACCOUNT_SID"
TWILIO_TOKEN = "TWILIO_AUTH_TOKEN"
TWILIO_FROM = "whatsapp:+14155238886"
ADMIN_WHATSAPP = "whatsapp:+91XXXXXXXXXX"

# ---------------- DB CONNECTION ----------------
def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# ---------------- PASSWORD ----------------
def hash_password(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(pw, hashed):
    return bcrypt.checkpw(pw.encode(), hashed.encode())

# ---------------- EMAIL ----------------
def send_email(msg):
    mail = MIMEText(msg)
    mail["Subject"] = "New Tuition Inquiry"
    mail["From"] = EMAIL_CONFIG["email"]
    mail["To"] = EMAIL_CONFIG["admin_email"]

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_CONFIG["email"], EMAIL_CONFIG["password"])
    server.send_message(mail)
    server.quit()

# ---------------- WHATSAPP ----------------
def send_whatsapp(msg):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.messages.create(
        from_=TWILIO_FROM,
        to=ADMIN_WHATSAPP,
        body=msg
    )

# ---------------- LOGIN ----------------
def login_user(email, password):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    db.close()

    if user and verify_password(password, user["password"]):
        return user
    return None

# ---------------- SIGNUP ----------------
def signup(name, email, password, role):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
        (name, email, hash_password(password), role)
    )
    db.commit()
    db.close()

# ---------------- PARENT DASHBOARD ----------------
def parent_dashboard(user):
    st.subheader("📋 Tuition Inquiry Form")

    with st.form("inquiry"):
        sname = st.text_input("Student Name")
        cls = st.selectbox("Class", [f"{i}th" for i in range(1,13)])
        subjects = st.multiselect("Subjects", ["Maths","Science","English","Hindi"])
        contact = st.text_input("Contact")
        location = st.text_input("Location")

        if st.form_submit_button("Submit Inquiry"):
            db = get_db()
            cur = db.cursor()
            cur.execute("""
                INSERT INTO inquiries (student_name,class,subjects,contact,location)
                VALUES (%s,%s,%s,%s,%s)
            """,(sname,cls,",".join(subjects),contact,location))
            db.commit()
            db.close()

            send_email("📢 New tuition inquiry received")
            send_whatsapp("📢 New tuition inquiry received")

            st.success("Inquiry Submitted Successfully ✅")

# ---------------- TEACHER DASHBOARD ----------------
def teacher_dashboard(user):
    st.subheader("👨‍🏫 Teacher Profile")

    qualification = st.text_input("Qualification")
    experience = st.number_input("Experience (Years)",0,30)
    subjects = st.multiselect("Subjects",["Maths","Science","English","Physics","Chemistry"])
    location = st.text_input("Preferred Location")

    if st.button("Save Profile"):
        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO teachers (user_id,qualification,experience,subjects,location)
            VALUES (%s,%s,%s,%s,%s)
        """,(user["id"],qualification,experience,",".join(subjects),location))
        db.commit()
        db.close()
        st.success("Profile Saved ✅")

# ---------------- ADMIN DASHBOARD ----------------
def admin_dashboard():
    st.subheader("📊 Admin Panel")

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM inquiries")
    data = cur.fetchall()
    db.close()

    for d in data:
        st.write(d)

# ---------------- MAIN APP ----------------
st.set_page_config("Home Tuition Portal","📚")

if "user" not in st.session_state:
    st.session_state.user = None

st.title("🏫 Home Tuition Management System")

menu = st.sidebar.radio("Menu", ["Login","Signup"])

if st.session_state.user is None:

    if menu == "Login":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(email,password)
            if user:
                st.session_state.user = user
                st.success("Login Successful")
            else:
                st.error("Invalid credentials")

    if menu == "Signup":
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["parent","teacher"])

        if st.button("Signup"):
            signup(name,email,password,role)
            st.success("Account Created. Please Login")

else:
    user = st.session_state.user
    st.sidebar.success(f"Logged in as {user['role']}")

    if user["role"] == "parent":
        parent_dashboard(user)
    elif user["role"] == "teacher":
        teacher_dashboard(user)
    elif user["role"] == "admin":
        admin_dashboard()

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()
