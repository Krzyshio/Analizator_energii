import csv
import os
import time
from datetime import datetime

from daqhats import mcc118, hat_list, HatIDs, OptionFlags
from gui import EnergyMonitorAppGUI
from constants import VOLTAGE_MODE, CURRENT_MODE, POWER_MODE


def is_channel_visible(channel, mode):
    if mode == VOLTAGE_MODE:
        return channel in range(3)
    elif mode == CURRENT_MODE:
        return channel in range(3, 6)
    elif mode == POWER_MODE:
        return channel in [0, 2, 4]
    else:
        return False


# Main Class
class EnergyMonitor:
    def __init__(self):
        self.mode = 0
        self.channel_mask = None
        self.num_samples = 5000
        self.scan_rate = 1000
        self.running = False
        self.board = self.initialize_board()
        self.app = self.create_app()
        self.current_file_name = None

    def initialize_board(self):
        board_list = hat_list(HatIDs.MCC_118)
        if len(board_list) == 0:
            print("No MCC118 boards found.")
            exit()

        selected_board = board_list[0]
        return mcc118(selected_board.address)

    def create_app(self):
        return EnergyMonitorAppGUI(self.start_measurement,
                                   self.stop_measurement,
                                   lambda: self.select_mode(VOLTAGE_MODE),
                                   lambda: self.select_mode(CURRENT_MODE),
                                   lambda: self.select_mode(POWER_MODE),
                                   self.running)

    def select_mode(self, mode):
        self.mode = mode
        self.channel_mask = {
            VOLTAGE_MODE: 0b00000111,
            CURRENT_MODE: 0b00111000,
            POWER_MODE: 0b00111111
        }.get(mode, None)

        mode_text = {
            VOLTAGE_MODE: '0 to 2',
            CURRENT_MODE: '3 to 5',
            POWER_MODE: '0 to 6'
        }.get(mode, '')
        print(f"Mode selected: {mode}, Channel mask set to: {self.channel_mask}")

        self.app.selected_channels_label.configure(text=f'Selected Channels: {mode_text}')
        self.app.update_labels_for_mode(self.mode)
        self.app.update()
        self.update_channel_display()

    def get_csv_file_name(self):
        base_name = datetime.now().strftime("%Y-%m-%d")
        mode_str = {VOLTAGE_MODE: "voltage", CURRENT_MODE: "current", POWER_MODE: "power"}.get(self.mode, "measurement")
        file_name = f"{base_name}-{mode_str}"
        extension = ".csv"
        final_name = file_name + extension
        counter = 1
        while os.path.exists(final_name):
            final_name = f"{file_name}-{counter}{extension}"
            counter += 1
        return final_name

    def append_data_to_csv(self, timestamp, readings, unit):
        with open(self.current_file_name, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=';')
            csvwriter.writerow([timestamp] + readings + [unit])

    def select_voltage_mode(self):
        self.select_mode(VOLTAGE_MODE)

    def select_current_mode(self):
        self.select_mode(CURRENT_MODE)

    def select_power_mode(self):
        self.select_mode(POWER_MODE)

    def update_channel_display(self):
        for channel in range(8):
            is_visible = is_channel_visible(channel, self.mode)
            if self.mode == POWER_MODE and channel % 2 == 0:
                if (self.channel_mask >> channel) & 1 and (self.channel_mask >> (channel + 1)) & 1:
                    label = self.app.channel_data_labels[channel]['Voltage']
                    label.grid()

                    self.app.channel_data_labels[channel + 1]['Voltage'].grid_remove()
            else:
                for label in self.app.channel_data_labels[channel].values():
                    if is_visible:
                        label.grid()
                    else:
                        label.grid_remove()

    def start_measurement(self):
        if self.running:
            print("A scan is already active.")
            return

        self.running = True
        self.app.measurement_status_label.configure(text='Measurement Status: Active')
        self.app.start_time = time.time()
        self.app.update_timer()

        if self.channel_mask is None:
            print("No measurement mode selected.")
            return

        if not (1 <= self.num_samples <= 10000):
            print("Invalid number of samples. Please set a value between 1 and 10000.")
            return

        if not (10 <= self.scan_rate <= 5000):
            print("Invalid scan rate. Please set a value between 10 and 5000 Hz.")
            return
        print(f"Starting measurement with channel mask: {self.channel_mask}")

        try:
            self.current_file_name = self.get_csv_file_name()
            options = OptionFlags.CONTINUOUS
            self.board.a_in_scan_start(self.channel_mask, self.num_samples, self.scan_rate, options)
            self.read_data()
        except ValueError as e:
            print(f"Error starting measurement: {e}")

    def stop_measurement(self):
        if self.running:
            self.running = False
            self.board.a_in_scan_stop()
            self.board.a_in_scan_cleanup()
            elapsed_time = time.time() - self.app.start_time
            self.app.measurement_status_label.configure(text=f'Measurement Finished. Time: {elapsed_time:.2f} sec')
            print(f"Stopping measurement with channel mask: {self.channel_mask}")
        else:
            print("Measurement is not running, so it cannot be stopped.")

    def read_data(self):
        read_request_size = -1
        timeout = -1

        total_samples_read = 0

        print("Measurement started...")

        while self.running and total_samples_read < self.num_samples:
            read_result = self.board.a_in_scan_read_numpy(read_request_size, timeout)
            data = read_result.data

            if data.size > 0:
                num_channels = bin(self.channel_mask).count('1')
                samples_per_channel = len(data) // num_channels
                total_samples_read += samples_per_channel

                print(
                    f"Data received: {data.size} points, Num channels: {num_channels}, Samples/channel: {samples_per_channel}")

                if samples_per_channel > 0:
                    for i in range(8):
                        if (self.channel_mask >> i) & 1:
                            channel_data_index = (i % num_channels) * samples_per_channel
                            voltage = data[channel_data_index]
                            if self.mode == VOLTAGE_MODE:
                                print(f'    Channel {i}: {voltage:.5f} V')
                                self.app.channel_data_labels[i]['Voltage'].configure(text=f'{voltage:.2f} V')
                            elif self.mode == CURRENT_MODE:
                                current = voltage * self.app.current_multiplier
                                print(f'    Channel {i} (CURRENT_MODE): {current:.5f} A')
                                self.app.channel_data_labels[i]['Voltage'].configure(text=f'{current:.2f} A')
                            elif self.mode == POWER_MODE:
                                current_channel_index = i + 3
                                current_data_index = (current_channel_index % num_channels) * samples_per_channel
                                current = data[current_data_index] * self.app.current_multiplier
                                power = voltage * current
                                self.app.channel_data_labels[i]['Voltage'].configure(text=f'{power:.2f} W')

                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        readings = [data[i] for i in range(8) if (self.channel_mask >> i) & 1]
                        unit = "V" if self.mode == VOLTAGE_MODE else "A" if self.mode == CURRENT_MODE else "W"
                        self.append_data_to_csv(timestamp, readings, unit)

                    self.app.update()
        self.stop_measurement()
        print("Measurement stopped.")


if __name__ == '__main__':
    energy_monitor = EnergyMonitor()
    energy_monitor.app.mainloop()
