import cv2
import threading
import time
import os
import requests
from flask import Flask, Response
import platform
import yagmail


EMAIL_SENDER = 'itworkermykola@gmail.com'
EMAIL_PASSWORD = 'golov200811'
EMAIL_RECEIVER = 'beslejmikola0@gmail.com'


VIDEO_FOLDER = 'video'
SNAPSHOT_FOLDER = 'snapshots'

for folder in [VIDEO_FOLDER, SNAPSHOT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)


def internet_on():
    try:
        requests.get('https://www.google.com', timeout=3)
        return True
    except requests.RequestException:
        return False


def dim_screen():
    if platform.system() == "Windows":
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(0)
        except ImportError:
            print("Для затемнення екрана встановіть 'screen_brightness_control'")
    else:
        print("Затемнення екрану підтримується тільки на Windows")


def send_email(snapshot_path):
    try:
        yag = yagmail.SMTP(EMAIL_SENDER, EMAIL_PASSWORD)
        contents = [
            "Увага! Виявлено рух. Ось скріншот.",
            yagmail.inline(snapshot_path)
        ]
        yag.send(EMAIL_RECEIVER, 'Сповіщення про рух', contents)
        print("[INFO] Email надіслано.")
    except Exception as e:
        print(f"[ERROR] Не вдалося надіслати email: {e}")


def detect_motion_and_record():
    cap = cv2.VideoCapture(0)
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()

    last_email_time = 0
    email_interval = 60
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    filename = time.strftime("%Y-%m-%d_%H-%M-%S") + ".avi"
    out = cv2.VideoWriter(os.path.join(VIDEO_FOLDER, filename), fourcc, 20.0, (640, 480))

    while True:
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) < 1000:
                continue
            motion_detected = True
            break

        if motion_detected:
            # Записуємо кадри
            out.write(frame1)
            current_time = time.time()
            if current_time - last_email_time > email_interval:
                snapshot_path = os.path.join(SNAPSHOT_FOLDER, f"snapshot_{int(current_time)}.jpg")
                cv2.imwrite(snapshot_path, frame1)
                send_email(snapshot_path)
                last_email_time = current_time

        frame1 = frame2
        ret, frame2 = cap.read()
        if not ret:
            break

    cap.release()
    out.release()


def gen_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

app = Flask(__name__)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    dim_screen()
    while True:
        if internet_on():
            print("[INFO] Інтернет є — запускаємо стрім...")
            flask_thread = threading.Thread(target=run_flask)
            flask_thread.daemon = True
            flask_thread.start()
            flask_thread.join()
        else:
            print("[INFO] Інтернету немає — детекція руху і локальний запис...")
            detect_motion_and_record()
