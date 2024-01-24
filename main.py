# -*- coding: utf-8 -*-

from daqhats import mcc118, hat_list, HatIDs, OptionFlags
import numpy as np
import time
import customtkinter as ctk


# Define the GUI application
class EnergyMonitorApp(ctk.CTk):
    def __init__(self, mcc118_board, *args, **kwargs):
        # Set CustomTkinter theme to dark
        ctk.set_appearance_mode("dark")  # Add this line to set the appearance to dark
        ctk.set_default_color_theme("blue")  # Optional: set a color theme

        super().__init__(*args, **kwargs)
        self.mcc118_board = mcc118_board
        self.num_samples = 100
        self.scan_rate = 1000.0
        self.mean_voltage = '0.0 V'
        self.running = False
        self.setup_gui()

    def setup_gui(self):
        self.title('Energy Monitor')

        # Create two frames: one for settings on the left, one for display and controls on the right
        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(side='left', fill='y', padx=20, pady=20)

        display_control_frame = ctk.CTkFrame(self)
        display_control_frame.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        # Settings title
        settings_title = ctk.CTkLabel(settings_frame, text='Settings', text_font=('default_theme', 30, 'bold'))
        settings_title.pack(pady=(0, 20))

        # Num samples slider and value label
        samples_label = ctk.CTkLabel(settings_frame, text='Number of Samples')
        samples_label.pack()
        self.samples_slider = ctk.CTkSlider(settings_frame, from_=1, to=1000, command=self.update_num_samples)
        self.samples_slider.pack()
        self.samples_value_label = ctk.CTkLabel(settings_frame, text=f'Value: {self.num_samples}')
        self.samples_value_label.pack()

        # Scan rate slider and value label
        rate_label = ctk.CTkLabel(settings_frame, text='Scan Rate (Hz)')
        rate_label.pack()
        self.rate_slider = ctk.CTkSlider(settings_frame, from_=10, to=5000, command=self.update_scan_rate)
        self.rate_slider.pack()
        self.rate_value_label = ctk.CTkLabel(settings_frame, text=f'Value: {self.scan_rate} Hz')
        self.rate_value_label.pack()

        # Voltage display
        self.voltage_label = ctk.CTkLabel(display_control_frame, text=self.mean_voltage)
        self.voltage_label.pack(pady=20)

        # Start button
        start_button = ctk.CTkButton(display_control_frame, text='Start Measurement', command=self.start_measurement)
        start_button.pack(pady=10)

        # Stop button
        stop_button = ctk.CTkButton(display_control_frame, text='Stop Measurement', command=self.stop_measurement)
        stop_button.pack(pady=10)

    def update_num_samples(self, value):
        self.num_samples = int(value)
        self.samples_value_label.configure(text=f'Value: {self.num_samples}')

    def update_scan_rate(self, value):
        self.scan_rate = round(float(value), 2)  # Round to 2 decimal places
        self.rate_value_label.configure(text=f'Value: {self.scan_rate} Hz')

    def start_measurement(self):
        self.running = True
        channel_mask = (1 << 0)  # Assuming you're using channel 0
        options = OptionFlags.DEFAULT
        self.mcc118_board.a_in_scan_start(channel_mask, self.num_samples, self.scan_rate, options)
        self.read_data()

    def stop_measurement(self):
        self.running = False
        self.mcc118_board.a_in_scan_stop()
        self.mcc118_board.a_in_scan_cleanup()
        self.mean_voltage.set('0.0')

    def read_data(self):
        if self.running:
            read_result = self.mcc118_board.a_in_scan_read_numpy(self.num_samples.get(), timeout=5.0)
            data = read_result.data
            if data.size > 0:
                mean_voltage = np.mean(data)
                self.mean_voltage.set(f"{mean_voltage:.3f} V")
            self.after(100, self.read_data)


# Main script logic
if __name__ == '__main__':
    # List available MCC boards
    board_list = hat_list(HatIDs.MCC_118)
    if len(board_list) == 0:
        print("No MCC118 boards found.")
        exit()

    # Select the board to work with
    selected_board = board_list[0]
    print(f"Selected MCC118 board at address {selected_board.address}.")

    # Initialize the MCC118 board
    mcc118_board = mcc118(selected_board.address)

    # Configure the channels
    channels = [0]
    channel_mask = 0
    for channel in channels:
        channel_mask |= (1 << channel)

    options = OptionFlags.DEFAULT  # Using default options

    # Create and run the GUI
    app = EnergyMonitorApp(mcc118_board)
    app.mainloop()

    print("Application closed.")
