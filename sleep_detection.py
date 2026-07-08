import cv2
import time

sleep_tracker = {}
SLEEP_THRESHOLD = 120
alerted_students = set()
eye_closed_frames = {}
eye_open_frames = {}

CLOSED_FRAMES_NEEDED = 20
OPEN_FRAMES_NEEDED = 5

eye_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml'
)

def check_sleep(frame, student_id):
    global sleep_tracker, alerted_students
    global eye_closed_frames, eye_open_frames

    is_sleeping = False
    sleep_duration = 0

    h, w = frame.shape[:2]

    # Upper half of face only — eyes இருக்கும் area
    upper_face = frame[0:h//2, 0:w]

    # Multiple sizes try பண்றோம்
    sizes = [(200, 200), (300, 300), (150, 150)]
    eyes_detected = False

    for size in sizes:
        resized = cv2.resize(upper_face, size)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        eyes = eye_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(15, 15)
        )

        if len(eyes) >= 1:
            eyes_detected = True
            break

    print(f"[EYE] {student_id} - {'OPEN' if eyes_detected else 'CLOSED'}")

    if not eyes_detected:
        if student_id not in eye_closed_frames:
            eye_closed_frames[student_id] = 0
        eye_closed_frames[student_id] += 1
        eye_open_frames[student_id] = 0

        print(f"[CLOSED] {student_id} - {eye_closed_frames[student_id]} frames")

        if eye_closed_frames[student_id] >= CLOSED_FRAMES_NEEDED:
            if student_id not in sleep_tracker:
                sleep_tracker[student_id] = time.time()
                print(f"[SLEEP TIMER STARTED] {student_id}")
            else:
                sleep_duration = time.time() - sleep_tracker[student_id]
                print(f"[SLEEP] {student_id} - {int(sleep_duration)}s")
                if sleep_duration >= SLEEP_THRESHOLD:
                    is_sleeping = True
    else:
        if student_id not in eye_open_frames:
            eye_open_frames[student_id] = 0
        eye_open_frames[student_id] += 1

        if eye_open_frames[student_id] >= OPEN_FRAMES_NEEDED:
            eye_closed_frames[student_id] = 0
            if student_id in sleep_tracker:
                del sleep_tracker[student_id]
                print(f"[RESET] {student_id} - eyes open confirmed!")
            if student_id in alerted_students:
                alerted_students.discard(student_id)

    return is_sleeping, sleep_duration

def should_send_alert(student_id):
    if student_id not in alerted_students:
        alerted_students.add(student_id)
        return True
    return False

def reset_tracker():
    global sleep_tracker, alerted_students
    global eye_closed_frames, eye_open_frames
    sleep_tracker.clear()
    alerted_students.clear()
    eye_closed_frames.clear()
    eye_open_frames.clear()