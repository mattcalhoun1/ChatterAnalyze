import time
import serial

class ChatterConnector:
    def __init__(self, usb_port_list):
        self.__usb_ports = usb_port_list
        self.__max_wait_time_per_cycle = 20.0

    # retrieve complete graph from the usb-connected ChatterBox and write it to text file
    def pull_graph_data (self, output_file):
        # all of these are required via serial to verify we have a complete graph
        req_str = [
            '= Begin Devices =',
            '= End Devices =',
            '= Mesh Graph =',
            '= End Mesh Graph ='
        ]

        # wait for a serial connection and ingest serial data,
        # writing to the given text file until we've 
        # received complete graph data
        streamed = False
        while not streamed:
            for p in self.__usb_ports:
                try:
                    streamed = self.stream_serial_to_file (p, output_file, req_str, self.__max_wait_time_per_cycle)
                    if streamed:
                        break
                except Exception as e:
                    print(f"No connection yet on port: {p}. Scanning...")
                    time.sleep(5.0)                


    def stream_serial_to_file (self, usb_port, file_name, required_strings, timeout):
        found_strings = False
        start_time = time.time()

        found = {}
        for r in required_strings:
            found[r] = False

        self.__serial = serial.Serial(port=usb_port, baudrate=9600, timeout=timeout)
        with open(file_name, 'wt') as out_file:
            while time.time() - start_time < timeout and not found_strings:
                if self.__has_serial_content():
                    this_line = self.__get_serial_line(timeout=timeout)

                    # reset the start_time since we're getting content
                    start_time = time.time()

                    print(this_line)

                    out_file.write(this_line)
                    out_file.write('\n')

                    for r in required_strings:
                        if r in this_line:
                            found[r] = True
                    
                # check if all strings found
                found_strings = True
                for r in required_strings:
                    if not found[r]:
                        found_strings = False


        return found_strings

    def __has_serial_content (self):
        hasmsg = self.__serial.in_waiting > 0
        return hasmsg
    
    def __get_serial_line (self, timeout = 10.0):
        # read bytes until we hit a carriage return or newline
        complete_message = False
        message_buffer = ""
        start_time = time.time()
        while complete_message == False and (time.time() - start_time <= timeout):
            if self.__serial.in_waiting > 0:
                next_byte = self.__serial.read()
                try:
                    next_str = next_byte.decode('utf-8')
                    if next_str == '\n' or next_str == '\r':
                        complete_message = True
                    elif next_str == '\0' or next_str == '\x00':
                        # ignore these characters, they may be c string terminators, but we dont care about those
                        pass
                    else:
                        message_buffer += next_str
                except Exception as e:
                    print(f"Exception reading serial port: {e}")
            else:
                # wait for more bytes
                time.sleep(0.05)

        return message_buffer.rstrip()
