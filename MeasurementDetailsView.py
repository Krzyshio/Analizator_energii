import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class MeasurementDetailsView(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Measurement Details")
        self.geometry("800x600")

        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.measurements_list = tk.Listbox(self)
        self.paned_window.add(self.measurements_list, weight=1)

        self.plot_frame = ttk.Frame(self)
        self.paned_window.add(self.plot_frame, weight=3)

        self.measurements_list.insert(tk.END, "Measurement 1")
        self.measurements_list.insert(tk.END, "Measurement 2")
        self.measurements_list.bind("<<ListboxSelect>>", self.on_measurement_select)

        self.figure = plt.Figure(figsize=(5, 4), dpi=100)
        self.plot = self.figure.add_subplot(1, 1, 1)
        self.canvas = FigureCanvasTkAgg(self.figure, self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def on_measurement_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            measurement = event.widget.get(index)
            self.plot.clear()
            self.plot.plot([1, 2, 3], [4, 5, 6])
            self.canvas.draw()
