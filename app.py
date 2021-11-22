import datetime
import logging
import mmap
import os
import re
import subprocess
import tkinter as tk
import webbrowser
from pathlib import PurePath
from tkinter import filedialog as fd, HORIZONTAL
from tkinter import messagebox as mb
from tkinter.ttk import Progressbar

from main import Dump

# 0x280020 - 19MK3
# 0x600020 - 19MK4

_logger = logging.getLogger("app")
_logger.setLevel(logging.DEBUG)
stream_h = logging.StreamHandler()
stream_h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
stream_h.setLevel(logging.DEBUG)
_logger.addHandler(hdlr=stream_h)


# TODO REFACTORING
class Main(tk.Frame):
    pattern_key = re.compile(rb'\w{5}-\w{5}-\w{5}-\w{5}-\w{5}', flags=re.ASCII)
    OFFSETS = (
        0x280020,
        0x800020,
        0xA00020,
        0xA80020,
        0x580020,
        0x600020,
    )

    def __init__(self, _root, *args, **kwargs):
        super().__init__(_root, *args, **kwargs)
        self.root = _root
        self.home_dir = os.getcwd()
        self.image = None
        self.read_img = None
        self.save_img = None
        self.read_key_img = None
        self.serial_number = None
        self.unlock_cam_img = None
        self.fix_misc_img = None
        self.clear_me_img = None
        self.btn_save = None
        self.field_sn = None
        self.old_dump = None
        self.current_offset = None
        self.list_to_clear = list()
        self.init_app()

    def init_app(self):

        toolbar = tk.Frame(bg="#FFFFFF", bd=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.read_img = tk.PhotoImage(file='img/open.gif')
        btn_read = tk.Button(toolbar, text="Open", bg="#FFFFFF", bd=2, command=self.check_sn,
                             compound=tk.TOP, image=self.read_img)
        btn_read.pack(side=tk.LEFT, padx=2)

        self.fix_misc_img = tk.PhotoImage(file='img/fix_misc.gif')
        btn_fix_misc = tk.Button(toolbar, text="Fix MISC", bg="#FFFFFF", bd=2, command=self.fix_misc,
                                 compound=tk.TOP, image=self.fix_misc_img)
        btn_fix_misc.pack(side=tk.LEFT, padx=2)

        self.unlock_cam_img = tk.PhotoImage(file='img/cam.gif')
        btn_unlock_cam = tk.Button(toolbar, text="Fix M1-2", bg="#FFFFFF", bd=2, command=self.unlock_cam,
                                   compound=tk.TOP, image=self.unlock_cam_img)
        btn_unlock_cam.pack(side=tk.LEFT, padx=2)

        self.read_key_img = tk.PhotoImage(file='img/key.gif')
        btn_read_key = tk.Button(toolbar, text="OEM Key", bg="#FFFFFF", bd=2, command=self.open_file_oem,
                                 compound=tk.TOP, image=self.read_key_img)
        btn_read_key.pack(side=tk.LEFT, padx=2)

        self.clear_me_img = tk.PhotoImage(file='img/me.gif')
        btn_me = tk.Button(toolbar, text="ME", bg="#FFFFFF", bd=2, command=self.clear_me,
                           compound=tk.TOP, image=self.clear_me_img)
        btn_me.pack(side=tk.LEFT, padx=2)

    def create_save_btn(self, *, bg, fg):
        if self.btn_save:
            self.btn_save.destroy()

        self.btn_save = tk.Button(root, text="SAVE", bg=bg, bd=3, command=self.save_serial,
                                  fg=fg, height=1, width=18)

        self.btn_save.pack()
        self.btn_save.place(x=102, y=185)

    def clear_window(self):
        """
        Clear all labels
        :return: None
        """
        for val in self.list_to_clear:
            val.destroy()

        self.list_to_clear.clear()

    def open_file(self):
        """
        open the file and return the file path,
        if there is no file -> -1
        :return: path name or -1
        """
        file_path = fd.askopenfile()
        if file_path:
            return file_path.name
        return -1

    def verbose_log(self, *, txt_label, fg="grey", x=2, y):
        """

        :param txt_label:
        :param fg:
        :param x:
        :param y:
        :return: None
        """
        label_me = tk.Label(root, text=txt_label, fg=fg, font="Verdana 10")
        label_me.place(x=x, y=y)
        self.list_to_clear.append(label_me)

    def clear_me(self):
        """
        :return: None
        """
        self.clear_window()
        if self.image is None:
            mb.showinfo("info", "Not open image for editing Serial Number")
            return

        me_file = self.open_file()
        dir_output = self.image.path
        if me_file != -1:
            self.verbose_log(txt_label=f"[*] ME file: {me_file}", y=230)
            wd = os.getcwd()
            current_dir = PurePath(wd)
            if current_dir.parts[-1] != "fit11":
                os.chdir("fit11")
            output_path = F"{PurePath(dir_output).parent}/{PurePath(dir_output).stem}_CleanME.bin"
            # -w<path>               Overrides the $WorkingDir environment variable.
            # -s<path>               Overrides the $SourceDir environment variable
            fit_proc = subprocess.Popen(f"fit.exe -b -o {output_path} "
                                        f"-f {self.image} "
                                        f"-me {me_file}")
            progress = Progressbar(root, orient=HORIZONTAL, length=100, mode='indeterminate')
            progress.place(x=50, y=260)
            self.list_to_clear.append(progress)

            import time
            while True:
                progress['value'] += 20
                root.update_idletasks()
                time.sleep(0.5)
                fit_status = fit_proc.poll()
                if fit_status is not None:
                    _logger.debug(F"FIT status ==> {fit_status}")
                    if fit_status == 5002:
                        self.verbose_log(txt_label=F"[*] ERROR: Invalid input file type.", y=260, fg="red")
                        break
                    elif fit_proc.poll() == 0:
                        self.verbose_log(txt_label=F"[*] Full Flash image written to ==>", y=260, fg="green")
                        self.verbose_log(txt_label=F"\t{output_path}", y=280)
                        mv_source_dir = PurePath(self.image.path)
                        mv_destination_dir = PurePath.joinpath(PurePath(output_path).parent,
                                                               datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
                        _logger.debug(F"build dir ==> {mv_destination_dir}")
                        subprocess.run(F"mkdir {mv_destination_dir}")
                        subprocess.run(F"mv {mv_source_dir.stem} {mv_destination_dir}")
                        break
                    else:
                        self.verbose_log(txt_label=F"[*] ERROR: Build Failed!", y=260, fg="red")
                        break

    def choice_dir(self, sufix):
        """
        :param sufix: sufix for name file
        :return: file name or None
        """
        file_name_current = os.path.basename(self.image.path).rsplit(".", 1)[0]
        file_types = [('bin', '.bin'), ('all files', '.*')]
        file_name = fd.asksaveasfilename(initialfile=F"{file_name_current}_{sufix}", filetypes=file_types,
                                         defaultextension=".bin")
        _logger.debug(f"current choice file - {file_name}")

        if file_name:
            return file_name
        else:
            mb.showerror("error", "could not open file")
            return

    def check_sn(self):
        """
        open file to search serial number
        :return: None
        """

        file = self.open_file()
        if file != -1:
            font = "Verdana 10"
            self.field_sn = tk.Text(root, width=17, height=1.4, font=font, bd=3)
            label_sn = tk.Label(root, text="Current SN:", fg="grey", font=font)
            self.serial_number = self.get_serial_number(file)
            if self.serial_number is None:
                mb.showinfo("info", "У-п-с.... Голяк :=)")
                self.create_text_field(obj_label=label_sn, obj_field=self.field_sn, txt_field="Голяк")
                return None

            self.create_text_field(obj_label=label_sn, obj_field=self.field_sn, txt_field=self.serial_number)
            self.create_save_btn(fg="green", bg="#FFFFFF")

    def get_serial_number(self, file_name) -> str:
        """
        check the serial number in the dump,
            if you need it then return

        :param file_name: file name
        :return: serial number - str
        """
        sn = None
        self.clear_window()
        self.image = Dump(abspath=file_name)
        lbl_open_file = tk.Label(root, text=F"File: {self.image.path}", fg="grey", font="Verdana 10")
        lbl_model = tk.Label(root, text=F"Model: {self.get_platform()}", fg="grey", font="Verdana 10")
        lbl_open_file.place(x=2, y=100)
        lbl_model.place(x=2, y=130)

        for offset in self.OFFSETS:
            try:
                sn = self.image.read_sn(offset=offset)
            except (ValueError, Exception):
                continue
            else:
                self.current_offset = offset
                break
        return sn

    def open_file_oem(self):
        """
        open the file to search for oem key
            and display it
        :return: None
        """
        with open(self.image.path, "r+b") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                key = self.pattern_key.findall(mm)
                font = "Verdana 9"
                y_tf = 230
                field_oem = tk.Text(root, width=30, height=1.4, font=font, bd=2)
                label_oem = tk.Label(root, text="OEM Key:", fg="grey", font=font)
                if not key:
                    msg_info = "OEM Product Key not found"
                    mb.showinfo("info", msg_info)
                    self.create_text_field(obj_label=label_oem, obj_field=field_oem,
                                           txt_field="Key not found", y_tf=y_tf)

                    return

                self.create_text_field(obj_label=label_oem, obj_field=field_oem, txt_field=key[0], y_tf=y_tf)
                self.list_to_clear.extend([field_oem, label_oem])

    def create_text_field(self, *, obj_field, txt_field, obj_label=None, x_tf=2, y_tf=160):
        """
        Displays text in a field
        :param txt_field: text displayed in the field
        :param obj_field: text label
        :param obj_label: width field
        :param x_tf:
        :param y_tf:
        :return: None
        """
        self.clear_window()

        if obj_label:
            # drawing the text
            obj_label.place(x=x_tf, y=y_tf)
            x_tf = 100

        obj_field.pack()
        obj_field.place(x=x_tf, y=y_tf)
        obj_field.insert(0.1, txt_field)

    def save_serial(self):
        """
        Saves serial number to file
        :return: None
        """
        self.clear_window()
        if self.image is None:
            mb.showinfo("info", "Not open image for editing Serial Number")
            return
        current_sn = self.field_sn.get(0.1, "end")

        file_name = self.choice_dir(sufix="new_sn_")
        if not file_name:
            return
        try:
            self.image.write_sn(file_name=file_name, serial=current_sn)
        except ValueError:
            mb.showerror("error", "у-п-с.... \n incorrect serial number")
        else:
            label_save = tk.Label(root, text=F"[*] Write serial number.....OK", fg="green", font="Verdana 10")
            label_save.place(x=2, y=220)
            self.list_to_clear.append(label_save)
            self.create_save_btn(fg="black", bg="#32a852")

    def get_platform(self):
        with open(self.image.path, "r+b") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                for sig_padding, size in self.image.list_sig_paddings:
                    if (mm.find(sig_padding, int('580000', 16))) != -1:
                        name_model = sig_padding[4:10].decode("utf-8")
                        _logger.debug(name_model)
                        return name_model

    def print_log_write_file(self, file_name):
        self.verbose_log(txt_label=F"[*] Modify image written to ==>", y=260, fg="green")
        self.verbose_log(txt_label=F"\t{file_name}", y=280)

    def fix_misc(self):
        """
        fixes data for MISC driver
        :return: None
        """
        self.clear_window()
        misc_t_old = n_var_full_old = misc_t_new = n_var_full_new = str()

        mb.showinfo("info", "Open old BIOS dump\n")

        old_dump = self.open_file()
        if old_dump == -1:
            mb.showerror("error", "can't open file")
            return

        self.old_dump = Dump(abspath=old_dump)

        misc_t_old = self.old_dump.get_misc_data()
        # n_var_full_old = self.old_dump.find_get_for_fix_data(self.old_dump.list_sig_n_var_full, n_offset=32)

        if not misc_t_old:
            mb.showerror("error", "mutable data not found")
            return

        misc_t_new = self.image.get_misc_data(save_full=True)
        # n_var_full_new = self.image.find_get_for_fix_data(self.new_dump.list_sig_n_var_full, n_offset=32)

        if not misc_t_new:
            mb.showerror("error", "mutable data not found")
            return None

        if self.image.is_check_data(misc_t_new, misc_t_old):
            self.image.dump_full = self.image.dump_full.replace(misc_t_new, misc_t_old)
        elif self.image.is_check_data(n_var_full_new, n_var_full_old):
            self.image.dump_full = self.image.dump_full.replace(n_var_full_new, n_var_full_old)
        else:
            mb.showerror("error", "variable data does not match size")

        file_name = self.choice_dir(sufix="misc")
        if not file_name:
            return

        with open(file_name, "w+b") as file:
            file.write(self.image.dump_full)
            # name_file_save = os.path.basename(file_name).rsplit(".", 1)[0]
            self.print_log_write_file(file_name)

    def verbose_cam(self, file_name):

        def download(url):
            webbrowser.open_new(url)

        def uefi_tool(event):
            subprocess.Popen(['uefitool//UEFITool.exe', '-new-tab'])

        self.print_log_write_file(file_name)

        var = tk.StringVar()
        label_info = tk.Label(root, justify=tk.LEFT, textvariable=var,
                              fg="orange", font="Verdana 10")
        var.set("Don't forget to change DXE_driver_UsbCameraCtrlDxe!")
        label_info.place(x=2, y=310)
        self.list_to_clear.append(label_info)

        label_download = tk.Label(root, justify=tk.LEFT, text="Download UsbCameraCtrlDxe",
                                  fg="blue", cursor="hand2")
        label_download.pack()
        label_download.place(x=5, y=330)
        uri = "https://mega.nz/file/Hx1RUI5J#thRGIXVtGsVisbDJ0VphQ7jrCGhpMW2dyH_Ga0M_4UQ"
        label_download.bind("<Button-1>", lambda e: download(uri))
        self.list_to_clear.append(label_download)

        label_uefitool = tk.Label(root, justify=tk.LEFT, text="Open UEFITool",
                                  fg="green", cursor="hand2")
        label_uefitool.pack()
        label_uefitool.place(x=5, y=350)
        label_uefitool.bind("<Button-1>", uefi_tool)
        self.list_to_clear.append(label_uefitool)

    def unlock_cam(self):
        """
        Fix camera
        :return: None
        """
        self.clear_window()

        with open(self.image.path, "r+b") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm_dump:

                # amit
                # search nvar mod
                amit_dump = self.image.find_get_data_n_var(mm_instance=mm_dump, signature=self.image.sig_amit,
                                                           size=self.image.ful_size_amit, offset_n=11)

                # n_var_full
                high_n_var_ind = mm_dump.rfind(self.image.sig_nvar_full, int('840048', 16))
                low_n_var_ind = mm_dump.find(self.image.sig_nvar_full, int('840048', 16))
                _logger.debug(F"Find\n"
                              F"high index = {hex(high_n_var_ind)}\n"
                              F"low index = {hex(low_n_var_ind)}")
                mm_dump.seek(high_n_var_ind)

                # read nvar mod from dump
                nvar_mod_dump = mm_dump.read(self.image.ful_size_nvar)

                # cam driver
                # cam_dump_ind = mm_dump.find(self.dump_obj.sig_drv_cam)
                # print(hex(cam_dump_ind))
                # mm_dump.seek(cam_dump_ind)
                # cam_dump = mm_dump.read(self.dump_obj.ful_size_drv_cam)
                #
                # with open("data/DXE_driver_UsbCameraCtrlDxe.ffs", "r+b") as f_nvar:
                #     with mmap.mmap(f_nvar.fileno(), 0, access=mmap.ACCESS_READ) as mm_cam_data:
                #         cam_data = mm_cam_data.read()
                #         if len(cam_dump) != mm_cam_data.size():
                #             print(2)

                # read nvar mod from data/NVRAM_NVAR_store_full.ffs
                os.chdir(self.home_dir)
                with open("data/NVRAM_NVAR_store_full.ffs", "r+b") as f_nvar:
                    with mmap.mmap(f_nvar.fileno(), 0, access=mmap.ACCESS_READ) as mm_n_var_data:
                        if mm_n_var_data.size() != len(nvar_mod_dump):
                            print(mm_n_var_data.size(), len(nvar_mod_dump))

                        # amit_data
                        # search nvar AMIT for fix pswd
                        amit_data = self.image.find_get_data_n_var(mm_instance=mm_n_var_data,
                                                                   signature=self.image.sig_amit,
                                                                   size=self.image.ful_size_amit,
                                                                   offset_n=11)
                        assert len(amit_data) == len(amit_dump)

                        mm_n_var_data.seek(0)
                        nvar_mod_data = mm_n_var_data.read()

                        # replace nvar AMIT
                        nvar_mod_data = nvar_mod_data.replace(amit_data, amit_dump)

                        assert len(nvar_mod_data) == mm_n_var_data.size()
                        if len(nvar_mod_data) == mm_n_var_data.size():
                            mm_dump.seek(0)
                            self.image.dump_full = mm_dump.read()
                            # self.dump_obj.dump_full = self.dump_obj.dump_full.replace(cam_dump, cam_data)

                            file_name = self.choice_dir(sufix="CAM")
                            if not file_name:
                                return

                            with open(file_name, "w+b") as file:
                                file.write(self.image.dump_full.replace(nvar_mod_dump, nvar_mod_data))
                                self.verbose_cam(file_name)

                        else:
                            mb.showerror(title="Size Error", message="inconsistency of sizes NVRAM_NVAR")


if __name__ == "__main__":
    root = tk.Tk()
    app = Main(root)
    app.pack()
    root.title("PanasonicTool 1.4b")
    root.geometry("350x450+400+200")
    root.resizable(False, False)
    root.geometry("380x450")
    icon = tk.PhotoImage(file='img/p_blue.ico')
    root.tk.call('wm', 'iconphoto', root._w, icon)
    root.mainloop()
