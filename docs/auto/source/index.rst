.. DataMole documentation master file, created by
    sphinx-quickstart on Wed Apr 15 08:33:05 2020.
    You can adapt this file completely to your liking, but it should at least
    contain the root `toctree` directive.

DataMole documentation
============================================

************
Introduction
************

DataMole is a data science tool written in Python with a graphical interface, that can support researchers during
data exploration and preprocessing activities. It allows to define pipelines of operations within a user-friendly
graphical environment, providing an intuitive approach to data manipulation.
The tool also embeds some data visualisation features, like scatterplots and line charts,
as well as a specific feature for the extraction of time series from longitudinal
datasets.

Additional documentation can be found in the ``docs/manuals`` folder, which contains a developer manual and a user guide.

************
Requirements
************
The following packages must be installed in order to run DataMole:

- PySide2 5.15.1
- PyQtGraph 0.11.0
- numpy 1.19.1
- pandas 1.0.5
- networkx 2.4
- scikit-learn 0.23.1
- prettytable

The requirements are also listed in the ``requirements.txt`` file.
Additional requirements for developers are in the ``requirements.dev.txt`` file.

*************
Main packages
*************
The main sub-packages of DataMole are listed below.

.. autosummary::
   :toctree: _stubs
   :caption: API Reference
   :template: custom-module-template.rst
   :recursive:

   dataMole.data
   dataMole.flow
   dataMole.gui
   dataMole.operation
   dataMole.flogging

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
