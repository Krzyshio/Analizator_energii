import tkinter as tk
import customtkinter as ctk
from daqhats import mcc118, hat_list, HatIDs, OptionFlags
import numpy as np

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
        self.channel_mask = None
        self.setup_gui()

    def setup_gui(self):
        self.title('Energy Monitor')

        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(side='left', fill='y', padx=20, pady=20)

        display_control_frame = ctk.CTkFrame(self)
        display_control_frame.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        mode_buttons_frame = ctk.CTkFrame(display_control_frame)
        mode_buttons_frame.pack(side='top', fill='x', padx=20, pady=10)

        voltage_button = ctk.CTkButton(mode_buttons_frame, text='Measure Voltage', command=self.select_voltage_mode)
        voltage_button.pack(side='left', padx=10, pady=10, expand=True)

        current_button = ctk.CTkButton(mode_buttons_frame, text='Measure Current', command=self.select_current_mode)
        current_button.pack(side='left', padx=10, pady=10, expand=True)

        power_button = ctk.CTkButton(mode_buttons_frame, text='Measure Power', command=self.select_power_mode)
        power_button.pack(side='left', padx=10, pady=10, expand=True)

        self.selected_channels_label = ctk.CTkLabel(display_control_frame, text='Selected Channels: None')
        self.selected_channels_label.pack(side='top', padx=20, pady=10)

        # Settings
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

        self.voltage_label = ctk.CTkLabel(display_control_frame, text=self.mean_voltage)
        self.voltage_label.configure(font=('default_theme', 40, 'bold'))
        self.voltage_label.pack(pady=20, expand=True)

        control_buttons_frame = ctk.CTkFrame(display_control_frame)
        control_buttons_frame.pack(side='bottom', fill='x', padx=20, pady=20)

        start_button = ctk.CTkButton(control_buttons_frame, text='Start Measurement', command=self.start_measurement)
        start_button.pack(side='left', padx=10, pady=10, expand=True)

        stop_button = ctk.CTkButton(control_buttons_frame, text='Stop Measurement', command=self.stop_measurement)
        stop_button.pack(side='right', padx=10, pady=10, expand=True)

    def select_voltage_mode(self):
        self.channel_mask = 0b00001111
        self.selected_channels_label.configure(text='Selected Channels: 0 to 3')

    def select_current_mode(self):
        self.channel_mask = 0b11110000
        self.selected_channels_label.configure(text='Selected Channels: 4 to 7')

    def select_power_mode(self):
        self.channel_mask = 0b11111111
        self.selected_channels_label.configure(text='Selected Channels: 0 to 7')

    def update_num_samples(self, value):
        self.num_samples = int(value)
        self.samples_value_label.configure(text=f'Value: {self.num_samples}')

    def update_scan_rate(self, value):
        self.scan_rate = round(float(value), 2)
        self.rate_value_label.configure(text=f'Value: {self.scan_rate} Hz')

    def start_measurement(self):
        if self.channel_mask is None:
            print("No measurement mode selected.")
            return

        self.running = True
        options = OptionFlags.DEFAULT
        self.mcc118_board.a_in_scan_start(self.channel_mask, self.num_samples, self.scan_rate, options)
        self.read_data()

    def stop_measurement(self):
        self.running = False
        self.mcc118_board.a_in_scan_stop()
        self.mcc118_board.a_in_scan_cleanup()
        self.mean_voltage = '0.0 V'
        self.voltage_label.configure(text=self.mean_voltage)

    def read_data(self):
        if self.running:
            read_result = self.mcc118_board.a_in_scan_read_numpy(self.num_samples, timeout=5.0)
            data = read_result.data
            if data.size > 0:
                mean_voltage = np.mean(data)
                self.mean_voltage = f'{mean_voltage:.2f} V'
                self.voltage_label.configure(text=self.mean_voltage)
            self.after(100, self.read_data)

if __name__ == '__main__':
    board_list = hat_list(HatIDs.MCC_118)
    if len(board_list) == 0:
        print("No MCC118 boards found.")
        exit()

    selected_board = board_list[0]
    mcc118_board = mcc118(selected_board.address)

    app = EnergyMonitorApp(mcc118_board)
    app.mainloop()
