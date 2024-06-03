# flyzer

flyzer is a Python package designed to test arousal levels of a sleeping fly. It has two main components: the experimental part, which includes hardware and software control, and the data analysis part, which focuses on processing and analyzing the generated data.

## Experimental Part

The experimental part of Flyzer is designed to work with the following hardware:

- A 1064 nm laser
- FLIR Blackfly S camera
- 3D printed chamber for a fly
- NI-DAQ for laser control

The `closedLoopArousal.py` script is used to process the incoming video feed from the FLIR Blackfly S camera. The laser is turned on based on the given parameters when the animal is quiescent.

## Data Analysis Part

The data analysis part of Flyzer focuses on processing and analyzing the generated data from the experiments. It includes:

- Data preprocessing and cleaning
- Data visualization
- Statistical analysis
- Breakpoint detection
