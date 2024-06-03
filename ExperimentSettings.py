import json
import os


class ExperimentSettings:
    def __init__(self, fps, daq_sampling_rate, daq_buffer_size, frames_to_persist, daq_interval, min_size_for_movement,
                 arousal_persistence, movement_detected_persistence, total_frames, threshold_percentage):
        self.fps = fps
        self.daq_sampling_rate = daq_sampling_rate
        self.daq_buffer_size = daq_buffer_size
        self.frames_to_persist = frames_to_persist
        self.daq_interval = daq_interval
        self.minimum_size_for_movement = min_size_for_movement
        self.arousal_persistence = arousal_persistence
        self.movement_detected_persistence = movement_detected_persistence
        self.total_frames = total_frames
        self.threshold_percentage = threshold_percentage

    def to_dict(self):
        return {
            'fps': self.fps,
            'daq_sampling_rate': self.daq_sampling_rate,
            'daq_buffer_size': self.daq_buffer_size,
            'daq_interval': self.daq_interval,
            'frames_to_persist': self.frames_to_persist,
            'minimum_size_for_movement': self.minimum_size_for_movement,
            'total_frames': self.total_frames,
            'arousal_persistence': self.arousal_persistence,
            'movement_detected_persistence': self.movement_detected_persistence
        }

    def save_settings(self, folder_path):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        with open(os.path.join(folder_path, 'settings.json'), 'w') as f:
            json.dump(self.to_dict(), f)
