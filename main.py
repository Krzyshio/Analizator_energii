import tkinter as tk
import customtkinter as ctk
from daqhats import mcc118, hat_list, HatIDs, OptionFlags
import numpy as np


class EnergyMonitorApp(ctk.CTk):
    def __init__(self, mcc118_board, *args, **kwargs):
        self.channel_data_frame = None
        self.rate_value_label = None
        self.rate_slider = None
        self.samples_slider = None
        self.samples_value_label = None
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__(*args, **kwargs)
        self.geometry("800x480")

        self.mcc118_board = mcc118_board
        self.num_samples = 100
        self.scan_rate = 1000.0
        self.running = False
        self.channel_mask = None
        self.channel_data_labels = {}

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

        display_control_frame = ctk.CTkFrame(self)
        display_control_frame.pack(side='top', fill='both', expand=True, padx=20, pady=20)

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

        self.channel_data_frame = ctk.CTkFrame(display_control_frame)
        self.channel_data_frame.pack(side='top', fill='both', expand=True, padx=20, pady=20)

        column_names = [''] + ['CH' + str(i) for i in range(8)]
        for idx, text in enumerate(column_names):
            header_label = ctk.CTkLabel(self.channel_data_frame, text=text)
            header_label.grid(row=0, column=idx, padx=5, pady=5)

        for idx, text in enumerate(['Urms', 'Upk', 'CF']):
            label = ctk.CTkLabel(self.channel_data_frame, text=text)
            label.grid(row=idx + 1, column=0)

        for channel in range(8):
            if self.channel_mask in [0b00001111, 0b11110000] and channel not in range(4):
                continue
            for idx, text in enumerate(['Urms', 'Upk', 'CF']):
                value_label = ctk.CTkLabel(self.channel_data_frame, text='0.0', anchor='center')
                value_label.grid(row=idx + 1, column=channel + 1, padx=5, sticky='w')
                self.channel_data_labels[channel][text] = value_label

        control_buttons_frame = ctk.CTkFrame(display_control_frame)
        control_buttons_frame.pack(side='bottom', fill='x', padx=20, pady=20)

        start_button = ctk.CTkButton(control_buttons_frame, text='Start Measurement', command=self.start_measurement)
        start_button.pack(side='left', padx=10, pady=10, expand=True)
        stop_button = ctk.CTkButton(control_buttons_frame, text='Stop Measurement', command=self.stop_measurement)
        stop_button.pack(side='right', padx=10, pady=10, expand=True)

    def select_voltage_mode(self):
        self.channel_mask = 0b00001111
        self.selected_channels_label.configure(text='Selected Channels: 0 to 3')
        self.update_channel_display()

    def select_current_mode(self):
        self.channel_mask = 0b11110000
        self.selected_channels_label.configure(text='Selected Channels: 4 to 7')
        self.update_channel_display()

    def select_power_mode(self):
        self.channel_mask = 0b11111111
        self.selected_channels_label.configure(text='Selected Channels: 0 to 7')
        self.update_channel_display()

    def update_channel_display(self):
        for channel in range(8):
            is_visible = (self.channel_mask >> channel) & 1

            if self.channel_mask == 0b00001111:
                if channel not in range(4):
                    is_visible = False
            elif self.channel_mask == 0b11110000:
                if channel not in range(4, 8):
                    is_visible = False

            for label in self.channel_data_labels[channel].values():
                if is_visible:
                    label.grid()
                else:
                    label.grid_remove()

        self.update()

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

        if not self.running:
            self.running = True
            options = OptionFlags.DEFAULT
            self.mcc118_board.a_in_scan_start(self.channel_mask, self.num_samples, self.scan_rate, options)
            self.read_data()
        else:
            print("Measurement is already running.")

    def stop_measurement(self):
        if self.running:
            self.running = False
            self.mcc118_board.a_in_scan_stop()
            self.mcc118_board.a_in_scan_cleanup()
        else:
            print("Measurement is not running, so it cannot be stopped.")

    def read_data(self):
        if self.running:
            read_result = self.mcc118_board.a_in_scan_read_numpy(self.num_samples, timeout=5.0)
            data = read_result.data

            if data.size > 0:
                num_channels = 8
                samples_per_channel = len(data) // num_channels

                for channel in range(num_channels):
                    if self.channel_mask in [0b00001111, 0b11110000] and channel not in range(4):
                        continue

                    start_idx = channel * samples_per_channel
                    end_idx = (channel + 1) * samples_per_channel
                    channel_data = data[start_idx:end_idx]

                    if channel_data.size > 0:
                        urms = np.sqrt(np.mean(np.square(channel_data)))
                        upk = np.max(np.abs(channel_data))
                        cf = upk / urms if urms != 0 else float('nan')

                        self.channel_data_labels[channel]['Urms'].configure(text=f'{urms:.2f} V')
                        self.channel_data_labels[channel]['Upk'].configure(text=f'{upk:.2f} V')
                        self.channel_data_labels[channel]['CF'].configure(text=f'{cf:.2f}')

        else:
            for channel in range(8):
                for text in ['Urms', 'Upk', 'CF']:
                    self.channel_data_labels[channel][text].configure(text='0.0')

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
