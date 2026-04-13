#!/usr/bin/env python3
import gi
import os
import shutil
import tempfile
import subprocess
import threading
import re
import atexit
from pathlib import Path
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, GObject, Gdk
import locale
import importlib.util
def load_translations():
    try:
        lang = locale.getdefaultlocale()[0]
        if not lang:
            lang = "en_US"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        loc_file = os.path.join(base_dir, "localization", lang, "package_converter_dictionary.py")
        if not os.path.exists(loc_file):
            loc_file = os.path.join(base_dir, "localization", "en_US", "package_converter_dictionary.py")
        if os.path.exists(loc_file):
            spec = importlib.util.spec_from_file_location("package_converter_dictionary", loc_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "translations"):
                return module.translations
    except Exception as e:
        print(f"Failed to load translations: {e}")
    return {}
_translations = load_translations()
def _(msg):
    return _translations.get(msg, msg)
class PackageConverterWidget(Gtk.Box):
    def __init__(self, hide_sidebar=False, window=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.widgetname = "Package Converter"
        self.widgeticon = "/usr/share/icons/linpaco.svg"
        self.window = window
        self.hide_sidebar = hide_sidebar
        self.selected_file = None
        self.is_converting = False
        self.user_password = None
        self.set_margin_top(12)
        self.set_margin_bottom(50)
        self.set_margin_start(50)
        self.set_margin_end(50)
        self.setup_ui()
    def setup_ui(self):
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_margin_bottom(20)
        icon = Gtk.Image.new_from_file("/usr/share/icons/linpaco.svg")
        icon.set_pixel_size(48)
        header_box.append(icon)
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title_label = Gtk.Label(label=_("Package Converter"))
        title_label.add_css_class("title-2")
        title_label.set_halign(Gtk.Align.START)
        title_box.append(title_label)
        desc_label = Gtk.Label(label=_("Convert .deb/.rpm to Arch Linux Package"))
        desc_label.add_css_class("dim-label")
        desc_label.set_halign(Gtk.Align.START)
        title_box.append(desc_label)
        header_box.append(title_box)
        h_spacer = Gtk.Box()
        h_spacer.set_hexpand(True)
        header_box.append(h_spacer)
        self.btn_toggle_log = Gtk.Button()
        self.btn_toggle_log.set_icon_name("pan-end-symbolic-rtl") 
        self.btn_toggle_log.set_tooltip_text(_("Show/Hide Log"))
        self.btn_toggle_log.connect("clicked", self.on_toggle_log_clicked)
        self.btn_toggle_log.add_css_class("flat")
        self.btn_toggle_log.set_valign(Gtk.Align.CENTER)
        header_box.append(self.btn_toggle_log)
        self.append(header_box)
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        main_box.set_homogeneous(False)
        main_box.set_vexpand(True) 
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        left_box.set_hexpand(True) 
        self.drop_zone = Gtk.Button()
        self.drop_zone.add_css_class("card")
        self.drop_zone.set_size_request(-1, 150)
        self.drop_zone.connect("clicked", self.on_select_file_clicked)
        drop_target = Gtk.DropTarget(actions=Gdk.DragAction.COPY)
        drop_target.set_gtypes([Gio.File])
        drop_target.connect("drop", self.on_file_drop)
        self.drop_zone.add_controller(drop_target)
        drop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        drop_box.set_valign(Gtk.Align.CENTER)
        drop_box.set_halign(Gtk.Align.CENTER)
        dz_icon = Gtk.Image.new_from_icon_name("folder-open-symbolic")
        dz_icon.set_pixel_size(48)
        drop_box.append(dz_icon)
        self.file_label = Gtk.Label(label=_("Select Package File"))
        self.file_label.add_css_class("title-4")
        self.file_label.set_ellipsize(3) 
        drop_box.append(self.file_label)
        dz_hint = Gtk.Label(label=_("Or Drag & Drop file here"))
        dz_hint.add_css_class("dim-label")
        drop_box.append(dz_hint)
        self.drop_zone.set_child(drop_box)
        left_box.append(self.drop_zone)
        options_grp = Adw.PreferencesGroup()
        options_grp.set_title(_("Conversion Options"))
        self.opt_install = Adw.ActionRow()
        self.opt_install.set_title(_("Install after conversion"))
        self.switch_install = Gtk.Switch()
        self.switch_install.set_valign(Gtk.Align.CENTER)
        self.switch_install.set_active(True) 
        self.opt_install.add_suffix(self.switch_install)
        options_grp.add(self.opt_install)
        self.opt_deps = Adw.ActionRow()
        self.opt_deps.set_title(_("Ignore strict dependency checks"))
        self.opt_deps.set_subtitle(_("May result in broken packages if dependencies are missing"))
        self.opt_deps.set_title_lines(2)
        self.switch_deps = Gtk.Switch()
        self.switch_deps.set_valign(Gtk.Align.CENTER)
        self.switch_deps.set_active(True) 
        self.opt_deps.add_suffix(self.switch_deps)
        options_grp.add(self.opt_deps)
        left_box.append(options_grp)
        main_box.append(left_box)
        self.log_revealer = Gtk.Revealer()
        self.log_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_LEFT)
        self.log_revealer.set_reveal_child(False) 
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_box.set_size_request(350, -1) 
        log_label = Gtk.Label(label=_("Conversion Log"))
        log_label.add_css_class("heading")
        log_label.set_halign(Gtk.Align.START)
        right_box.append(log_label)
        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_vexpand(True)
        log_scroll.add_css_class("card")
        self.log_buffer = Gtk.TextBuffer()
        self.log_view = Gtk.TextView.new_with_buffer(self.log_buffer)
        self.log_view.set_editable(False)
        self.log_view.set_monospace(True)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.log_view.set_bottom_margin(10)
        self.log_view.set_top_margin(10)
        self.log_view.set_left_margin(10)
        self.log_view.set_right_margin(10)
        log_scroll.set_child(self.log_view)
        right_box.append(log_scroll)
        self.log_revealer.set_child(right_box)
        main_box.append(self.log_revealer)
        self.append(main_box)
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom_box.set_margin_top(10)
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        bottom_box.append(spacer)
        self.convert_btn = Gtk.Button(label=_("Convert"))
        self.convert_btn.add_css_class("suggested-action")
        self.convert_btn.add_css_class("buttons_all")
        self.convert_btn.set_sensitive(False)
        self.convert_btn.connect("clicked", self.on_convert_clicked)
        bottom_box.append(self.convert_btn)
        self.append(bottom_box)
        self.log_buffer.create_tag("error", foreground="red")
        self.log_buffer.create_tag("success", foreground="green")
        self.log_buffer.create_tag("info", foreground="blue")
    def clear_credentials(self):
        """Clear stored password and sudo timestamp"""
        self.user_password = None
        if sudo_manager:
            sudo_manager.forget_password()
    def cleanup_temp_files(self):
        self.clear_credentials()
    def prompt_for_password(self, callback_arg1, callback_arg2):
        """Prompt user for sudo password using Adw.MessageDialog"""
        root = self.window
        dialog = Adw.MessageDialog(
            heading=_("Authentication Required"),
            body=_("Please enter your password to proceed with the installation."),
            transient_for=root
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("unlock", _("Unlock"))
        dialog.set_response_appearance("unlock", Adw.ResponseAppearance.SUGGESTED)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        entry = Gtk.PasswordEntry()
        entry.set_property("placeholder-text", _("Password"))
        box.append(entry)
        dialog.set_extra_child(box)
        def on_response(dialog, response):
            if response == "unlock":
                pwd = entry.get_text()
                if pwd:
                    if sudo_manager.validate_password(pwd):
                        sudo_manager.set_password(pwd)
                        self.user_password = pwd
                        self.install_package(callback_arg1, callback_arg2)
                    else:
                        err_dlg = Adw.MessageDialog(
                            heading=_("Authentication Failed"),
                            body=_("Incorrect password."),
                            transient_for=self.window
                        )
                        err_dlg.add_response("ok", _("OK"))
                        translate_dialog(err_dlg)
                        err_dlg.present()
            dialog.close()
        dialog.connect("response", on_response)
        def on_entry_activate(widget):
            dialog.response("unlock")
        entry.connect("activate", on_entry_activate)
        translate_dialog(dialog)
        dialog.present()
    def validate_password(self):
        """Validate the sudo password using sudo -S"""
        if not self.user_password:
            return False
        return sudo_manager.validate_password(self.user_password)
    def on_select_file_clicked(self, button):
        self.file_chooser = Gtk.FileDialog(title=_("Select Package File"))
        filters = Gio.ListStore.new(Gtk.FileFilter)
        all_filter = Gtk.FileFilter()
        all_filter.set_name("Package Files (*.deb, *.rpm)")
        all_filter.add_pattern("*.deb")
        all_filter.add_pattern("*.rpm")
        filters.append(all_filter)
        deb_filter = Gtk.FileFilter()
        deb_filter.set_name("Debian Package (*.deb)")
        deb_filter.add_pattern("*.deb")
        filters.append(deb_filter)
        rpm_filter = Gtk.FileFilter()
        rpm_filter.set_name("RPM Package (*.rpm)")
        rpm_filter.add_pattern("*.rpm")
        filters.append(rpm_filter)
        self.file_chooser.set_filters(filters)
        self.file_chooser.open(self.window, None, self.on_file_selected)
    def on_file_selected(self, source, result):
        try:
            f = source.open_finish(result)
            self.set_selected_file(f.get_path())
        except Exception as e:
            print(f"Error selecting file: {e}")
    def on_file_drop(self, target, value, x, y):
        if value:
            self.set_selected_file(value.get_path())
            return True
        return False
    def set_selected_file(self, path):
        if path and (path.endswith(".deb") or path.endswith(".rpm")):
            self.selected_file = path
            filename = os.path.basename(path)
            self.file_label.set_text(filename)
            self.convert_btn.set_sensitive(True)
            self.log_message(f"Selected file: {path}", "info")
        else:
            self.log_message(_("Invalid file extension"), "error")
    def log_message(self, message, tag=None):
        end_iter = self.log_buffer.get_end_iter()
        if tag:
            self.log_buffer.insert_with_tags_by_name(end_iter, message + "\n", tag)
        else:
            self.log_buffer.insert(end_iter, message + "\n")
        adj = self.log_view.get_parent().get_vadjustment()
        GLib.idle_add(lambda: adj.set_value(adj.get_upper() - adj.get_page_size()))
    def on_convert_clicked(self, button):
        if not self.selected_file:
            return
        if self.is_converting:
            return
        self.is_converting = True
        self.convert_btn.set_sensitive(False)
        self.drop_zone.set_sensitive(False)
        self.switch_deps.set_sensitive(False)
        self.switch_install.set_sensitive(False)
        self.log_revealer.set_reveal_child(True)
        self.btn_toggle_log.set_icon_name("pan-start-symbolic-rtl") 
        self.log_buffer.set_text("")
        self.log_message(_("Starting conversion..."), "info")
        threading.Thread(target=self.run_conversion, daemon=True).start()
    def on_toggle_log_clicked(self, button):
        is_revealed = self.log_revealer.get_reveal_child()
        self.log_revealer.set_reveal_child(not is_revealed)
        if not is_revealed: 
            self.btn_toggle_log.set_icon_name("pan-start-symbolic-rtl")
        else: 
             self.btn_toggle_log.set_icon_name("pan-end-symbolic-rtl")
    def run_conversion(self):
        try:
            pkg_path = os.path.abspath(self.selected_file)
            pkg_type = "deb" if pkg_path.endswith(".deb") else "rpm"
            output_dir = os.path.dirname(pkg_path)
            with tempfile.TemporaryDirectory() as temp_dir:
                work_dir = Path(temp_dir)
                GLib.idle_add(self.log_message, _("Extracting package info..."))
                pkgname = "unknown"
                pkgver = "0.0.1"
                pkgrel = "1"
                pkgdesc = "Converted package"
                arch = "any"
                if pkg_type == "deb":
                    cmd_ar = ["ar", "x", pkg_path]
                    res = subprocess.run(cmd_ar, cwd=work_dir, capture_output=True, text=True)
                    if res.returncode != 0:
                        raise Exception(f"Failed to unpack deb: {res.stderr}")
                    control_archive = list(work_dir.glob("control.tar*"))
                    if not control_archive:
                        raise Exception("No control.tar.* found in deb archive")
                    control_archive = control_archive[0]
                    cmd_tar = ["tar", "xf", str(control_archive)]
                    res = subprocess.run(cmd_tar, cwd=work_dir, capture_output=True, text=True)
                    if res.returncode != 0:
                        raise Exception(f"Failed to extract control archive: {res.stderr}")
                    control_file = None
                    if (work_dir / "control").exists():
                        control_file = work_dir / "control"
                    elif (work_dir / "./control").exists():
                        control_file = work_dir / "./control"
                    if not control_file:
                         raise Exception("control file not found after extraction")
                    metadata = {}
                    with open(control_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        current_key = None
                        for line in content.splitlines():
                            if not line: continue
                            if line.startswith(" "):
                                if current_key:
                                    metadata[current_key] += "\n" + line.strip()
                            elif ":" in line:
                                key, val = line.split(":", 1)
                                current_key = key.strip()
                                metadata[current_key] = val.strip()
                    pkgname = metadata.get("Package", pkgname).lower()
                    pkgver_full = metadata.get("Version", pkgver)
                    desc_raw = metadata.get("Description", pkgdesc)
                    pkgdesc = desc_raw.split("\n")[0]
                    architecture = metadata.get("Architecture", arch)
                    # Strip epoch (e.g., "2:1.2.3-1" -> "1.2.3-1")
                    if ":" in pkgver_full:
                        pkgver_full = pkgver_full.split(":", 1)[1]
                    if "-" in pkgver_full:
                        parts = pkgver_full.rsplit("-", 1)
                        pkgver = parts[0]
                        pkgrel = parts[1]
                    else:
                        pkgver = pkgver_full
                    arch_map = {"amd64": "x86_64", "arm64": "aarch64", "all": "any"}
                    arch = arch_map.get(architecture, architecture)
                else: 
                    rpm_cmd_available = shutil.which("rpm") is not None
                    found_metadata = False
                    if rpm_cmd_available:
                        res = subprocess.run(
                            ["rpm", "-qp", "--queryformat", "%{NAME}|%{VERSION}|%{RELEASE}|%{SUMMARY}|%{ARCH}", pkg_path],
                            capture_output=True, text=True
                        )
                        if res.returncode == 0:
                            parts = res.stdout.split("|")
                            if len(parts) >= 5:
                                pkgname = parts[0].lower()
                                pkgver = parts[1]
                                pkgrel = parts[2]
                                pkgdesc = parts[3]
                                arch_rpm = parts[4]
                                arch_map = {"x86_64": "x86_64", "noarch": "any", "aarch64": "aarch64"}
                                arch = arch_map.get(arch_rpm, arch_rpm)
                                found_metadata = True
                        else:
                             GLib.idle_add(self.log_message, f"Warning: rpm command failed: {res.stderr}", "error")
                    if not found_metadata:
                        fname = os.path.basename(pkg_path)
                        if fname.lower().endswith(".rpm"):
                            fname = fname[:-4]
                        GLib.idle_add(self.log_message, _("Warning: Metadata parsed from filename, may be inaccurate."), "info")
                        arch_map = {"x86_64": "x86_64", "noarch": "any", "amd64": "x86_64"}
                        arch = "any"
                        for a_key, a_val in arch_map.items():
                             if fname.endswith(a_key):
                                 arch = a_val
                                 fname = fname[:-len(a_key)].strip("-_.")
                                 break
                        match = re.search(r"\d", fname)
                        if match:
                            idx = match.start()
                            if idx > 0:
                                pkgname = fname[:idx].strip("-_.")
                                ver_part = fname[idx:].strip("-_.")
                                if "-" in ver_part:
                                    parts = ver_part.split("-")
                                    pkgver = parts[0]
                                    if len(parts) > 1:
                                        pkgrel = parts[1]
                                elif "_" in ver_part:
                                    parts = ver_part.split("_")
                                    pkgver = parts[0]
                                    if len(parts) > 1:
                                        pkgrel = parts[1]
                                else:
                                    pkgver = ver_part
                            else:
                                pkgname = fname 
                        else:
                            pkgname = fname
                pkgname = re.sub(r"[^a-z0-9@._+-]", "", pkgname.lower())
                pkgver = re.sub(r"[^a-zA-Z0-9._+]", "_", pkgver)
                if not pkgver: pkgver = "0.0.1"
                if not re.match(r"^[0-9]+(\.[0-9]+)?$", pkgrel):
                     GLib.idle_add(self.log_message, f"Warning: Invalid pkgrel '{pkgrel}', defaulting to '1'.", "info")
                     pkgrel = "1"
                # Sanitize pkgdesc for shell safety
                pkgdesc = re.sub(r"['\"`$]", "", pkgdesc)
                GLib.idle_add(self.log_message, f"Package: {pkgname}\nVersion: {pkgver}-{pkgrel}\nArch: {arch}", "info")
                src_basename = os.path.basename(pkg_path)
                if pkg_type == "deb":
                    extraction_code = f"""    cd "$srcdir"
    bsdtar -xf "{src_basename}"
    cd "$pkgdir"
    bsdtar -xpf "$srcdir"/data.tar*"""
                else:
                    extraction_code = f"""    cd "$pkgdir"
    bsdtar -xpf "$srcdir/{src_basename}""""
                pkgbuild_content = f"""# Auto-generated by Linexin Package Converter
pkgname="{pkgname}-bin"
pkgver="{pkgver}"
pkgrel="{pkgrel}"
pkgdesc='{pkgdesc}'
arch=('{arch}')
url=""
license=('custom')
depends=()
source=("{src_basename}")
md5sums=('SKIP')
noextract=("{src_basename}")
options=('!strip')

package() {{
{extraction_code}
    # Fix permissions
    find . -type d -exec chmod 755 {{}} +
}}
"""
                GLib.idle_add(self.log_message, _("Generating PKGBUILD..."))
                with open(work_dir / "PKGBUILD", "w") as f:
                    f.write(pkgbuild_content)
                shutil.copy(pkg_path, work_dir)
                GLib.idle_add(self.log_message, _("Running makepkg..."))
                env = os.environ.copy()
                env["PKGDEST"] = output_dir 
                cmd_makepkg = ["makepkg", "-f", "--noconfirm"]
                if self.switch_deps.get_active():
                    cmd_makepkg.append("-d")
                process = subprocess.Popen(
                    cmd_makepkg,
                    cwd=work_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        GLib.idle_add(self.log_message, line.strip())
                if process.returncode == 0:
                    GLib.idle_add(self.log_message, _("Conversion successful!"), "success")
                    GLib.idle_add(self.on_conversion_finished, True)
                    if self.switch_install.get_active():
                        GLib.idle_add(self.install_package, pkgname, output_dir)
                else:
                    GLib.idle_add(self.log_message, _("Conversion failed during packaging."), "error")
                    GLib.idle_add(self.on_conversion_finished, False)
        except Exception as e:
            GLib.idle_add(self.log_message, f"Error: {e}", "error")
            import traceback
            traceback.print_exc()
            GLib.idle_add(self.on_conversion_finished, False)
    def on_conversion_finished(self, success):
        self.is_converting = False
        self.convert_btn.set_sensitive(True)
        self.drop_zone.set_sensitive(True)
        self.switch_deps.set_sensitive(True)
        self.switch_install.set_sensitive(True)
        if success:
             self.show_toast(_("Package created successfully!"))
    def install_package(self, pkgname, output_dir):
        if not self.user_password:
            self.prompt_for_password(pkgname, output_dir)
            return
        if not self.validate_password():
            self.clear_credentials() 
            dialog = Adw.MessageDialog(
                heading=_("Authentication Failed"),
                body=_("The password you entered is incorrect. Please try again."),
                transient_for=self.window
            )
            dialog.add_response("ok", _("OK"))
            dialog.set_response_appearance("ok", Adw.ResponseAppearance.DEFAULT)
            dialog.connect("response", lambda d, r: d.close())
            translate_dialog(dialog)
            dialog.present()
            self.log_message(_("Authentication failed."), "error")
            return
        self.log_message(_("Installing package..."), "info")
        try:
            files = list(Path(output_dir).glob("*.pkg.tar.zst"))
            debug_prefix = f"{pkgname}-bin-debug-"
            files = [f for f in files if not f.name.startswith(debug_prefix)]
            if not files:
                 self.log_message(_("Could not find package file to install."), "error")
                 return
            latest_pkg = max(files, key=os.path.getmtime)
            pkg_path = str(latest_pkg)
            self.log_message(f"Installing {latest_pkg.name}...")
            skip_deps = self.switch_deps.get_active()
            threading.Thread(target=self.run_install_command, args=(pkg_path, skip_deps), daemon=True).start()
        except Exception as e:
             self.log_message(f"Failed to launch installer: {e}", "error")
    def run_install_command(self, pkg_path, skip_deps=False):
        if sudo_manager:
            sudo_manager.start_privileged_session()
        try:
            env = sudo_manager.get_env()
            nodeps_flag = " --nodeps" if skip_deps else ""
            cmd = f"{sudo_manager.wrapper_path} pacman -U --noconfirm{nodeps_flag} '{pkg_path}'"
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    GLib.idle_add(self.log_message, line.strip())
            if process.returncode == 0:
                GLib.idle_add(self.log_message, _("Installation successful!"), "success")
                GLib.idle_add(self.show_toast, _("Package installed successfully!"))
            else:
                 GLib.idle_add(self.log_message, _("Installation failed."), "error")
        except Exception as e:
            GLib.idle_add(self.log_message, f"Installation error: {e}", "error")
        finally:
            if sudo_manager:
                sudo_manager.stop_privileged_session()
            self.clear_credentials()
    def show_toast(self, message):
        toast = Adw.Toast.new(message)
        if self.window:
            root = self.window.get_content()
            if hasattr(root, "add_toast"):
                 root.add_toast(toast)
