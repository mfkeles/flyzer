import os
import pandas as pd
import numpy as np


class events:
    """Provides easy access to output variables"""

    def __init__(self, path, timestamp):
        self.daq_event = []
        self.daq_event_list = []
        self.daq_data = []
        self.daq_event_list_path = os.path.join(path, f"Fly-{timestamp}-arousal_bouts.csv")
        self.daq_event_list_columns = ['Start', 'Stop', 'Vals']

        self.motion_event = []
        self.motion_event_list = []
        self.event_list_path = os.path.join(path, f"Fly-{timestamp}-all_events.csv")

        self.event_list_columns = ['Quiescence State Start', 'Start_Idx', 'Quiescence State Ended', 'Stop_Idx']
        self.status = []
        self.status_save_path = os.path.join(path, f"Fly-{timestamp}-status.npy")


    def save_outputs(self):
        df = pd.DataFrame(self.motion_event_list, columns=self.event_list_columns)
        df.to_csv(self.event_list_path, index=False)

        arousal_df = pd.DataFrame(self.daq_event_list, columns=self.daq_event_list_columns)
        arousal_df.to_csv(self.daq_event_list_path, index=False)

        np_arr = np.array(self.status, dtype=np.uint8)
        np.save(self.status_save_path, np_arr)
