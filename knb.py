import tkinter as tk
from tkinter import messagebox, font
import cv2
from PIL import Image, ImageTk
import numpy as np
import time
import threading
import random
import mediapipe as mp


class RockPaperScissors:
    def __init__(self, root):
        self.root = root
        self.root.title("Камень-Ножницы-Бумага с AI")
        self.root.geometry("1100x750")
        self.root.configure(bg="#2c3e50")

        # Инициализация MediaPipe Hands для распознавания
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,  # Распознаем только одну руку
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=1
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # Переменные игры
        self.player_score = 0
        self.computer_score = 0
        self.round_count = 1
        self.max_rounds = 5
        self.is_capturing = False
        self.cap = None
        self.player_choice = None
        self.computer_choice = None
        self.result_text = "Давайте начнем!"

        # Для распознавания
        self.last_gesture = "Не обнаружено"
        self.confidence = 0
        self.hand_detected = False
        self.finger_count = 0
        self.gesture_history = []  # История жестов для стабилизации

        # Создаем GUI
        self.create_widgets()

    def create_widgets(self):
        # Заголовок с современным дизайном
        header_frame = tk.Frame(self.root, bg="#1a5276", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="🎮 КАМЕНЬ • НОЖНИЦЫ • БУМАГА 🎮",
                 font=("Arial", 24, "bold"), bg="#1a5276", fg="white").pack(expand=True)

        # Основной контейнер
        main_container = tk.Frame(self.root, bg="#2c3e50")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Левая колонка - камера
        left_column = tk.Frame(main_container, bg="#34495e", relief=tk.RAISED, bd=2)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Заголовок камеры
        cam_header = tk.Frame(left_column, bg="#1a5276", height=40)
        cam_header.pack(fill=tk.X)
        cam_header.pack_propagate(False)
        tk.Label(cam_header, text="ВЕБ-КАМЕРА - ПОКАЖИТЕ ЖЕСТ", font=("Arial", 14, "bold"),
                 bg="#1a5276", fg="white").pack(pady=10)

        # Видео
        self.video_label = tk.Label(left_column, bg="black",
                                    text="Нажмите 'Начать игру'\n\nКамера не активна",
                                    font=("Arial", 12), fg="white", justify=tk.CENTER)
        self.video_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Кнопки управления камерой
        control_frame = tk.Frame(left_column, bg="#34495e")
        control_frame.pack(fill=tk.X, padx=20, pady=10)

        self.start_btn = tk.Button(control_frame, text="▶ НАЧАТЬ ИГРУ",
                                   command=self.start_camera, font=("Arial", 12, "bold"),
                                   bg="#27ae60", fg="white", width=15, height=2,
                                   activebackground="#229954", activeforeground="white")
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.capture_btn = tk.Button(control_frame, text="✋ СДЕЛАТЬ ХОД",
                                     command=self.capture_hand, font=("Arial", 12, "bold"),
                                     bg="#3498db", fg="white", width=15, height=2,
                                     state=tk.DISABLED, activebackground="#2980b9", activeforeground="white")
        self.capture_btn.pack(side=tk.LEFT, padx=5)

        # Правая колонка - игра
        right_column = tk.Frame(main_container, bg="#34495e", relief=tk.RAISED, bd=2)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Панель счета
        score_header = tk.Frame(right_column, bg="#1a5276", height=40)
        score_header.pack(fill=tk.X)
        score_header.pack_propagate(False)
        tk.Label(score_header, text="СЧЕТ ИГРЫ", font=("Arial", 14, "bold"),
                 bg="#1a5276", fg="white").pack(pady=10)

        # Отображение счета
        score_display = tk.Frame(right_column, bg="#34495e")
        score_display.pack(pady=20)

        # Игрок
        player_frame = tk.Frame(score_display, bg="#34495e")
        player_frame.pack(side=tk.LEFT, padx=30)
        tk.Label(player_frame, text="ИГРОК", font=("Arial", 14, "bold"),
                 bg="#34495e", fg="#3498db").pack()
        self.player_score_label = tk.Label(player_frame, text="0",
                                           font=("Arial", 48, "bold"), bg="#34495e", fg="white")
        self.player_score_label.pack()

        # VS
        tk.Label(score_display, text="VS", font=("Arial", 24, "bold"),
                 bg="#34495e", fg="#7f8c8d").pack(side=tk.LEFT, padx=20)

        # Компьютер
        computer_frame = tk.Frame(score_display, bg="#34495e")
        computer_frame.pack(side=tk.RIGHT, padx=30)
        tk.Label(computer_frame, text="КОМПЬЮТЕР", font=("Arial", 14, "bold"),
                 bg="#34495e", fg="#e74c3c").pack()
        self.computer_score_label = tk.Label(computer_frame, text="0",
                                             font=("Arial", 48, "bold"), bg="#34495e", fg="white")
        self.computer_score_label.pack()

        # Раунд
        round_frame = tk.Frame(right_column, bg="#34495e")
        round_frame.pack(pady=10)
        self.round_label = tk.Label(round_frame, text=f"Раунд: {self.round_count}/{self.max_rounds}",
                                    font=("Arial", 16), bg="#34495e", fg="#f1c40f")
        self.round_label.pack()

        # Панель текущего раунда
        current_frame = tk.Frame(right_column, bg="#2c3e50", relief=tk.GROOVE, bd=2)
        current_frame.pack(pady=20, padx=20, fill=tk.X)

        # Распознанный жест
        recognition_frame = tk.Frame(current_frame, bg="#2c3e50")
        recognition_frame.pack(pady=15)

        tk.Label(recognition_frame, text="РАСПОЗНАНО:", font=("Arial", 12),
                 bg="#2c3e50", fg="#95a5a6").pack()
        self.recognition_label = tk.Label(recognition_frame, text="—",
                                          font=("Arial", 28, "bold"), bg="#2c3e50", fg="#2ecc71")
        self.recognition_label.pack()

        # Индикатор обнаружения руки
        status_frame = tk.Frame(current_frame, bg="#2c3e50")
        status_frame.pack(pady=10)

        self.status_indicator = tk.Label(status_frame, text="●",
                                         font=("Arial", 20), bg="#2c3e50", fg="#e74c3c")
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))

        self.status_text = tk.Label(status_frame, text="Камера выключена",
                                    font=("Arial", 12), bg="#2c3e50", fg="#95a5a6")
        self.status_text.pack(side=tk.LEFT)

        # Выборы
        choices_frame = tk.Frame(current_frame, bg="#2c3e50")
        choices_frame.pack(pady=20)

        # Ваш выбор
        player_choice_frame = tk.Frame(choices_frame, bg="#2c3e50")
        player_choice_frame.pack(pady=10)
        tk.Label(player_choice_frame, text="ВАШ ВЫБОР:", font=("Arial", 12),
                 bg="#2c3e50", fg="#3498db").pack()
        self.player_choice_display = tk.Label(player_choice_frame, text="—",
                                              font=("Arial", 20, "bold"), bg="#2c3e50", fg="#3498db")
        self.player_choice_display.pack()

        # Выбор компьютера
        computer_choice_frame = tk.Frame(choices_frame, bg="#2c3e50")
        computer_choice_frame.pack(pady=10)
        tk.Label(computer_choice_frame, text="ВЫБОР КОМПЬЮТЕРА:", font=("Arial", 12),
                 bg="#2c3e50", fg="#e74c3c").pack()
        self.computer_choice_display = tk.Label(computer_choice_frame, text="—",
                                                font=("Arial", 20, "bold"), bg="#2c3e50", fg="#e74c3c")
        self.computer_choice_display.pack()

        # Результат
        result_frame = tk.Frame(current_frame, bg="#34495e", relief=tk.SUNKEN, bd=2)
        result_frame.pack(pady=15, padx=10, fill=tk.X)

        self.result_label = tk.Label(result_frame, text=self.result_text,
                                     font=("Arial", 18, "bold"), bg="#34495e", fg="#f1c40f")
        self.result_label.pack(pady=10)

        # Панель управления игрой
        game_controls = tk.Frame(right_column, bg="#34495e")
        game_controls.pack(pady=20)

        self.new_game_btn = tk.Button(game_controls, text="🔄 НОВАЯ ИГРА",
                                      command=self.new_game, font=("Arial", 12),
                                      bg="#9b59b6", fg="white", width=20, height=2,
                                      state=tk.DISABLED, activebackground="#8e44ad", activeforeground="white")
        self.new_game_btn.pack(side=tk.LEFT, padx=5)

        self.manual_btn = tk.Button(game_controls, text="🎯 РУЧНОЙ ВЫБОР",
                                    command=self.manual_selection, font=("Arial", 12),
                                    bg="#e67e22", fg="white", width=20, height=2,
                                    activebackground="#d35400", activeforeground="white")
        self.manual_btn.pack(side=tk.LEFT, padx=5)

        # Инструкции
        instructions_frame = tk.Frame(right_column, bg="#34495e")
        instructions_frame.pack(pady=10, padx=20)

        tk.Label(instructions_frame, text="✊ Камень = сжатый кулак\n✌️ Ножницы = 2 пальца\n✋ Бумага = открытая ладонь",
                 font=("Arial", 10), bg="#34495e", fg="#bdc3c7", justify=tk.LEFT).pack()

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Ошибка", "Не удалось подключить камеру!")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.is_capturing = True
        self.start_btn.config(state=tk.DISABLED)
        self.capture_btn.config(state=tk.NORMAL)
        self.new_game_btn.config(state=tk.NORMAL)

        # Обновляем статус
        self.status_indicator.config(fg="#2ecc71")
        self.status_text.config(text="Камера активна - покажите жест")

        # Запускаем поток для отображения видео
        threading.Thread(target=self.show_video, daemon=True).start()

    def show_video(self):
        while self.is_capturing and self.cap:
            ret, frame = self.cap.read()
            if ret:
                # Зеркально отражаем кадр для удобства
                frame = cv2.flip(frame, 1)

                # Анализируем кадр с помощью MediaPipe
                processed_frame, gesture, confidence, finger_count = self.analyze_frame_with_mediapipe(frame)

                # Сохраняем историю жестов (скользящее окно из 5 последних жестов)
                if gesture != "Не обнаружено":
                    self.gesture_history.append(gesture)
                    if len(self.gesture_history) > 5:
                        self.gesture_history.pop(0)

                    # Определяем наиболее частый жест в истории для стабильности
                    if len(self.gesture_history) >= 3:
                        from collections import Counter
                        most_common = Counter(self.gesture_history).most_common(1)[0][0]
                        gesture = most_common

                # Обновляем информацию
                self.last_gesture = gesture
                self.confidence = confidence
                self.finger_count = finger_count
                self.hand_detected = gesture != "Не обнаружено"

                # Обновляем отображение
                if self.hand_detected:
                    self.recognition_label.config(text=gesture)
                    self.status_indicator.config(fg="#2ecc71")
                    self.status_text.config(text=f"Рука обнаружена ({confidence}%)")
                else:
                    self.recognition_label.config(text="—")
                    self.status_indicator.config(fg="#e74c3c")
                    self.status_text.config(text="Покажите руку в кадре")

                # Конвертируем для отображения в Tkinter
                rgb_img = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_img)
                img = img.resize((500, 380))
                imgtk = ImageTk.PhotoImage(image=img)

                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)

            time.sleep(0.03)  # ~30 FPS

    def analyze_frame_with_mediapipe(self, frame):
        """Анализ кадра с использованием MediaPipe Hands"""
        # Конвертируем BGR в RGB
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False

        # Обрабатываем кадр
        results = self.hands.process(image_rgb)

        # Включаем запись обратно
        image_rgb.flags.writeable = True
        processed_frame = frame.copy()

        gesture = "Не обнаружено"
        confidence = 0
        finger_count = 0

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Рисуем landmarks на кадре
                self.mp_drawing.draw_landmarks(
                    processed_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )

                # Получаем координаты ключевых точек
                landmarks = hand_landmarks.landmark

                # Определяем жест
                gesture, confidence, finger_count = self.recognize_gesture(landmarks, processed_frame.shape)

                # Отображаем жест на кадре
                if gesture != "Не обнаружено":
                    cv2.putText(processed_frame, f"{gesture} ({confidence}%)",
                                (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Добавляем подсказки
                cv2.putText(processed_frame, "Покажите: Камень ✊, Ножницы ✌️ или Бумага ✋",
                            (10, processed_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                break  # Обрабатываем только первую руку

        return processed_frame, gesture, confidence, finger_count

    def recognize_gesture(self, landmarks, frame_shape):
        """Определение жеста по ключевым точкам"""
        # Индексы ключевых точек для пальцев
        thumb_tip = landmarks[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = landmarks[self.mp_hands.HandLandmark.THUMB_IP]
        thumb_mcp = landmarks[self.mp_hands.HandLandmark.THUMB_MCP]

        index_tip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        index_pip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
        index_mcp = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]

        middle_tip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        middle_pip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        middle_mcp = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]

        ring_tip = landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        ring_pip = landmarks[self.mp_hands.HandLandmark.RING_FINGER_PIP]
        ring_mcp = landmarks[self.mp_hands.HandLandmark.RING_FINGER_MCP]

        pinky_tip = landmarks[self.mp_hands.HandLandmark.PINKY_TIP]
        pinky_pip = landmarks[self.mp_hands.HandLandmark.PINKY_PIP]
        pinky_mcp = landmarks[self.mp_hands.HandLandmark.PINKY_MCP]

        wrist = landmarks[self.mp_hands.HandLandmark.WRIST]

        # Подсчитываем поднятые пальцы
        fingers_up = 0

        # Проверяем большой палец (специальная логика)
        thumb_angle = self.calculate_angle(thumb_tip, thumb_ip, thumb_mcp)
        if thumb_tip.y < thumb_ip.y and abs(thumb_tip.x - thumb_ip.x) > 0.05:
            fingers_up += 1

        # Проверяем указательный палец
        if index_tip.y < index_pip.y:
            fingers_up += 1

        # Проверяем средний палец
        if middle_tip.y < middle_pip.y:
            fingers_up += 1

        # Проверяем безымянный палец
        if ring_tip.y < ring_pip.y:
            fingers_up += 1

        # Проверяем мизинец
        if pinky_tip.y < pinky_pip.y:
            fingers_up += 1

        # Определяем жест по количеству поднятых пальцев
        if fingers_up == 0:
            gesture = "Камень"
            confidence = 95
        elif fingers_up == 2:
            # Проверяем, какие именно пальцы подняты
            index_up = index_tip.y < index_pip.y
            middle_up = middle_tip.y < middle_pip.y
            ring_up = ring_tip.y < ring_pip.y
            pinky_up = pinky_tip.y < pinky_pip.y

            if index_up and middle_up and not ring_up and not pinky_up:
                gesture = "Ножницы"
                confidence = 90
            else:
                gesture = "Неизвестно"
                confidence = 50
        elif fingers_up >= 4:
            gesture = "Бумага"
            confidence = 85
        else:
            gesture = "Неизвестно"
            confidence = 60

        return gesture, confidence, fingers_up

    def calculate_angle(self, a, b, c):
        """Вычисляет угол между тремя точками"""
        import math

        # Преобразуем в numpy массивы для удобства
        a_np = np.array([a.x, a.y])
        b_np = np.array([b.x, b.y])
        c_np = np.array([c.x, c.y])

        # Вычисляем векторы
        ba = a_np - b_np
        bc = c_np - b_np

        # Вычисляем косинус угла
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(cosine_angle)

        return np.degrees(angle)

    def capture_hand(self):
        if not self.cap or not self.is_capturing:
            messagebox.showwarning("Внимание", "Камера не готова!")
            return

        if not self.hand_detected:
            messagebox.showwarning("Внимание", "Рука не обнаружена! Поднесите руку к камере.")
            return

        # Определяем выбор игрока
        if "Камень" in self.last_gesture:
            self.player_choice = "камень"
        elif "Ножницы" in self.last_gesture:
            self.player_choice = "ножницы"
        elif "Бумага" in self.last_gesture:
            self.player_choice = "бумага"
        else:
            response = messagebox.askyesno(
                "Нечеткий жест",
                f"Распознано: {self.last_gesture}\nУверенность: {self.confidence}%\n\n"
                "Не удалось четко определить жест. Использовать 'Неизвестно' как 'Камень'?",
                detail="Нажмите 'Нет' для повторной попытки"
            )
            if response:
                self.player_choice = "камень"  # По умолчанию камень
            else:
                return

        # Ход компьютера
        self.computer_choice = random.choice(["камень", "ножницы", "бумага"])

        # Обновляем отображение выборов
        emoji_dict = {
            "камень": "✊ Камень",
            "ножницы": "✌️ Ножницы",
            "бумага": "✋ Бумага"
        }

        self.player_choice_display.config(text=emoji_dict.get(self.player_choice, "❓ Неизвестно"))
        self.computer_choice_display.config(text=emoji_dict.get(self.computer_choice))

        # Определяем победителя
        self.determine_winner()

        # Обновляем результат
        self.result_label.config(text=self.result_text)

        # Обновляем счет
        self.player_score_label.config(text=str(self.player_score))
        self.computer_score_label.config(text=str(self.computer_score))

        self.round_count += 1
        self.round_label.config(text=f"Раунд: {self.round_count}/{self.max_rounds}")

        # Проверяем конец игры
        if self.round_count > self.max_rounds:
            self.end_game()

    def manual_selection(self):
        """Ручной выбор жеста"""
        manual_window = tk.Toplevel(self.root)
        manual_window.title("Ручной выбор жеста")
        manual_window.geometry("400x400")
        manual_window.configure(bg="#34495e")

        tk.Label(manual_window, text="ВЫБЕРИТЕ ЖЕСТ ВРУЧНУЮ",
                 font=("Arial", 16, "bold"), bg="#34495e", fg="white").pack(pady=20)

        tk.Label(manual_window,
                 text="Используйте, если автоматическое распознавание не работает",
                 font=("Arial", 10), bg="#34495e", fg="#cccccc").pack(pady=10)

        def select_gesture(gesture):
            self.player_choice = gesture
            manual_window.destroy()

            # Ход компьютера
            self.computer_choice = random.choice(["камень", "ножницы", "бумага"])

            # Обновляем отображение
            emoji_dict = {
                "камень": "✊ Камень",
                "ножницы": "✌️ Ножницы",
                "бумага": "✋ Бумага"
            }

            self.player_choice_display.config(text=emoji_dict.get(self.player_choice))
            self.computer_choice_display.config(text=emoji_dict.get(self.computer_choice))

            # Определяем победителя
            self.determine_winner()

            # Обновляем результат
            self.result_label.config(text=self.result_text)

            # Обновляем счет
            self.player_score_label.config(text=str(self.player_score))
            self.computer_score_label.config(text=str(self.computer_score))

            self.round_count += 1
            self.round_label.config(text=f"Раунд: {self.round_count}/{self.max_rounds}")

            if self.round_count > self.max_rounds:
                self.end_game()

        # Кнопки жестов
        gestures_frame = tk.Frame(manual_window, bg="#34495e")
        gestures_frame.pack(pady=20)

        tk.Button(gestures_frame, text="✊ Камень",
                  command=lambda: select_gesture("камень"),
                  font=("Arial", 14), bg="#e74c3c", fg="white", width=15, height=2).pack(pady=10)

        tk.Button(gestures_frame, text="✌️ Ножницы",
                  command=lambda: select_gesture("ножницы"),
                  font=("Arial", 14), bg="#3498db", fg="white", width=15, height=2).pack(pady=10)

        tk.Button(gestures_frame, text="✋ Бумага",
                  command=lambda: select_gesture("бумага"),
                  font=("Arial", 14), bg="#2ecc71", fg="white", width=15, height=2).pack(pady=10)

        # Кнопка отмены
        tk.Button(manual_window, text="Отмена",
                  command=manual_window.destroy,
                  font=("Arial", 12), bg="#7f8c8d", fg="white", width=15).pack(pady=10)

    def determine_winner(self):
        if self.player_choice == self.computer_choice:
            self.result_text = "НИЧЬЯ! 🤝"
        elif (self.player_choice == "камень" and self.computer_choice == "ножницы") or \
                (self.player_choice == "ножницы" and self.computer_choice == "бумага") or \
                (self.player_choice == "бумага" and self.computer_choice == "камень"):
            self.result_text = "ВЫ ВЫИГРАЛИ! 🎉"
            self.player_score += 1
        else:
            self.result_text = "КОМПЬЮТЕР ВЫИГРАЛ! 💻"
            self.computer_score += 1

    def end_game(self):
        self.is_capturing = False
        self.capture_btn.config(state=tk.DISABLED)

        if self.player_score > self.computer_score:
            final_message = f"🏆 ПОБЕДА! Счет: {self.player_score}:{self.computer_score}"
        elif self.player_score < self.computer_score:
            final_message = f"💔 ПОРАЖЕНИЕ! Счет: {self.player_score}:{self.computer_score}"
        else:
            final_message = f"🤝 НИЧЬЯ! Счет: {self.player_score}:{self.computer_score}"

        messagebox.showinfo("Игра окончена!", final_message)

    def new_game(self):
        self.player_score = 0
        self.computer_score = 0
        self.round_count = 1
        self.player_choice = None
        self.computer_choice = None
        self.result_text = "Давайте начнем!"
        self.gesture_history = []

        self.player_score_label.config(text="0")
        self.computer_score_label.config(text="0")
        self.player_choice_display.config(text="—")
        self.computer_choice_display.config(text="—")
        self.result_label.config(text=self.result_text)
        self.round_label.config(text=f"Раунд: {self.round_count}/{self.max_rounds}")
        self.recognition_label.config(text="—")
        self.status_indicator.config(fg="#e74c3c")
        self.status_text.config(text="Камера выключена")

        if not self.is_capturing:
            self.start_camera()
        else:
            self.capture_btn.config(state=tk.NORMAL)

    def on_closing(self):
        self.is_capturing = False
        if self.cap:
            self.cap.release()
        self.hands.close()  # Закрываем MediaPipe
        self.root.destroy()


# Запуск программы
if __name__ == "__main__":
    print("=" * 60)
    print("КАМЕНЬ-НОЖНИЦЫ-БУМАГА с AI-распознаванием жестов")
    print("Использует MediaPipe для точного распознавания рук")
    print("=" * 60)
    print("Установка зависимостей:")
    print("pip install opencv-python pillow mediapipe")
    print("=" * 60)
    print("Советы:")
    print("1. Показывайте руку четко на фоне камеры")
    print("2. Держите руку на расстоянии 30-50 см от камеры")
    print("3. Используйте хорошее освещение")
    print("=" * 60)

    root = tk.Tk()
    game = RockPaperScissors(root)
    root.protocol("WM_DELETE_WINDOW", game.on_closing)
    root.mainloop()
