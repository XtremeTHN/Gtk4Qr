import gi

gi.require_versions({"Adw": "1", "Gtk": "4.0"})

from gi.repository import Adw, Gtk, Gio, Gdk
from .scanner import Scanner


class QrPage(Adw.NavigationPage):
    def __init__(self, qr):
        super().__init__(tag="qr", title="Scan")

        self.cancellable = None

        view = Adw.ToolbarView.new()
        view.add_top_bar(Adw.HeaderBar.new())

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_bottom=10,
            margin_start=10,
            margin_end=10,
            margin_top=10,
            valign=Gtk.Align.CENTER,
        )

        self.picture = Gtk.Picture.new()
        frame = Gtk.Frame(child=self.picture)

        qr.set_widget(self.picture)
        qr.bind_property("paintable", self.picture, "paintable")

        btt = Gtk.Button(css_classes=["pill"], label="Stop")

        box.append(frame)
        box.append(btt)

        view.set_content(Adw.Clamp(child=box))
        self.set_child(view)

        self.connect("showing", lambda *_: self.start_qr_scanning(qr))
        self.connect("hiding", lambda *_: self.cancellable.cancel())

        self.start_qr_scanning(qr)

    def start_qr_scanning(self, qr):
        self.cancellable = Gio.Cancellable.new()
        qr.start(self.cancellable)


class ResultsPage(Adw.NavigationPage):
    def __init__(self):
        super().__init__(tag="results", title="Results")

        view = Adw.ToolbarView.new()
        view.add_top_bar(Adw.HeaderBar.new())

        self.label = Gtk.Label(
            margin_bottom=10,
            margin_start=10,
            margin_end=10,
            margin_top=10,
            valign=Gtk.Align.CENTER,
        )

        view.set_content(self.label)
        self.set_child(view)

    def set_result(self, res):
        self.label.set_label(res)


class Window(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)

        self.nav_view = Adw.NavigationView.new()

        qr = Scanner()

        try:
            qr.open_camera()
        except Exception as e:
            print(e)
            self.close()

        self.nav_view.add(QrPage(qr))

        self.results = ResultsPage()
        self.nav_view.add(self.results)

        qr.connect("detected", self.on_detected)
        self.connect("close-request", self.close_request, qr)

        self.set_content(self.nav_view)

    def on_detected(self, qr, content):
        self.nav_view.push_by_tag("results")
        self.results.set_result(content)

    def close_request(self, _, qr):
        qr.finalize()
        return False


class App(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.github.XtremeTHN.QrDecoder",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self):
        Adw.Application.do_activate(self)

        if not self.props.active_window:
            win = Window(self)
            win.present()


def main():
    app = App()
    return app.run()
