import sys
import time
import json

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

    def __load_graph (self):
        # load the file
        if self.__load_graph_file() and self.__load_device_file():
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
        
    def __load_device_file (self):
        # Opening JSON file
        found = False
        foundHeader = False
        with(open('data/sample_raw_serial.json', 'r') as f):
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

    def __load_graph_file (self):
        # Opening JSON file
        found = False
        foundHeader = False
        with(open('data/sample_raw_serial.json', 'r') as f):
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

    def draw_graph (self):
        if self.__load_graph():
            nx.draw_shell(self.__MG, with_labels=True, font_weight='bold', ax=self._static_ax, edge_color=self.__edge_colors, width=self.__line_widths)
        else:
            print("no graph available yet")

if __name__ == "__main__":
    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QtWidgets.QApplication.instance()
    if not qapp:
        qapp = QtWidgets.QApplication(sys.argv)

    app = ApplicationWindow()
    app.draw_graph()
    app.show()
    app.activateWindow()
    app.raise_()
    qapp.exec()