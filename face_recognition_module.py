import cv2
import face_recognition
import numpy as np
import sqlite3
import datetime

def load_known_faces():
    """ Загружает известных пользователей из базы данных """
    conn = sqlite3.connect("faceid.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, photo FROM users")
    users = cursor.fetchall()
    conn.close()

    known_face_encodings = []
    known_face_names = []

    for name, photo in users:
        np_array = np.frombuffer(photo, dtype=np.uint8)
        face_image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        face_encoding = face_recognition.face_encodings(face_image)

        if face_encoding:
            known_face_encodings.append(face_encoding[0])
            known_face_names.append(name)

    return known_face_encodings, known_face_names

def recognize_face():
    """ Включает камеру и проверяет лицо по базе """
    known_face_encodings, known_face_names = load_known_faces()

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Неизвестный"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances) if face_distances.size else None

            if best_match_index is not None and matches[best_match_index]:
                name = known_face_names[best_match_index]
                mark_attendance(name)

            for (top, right, bottom, left) in face_locations:
                top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Face Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def mark_attendance(name):
    """ Записывает факт прихода в базу данных """
    conn = sqlite3.connect("faceid.db")
    cursor = conn.cursor()

    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    cursor.execute("INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)", (name, date, time))
    conn.commit()
    conn.close()
