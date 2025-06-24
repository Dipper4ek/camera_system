# camera_system


Твій код уже досить функціональний, але для досягнення цілей:

Зробити стрім доступним з будь-якого пристрою через будь-який інтернет.

Зберігати всі відео 24 години та дозволити перегляд будь-якого моменту.

Додати можливість створення скріншотів через веб-інтерфейс.

Потрібно суттєво розширити функціонал. Ось повний план із поетапною реалізацією:

✅ 1. Доступ до стріму з будь-якого пристрою
Твій Flask-сервер працює на 0.0.0.0, що дозволяє доступ у локальній мережі. Щоб працювало через інтернет:

Варианти:
Використати ngrok (безкоштовно для тестів)

Використати VPS або хостинг із відкритим портом

Налаштувати порт-форвардинг на роутері (менш безпечно)

Приклад з ngrok:
Встанови ngrok

Запусти:

bash
Kopieren
Bearbeiten
ngrok http 5000
Отримаєш публічне посилання, яке можна використовувати будь-де.

✅ 2. Можливість робити скріншоти через веб
🔧 Рішення:
Додати новий ендпоінт /snapshot, який робитиме скріншот з камери:

python
Kopieren
Bearbeiten
@app.route('/snapshot')
def take_snapshot():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        timestamp = int(time.time())
        snapshot_path = os.path.join(SNAPSHOT_FOLDER, f"snapshot_{timestamp}.jpg")
        cv2.imwrite(snapshot_path, frame)
        return f"Скріншот збережено: {snapshot_path}"
    else:
        return "Помилка зчитування камери", 500
✅ 3. Перегляд архіву відео за 24 години
Твій код уже зберігає відео. Додай веб-сторінку для перегляду:

🔧 HTML інтерфейс:
python
Kopieren
Bearbeiten
from flask import send_from_directory, render_template_string

@app.route('/')
def index():
    files = sorted(os.listdir(VIDEO_FOLDER), reverse=True)
    file_list_html = "".join(f"<li><a href='/video/{file}'>{file}</a></li>" for file in files)
    return render_template_string("""
        <h1>Записи відео за останні 24 години</h1>
        <ul>{{ files|safe }}</ul>
        <br>
        <a href='/video_feed'>🎥 Переглянути стрім</a><br>
        <a href='/snapshot'>📸 Зробити скріншот</a>
    """, files=file_list_html)

@app.route('/video/<filename>')
def video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)
✅ 4. Автоматичне видалення відео старше 24 годин
python
Kopieren
Bearbeiten
def clean_old_videos():
    now = time.time()
    for filename in os.listdir(VIDEO_FOLDER):
        path = os.path.join(VIDEO_FOLDER, filename)
        if os.stat(path).st_mtime < now - 24 * 3600:
            os.remove(path)
Додай виклик цієї функції щогодини або перед початком запису:

python
Kopieren
Bearbeiten
clean_old_videos()
✅ 5. Оновлений main запуск
python
Kopieren
Bearbeiten
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
            clean_old_videos()
            detect_motion_and_record()
📌 Безпека:
Ніколи не зберігай email-паролі в коді! Використовуй змінні середовища або .env.

Захисти доступ до веб-інтерфейсу через пароль або авторизацію, якщо стрім доступний публічно.
