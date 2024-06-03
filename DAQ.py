
import copy
import nidaqmx
import nidaqmx.constants as constants
import nidaqmx.stream_readers as stream_readers
import nidaqmx.stream_writers as stream_writers
import numpy as np
import threading


class DAQ:
    """Wrapper class to have easy access to NIDAQ. Allows continuous read/write tasks.
        code modified from:
        https://github.com/TheRandomWalk/Mechanical-Timepiece-Vibration-Analysis/blob/c8a23606a601ef8fbb291d76832326eb442dfa0d/Code/DAQ.py"""

    def __init__(self, samplingRate, bufferSize):
        self.read_task_ = nidaqmx.Task()
        self.write_task_ = nidaqmx.Task()
        self.samplingRate = samplingRate
        self.bufferSize = bufferSize
        self.state = 0
        self.counter = None
        self.data_ = []
        self.threads = []

    @staticmethod
    def _generate_sample(fs, step_dur = 3, num_steps =11, start_v = 0, end_v = 5):
        step_size = (end_v - start_v) / num_steps
        sample = []

        for step in range(num_steps):
            current_start = start_v + step * step_size
            current_end = start_v + (step + 1) * step_size
            num_samples = int(fs * step_dur)

            step_samples = np.linspace(current_start, current_end, num_samples, endpoint=False)
            sample.extend(step_samples)
        # add 30 seconds of full power to the end in case
        sample = np.append(sample, np.ones(fs * 30) * end_v)

        return np.array(sample)

    def __del__(self):
        self.read_task_.close()
        self.write_task_.close()

    def _create_ao_chan(self):
        self.write_task_.ao_channels.add_ao_voltage_chan('Dev2/ao0')
        self.send_signal = self._generate_sample(self.samplingRate)
        self.write_task_.timing.cfg_samp_clk_timing(rate=self.samplingRate,
                                                    sample_mode=constants.AcquisitionType.CONTINUOUS,
                                                    samps_per_chan=self.send_signal.size)

    def _create_ai_chan(self):
        self.read_task_.ai_channels.add_ai_voltage_chan("Dev2/ai0")
        self.read_task_.timing.cfg_samp_clk_timing(rate=self.samplingRate,
                                                   sample_mode=constants.AcquisitionType.CONTINUOUS,
                                                   samps_per_chan=self.bufferSize)
        self.analogSingleChannelReader_ = stream_readers.AnalogSingleChannelReader(self.read_task_.in_stream)
        self.read_task_.register_every_n_samples_acquired_into_buffer_event(self.bufferSize, self.callback)
        self.mutex_ = threading.Lock()

    def setup_chans(self):
        self._create_ai_chan()
        self._create_ao_chan()

    def synchronized_start(self):
        # ao expects ai to start
        self.write_task_.triggers.start_trigger.cfg_dig_edge_start_trig(self.read_task_.triggers.start_trigger.term)

        self.writer = stream_writers.AnalogSingleChannelWriter(self.write_task_.out_stream, auto_start=False)
        self.writer.write_many_sample(self.send_signal)

        self.write_task_.start()
        self.read_task_.start()

        try:
            bool_task = self.read_task_.is_task_done()
            if bool_task:
                self.read_task_.start()
        except Exception as e:
            print('Read task is not started' , e)
            self.read_task_.start()
        self.data_ = []

    def synchronized_stop(self):
        self.write_task_.stop()
        zeroIt = np.zeros(10)
        self.writer = stream_writers.AnalogSingleChannelWriter(self.write_task_.out_stream, auto_start=False)
        self.writer.write_many_sample(zeroIt)

        # disable trigger
        self.write_task_.triggers.start_trigger.disable_start_trig()
        self.write_task_.start()
        self.write_task_.stop()

        # grab the data
        data = self.download()
        self.read_task_.stop()

        return data

    def download(self):
        self.mutex_.acquire()
        data = copy.deepcopy(self.data_)
        self.data_ = []
        self.mutex_.release()
        return data

    def callback(self, taskHandle, eventType, samples, callbackData):
        buffer = np.squeeze(np.zeros((1, samples)))
        self.analogSingleChannelReader_.read_many_sample(buffer, samples, timeout=constants.READ_ALL_AVAILABLE)
        self.mutex_.acquire()
        self.data_.extend(buffer.tolist())
        self.mutex_.release()
        return 0
