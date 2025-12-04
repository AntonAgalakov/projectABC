import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
from deepface import DeepFace
import threading
import time


class EmotionCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Распознавание эмоций")
        self.root.geometry("800x700")

        # Заголовок
        tk.Label(root, text="Распознавание эмоций", font=("Arial", 16)).pack(pady=10)

        # Кнопки
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(
            btn_frame, text="Запустить", command=self.start_camera,
            font=("Arial", 12), bg="green", fg="white", width=15
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(
            btn_frame, text="Остановить", command=self.stop_camera,
            font=("Arial", 12), bg="red", fg="white", width=15, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Видео (увеличенный размер)
        self.video_label = tk.Label(root, bg="black")
        self.video_label.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Результат
        self.result_label = tk.Label(
            root, text="Эмоция: —", font=("Arial", 18, "bold"), fg="blue"
        )
        self.result_label.pack(pady=5)

        self.confidence_label = tk.Label(
            root, text="Уверенность: —", font=("Arial", 14)
        )
        self.confidence_label.pack()

        # Переменные
        self.is_running = False
        self.cap = None
        self.current_emotion = "—"
        self.current_confidence = 0

        # Перевод эмоций
        self.emotion_dict = {
            "angry": "Злость", "disgust": "Отвращение", "fear": "Страх",
            "happy": "Радость", "sad": "Грусть", "surprise": "Удивление",
            "neutral": "Нейтральное"
        }

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_camera(self):
        if self.is_running:
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Ошибка", "Не удалось открыть камеру")
            return

        # Устанавливаем хорошее разрешение
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        # Запускаем поток
        threading.Thread(target=self.process_camera, daemon=True).start()

    def process_camera(self):
        last_analysis = 0

        while self.is_running and self.cap:
            ret, frame = self.cap.read()
            if not ret:
                break

            current_time = time.time()

            # Анализируем каждую секунду
            if current_time - last_analysis > 1.0:
                try:
                    # Распознавание эмоций
                    result = DeepFace.analyze(
                        frame,
                        actions=['emotion'],
                        detector_backend='opencv',  # Надежный и быстрый
                        enforce_detection=False,
                        silent=True
                    )

                    if isinstance(result, list):
                        result = result[0]

                    self.current_emotion = result["dominant_emotion"]
                    self.current_confidence = result["emotion"][self.current_emotion]

                    # Рисуем рамку
                    if "region" in result:
                        x, y, w, h = result["region"]["x"], result["region"]["y"], \
                            result["region"]["w"], result["region"]["h"]
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(frame, self.current_emotion, (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                    last_analysis = current_time

                except Exception as e:
                    print(f"Ошибка анализа: {e}")
                    self.current_emotion = "Ошибка"
                    self.current_confidence = 0

            # Конвертируем кадр для Tkinter
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)

            # Подгоняем под размер окна
            img.thumbnail((700, 500))
            imgtk = ImageTk.PhotoImage(image=img)

            # Обновляем GUI
            self.root.after(0, self.update_gui, imgtk)

            time.sleep(0.05)  # ~20 FPS

    def update_gui(self, imgtk):
        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)

        # Обновляем результат
        if self.current_emotion in self.emotion_dict:
            emotion_text = self.emotion_dict[self.current_emotion]
        else:
            emotion_text = self.current_emotion

        self.result_label.config(text=f"Эмоция: {emotion_text}")

        if self.current_confidence > 0:
            self.confidence_label.config(text=f"Уверенность: {self.current_confidence:.1f}%")
        else:
            self.confidence_label.config(text="Уверенность: —")

    def stop_camera(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.video_label.config(image='', text="Камера остановлена", bg="gray")
        self.result_label.config(text="Эмоция: —")
        self.confidence_label.config(text="Уверенность: —")

    def on_closing(self):
        self.stop_camera()
        self.root.destroy()


if __name__ == "__main__":
    print("Запуск программы...")
    print("Первый запуск займет время для загрузки моделей")

    root = tk.Tk()
    app = EmotionCameraApp(root)
    root.mainloop()
