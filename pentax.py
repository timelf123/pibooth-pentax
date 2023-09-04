import pibooth
from pibooth.utils import LOGGER
from pibooth.camera.base import BaseCamera
from pibooth import camera
import subprocess
from PIL import Image
import glob

__version__ = "1.0.0"

class PkTriggerCordCliCamera(BaseCamera):
    def __init__(self, camera_proxy=None):
        super().__init__(camera_proxy)

    def cleanup_old_images(self, basename):
        for file_path in glob.glob('/tmp/{}_*'.format(basename)):
            os.remove(file_path)

    def capture(self, effect=None):
        self.cleanup_old_images("pentax_capture")
        image_path = "/tmp/pentax_capture.jpg"
        cmd = ["pktriggercord-cli", "-f", "-o", image_path]
        subprocess.call(cmd)
        image = Image.open("/tmp/pentax_capture-0000.jpg")
        self._captures.append(image)

    def _post_process_capture(self, capture_data):
        return capture_data  # Already a PIL Image object in this case

class HybridRpiAndPkCamera(BaseCamera):
    
    def __init__(self, rpi_camera_proxy, pk_camera_proxy):
        super().__init__(None)  # No common camera proxy for hybrid camera
        self._rpi_cam = camera.RpiCamera(rpi_camera_proxy)
        self._pk_cam = PkTriggerCordCliCamera(pk_camera_proxy)
        self._rpi_cam._captures = self._captures  # Share captures dict between cameras
        self._pk_cam._captures = self._captures  # Share captures dict between cameras

    def _post_process_capture(self, capture_data):
        # You can call the post_process of individual cameras
        # or define new behavior specific to the hybrid camera

        # Here I'm calling the post_process of the pk_camera for demonstration
        return self._pk_cam._post_process_capture(capture_data)

    def initialize(self, *args, **kwargs):
        self._rpi_cam.initialize(*args, **kwargs)
        # No initialization for pk_cam as it may not have the same methods

    def capture(self, *args, **kwargs):
        self._pk_cam.capture(*args, **kwargs)  # Use Pentax for capturing stills

    def preview(self, window, flip=True):
        self._rpi_cam.preview(window, flip)  # Use RPi for preview

    def preview_wait(self, timeout, alpha=60):
        self._rpi_cam.preview_wait(timeout, alpha)  # Use RPi for preview wait

    def preview_countdown(self, timeout, alpha=60):
        self._rpi_cam.preview_countdown(timeout, alpha)  # Use RPi for countdown

    def stop_preview(self):
        self._rpi_cam.stop_preview()  # Stop RPi preview

    def quit(self):
        self._rpi_cam.quit()  # Quit RPi camera


@pibooth.hookimpl
def pibooth_setup_camera():
    rpi_cam_proxy = camera.get_rpi_camera_proxy()
    pk_cam_proxy = PkTriggerCordCliCamera()

    if rpi_cam_proxy and pk_cam_proxy:
        LOGGER.info("Configuring hybrid camera (Picamera + PkTriggerCordCli) ...")
        return HybridRpiAndPkCamera(rpi_cam_proxy, pk_cam_proxy)
    elif pk_cam_proxy:
        LOGGER.info("Configuring PkTriggerCordCli camera ...")
        return PkTriggerCordCliCamera(pk_cam_proxy)
    elif rpi_cam_proxy:
        LOGGER.info("Configuring Picamera camera ...")
        return camera.RpiCamera(rpi_cam_proxy)
