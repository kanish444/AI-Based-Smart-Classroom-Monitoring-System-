import openpyxl
import os
from datetime import datetime

EXCEL_FOLDER = "attendance_records"

def ensure_folder():
    if not os.path.exists(EXCEL_FOLDER):
        os.makedirs(EXCEL_FOLDER)

def save_attendance(attendance_dict):
    ensure_folder()
    
    today = datetime.now().strftime("%d-%m-%Y")
    filename = f"{EXCEL_FOLDER}/Attendance_{today}.xlsx"

    # File already exists check
    if os.path.exists(filename):
        wb = openpyxl.load_workbook(filename)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Attendance {today}"
        # Header row
        ws.append(["Reg No", "Student Name", "Status", "Date", "Time"])

    # Data save
    current_time = datetime.now().strftime("%I:%M %p")
    for reg_no, name in attendance_dict.items():
        ws.append([reg_no, name, "Present", today, current_time])

    wb.save(filename)
    print(f"[EXCEL SAVED] {filename}")

def send_monthly_report():
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders

    # ⚠️ உன் Gmail details போடு
    SENDER_EMAIL = "kanishvanjiaman444z@gmail.com"
    SENDER_PASSWORD = "hscptlqnedmqwccd"
    TEACHER_EMAIL = "kanishkanish486z@gmail.com"

    ensure_folder()
    month = datetime.now().strftime("%B_%Y")
    
    files = [f for f in os.listdir(EXCEL_FOLDER) if f.endswith(".xlsx")]
    
    if not files:
        print("[EMAIL] No files to send!")
        return

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = TEACHER_EMAIL
    msg['Subject'] = f"Monthly Attendance Report - {month}"
    msg.attach(MIMEText(f"Please find attached the attendance report for {month}.", 'plain'))

    for file in files:
        filepath = os.path.join(EXCEL_FOLDER, file)
        with open(filepath, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={file}')
            msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[EMAIL SENT] Monthly report sent to {TEACHER_EMAIL}")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")