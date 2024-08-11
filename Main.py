import tkinter as tk
import keyboard
import pyautogui
import time
from pynput import mouse
import tkinter.messagebox as messagebox
import tkinter.simpledialog as simpledialog
import os
import json
import threading

# Список для хранения действий
actions = []

# Путь для сохранения файлов
save_dir = "saves"
os.makedirs(save_dir, exist_ok=True)

# Переменные для хранения состояния воспроизведения
playback_thread = None
is_playing = False
current_save_name = ""

# Переменная для хранения времени начала записи
start_time = None
listener = None

# Переменная для хранения выбранного сохранения
selected_save = None

def start_recording():
    global start_time, listener
    actions.clear()  # Очищаем список действий перед началом записи
    start_time = time.time()  # Фиксируем время начала записи
    print("Запись началась...")
    
    listener = mouse.Listener(on_click=record_mouse_click)
    listener.start()  # Запускаем отслеживание кликов мыши
    
    # Запуск записи клавиш
    keyboard.on_press(record_key_event)

def stop_recording():
    global listener
    listener.stop()  # Останавливаем отслеживание кликов мыши
    keyboard.unhook_all()  # Останавливаем запись клавиш
    print("Запись завершена.")
    
    # Переключаем выполнение save_recording() на основной поток Tkinter
    window.after(100, save_recording)

def save_recording():
    try:
        while True:
            save_name = simpledialog.askstring("Дайте имя сохранению", "Введите имя сохранения:")
            if save_name:
                save_path = os.path.join(save_dir, f"{save_name}.json")
                if os.path.exists(save_path):
                    messagebox.showerror("Ошибка", "Сохранение с таким именем уже существует. Выберите другое имя.")
                else:
                    with open(save_path, 'w') as file:
                        json.dump(actions, file)
                    print(f"Запись сохранена как {save_name}")
                    break
            else:
                messagebox.showinfo("Отмена", "Сохранение отменено.")
                break
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка при сохранении записи: {e}")

def play_recording():
    global is_playing, playback_thread, current_save_name, selected_save
    save_files = os.listdir(save_dir)
    
    if not save_files:
        messagebox.showinfo("Нет сохранений", "Нет доступных сохранений.")
        return
    
    def on_save_select(event):
        global selected_save
        selected_save = event.widget.get(event.widget.curselection())
        for button in buttons:
            if button == play_button:
                button.config(bg="lightgreen")
            elif button == delete_button:
                button.config(bg="red")
            else:
                button.config(bg="lightgray")
        print(f"Выбрано сохранение: {selected_save}")

    def start_playback():
        global is_playing, playback_thread, current_save_name
        if not selected_save:
            messagebox.showerror("Ошибка", "Сохранение не выбрано.")
            return

        is_playing = True
        current_save_name = selected_save
        playback_thread = threading.Thread(target=play_actions, args=(selected_save,))
        playback_thread.start()

    def stop_playback():
        global is_playing
        is_playing = False
        print("Воспроизведение остановлено.")
        playback_window.destroy()  # Закрываем окно воспроизведения
        window.deiconify()  # Возвращаем главное окно в фокус

    def delete_save():
        global selected_save
        if not selected_save:
            messagebox.showerror("Ошибка", "Сохранение не выбрано.")
            return
        
        save_path = os.path.join(save_dir, f"{selected_save}.json")
        if os.path.exists(save_path):
            os.remove(save_path)
            print(f"Сохранение {selected_save} удалено.")
            save_listbox.delete(save_listbox.curselection())
            # Обновляем список сохранений
            update_save_listbox()
            # Сбрасываем переменную выбранного сохранения
            selected_save = None
            for button in buttons:
                button.config(bg="lightgray")
        else:
            messagebox.showerror("Ошибка", "Сохранение с таким именем не найдено.")
    
    def update_save_listbox():
        save_listbox.delete(0, tk.END)
        save_files = os.listdir(save_dir)
        for save_file in save_files:
            save_listbox.insert(tk.END, save_file[:-5])  # Убираем ".json" из имени файла
    
    def go_back():
        playback_window.destroy()
        window.deiconify()  # Возвращаем главное окно в фокус
    
    window.withdraw()  # Скрываем главное окно
    playback_window = tk.Toplevel()
    playback_window.title("Выбор сохранения")
    playback_window.geometry("300x300")
    
    # Создаем кнопку "Назад"
    back_button = tk.Button(playback_window, text="Назад", command=go_back)
    back_button.pack(pady=10, padx=10, anchor="nw")
    
    save_listbox = tk.Listbox(playback_window, selectmode=tk.SINGLE)
    save_listbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
    save_listbox.bind("<ButtonRelease-1>", on_save_select)
    
    update_save_listbox()
    
    buttons_frame = tk.Frame(playback_window)
    buttons_frame.pack(pady=10)

    play_button = tk.Button(buttons_frame, text="Воспроизвести сохранение / CTRL+E", command=start_playback, bg="lightgray", fg="black")
    stop_button = tk.Button(buttons_frame, text="Остановить воспроизведение / CTRL+R", command=stop_playback, bg="lightgray", fg="black")
    delete_button = tk.Button(buttons_frame, text="Удалить сохранение", command=delete_save, bg="lightgray", fg="black")

    play_button.pack(side=tk.LEFT, padx=5)
    stop_button.pack(side=tk.LEFT, padx=5)
    delete_button.pack(side=tk.LEFT, padx=5)
    
    buttons = [play_button, stop_button, delete_button]

    keyboard.add_hotkey('ctrl+e', start_playback, suppress=True)  # Воспроизвести сохранение только в этом окне
    keyboard.add_hotkey('ctrl+r', stop_playback, suppress=True)

