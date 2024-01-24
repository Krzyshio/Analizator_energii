# -*- coding: utf-8 -*-

from daqhats import mcc118, hat_list, HatIDs, OptionFlags
import numpy as np
import time
import customtkinter as ctk
from customtkinter import CTkComboBox


class EnergyMonitorApp(ctk.CTk):
    def __init__(self, mcc118_board, *args, **kwargs):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        super().__init__(*args, **kwargs)
        self.geometry("800x480")

        self.mcc118_board = mcc118_board
        self.num_samples = 100
        self.scan_rate = 1000.0
        self.mean_voltage = '0.0 V'
        self.running = False
        self.setup_gui()

    def setup_gui(self):
        self.title('Energy Monitor')

        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(side='left', fill='y', padx=20, pady=20)

        display_control_frame = ctk.CTkFrame(self)
        display_control_frame.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        settings_title = ctk.CTkLabel(settings_frame, text='Settings')
        settings_title.configure(font=('default_theme', 25, 'bold'))
        settings_title.pack(pady=(0, 20))

        channel_label = ctk.CTkLabel(settings_frame, text='Select Channel')
        channel_label.pack(pady=(10, 0))

        self.channel_options = ["Channel 0", "Channel 1", "Channel 2", "Channel 3"]
        self.channel_combobox = CTkComboBox(settings_frame, values=self.channel_options)
        self.channel_combobox.set("Channel 0")
        self.channel_combobox.pack(pady=(0, 20))

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

        self.voltage_label = ctk.CTkLabel(display_control_frame, text=self.mean_voltage)
        self.voltage_label.configure(font=('default_theme', 40, 'bold'))  # Increase font size for better visibility
        self.voltage_label.pack(pady=20, expand=True)  # Center this in the frame

        control_buttons_frame = ctk.CTkFrame(display_control_frame)
        control_buttons_frame.pack(side='bottom', fill='x', padx=20, pady=20)

        start_button = ctk.CTkButton(control_buttons_frame, text='Start Measurement', command=self.start_measurement)
        start_button.pack(side='left', padx=10, pady=10, expand=True)

        stop_button = ctk.CTkButton(control_buttons_frame, text='Stop Measurement', command=self.stop_measurement)
        stop_button.pack(side='right', padx=10, pady=10, expand=True)

    def update_num_samples(self, value):
        self.num_samples = int(value)
        self.samples_value_label.configure(text=f'Value: {self.num_samples}')

    def update_scan_rate(self, value):
        self.scan_rate = round(float(value), 2)
        self.rate_value_label.configure(text=f'Value: {self.scan_rate} Hz')

    def start_measurement(self):
        selected_channel_text = self.channel_combobox.get()
        selected_channel_index = self.channel_options.index(selected_channel_text)

        self.running = True
        channel_mask = (1 << selected_channel_index)
        options = OptionFlags.DEFAULT
        self.mcc118_board.a_in_scan_start(channel_mask, self.num_samples, self.scan_rate, options)
        self.read_data()

    def stop_measurement(self):
        self.running = False
        self.mcc118_board.a_in_scan_stop()
        self.mcc118_board.a_in_scan_cleanup()
        self.mean_voltage = 0.0

    def read_data(self):
        if self.running:
            read_result = self.mcc118_board.a_in_scan_read_numpy(self.num_samples, timeout=5.0)
            data = read_result.data
            if data.size > 0:
                mean_voltage = np.mean(data)
                self.mean_voltage = mean_voltage
            self.after(100, self.read_data)


if __name__ == '__main__':
    board_list = hat_list(HatIDs.MCC_118)
    if len(board_list) == 0:
        print("No MCC118 boards found.")
        exit()

    selected_board = board_list[0]
    print(f"Selected MCC118 board at address {selected_board.address}.")

    mcc118_board = mcc118(selected_board.address)

    channels = [0]
    channel_mask = 0
    for channel in channels:
        channel_mask |= (1 << channel)

    options = OptionFlags.DEFAULT

    app = EnergyMonitorApp(mcc118_board)
    app.mainloop()

    print("Application closed.")

