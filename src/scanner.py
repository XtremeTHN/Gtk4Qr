import cv2
import queue
import threading

from gi.repository import GObject, GLib, Gdk, Gtk, Gio


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

    outline_qr = GObject.Property(type=bool, default=False)
    cam: cv2.VideoCapture = None
    frame_queue = queue.Queue()
    paintable = GObject.Property(type=Gdk.MemoryTexture)

    def __init__(self):
        super().__init__()

        self.decoder = cv2.QRCodeDetector()

        self.cancellable = None

    def set_widget(self, widget: Gtk.Widget, callback=None):
        widget.add_tick_callback(self.iter)
        if callback:
            widget.add_tick_callback(callback, self)

    def frame_is_null(self, frame):
        return isinstance(frame, type(None))

    def get_texture(self, frame: cv2.typing.MatLike):
        if self.frame_is_null(frame):
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        data = frame.tobytes()

        if not data:
            return
        
        return Gdk.MemoryTexture.new(
            frame.shape[1],
            frame.shape[0],
            Gdk.MemoryFormat.R8G8B8,
            GLib.Bytes.new(data),
            frame.shape[1] * frame.shape[2]
        )

    def open_camera(self):
        self.cam = cv2.VideoCapture(0)
        if self.cam.isOpened() is False:
            self.cam.release()
            raise Exception("No camera connected")

    def read_frame(self) -> cv2.typing.MatLike:
        _, frame = self.cam.read()

        self.paintable = self.get_texture(frame)
        return frame

    def try_detect(self, frame: cv2.typing.MatLike) -> bool:
        if self.frame_is_null(frame):
            print("frame is none")
            return False

        ret, points = self.decoder.detect(frame)

        if ret is False:
            return False

        try:
            content, _ = self.decoder.decode(frame, points)
        except Exception as e:
            self.emit("error", "Error while decoding data: " + " ".join(e.args))

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

            frame = self.read_frame()

            if self.try_detect(frame):
                break

    def finalize(self):
        self.cam.release()
