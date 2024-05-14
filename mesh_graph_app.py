import sys
import time
import json
import serial

import numpy as np

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure
import networkx as nx
import matplotlib.pyplot as plt


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        static_canvas = FigureCanvas(Figure(figsize=(10, 7)))
        # Ideally one would use self.addToolBar here, but it is slightly
        # incompatible between PyQt6 and other bindings, so we just add the
        # toolbar as a plain widget instead.
        layout.addWidget(NavigationToolbar(static_canvas, self))
        layout.addWidget(static_canvas)

        self._static_ax = static_canvas.figure.subplots()
        self.__graph_raw = {}

    def __load_graph_static (self):
        adj_list = {'4': ['5', '6'], '6': ['4'], '5': ['4','6']}

        self.__MG = nx.MultiDiGraph()
        #G.add_nodes_from([(4, {"color": "red"}), (5, {"color": "green"})])
        self.__MG.add_edge('4', '5', weight=4.7)
        self.__MG.add_edge('5', '4', weight=8.7)

        self.__MG.add_edge('4', '6', weight=1.7)
        self.__MG.add_edge('6', '4', weight=6.7)

        self.__MG.add_edge('5', '6', weight=12.0)

        self.__edge_colors = [
            'black',
            'black',
            'blue',
            'blue',
            'black'
        ]

    def __color_for_direct_rating(self, rating):
        if (rating > 80):
            return 'green'
        elif (rating > 50):
            return 'blue'
        elif (rating > 20):
            return 'cyan'
        elif (rating >= 5):
            return 'yellow'
        else:
            return 'gray'

    def __color_for_indirect_rating(self, rating):
        if (rating > 80):
            return 'darkorange'
        elif (rating > 50):
            return 'burlywood'
        elif (rating > 20):
            return 'bisque'
        elif (rating >= 5):
            return 'linen'
        else:
            return 'cornsilk'
        
    def __get_device_name (self, device_id):
        if device_id in self.__graph_raw['DeviceNames']:
            return self.__graph_raw['DeviceNames'][device_id]
        elif f'{int(device_id):03d}' in self.__graph_raw['DeviceNames']:
            return self.__graph_raw['DeviceNames'][f'{int(device_id):03d}']
        else:
            print(f'{int(device_id):03d} not found')
            print(f"Device {device_id} not found in device names")
        
        return f"id:{device_id}"

    def __load_graph (self, file_name):
        # load the file
        if self.__load_graph_file(file_name) and self.__load_device_file(file_name):
            self.__MG = nx.MultiDiGraph()
            self.__edge_colors = []
            self.__line_widths = []

            # parse into a networkx multigraph
            for node in self.__graph_raw['MeshGraph']:
                for neighbor in self.__graph_raw['MeshGraph'][node]:
                    if self.__get_device_name(neighbor) != self.__get_device_name(node):
                        # add direct connection (if any). otherwise show indirect (if any)
                        if (self.__graph_raw['MeshGraph'][node][neighbor]['direct'] > 1):
                            self.__MG.add_edge(
                                self.__get_device_name(node),
                                self.__get_device_name(neighbor),
                                weight=self.__graph_raw['MeshGraph'][node][neighbor]['direct']
                            )
                            self.__edge_colors.append(self.__color_for_direct_rating(self.__graph_raw['MeshGraph'][node][neighbor]['direct']))
                            self.__line_widths.append(1.0)
                        elif (self.__graph_raw['MeshGraph'][node][neighbor]['indirect'] > 1):
                            self.__MG.add_edge(
                                self.__get_device_name(node),
                                self.__get_device_name(neighbor),
                                weight=self.__graph_raw['MeshGraph'][node][neighbor]['indirect']
                            )
                            self.__edge_colors.append(self.__color_for_indirect_rating(self.__graph_raw['MeshGraph'][node][neighbor]['indirect']))
                            self.__line_widths.append(0.5)
            return True
        else:
            return False
        
    def __load_device_file (self, file_name):
        # Opening JSON file
        found = False
        foundHeader = False
        with(open(file_name, 'r') as f):
            for nextLine in f:
                print(nextLine)
                if '= Begin Devices =' in nextLine:
                    # the line following this one is the graph, ingest it and return
                    foundHeader = True
                    print('found header')
                elif foundHeader and nextLine.startswith('{'):
                    fullDevNames = json.loads(nextLine)

                    self.__graph_raw['DeviceNames'] = {}

                    # add just the address
                    for d in fullDevNames:
                        print(d[5:])
                        self.__graph_raw['DeviceNames'][d[5:]] = fullDevNames[d]


                    print('loaded devices!')
                    return True
            
        return found

    def __load_graph_file (self, graph_file):
        # Opening JSON file
        found = False
        foundHeader = False
        with(open(graph_file, 'r') as f):
            for nextLine in f:
                print(nextLine)
                if '= Mesh Graph =' in nextLine:
                    # the line following this one is the graph, ingest it and return
                    foundHeader = True
                    print('found header')
                elif foundHeader and nextLine.startswith('{'):
                    self.__graph_raw['MeshGraph'] = json.loads(nextLine)
                    print('loaded graph!')
                    return True
            
        return found

    def draw_graph (self, graph_file):
        if self.__load_graph(graph_file):
            nx.draw_shell(self.__MG, with_labels=True, font_weight='bold', ax=self._static_ax, edge_color=self.__edge_colors, width=self.__line_widths)
        else:
            print("no graph available yet")


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

        #logging.getLogger(__name__).info(f"Arduino: [{message_buffer}]")
        return message_buffer.rstrip()

if __name__ == "__main__":
    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QtWidgets.QApplication.instance()
    if not qapp:
        qapp = QtWidgets.QApplication(sys.argv)

    app = ApplicationWindow()

    # wait for a serial connection
    req_str = [
        '= Begin Devices =',
        '= End Devices =',
        '= Mesh Graph =',
        '= End Mesh Graph ='
    ]

    usb_ports = ['/dev/ttyACM0', '/dev/ttyUSB0']
    streamed = False
    while not streamed:
        for p in usb_ports:
            try:
                streamed = app.stream_serial_to_file (p, '/tmp/chatter_device_log.txt', req_str, 20.0)
                if streamed:
                    break
            except Exception as e:
                print(f"scan failed: {e}")
                time.sleep(5.0)                
                print("scanning usb ports")

    # begin ingesting serial data and writing to a temp file until we've received both required pieces



    app.draw_graph('/tmp/chatter_device_log.txt')
    app.show()
    app.activateWindow()
    app.raise_()
    qapp.exec()