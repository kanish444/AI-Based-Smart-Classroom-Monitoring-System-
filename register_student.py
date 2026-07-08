import cv2
import os
import json

STUDENT_DB = "student_db.json"
FACES_FOLDER = "student_faces"

def load_db():
    if os.path.exists(STUDENT_DB):
        with open(STUDENT_DB, 'r') as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(STUDENT_DB, 'w') as f:
        json.dump(db, f, indent=4)

def register_student():
    db = load_db()

    print("\n=============================")
    print("  Student Registration")
    print("=============================")
    reg_no = input("Enter Reg No (e.g. 21CS001): ").strip()
    name = input("Enter Student Name: ").strip()

    if reg_no in db:
        print(f"[!] {reg_no} already registered!")
        return

    # Create folder
    student_folder = os.path.join(FACES_FOLDER, reg_no)
    os.makedirs(student_folder, exist_ok=True)

    print(f"\n[*] Opening camera for {name}...")
    print("[*] Press SPACE to capture photo (need 30 photos)")
    print("[*] Press Q to quit\n")

    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.putText(frame, f"Photos: {count}/30 - SPACE to capture",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Student: {name}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.imshow("Register Student - Press SPACE to capture", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord(' '):  # Space bar
            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                face_img = gray[y:y+h, x:x+w]
                face_img = cv2.resize(face_img, (200, 200))
                img_path = os.path.join(student_folder, f"{count}.jpg")
                cv2.imwrite(img_path, face_img)
                count += 1
                print(f"[✓] Photo {count}/30 captured!")

                if count >= 30:
                    print("[✓] 30 photos captured!")
                    break
            else:
                print("[!] No face detected! Try again.")

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if count >= 10:
        db[reg_no] = name
        save_db(db)
        print(f"\n[✓] {name} ({reg_no}) registered successfully!")
        print(f"[✓] {count} photos saved!")
        print("\nNow run: python train_faces.py")
    else:
        print(f"\n[!] Only {count} photos captured. Need at least 10!")

if __name__ == "__main__":
    register_student()
    