def play_actions(save_name):
    global is_playing
    save_path = os.path.join(save_dir, f"{save_name}.json")
    
    if not os.path.exists(save_path):
        messagebox.showerror("Ошибка", "Сохранение с таким именем не найдено.")
        return
    
    # Загрузка сохранения и его воспроизведение
    with open(save_path, 'r') as file:
        loaded_actions = json.load(file)
    
    if not loaded_actions:
        messagebox.showinfo("Нет действий", "Сохранение не содержит действий.")
        return

    # Воспроизведение загруженных действий
    start_time = time.time()
    for action in loaded_actions:
        if not is_playing:
            break
        action_type, action_time, *action_details = action
        # Рассчитываем задержку до следующего действия
        delay = action_time - (time.time() - start_time)
        if delay > 0:
            time.sleep(delay)
        
        if action_type == 'click':
            x, y, button_str = action_details
            button = button_str if button_str in ['left', 'middle', 'right'] else 'left'
            pyautogui.click(x=x, y=y, button=button)
        elif action_type == 'keypress':
            key = action_details[0]
            pyautogui.press(key)  # Используем pyautogui для симуляции нажатия клавиши
    
    print(f"Воспроизведение {save_name} завершено.")

def record_mouse_click(x, y, button, pressed):
    if pressed:
        current_time = time.time() - start_time
        actions.append(('click', current_time, x, y, button.name))
        print(f"Клик мыши записан: ({x}, {y}), кнопка: {button.name}")

def record_key_event(event):
    # Проверяем, если нажатие клавиши сочетание с CTRL
    if keyboard.is_pressed('ctrl') and event.name in ['q', 'w', 'e', 'r', 'y']:
        return
    current_time = time.time() - start_time
    actions.append(('keypress', current_time, event.name))
    print(f"Клавиша {event.name} нажата.")

def open_selection_window():
    window.withdraw()  # Скрываем главное окно
    play_recording()  # Открываем окно выбора сохранения

def on_closing():
    global is_playing
    if is_playing:
        is_playing = False
        if playback_thread and playback_thread.is_alive():
            playback_thread.join()  # Дождаться завершения потока воспроизведения
    window.destroy()

# Создаем главное окно
window = tk.Tk()
window.title("Автокликер")
window.geometry("300x250")

# Создаем кнопки с цветами
btn_start = tk.Button(window, text="Записать / CTRL+Q", command=start_recording, bg="green", fg="white")
btn_stop = tk.Button(window, text="Завершить запись / CTRL+W", command=stop_recording, bg="red", fg="white")
btn_play = tk.Button(window, text="Воспроизвести / CTRL+E", command=open_selection_window, bg="blue", fg="white")

# Размещаем кнопки в окне
btn_start.pack(pady=10)
btn_stop.pack(pady=10)
btn_play.pack(pady=10)

# Привязка горячих клавиш
keyboard.add_hotkey('ctrl+q', start_recording)
keyboard.add_hotkey('ctrl+w', stop_recording)
keyboard.add_hotkey('ctrl+e', open_selection_window)

# Обработчик закрытия окна
window.protocol("WM_DELETE_WINDOW", on_closing)

# Запуск основного цикла обработки событий
window.mainloop()












