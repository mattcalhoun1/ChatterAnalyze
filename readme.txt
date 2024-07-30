requires:
python 3.1+

pip packatges:
pyserial
numpy
matplotlib
pyqt6
networkx

to run, connect a ChatterBox via USB and run:
python mesh_graph_app.py

If you know which USB port the ChatterBox is on, you can identify it like:
python mesh_graph_app.py -p /dev/ttyACM0


If you'd rather see indirect connections of the mesh graph, rather than direct, choose:
python mesh_graph_app.py -d

To exclude certain devices from the visualization, create a text file with the names of devices (one per line), use:
python mesh_graph_app.py -e /home/matt/my_exclusions.text
