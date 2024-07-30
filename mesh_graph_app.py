import getopt
import sys
import json
from chatter_connector import ChatterConnector
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
        self.__hidden_devices = []

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
        
    def __get_visible_device_name (self, device_id):
        dev_name = self.__get_device_name(device_id=device_id)

        if dev_name is not None:
            if dev_name in self.__hidden_devices:
                return None

        return dev_name
        
    def __get_device_name (self, device_id):
        if device_id in self.__graph_raw['DeviceNames']:
            return self.__graph_raw['DeviceNames'][device_id]
        elif f'{int(device_id):03d}' in self.__graph_raw['DeviceNames']:
            return self.__graph_raw['DeviceNames'][f'{int(device_id):03d}']
        else:
            print(f'{int(device_id):03d} not found')
            print(f"Device {device_id} not found in device names")
        
        return None #f"id:{device_id}"

    def __load_graph (self, file_name, show_direct_connections, show_indirect_connections, exclusions_file = None):
        if exclusions_file is not None:
            self.__load_exclusions_file(file_name=exclusions_file)

        # load the file
        if self.__load_graph_file(file_name) and self.__load_device_file(file_name):
            self.__MG = nx.MultiDiGraph()
            self.__edge_colors = []
            self.__line_widths = []

            link_threshold = 5 # a rating of at least 5 means devices have at some point been in range

            # parse into a networkx multigraph
            for node in self.__graph_raw['MeshGraph']:
                for neighbor in self.__graph_raw['MeshGraph'][node]:
                    if self.__get_visible_device_name(neighbor) != self.__get_visible_device_name(node):
                        # add direct connection (if any). otherwise show indirect (if any)
                        if (self.__graph_raw['MeshGraph'][node][neighbor]['direct'] > link_threshold and show_direct_connections):
                            if self.__get_visible_device_name(node) is not None and self.__get_visible_device_name(neighbor) is not None:
                                self.__MG.add_edge(
                                    self.__get_visible_device_name(node),
                                    self.__get_visible_device_name(neighbor),
                                    weight=self.__graph_raw['MeshGraph'][node][neighbor]['direct']
                                )
                                self.__edge_colors.append(self.__color_for_direct_rating(self.__graph_raw['MeshGraph'][node][neighbor]['direct']))
                                self.__line_widths.append(1.0)
                        elif (self.__graph_raw['MeshGraph'][node][neighbor]['indirect'] > link_threshold and show_indirect_connections):
                            if self.__get_visible_device_name(node) is not None and self.__get_visible_device_name(neighbor) is not None:
                                self.__MG.add_edge(
                                    self.__get_visible_device_name(node),
                                    self.__get_visible_device_name(neighbor),
                                    weight=self.__graph_raw['MeshGraph'][node][neighbor]['indirect']
                                )
                                self.__edge_colors.append(self.__color_for_indirect_rating(self.__graph_raw['MeshGraph'][node][neighbor]['indirect']))
                                self.__line_widths.append(0.5)
            return True
        else:
            return False

    def __load_exclusions_file (self, file_name):
        self.__hidden_devices = []
        # Opening JSON file
        with(open(file_name, 'r') as f):
            for next_line in f:
                #print(nextLine)
                trimmed_line = next_line.rstrip().lstrip()
                if len(trimmed_line) > 0:
                    self.__hidden_devices.append(trimmed_line)
        print(f"Excluding {len(self.__hidden_devices)} devices: {self.__hidden_devices}")
            
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

    def draw_graph (self, graph_file, show_direct_connections = True, show_indirect_connections = False, exclusions_file=None):
        if self.__load_graph(file_name=graph_file, show_direct_connections=show_direct_connections, show_indirect_connections=show_indirect_connections, exclusions_file=exclusions_file):
            nx.draw_shell(self.__MG, with_labels=True, font_weight='bold', ax=self._static_ax, edge_color=self.__edge_colors, width=self.__line_widths)
        else:
            print("no graph available yet")

def show_help ():
    print(f"Note: Your user will need permission to read the appropriate usb port. This visualization app has been tested on mac and linux only.")
    print(f"~~~~~~~~~~~~~~~~~~~")
    print(f"Usage: ")
    print(f"  python mesh_graph_app.py -h (help)")
    print(f"  python mesh_graph_app.py -d (show direct connections - choose direct or indirect, not both)")
    print(f"  python mesh_graph_app.py -i (show indirect connections - choose direct or indirect, not both)")
    print(f"  python mesh_graph_app.py -e <Exclusions File> (ex: /tmp/excluded_devices.txt)")
    print(f"  python mesh_graph_app.py -p <USB Port> (ex: /dev/ttyACM0)")    

if __name__ == "__main__":

    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QtWidgets.QApplication.instance()
    if not qapp:
        qapp = QtWidgets.QApplication(sys.argv)

    app = ApplicationWindow()

    argument_list = sys.argv[1:]
    options = "hdie:p:"
    long_options = ["Help", "Direct", "Indirect", "Exclusions=", "Port="]

    # default ports list
    default_usb_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/cu.usbmodem14101', '/dev/ttyUSB0']
    temp_graph_file = '/tmp/chatter_mesh_graph.txt'
    show_direct = True
    show_indirect = False
    exclusions_file = None

    arguments, values = getopt.getopt(argument_list, options, long_options)
    for curr_arg, curr_val in arguments:
        if curr_arg in ("-h", "--Help"):
            show_help()
            sys.exit(0)
        elif curr_arg in ("-d", "--Direct"):
            show_direct = True
            show_indirect = False
        elif curr_arg in ("-i", "--Indirect"):
            show_indirect = True
            show_direct = False
        elif curr_arg in ("-e", "--Exclusions"):
            exclusions_file = curr_val
            print(f"Excluding: {exclusions_file}")
        elif curr_arg in ("-p", "--Port"):
            default_usb_ports = [curr_val,]

    # connect to the ChatterBox (usb) and retrieve graph data.
    # will take at least a few seconds, maybe up to a minute
    chatter_conn = ChatterConnector(usb_port_list=default_usb_ports)
    chatter_conn.pull_graph_data(output_file=temp_graph_file)

    app.draw_graph(graph_file=temp_graph_file, show_direct_connections=show_direct, show_indirect_connections=show_indirect, exclusions_file=exclusions_file)
    app.show()
    app.activateWindow()
    app.raise_()
    qapp.exec()

