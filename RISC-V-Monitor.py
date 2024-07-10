import serial
import re
import datetime
import platform
import os
import time
import sys

def play_warning_sound():
    if platform.system() == "Windows":
        import winsound
        winsound.MessageBeep(winsound.MB_ICONHAND)
    else:
        # For Unix-based systems, use a simple beep sound
        os.system('echo -e "\a"')

def display_intro():
    ascii_art = """
********************************************************************************
*  ______     __                          _______   ______   ______    ______  *
* /      \   |  \                        |       \ |      \ /      \  /      \ *
*|  $$$$$$\ _| $$_     ______    ______  | $$$$$$$\ \$$$$$$|  $$$$$$\|  $$$$$$\*
*| $$___\$$|   $$ \   |      \  /      \ | $$__| $$  | $$  | $$___\$$| $$   \$$*
* \$$    \  \$$$$$$    \$$$$$$\|  $$$$$$\| $$    $$  | $$   \$$    \ | $$      *
* _\$$$$$$\  | $$ __  /      $$| $$   \$$| $$$$$$$\  | $$   _\$$$$$$\| $$   __ *
*|  \__| $$  | $$|  \|  $$$$$$$| $$      | $$  | $$ _| $$_ |  \__| $$| $$__/  \*
* \$$    $$   \$$  $$ \$$    $$| $$      | $$  | $$|   $$ \ \$$    $$ \$$    $$*
*  \$$$$$$     \$$$$   \$$$$$$$ \$$       \$$   \$$ \$$$$$$  \$$$$$$   \$$$$$$ *
*                                                                              *
*                                                                              *
*                                                                              *
* __       __                      __    __                                    *
*|  \     /  \                    |  \  |  \                                   *
*| $$\   /  $$  ______   _______   \$$ _| $$_     ______    ______             *
*| $$$\ /  $$$ /      \ |       \ |  \|   $$ \   /      \  /      \            *
*| $$$$\  $$$$|  $$$$$$\| $$$$$$$\| $$ \$$$$$$  |  $$$$$$\|  $$$$$$\           *
*| $$\$$ $$ $$| $$  | $$| $$  | $$| $$  | $$ __ | $$  | $$| $$   \$$           *
*| $$ \$$$| $$| $$__/ $$| $$  | $$| $$  | $$|  \| $$__/ $$| $$                 *
*| $$  \$ | $$ \$$    $$| $$  | $$| $$   \$$  $$ \$$    $$| $$                 *
* \$$      \$$  \$$$$$$  \$$   \$$ \$$    \$$$$   \$$$$$$  \$$                 *
********************************************************************************
    """
    print(ascii_art)
    print("Initializing StarRISC Monitor...\n")

    progress_bar()

def progress_bar():
    toolbar_width = 40
    sys.stdout.write("[%s]" % (" " * toolbar_width))
    sys.stdout.flush()
    sys.stdout.write("\b" * (toolbar_width + 1))  # return to start of line, after '['

    for i in range(toolbar_width):
        time.sleep(0.05)  # Adjust time to make it look intense
        sys.stdout.write("-")
        sys.stdout.flush()

    sys.stdout.write("\n")

def main():
    display_intro()

    # Initialize serial connection
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    ser.flush()

    single_bit_errors = 0
    double_bit_errors = 0

    single_bit_re = re.compile(r"Single Bit Errors: (\d+)")
    double_bit_re = re.compile(r"Double Bit Errors: (\d+)")

    # Open files for recording and logging
    data_file = open('serial_data.txt', 'a')
    log_file = open('error_log.txt', 'a')

    # Record the start time
    start_time = datetime.datetime.now()
    log_file.write(f"Script started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    last_received_time = time.time()

    try:
        while True:
            if ser.in_waiting > 0:
                last_received_time = time.time()  # Update the last received time
                try:
                    line = ser.readline().decode('utf-8').rstrip()
                except UnicodeDecodeError:
                    # Handle unreadable data
                    current_time = datetime.datetime.now()
                    elapsed_time = current_time - start_time
                    error_message = f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} (Elapsed: {elapsed_time}) - ERROR: Unreadable serial data received"
                    print(error_message)
                    log_file.write(error_message + '\n')
                    play_warning_sound()
                    continue
                
                # Record all serial data to data_file
                data_file.write(line + '\n')

                if "FAILED" in line:
                    print(line)
                    current_time = datetime.datetime.now()
                    elapsed_time = current_time - start_time
                    log_file.write(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} (Elapsed: {elapsed_time}) - {line}\n")
                    play_warning_sound()
                
                single_bit_match = single_bit_re.search(line)
                if single_bit_match:
                    single_bit_errors = int(single_bit_match.group(1))
                    print(f"Updated Single Bit Errors: {single_bit_errors}")
                    current_time = datetime.datetime.now()
                    elapsed_time = current_time - start_time
                    log_file.write(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} (Elapsed: {elapsed_time}) - Updated Single Bit Errors: {single_bit_errors}\n")
                
                double_bit_match = double_bit_re.search(line)
                if double_bit_match:
                    double_bit_errors = int(double_bit_match.group(1))
                    print(f"Updated Double Bit Errors: {double_bit_errors}")
                    current_time = datetime.datetime.now()
                    elapsed_time = current_time - start_time
                    log_file.write(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} (Elapsed: {elapsed_time}) - Updated Double Bit Errors: {double_bit_errors}\n")
            else:
                current_time = time.time()
                if current_time - last_received_time > 5:
                    # No data received for 5 seconds
                    elapsed_time = datetime.datetime.now() - start_time
                    error_message = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Elapsed: {elapsed_time}) - ERROR: No data received from UART for 5 seconds"
                    print(error_message)
                    log_file.write(error_message + '\n')
                    play_warning_sound()
                    last_received_time = current_time  # Reset the timer to avoid repeated warnings

    except KeyboardInterrupt:
        print("Monitoring stopped.")
    finally:
        ser.close()
        data_file.close()
        log_file.close()

if __name__ == "__main__":
    main()
