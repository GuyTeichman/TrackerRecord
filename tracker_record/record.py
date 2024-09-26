import time
import warnings
from pathlib import Path

import cv2
import numpy as np
import tqdm
from harvesters.core import Harvester
from harvesters.util.pfnc import mono_location_formats

MAX_FPS = 20


class TrackerRecorder:
    FOURCC = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')

    def __init__(self, cti_paths: list[str]):
        self.cti_paths = cti_paths
        print("Connecting to camera...")
        self.harvester = self._get_harvester()
        self.acquirer = self._get_acquirer()


    def get_writer(self, filename:Path,fps:int):
        width, height = self.get_dims()
        print(f"Capturing video in {height} * {width}")
        out = cv2.VideoWriter(filename.as_posix(), self.FOURCC, fps, (width, height), isColor=False)
        return out

    def run(self):
        fps = self.get_fps()
        recording_len = self.get_recording_len()
        video_filename = self.get_save_path()
        print(f"Video file will be captured in {fps} fps for {recording_len} seconds, "
              f"and will be saved to {video_filename}.")

        out = self.get_writer(video_filename,fps)
        try:
            for i in tqdm.tqdm(range(int(np.ceil(fps * recording_len))), desc='capturing video...',
                               unit='frames'):
                start_time = time.time()
                gray_1channel = self.get_frame()
                out.write(gray_1channel)
                if (time.time() - start_time) > (1 / fps):
                    warnings.warn("Camera appears to capture in a lower framerate than was requested. ")
                else:
                    while (time.time() - start_time) < (1 / fps):
                        pass
        except KeyboardInterrupt:
            print(f'Recording stopped prematurely after {i / fps} seconds. Saving video to output file.')
        finally:
            # close out the video writer
            out.release()
            self.stop()
            print(f"Video file successfully saved to {video_filename}.")

    def stop(self):
        self.acquirer.stop()
    def get_dims(self):
        with self.acquirer.fetch() as buffer:
            component = buffer.payload.components[0]
            width = component.width
            height = component.height
            return width, height

    def get_frame(self):
        with self.acquirer.fetch() as buffer:
            component = buffer.payload.components[0]
            width = component.width
            height = component.height
            data_format = component.data_format

            if data_format in mono_location_formats:
                gray_1channel = component.data.reshape(height, width)
            else:
                raise AssertionError
            return gray_1channel.copy()

    @staticmethod
    def _is_legal_fps(fps: float):
        return MAX_FPS >= fps > 0

    def get_fps(self) -> int:
        fps = float(input("Please enter the preferred video framerate in frames per second (fps):\n"))
        while not self._is_legal_fps(fps):
            fps = float(input(f"The camera can only capture in framerates up to {MAX_FPS} fps. \n"
                              "Please enter the preferred video framerate in frames per second (fps):\n"))
        return fps

    def get_recording_len(self):
        recording_length_sec = int(input("Please enter the chosen recording length in seconds:\n"))
        return recording_length_sec

    def get_save_path(self):
        save_path = Path(input("Please enter the full path of the save path"))
        return save_path

    def _get_harvester(self):
        h = Harvester()
        for cti_path in self.cti_paths:
            h.add_file(cti_path)
        h.update()
        return h

    def _get_acquirer(self):
        ia = self.harvester.create()
        ia.start()
        return ia


if __name__ == '__main__':
    recorder = TrackerRecorder()
    recorder.run()
