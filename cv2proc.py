import cv2
import numpy as np


class cv2proc:
    """Wrapper class for image processing when grabbing frames"""

    def __init__(self, cap, fps):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.size = (self.frame_width, self.frame_height)
        self.fps = fps
        self.first_frame = None
        self.next_frame = None
        self.FRAMES_TO_PERSIST = 10
        self.delay_counter = 0
        self.MIN_SIZE_FOR_MOVEMENT = 750
        cap.set(cv2.CAP_PROP_FPS, fps)

    def print_cam_res(self):
        print(f"camera resolution: ({self.frame_width}x{self.frame_height})")

    def print_text(self, frame, text):
        cv2.putText(frame, str(text), (10, 35), self.font, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        self.frame = frame

    def imshow(self, frame_delta):
        cv2.imshow("frame", np.hstack((frame_delta, self.frame)))

    def gaussianblur(self, frame):
        # Blur it to remove camera noise (reducing false positives)
        gray = cv2.GaussianBlur(frame, (21, 21), 0)
        return gray

    def movement_calc(self, frame):
        """Calculate if there is transient movement in the stream"""
        transient_movement_flag = False
        gray = self.gaussianblur(frame)

        if self.first_frame is None: self.first_frame = gray

        self.delay_counter += 1

        if self.delay_counter > self.FRAMES_TO_PERSIST:
            self.delay_counter = 0
            self.first_frame = self.next_frame

        self.next_frame = gray

        frame_delta, cnts, b = self.proc_images(self.first_frame, self.next_frame)

        # Process images
        for c in cnts:

            # Save the coordinates of all found contours
            (x, y, w, h) = cv2.boundingRect(c)

            # If the contour is too small, ignore it, otherwise, there's transient
            # movement
            if cv2.contourArea(c) > self.MIN_SIZE_FOR_MOVEMENT:
                transient_movement_flag = True
                # Draw a rectangle around big enough movements
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return transient_movement_flag





    @staticmethod
    def proc_images(first_frame, next_frame):
        # Compare the two frames, find the difference
        frame_delta = cv2.absdiff(first_frame, next_frame)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

        # Fill in holes via dilate(), and find contours of the thresholds
        thresh = cv2.dilate(thresh, None, iterations=2)
        (cnts, b) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return frame_delta, cnts, b

    @staticmethod
    def gaussianblur(frame):
        # Blur it to remove camera noise (reducing false positives)
        gray = cv2.GaussianBlur(frame, (21, 21), 0)
        return gray
