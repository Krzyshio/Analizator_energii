import time
import tkinter as tk
import customtkinter as ctk

from constants import VOLTAGE_MODE, CURRENT_MODE, POWER_MODE


class EnergyMonitorAppGUI(ctk.CTk):
    def __init__(self, start_measurement, stop_measurement, select_voltage_mode, select_current_mode, select_power_mode,
                 running, *args, **kwargs):
        super().__init__()
        self.current_multiplier_value_label = None
        self.current_multiplier = 1.0
        self.channel_data_frame = None
        self.rate_value_label = None
        self.rate_slider = None
        self.samples_slider = None
        self.current_multiplier_slider = None
        self.samples_value_label = None
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.geometry("800x480")

        self.num_samples = 100
        self.scan_rate = 1000.0
        self.running = running
        self.channel_mask = None
        self.channel_data_labels = {}

        self.start_measurement = start_measurement
        self.stop_measurement = stop_measurement
        self.select_voltage_mode = select_voltage_mode
        self.select_current_mode = select_current_mode
        self.select_power_mode = select_power_mode
        self.measurement_status_label = None
        self.start_time = None
        self.measurement_unit_label = None

        for channel in range(8):
            self.channel_data_labels[channel] = {}

        self.setup_gui()

    def setup_gui(self):
        self.title('Energy Monitor')

        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(side='left', fill='y', padx=20, pady=20)

        settings_title = ctk.CTkLabel(settings_frame, text='Settings')
        settings_title.configure(font=('default_theme', 25, 'bold'))
        settings_title.pack(pady=(0, 20))

        samples_label = ctk.CTkLabel(settings_frame, text='Number of Samples')
        samples_label.pack()
        self.samples_slider = ctk.CTkSlider(settings_frame, from_=1, to=1000, command=self.update_num_samples)
        self.samples_slider.pack()
        self.samples_value_label = ctk.CTkLabel(settings_frame, text=f'Value: {self.num_samples}')
        self.samples_value_label.pack()

        rate_label = ctk.CTkLabel(settings_frame, text='Scan Rate (Hz)')
        rate_label.pack()
        self.rate_slider = ctk.CTkSlider(settings_frame, from_=10, to=5000, command=self.update_scan_rate)
        self.rate_slider.pack()
        self.rate_value_label = ctk.CTkLabel(settings_frame, text=f'Value: {self.scan_rate} Hz')
        self.rate_value_label.pack()

        multiplier_label = ctk.CTkLabel(settings_frame, text='Current Multiplier')
        multiplier_label.pack()
        self.current_multiplier_slider = ctk.CTkSlider(settings_frame, from_=0.1, to=10,
                                                       command=self.update_current_multiplier)
        self.current_multiplier_slider.set(self.current_multiplier)
        self.current_multiplier_slider.pack()
        self.current_multiplier_value_label = ctk.CTkLabel(settings_frame,
                                                           text=f'Multiplier: {self.current_multiplier}')
        self.current_multiplier_value_label.pack()

        display_control_frame = ctk.CTkFrame(self)
        display_control_frame.pack(side='top', fill='both', expand=True, padx=20, pady=20)

        mode_buttons_frame = ctk.CTkFrame(display_control_frame)
        mode_buttons_frame.pack(side='top', fill='x', padx=20, pady=10)

        voltage_button = ctk.CTkButton(mode_buttons_frame, text='Measure Voltage',
                                       command=lambda: self.select_voltage_mode())
        voltage_button.pack(side='left', padx=10, pady=10, expand=True)

        current_button = ctk.CTkButton(mode_buttons_frame, text='Measure Current',
                                       command=lambda: self.select_current_mode())
        current_button.pack(side='left', padx=10, pady=10, expand=True)

        power_button = ctk.CTkButton(mode_buttons_frame, text='Measure Power', command=lambda: self.select_power_mode())
        power_button.pack(side='left', padx=10, pady=10, expand=True)

        self.selected_channels_label = ctk.CTkLabel(display_control_frame, text='Selected Channels: None')
        self.selected_channels_label.pack(side='top', padx=20, pady=10)

        measurement_status_label = ctk.CTkLabel(display_control_frame, text='Measurement Status: Idle')
        measurement_status_label.pack()
        self.measurement_status_label = measurement_status_label

        self.channel_data_frame = ctk.CTkFrame(display_control_frame)
        self.channel_data_frame.pack(side='top', fill='both', expand=True, padx=20, pady=20)

        column_names = [''] + ['CH' + str(i) for i in range(8)]
        for idx, text in enumerate(column_names):
            header_label = ctk.CTkLabel(self.channel_data_frame, text=text)
            header_label.grid(row=0, column=idx, padx=5, pady=5)

        self.measurement_unit_label = ctk.CTkLabel(self.channel_data_frame, text='Voltage (V)')
        self.measurement_unit_label.grid(row=1, column=0)

        for channel in range(8):
            value_label = ctk.CTkLabel(self.channel_data_frame, text='0.0', anchor='center')
            value_label.grid(row=1, column=channel + 1, padx=5, sticky='w')
            self.channel_data_labels[channel]['Voltage'] = value_label

        control_buttons_frame = ctk.CTkFrame(display_control_frame)
        control_buttons_frame.pack(side='bottom', fill='x', padx=20, pady=20)

        start_button = ctk.CTkButton(control_buttons_frame, text='Start Measurement', command=self.start_measurement)
        start_button.pack(side='left', padx=10, pady=10, expand=True)
        stop_button = ctk.CTkButton(control_buttons_frame, text='Stop Measurement', command=self.stop_measurement)
        stop_button.pack(side='right', padx=10, pady=10, expand=True)

    def update_timer(self):
        if self.running:
            elapsed_time = time.time() - self.start_time
            self.measurement_status_label.configure(text=f'Measurement Active. Time: {elapsed_time:.2f} sec')
            self.after(1000, self.update_timer)

    def update_num_samples(self, value):
        self.num_samples = int(value)
        self.samples_value_label.configure(text=f'Value: {self.num_samples}')

    def update_scan_rate(self, value):
        self.scan_rate = round(float(value), 2)
        self.rate_value_label.configure(text=f'Value: {self.scan_rate} Hz')

    def update_current_multiplier(self, value):
        self.current_multiplier = float(value)
        self.current_multiplier_value_label.configure(text=f'Multiplier: {self.app.current_multiplier:.2f}')

    def update_labels_for_mode(self, mode):
        label_text = "Voltage (V)"
        if mode == VOLTAGE_MODE:
            label_text = "Voltage (V)"
        elif mode == CURRENT_MODE:
            label_text = "Current (A)"
        elif mode == POWER_MODE:
            label_text = "Power (W)"
        self.measurement_unit_label.configure(text=label_text)
