import cv2
import queue
import threading

from gi.repository import GObject, GdkPixbuf, Gtk, Gio


def thread(func):
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.start()
        return t

    return wrapper


class Scanner(GObject.Object):
    __gsignals__ = {
        "detected": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "error": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    # pixbuf = GObject.Property(type=GdkPixbuf.Pixbuf)
    outline_qr = GObject.Property(type=bool, default=False)
    cam: cv2.VideoCapture = None
    pixbuf: GdkPixbuf.Pixbuf = None
    frame_queue = queue.Queue()

    def __init__(self):
        super().__init__()

        self.decoder = cv2.QRCodeDetector()

        self.cancellable = None

    def set_widget(self, widget, callback=None):
        widget.add_tick_callback(self.iter)
        if callback:
            widget.add_tick_callback(callback, self)

    def get_pixbuf(self, frame: cv2.typing.MatLike):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        data = frame.tobytes()

        if not data:
            return

        return GdkPixbuf.Pixbuf.new_from_data(
            data,
            GdkPixbuf.Colorspace.RGB,
            False,
            8,
            frame.shape[1],
            frame.shape[0],
            frame.shape[1] * frame.shape[2],
        )

    def open_camera(self):
        self.cam = cv2.VideoCapture(0)
        if self.cam.isOpened() is False:
            self.cam.release()
            raise Exception("No camera connected")

    def read(self):
        _, frame = self.cam.read()

        if isinstance(frame, type(None)):
            print("frame is none")
            return False

        self.pixbuf = self.get_pixbuf(frame)

        ret, points = self.decoder.detect(frame)

        if ret is False:
            return False

        try:
            content, _ = self.decoder.decode(frame, points)
        except Exception as e:
            self.emit("error", "Error while decoding data: ", " ".join(e.args))

        if content == "":
            return False

        self.emit("detected", content)
        return True

    def iter(self, _, frame_clock):
        self.frame_queue.put(frame_clock)
        return True

    @thread
    def start(self, cancellable=Gio.Cancellable.new()):
        if not self.cam:
            print("Camera is None")
            return

        while cancellable.is_cancelled() is False and self.cam.isOpened():
            self.frame_queue.get(block=True)

            if self.read():
                break

    def finalize(self):
        self.cam.release()
