import cv2
import os
import numpy as np
import json

print("Step 1: Libraries loaded", flush=True)

FACES_FOLDER = "student_faces"
STUDENT_DB = "student_db.json"
TRAINER_FILE = "trainer.yml"

def train():
    print("Step 2: Train function started", flush=True)
    
    if not os.path.exists(FACES_FOLDER):
        print("[ERROR] student_faces folder not found!")
        input("Press Enter...")
        return

    if not os.path.exists(STUDENT_DB):
        print("[ERROR] student_db.json not found!")
        input("Press Enter...")
        return

    print("Step 3: Loading database...", flush=True)
    
    with open(STUDENT_DB, 'r') as f:
        db = json.load(f)
    
    print(f"Step 4: Students found: {db}", flush=True)

    recognizer = cv2.face.LBPHFaceRecognizer_create()

    faces = []
    labels = []
    label_map = {}

    for idx, (reg_no, name) in enumerate(db.items()):
        label_map[idx] = reg_no
        student_folder = os.path.join(FACES_FOLDER, reg_no)

        print(f"Step 5: Loading photos for {name}...", flush=True)

        if not os.path.exists(student_folder):
            print(f"[!] No photos for {name} ({reg_no})")
            continue

        for img_file in os.listdir(student_folder):
            img_path = os.path.join(student_folder, img_file)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                img = cv2.resize(img, (200, 200))
                faces.append(img)
                labels.append(idx)

        print(f"[✓] {name} - {len(faces)} photos loaded", flush=True)

    if len(faces) == 0:
        print("[ERROR] No face photos found!")