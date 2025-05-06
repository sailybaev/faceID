import sys
import sqlite3
import pandas as pd
import cv2
import openpyxl
import face_recognition
import numpy as np
from docx import Document
from fpdf import FPDF
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QTabWidget, QFileDialog, QLabel, 
    QLineEdit, QHBoxLayout, QMessageBox, QListWidget, QListWidgetItem, 
    QInputDialog
)

from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime, timedelta

class FaceIDApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face ID Attendance System")
        self.setGeometry(100, 100, 900, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.last_seen = {}

        self.last_recognized = {}
        self.create_database_tab()
        self.create_export_tab()
        self.create_user_management_tab()
        self.create_camera_tab()

    # Вкладка 1: Просмотр базы данных
    def create_database_tab(self):
        self.db_tab = QWidget()
        layout = QVBoxLayout()

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.clear_history_button = QPushButton("🗑 Очистить историю")
        self.clear_history_button.clicked.connect(self.clear_history)
        layout.addWidget(self.clear_history_button)

        self.reset_ids_button = QPushButton("🔄 Обновить ID")
        self.reset_ids_button.clicked.connect(self.reset_ids)
        layout.addWidget(self.reset_ids_button)

        self.load_database()

        self.db_tab.setLayout(layout)
        self.tabs.addTab(self.db_tab, "📋 База данных")

    def load_database(self):
        conn = sqlite3.connect("faceid.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance")
        records = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(records))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Имя", "Дата", "Время"])

        for row_idx, row_data in enumerate(records):
            for col_idx, data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def clear_history(self):
        conn = sqlite3.connect("faceid.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance")
        conn.commit()
        conn.close()
        self.load_database()
        QMessageBox.information(self, "Очистка", "История успешно очищена!")

    def reset_ids(self):
        conn = sqlite3.connect("faceid.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, date, time FROM attendance ORDER BY id")
        records = cursor.fetchall()
        cursor.execute("DELETE FROM attendance")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='attendance'")
        for idx, record in enumerate(records, start=1):
            cursor.execute("INSERT INTO attendance (id, name, date, time) VALUES (?, ?, ?, ?)", (idx, record[0], record[1], record[2]))
        conn.commit()
        conn.close()
        self.load_database()
        QMessageBox.information(self, "Обновление ID", "ID успешно пересчитаны!")

    # Вкладка 2: Экспорт данных
    def create_export_tab(self):
        self.export_tab = QWidget()
        layout = QVBoxLayout()

        self.export_excel_button = QPushButton("📤 Экспорт в Excel")
        self.export_excel_button.clicked.connect(self.export_to_excel)
        layout.addWidget(self.export_excel_button)

        self.export_word_button = QPushButton("📄 Экспорт в Word")
        self.export_word_button.clicked.connect(self.export_to_word)
        layout.addWidget(self.export_word_button)

        self.export_pdf_button = QPushButton("📜 Экспорт в PDF")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        layout.addWidget(self.export_pdf_button)

        self.export_tab.setLayout(layout)
        self.tabs.addTab(self.export_tab, "📤 Экспорт")

    def export_to_excel(self):
        conn = sqlite3.connect("faceid.db")
        df = pd.read_sql_query("SELECT * FROM attendance", conn)
        conn.close()
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить как", "", "Excel Files (*.xlsx)")
        if file_path:
            df.to_excel(file_path, index=False)

    def export_to_word(self):
        conn = sqlite3.connect("faceid.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance")
        records = cursor.fetchall()
        conn.close()
        doc = Document()
        doc.add_heading("История посещений", level=1)
        for record in records:
            doc.add_paragraph(f"ID: {record[0]}, Имя: {record[1]}, Дата: {record[2]}, Время: {record[3]}")
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить как", "", "Word Files (*.docx)")
        if file_path:
            doc.save(file_path)

    def export_to_pdf(self):
        conn = sqlite3.connect("faceid.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance")
        records = cursor.fetchall()
        conn.close()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, "История посещений", ln=True, align='C')
        pdf.ln(10)
        for record in records:
            pdf.cell(200, 10, f"ID: {record[0]}, Имя: {record[1]}, Дата: {record[2]}, Время: {record[3]}", ln=True)
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить как", "", "PDF Files (*.pdf)")
        if file_path:
            pdf.output(file_path)

    # Вкладка 3: Управление пользователями
    def create_user_management_tab(self):
        self.user_tab = QWidget()
        layout = QVBoxLayout()

        self.user_list = QListWidget()
        layout.addWidget(self.user_list)

        self.add_user_button = QPushButton("➕ Добавить пользователя")
        self.add_user_button.clicked.connect(self.add_user)
        layout.addWidget(self.add_user_button)

        self.delete_user_button = QPushButton("❌ Удалить пользователя")
        self.delete_user_button.clicked.connect(self.delete_user)
        layout.addWidget(self.delete_user_button)

        self.load_users()

        self.user_tab.setLayout(layout)
        self.tabs.addTab(self.user_tab, "👤 Пользователи")

    def load_users(self):
        self.user_list.clear()
        conn = sqlite3.connect("faceid.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, photo FROM users")
        users = cursor.fetchall()
        conn.close()

        for user in users:
            item = QListWidgetItem(user[0])
            if user[1]:  
                pixmap = QPixmap(user[1]).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)
                icon = QIcon(pixmap)  
                item.setIcon(icon)
            self.user_list.addItem(item)

    def add_user(self):
     while True:
        name, ok = QInputDialog.getText(self, "Добавление пользователя", "Введите имя:")
        if not ok or not name:
            return

        if any(char.isdigit() for char in name):
            QMessageBox.warning(self, "Ошибка", "Имя не должно содержать цифр!")
            continue

        break  # Если имя прошло проверку, выходим из цикла

     file_path, _ = QFileDialog.getOpenFileName(self, "Выберите фото", "", "Images (*.png *.jpg *.jpeg)")
     if file_path:
        self.save_user(name, file_path)


    def save_user(self, name, file_path):
        conn = sqlite3.connect("faceid.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, photo) VALUES (?, ?)", (name, file_path))
        conn.commit()
        conn.close()
        self.load_users()

    def delete_user(self):
        selected_item = self.user_list.currentItem()
        if selected_item:
            name = selected_item.text()
            conn = sqlite3.connect("faceid.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE name = ?", (name,))
            conn.commit()
            conn.close()
            self.load_users()

    def create_camera_tab(self):
        self.camera_tab = QWidget()
        layout = QVBoxLayout()

        # Add fixed size for camera display
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("background-color: black;")
        layout.addWidget(self.camera_label)

        button_layout = QHBoxLayout()

        self.start_camera_button = QPushButton("📷 Включить камеру")
        self.start_camera_button.clicked.connect(self.start_camera)
        button_layout.addWidget(self.start_camera_button)

        self.stop_camera_button = QPushButton("🛑 Выключить камеру")
        self.stop_camera_button.clicked.connect(self.stop_camera)
        button_layout.addWidget(self.stop_camera_button)

        layout.addLayout(button_layout)
        self.camera_tab.setLayout(layout)
        self.tabs.addTab(self.camera_tab, "📷 Камера")


    def start_camera(self):
        # Remove the Windows-specific CAP_DSHOW parameter
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть камеру!")
            return

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera)
        self.timer.start(30)

    def stop_camera(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        self.camera_label.clear()
        if hasattr(self, 'timer'):
            self.timer.stop()

    def update_camera(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        recognized_name = self.recognize_face(rgb_frame)

        if recognized_name:
            if recognized_name != "Неизвестный":
                now = datetime.now()
                if recognized_name not in self.last_seen or now - self.last_seen[recognized_name] > timedelta(
                        minutes=1):
                    self.last_seen[recognized_name] = now
                    self.save_attendance(recognized_name)
                    self.load_database()
            else:
                self.show_unrecognized_face_warning()

        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # Scale image to fit label while preserving aspect ratio
        pixmap = QPixmap.fromImage(qt_img)
        scaled_pixmap = pixmap.scaled(self.camera_label.width(), self.camera_label.height(),
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)

        self.camera_label.setPixmap(scaled_pixmap)

    def show_unrecognized_face_warning(self):
     QMessageBox.warning(self, "Лицо не распознано", "Лицо не найдено в базе данных. Пожалуйста, зарегистрируйтесь!")


    def recognize_face(self, frame):
     conn = sqlite3.connect("faceid.db")
     cursor = conn.cursor()
     cursor.execute("SELECT name, photo FROM users")
     users = cursor.fetchall()
     conn.close()

     known_encodings = []
     known_names = []

     for user in users:
        try:
            image = face_recognition.load_image_file(user[1])
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(user[0])
        except Exception as e:
            print(f"Ошибка загрузки изображения {user[1]}: {e}")

     face_locations = face_recognition.face_locations(frame)
     face_encodings = face_recognition.face_encodings(frame, face_locations)

     if not face_encodings:
        return None

     for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        name = "Неизвестный"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_names[first_match_index]
            print(f"Распознан: {name}")
            return name

     return "Неизвестный"


    def save_attendance(self, name):
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        conn = sqlite3.connect("faceid.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)", (name, date, time))
        conn.commit()
        conn.close()
        print(f"{name} записан в базу на {date} {time}")


# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FaceIDApp()
    window.show()
    sys.exit(app.exec())
