import os
from datetime import datetime
import time
import threading
import EasyPySpin
import cv2
import queue
import DAQ
import events
import writer
from cv2proc import cv2proc
from ExperimentSettings import ExperimentSettings

daq_data_queue = queue.Queue()


def threaded_start():
    daq.synchronized_start()


def threaded_stop():
    daq_data = daq.synchronized_stop()
    daq_data_queue.put(daq_data)

# Start at ZT10
while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    start = '20:00:00'
    if current_time > start:
        print('Program Starting')
        break
    else:
        time.sleep(60)


folderPath = r'C:\Users\sleepdata\Desktop\ArousalThreshold'

# ===============================================================================
# nidaq related variables
# Sampling Rate for DAQ
fs = 1000

# Buffer size to grab
buffer = 100

# Initiate DAQ and setup channels only done once!
daq = DAQ.DAQ(fs, buffer)
daq.setup_chans()

t = time.localtime()
timestamp = time.strftime('%b-%d-%Y_%H%M', t)


fly_name = f"Fly-{timestamp}-closed_loop"
full_folder_name = os.path.join(folderPath, fly_name)


# Check if the folder exists
if not os.path.exists(full_folder_name):
    # If the folder doesn't exist, create it
    os.makedirs(full_folder_name)
    print(f"Created folder: {full_folder_name}")
else:
    print(f"Folder already exists: {full_folder_name}")


full_file_name = os.path.join(full_folder_name,fly_name+'.mp4')

# Use to prevent turning on Laser
evaluation_mode = False

# initiate events object to keep track of output data
events = events.events(full_folder_name, timestamp)

# =============================================================================
# USER-SET PARAMETERS
# =============================================================================
# Number of frames to pass before changing the frame to compare the current
# frame against
FRAMES_TO_PERSIST = 20

# Minimum boxed area for a detected motion to count as actual motion
# Use to filter out noise or small objects
MIN_SIZE_FOR_MOVEMENT = 1000

# Minimum length of time where no motion is detected it should take
# (in program cycles) for the program to declare that there is no movement
MOVEMENT_DETECTED_PERSISTENCE = 30 * 30

# DAQ Interval
INTERVAL = 30 * 60 * 15

# Total duration
TOTAL_FPS = 30 * 60 * 60 * 14

# Camera FPS
FPS = 30

# Duration of Arousal to Persist
AROUSAL_PERSISTENCE = FPS*3

# Define the threshold (e.g. 90%)
THRESHOLD_PERCENTAGE = 0.9

# =============================================================================

# Write all the settings and save it
settings = ExperimentSettings(FPS, fs, buffer, FRAMES_TO_PERSIST, INTERVAL,MIN_SIZE_FOR_MOVEMENT,AROUSAL_PERSISTENCE, MOVEMENT_DETECTED_PERSISTENCE, TOTAL_FPS,THRESHOLD_PERCENTAGE)

# Create capture object
cap = EasyPySpin.VideoCapture('21156756')
my_img = cv2proc(cap, FPS)

my_img.print_cam_res()

# Init frame variables
first_frame = None
next_frame = None

# Init display font and timeout counters

delay_counter = 0
movement_persistent_counter = 0
arousal_persistent_counter = 0

previously_moving = False
bin_transient_window = True


video_writer = writer.initiate_videowriter(full_file_name, my_img.frame_width, my_img.frame_height, my_img.fps)

idx = 0

