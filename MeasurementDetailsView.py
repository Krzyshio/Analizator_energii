import glob
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
import pandas as pd


class MeasurementDetailsView(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.measurements_data = None
        self.geometry('800x600')
        self.after(100, lambda: self.attributes('-fullscreen', True))

        self.title("Measurement Details")

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill=ctk.BOTH, expand=True)

        self.left_frame = ctk.CTkFrame(self.main_frame, width=200)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)

        self.list_title = ctk.CTkLabel(self.left_frame, text="Select a Measurement", anchor="center",
                                       font=("Arial", 12))
        self.list_title.pack(pady=(0, 10))

        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.measurements_list = tk.Listbox(self.left_frame, bg="#2b2b2b", fg="white", highlightthickness=0,
                                            selectbackground="#333333", selectforeground="white", borderwidth=0,
                                            highlightcolor="#2b2b2b", height=50)
        self.measurements_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        plt.style.use('dark_background')
        self.figure = plt.Figure(figsize=(5, 4), dpi=100, facecolor="#2b2b2b")
        self.plot = self.figure.add_subplot(1, 1, 1)
        self.plot.set_facecolor("#2b2b2b")
        self.plot.set_title("Your Plot Title Here", color="white")

        self.canvas = FigureCanvasTkAgg(self.figure, self.right_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.load_measurements_from_csv()

    def load_measurements_from_csv(self):
        csv_files = glob.glob("*.csv")
        self.measurements_data = {}
        for file_name in csv_files:
            try:
                column_names = ['timestamp'] + [f'channel_{i + 1}' for i in range(8)] + ['unit']
                data = pd.read_csv(file_name, sep=';', names=column_names, parse_dates=['timestamp'])

                self.measurements_data[file_name] = data
                self.measurements_list.insert(tk.END, file_name)
            except Exception as e:
                print(f"Nie można wczytać pliku {file_name}: {e}")

    def on_measurement_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            file_name = event.widget.get(index)
            data = self.measurements_data.get(file_name)
            if data is not None:
                x = data['timestamp']
                y = data['channel_1']
                self.plot.clear()
                self.plot.plot(x, y, color="cyan")
                self.plot.set_facecolor("#2b2b2b")
                self.plot.set_title(f"Dane z {file_name}", color="white")
                self.canvas.draw()