while True and idx <= TOTAL_FPS:
    start = time.time()
    # Set transient motion detected as false
    transient_movement_flag = False

    # Set arousal movement detected as false
    arousal_movement_flag = False


    # Read frame
    ret, frame = cap.read()
    text = "Unoccupied"

    # Interrupt trigger by pressing q to quit the open CV program, write to data frame and check if frame is empty or
    # not
    ch = cv2.waitKey(1)
    if frame is None or ch & 0xFF == ord('q'):
        print(events.motion_event_list)
        events.save_outputs()
        break

    # If there's an error in capturing
    if not ret:
        print("CAPTURE ERROR")
        continue

    # capture the frame
    video_writer.send(frame)

    # gaussian blur
    gray = my_img.gaussianblur(frame)

    # If the first frame is nothing, initialise it
    if first_frame is None: first_frame = gray

    delay_counter += 1

    # Otherwise, set the first frame to compare as the previous frame
    # But only if the counter reaches the appropriate value
    # The delay is to allow relatively slow motions to be counted as large
    # motions if they're spread out far enough
    if delay_counter > FRAMES_TO_PERSIST:
        delay_counter = 0
        first_frame = next_frame

    # Set the next frame to compare (the current frame)
    next_frame = gray

    # Process images
    frame_delta, cnts, b = my_img.proc_images(first_frame, next_frame)

    # loop over the contours
    for c in cnts:

        # Save the coordinates of all found contours
        (x, y, w, h) = cv2.boundingRect(c)

        # If the contour is too small, ignore it, otherwise, there's transient
        # movement
        if cv2.contourArea(c) > MIN_SIZE_FOR_MOVEMENT:

            if not previously_moving:

                endtime = datetime.now()
                print("Movement Detected - Fly Awake", endtime.strftime('%Y-%m-%d %H:%M:%S'), "\n")

                events.motion_event.append(endtime.strftime('%Y-%m-%d %H:%M:%S'))
                events.motion_event.append(idx)
                events.motion_event_list.append(events.motion_event)
                events.motion_event = []
                previously_moving = True

            transient_movement_flag = True
            # Draw a rectangle around big enough movements
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)




    if transient_movement_flag == False:
        events.status.append(0)
    else:
        events.status.append(1)

    if daq.state:

        #if Laser is ON then create a transient movement window
        if bin_transient_window:
            # Initialize the sliding window
            transient_movement_window = [False] * AROUSAL_PERSISTENCE
            bin_transient_window = False

        # Update the sliding window
        transient_movement_window.pop(0)
        transient_movement_window.append(transient_movement_flag)

        # Calculate the percentage of True values in the sliding window
        true_percentage = sum(transient_movement_window) / AROUSAL_PERSISTENCE

        if arousal_persistent_counter < AROUSAL_PERSISTENCE:
            arousal_persistent_counter += 1

        elif arousal_persistent_counter == AROUSAL_PERSISTENCE and true_percentage >= THRESHOLD_PERCENTAGE:
            t2 = threading.Thread(target=threaded_stop)
            t2.start()
            events.daq_data = daq_data_queue.get()
            daq.state = 0
            events.daq_event.append(idx)
            events.daq_event.append(events.daq_data)
            events.daq_event_list.append(events.daq_event)
            events.daq_data = []
            events.daq_event = []
            print("Laser OFF")
            bin_transient_window = True
            arousal_persistent_counter = 0


    # The moment something moves momentarily, reset the persistent
    # movement timer.
    if transient_movement_flag:
        movement_persistent_flag = True
        movement_persistent_counter = MOVEMENT_DETECTED_PERSISTENCE

    # As long as there was a recent transient movement, say a movement
    # was detected
    if movement_persistent_counter > 1:
        text = "Movement Detected " + str(movement_persistent_counter)
        movement_persistent_counter -= 1

    elif movement_persistent_counter == 1:
        text = "Quiescence Detected"
        start_time = datetime.now()
        print("Quiescence Detected -  Fly Asleep", start_time.strftime('%Y-%m-%d %H:%M:%S'))
        events.motion_event.append(start_time.strftime('%Y-%m-%d %H:%M:%S'))
        events.motion_event.append(idx)

        if daq.counter is None or idx - daq.counter > INTERVAL:
            # initiate daq
            daq.state = 1
            t1 = threading.Thread(target=threaded_start)
            t1.start()
            daq.counter = idx
            events.daq_event.append(idx)
            print('Laser ON')
        movement_persistent_counter -= 1
        previously_moving = False
    else:
        text = "No Movement Detected"

    # Print the text on the screen, and display the raw and processed video
    # feeds
    my_img.print_text(frame, text)

    # Splice the two video frames together to make one long horizontal one
    my_img.imshow(frame_delta)

    idx += 1

# Cleanup when closed
if daq.state == 1:
    daq.synchronized_stop()
    daq.__del__()

settings.save_settings(full_folder_name)
cap.release()
video_writer.close()
cv2.waitKey(0)
cv2.destroyAllWindows()
daq.__del__()
events.save_outputs()
