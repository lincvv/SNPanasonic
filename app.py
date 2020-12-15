import logging
import mmap
import os
import re
import subprocess
import tkinter as tk
import webbrowser
from tkinter import filedialog as fd
from tkinter import messagebox as mb
from main import Dump

# 0x280020 - 19MK3
# 0x600020 - 19MK4

_logger = logging.getLogger("app")
_logger.setLevel(logging.DEBUG)
stream_h = logging.StreamHandler()
stream_h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
stream_h.setLevel(logging.DEBUG)
_logger.addHandler(hdlr=stream_h)


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
        self.msg_save_file = "[*] SAVE FILE\n[*] {0}\n[*] OK"
        self.read_img = None
        self.save_img = None
        self.read_key_img = None
        self.serial_number = None
        self.unlock_cam_img = None
        self.fix_misc_img = None
        self.lab_file = None
        self.text_field = None
        self.new_dump = None
        self.old_dump = None
        self.current_offset = None
        self.label_list = list()
        self.init_app()

    def init_app(self):

        toolbar = tk.Frame(bg="#FFFFFF", bd=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.read_img = tk.PhotoImage(file='img/open.gif')
        btn_read = tk.Button(toolbar, text="Check SN", bg="#FFFFFF", bd=2, command=self.check_sn,
                             compound=tk.TOP, image=self.read_img)
        btn_read.pack(side=tk.LEFT)

        self.save_img = tk.PhotoImage(file='img/save.gif')
        btn_save = tk.Button(toolbar, text="Save SN", bg="#FFFFFF", bd=2, command=self.save_serial,
                             compound=tk.TOP, image=self.save_img)
        btn_save.pack(side=tk.LEFT)

        self.fix_misc_img = tk.PhotoImage(file='img/fix_misc.gif')
        btn_fix_misc = tk.Button(toolbar, text="Fix MISC", bg="#FFFFFF", bd=2, command=self.fix_misc,
                                 compound=tk.TOP, image=self.fix_misc_img)
        btn_fix_misc.pack(side=tk.LEFT)

        self.unlock_cam_img = tk.PhotoImage(file='img/cam.gif')
        btn_unlock_cam = tk.Button(toolbar, text="Fix M1-2", bg="#FFFFFF", bd=2, command=self.unlock_cam,
                                   compound=tk.TOP, image=self.unlock_cam_img)
        btn_unlock_cam.pack(side=tk.LEFT)

        self.read_key_img = tk.PhotoImage(file='img/key.gif')
        btn_read_key = tk.Button(toolbar, text="OEM Key", bg="#FFFFFF", bd=2, command=self.open_file_oem,
                                 compound=tk.TOP, image=self.read_key_img)
        btn_read_key.pack(side=tk.LEFT)

    def clean_label(self):
        """
        Clear all labels
        :return: None
        """

        for val in self.label_list:
            val.destroy()

        self.label_list.clear()

    def open_file(self):
        """
        open the file and return the file path,
        if there is no file -> -1
        :return: path name or -1
        """

        file_path = fd.askopenfile()
        if file_path:
            self.set_label_file(F"File: {os.path.basename(file_path.name)}")
            return file_path.name
        return -1

    def save_file(self, sufix):
        """

        :param sufix: sufix for name file
        :return: file name or None
        """
        file_name_current = os.path.basename(self.new_dump.path_dump).rsplit(".", 1)[0]
        file_types = [('bin', '.bin'), ('all files', '.*')]
        file_name = fd.asksaveasfilename(initialfile=F"{file_name_current}_{sufix}",
                                         filetypes=file_types,
                                         defaultextension=".bin")
        _logger.debug(f"current open file - {file_name}")

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
            self.serial_number = self.get_check_sn(file)
            if self.serial_number is None:
                mb.showinfo("info", "У-п-с.... Голяк :=)")
                self.set_text(text="Голяк", font_txt_field="Verdana 10")
                return None

            self.set_text(
                text=self.serial_number,
                font_txt_field="Arial 10",
            )

    def open_file_oem(self):
        """
        open the file to search for oem key
            and display it
        :return: None
        """

        file = self.open_file()
        if file != -1:
            with open(file, "r+b") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    key = self.pattern_key.findall(mm)

                    if not key:
                        self.set_key_info()

                        return None

                    self.set_text(
                        text=key,
                        text_lbl="OEM Key:",
                        width_field=32,
                        height_field=1,
                        font_txt_field="Verdana 8",
                    )

    def get_check_sn(self, file_name) -> str:
        """
        check the serial number in the dump,
            if you need it then return

        :param file_name: file name
        :return: serial number - str
        """

        sn = None
        self.clean_label()
        self.new_dump = Dump(abspath=file_name)

        for offset in self.OFFSETS:
            try:
                sn = self.new_dump.read_sn(offset=offset)
            except (ValueError, Exception):
                continue
            else:
                self.current_offset = offset
                break
        return sn

    def set_key_info(self):
        """
        message that the key is not found
        :return: None
        """

        msg_info = "OEM Product Key not found"
        mb.showinfo("info", msg_info)
        self.set_text(text="Key not found", font_txt_field="Verdana 10", text_lbl="OEM Key:")

    def set_label_file(self, text):
        """
        display open file name
        :param text: text for display
        :return: None
        """
        if self.lab_file:
            self.lab_file.destroy()
        self.lab_file = tk.Label(root, text=text, fg="grey", font="Verdana 10")
        self.lab_file.place(x=2, y=100)

    def set_text(self, *, text, text_lbl="Current SN:", width_field=15, height_field=1, font_txt_field):
        """
        Displays text in a field
        :param text: text displayed in the field
        :param text_lbl: text label
        :param width_field: width field
        :param height_field: height field
        :param font_txt_field: font for text
        :return: None
        """
        self.clean_label()

        # drawing the text
        label_value = tk.Label(root, text=text_lbl, fg="grey", font="Verdana 10")
        label_value.place(x=2, y=130)
        self.label_list.append(label_value)

        self.text_field = tk.Text(root, width=width_field, height=height_field, font=font_txt_field)
        self.text_field.pack()
        self.text_field.place(x=100, y=130)
        self.text_field.insert(0.1, text)
        self.label_list.append(self.text_field)

    def save_serial(self):
        """
        Saves serial number to file
        :return: None
        """
        if self.new_dump is None:
            mb.showinfo("info", "Not open image for editing Serial Number")
            return
        current_sn = self.text_field.get(0.1, "end")

        file_name = self.save_file(sufix="NEW_SN_")
        if not file_name:
            return
        try:
            self.new_dump.write_sn(file_name=file_name, serial=current_sn)
        except ValueError:
            mb.showerror("error", "у-п-с.... \n incorrect serial number")
        else:
            label_save = tk.Label(root, text=F"[*] Write serial number.....OK", fg="grey", font="Verdana 10")
            label_save.place(x=2, y=160)
            self.label_list.append(label_save)
    # TODO обьединить в один метод

    def fix_misc(self):
        """
        fixes data for MISC driver
        :return: None
        """
        self.clean_label()
        misc_t_old = n_var_full_old = misc_t_new = n_var_full_new = str()

        mb.showinfo("info", "Open old BIOS dump\n")

        old_dump = self.open_file()
        if old_dump == -1:
            mb.showerror("error", "can't open file")
            return
        self.old_dump = Dump(abspath=old_dump)

        # padding_old = self.old_dump.get_fix_data(self.old_dump.list_sig_paddings, padding=True)
        misc_t_old = self.old_dump.get_misc_data(self.old_dump.list_sig_misc_t)
        # n_var_full_old = self.old_dump.find_get_for_fix_data(self.old_dump.list_sig_n_var_full, n_offset=32)

        if not misc_t_old:
            mb.showerror("error", "mutable data not found")
            return

        mb.showinfo("info", "Open new BIOS dump")

        new_dump = self.open_file()
        if new_dump == -1:
            mb.showerror("error", "can't open file")
            return
        self.new_dump = Dump(abspath=new_dump)

        # padding_new = self.new_dump.get_fix_data(self.new_dump.list_sig_paddings, padding=True, save_full=True)
        misc_t_new = self.new_dump.get_misc_data(self.new_dump.list_sig_misc_t, save_full=True)
        # n_var_full_new = self.new_dump.find_get_for_fix_data(self.new_dump.list_sig_n_var_full, n_offset=32)

        if not misc_t_new:
            mb.showerror("error", "mutable data not found")
            return None

        if self.new_dump.is_check_data(misc_t_new, misc_t_old):
            self.new_dump.dump_full = self.new_dump.dump_full.replace(misc_t_new, misc_t_old)
        elif self.new_dump.is_check_data(n_var_full_new, n_var_full_old):
            self.new_dump.dump_full = self.new_dump.dump_full.replace(n_var_full_new, n_var_full_old)
        else:
            mb.showerror("error", "variable data does not match size")

        file_name = self.save_file(sufix="MISC")
        if not file_name:
            return

        with open(file_name, "w+b") as file:
            file.write(self.new_dump.dump_full)
            name_file_save = os.path.basename(file_name).rsplit(".", 1)[0]
            label_save = tk.Label(root, justify=tk.LEFT, text=self.msg_save_file.format(name_file_save),
                                       fg="grey", font="Verdana 10")
            label_save.place(x=5, y=120)
            self.label_list.append(label_save)

    def unlock_cam(self):
        """
        Fix camera
        :return: None
        """
        self.clean_label()

        file = self.open_file()

        if file == -1:
            mb.showerror("error", "can't open file")
            return

        self.new_dump = Dump(abspath=file)

        with open(file, "r+b") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm_dump:

                # amit
                # search nvar mod
                amit_dump = self.new_dump.find_get_data_n_var(mm_instance=mm_dump, signature=self.new_dump.sig_amit,
                                                              size=self.new_dump.ful_size_amit, offset_n=11)

                # n_var_full
                high_n_var_ind = mm_dump.rfind(self.new_dump.sig_nvar_full, int('840048', 16))
                low_n_var_ind = mm_dump.find(self.new_dump.sig_nvar_full, int('840048', 16))
                _logger.debug(F"Find\n"
                              F"high index = {hex(high_n_var_ind)}\n"
                              F"low index = {hex(low_n_var_ind)}")
                mm_dump.seek(high_n_var_ind)

                # read nvar mod from dump
                nvar_mod_dump = mm_dump.read(self.new_dump.ful_size_nvar)

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
                with open("data/NVRAM_NVAR_store_full.ffs", "r+b") as f_nvar:
                    with mmap.mmap(f_nvar.fileno(), 0, access=mmap.ACCESS_READ) as mm_n_var_data:
                        if mm_n_var_data.size() != len(nvar_mod_dump):
                            print(mm_n_var_data.size(), len(nvar_mod_dump))

                        # amit_data
                        # search nvar AMIT for fix pswd
                        amit_data = self.new_dump.find_get_data_n_var(mm_instance=mm_n_var_data,
                                                                      signature=self.new_dump.sig_amit,
                                                                      size=self.new_dump.ful_size_amit,
                                                                      offset_n=11)
                        assert len(amit_data) == len(amit_dump)

                        mm_n_var_data.seek(0)
                        nvar_mod_data = mm_n_var_data.read()

                        # replace nvar AMIT
                        nvar_mod_data = nvar_mod_data.replace(amit_data, amit_dump)

                        assert len(nvar_mod_data) == mm_n_var_data.size()
                        if len(nvar_mod_data) == mm_n_var_data.size():
                            mm_dump.seek(0)
                            self.new_dump.dump_full = mm_dump.read()
                            # self.dump_obj.dump_full = self.dump_obj.dump_full.replace(cam_dump, cam_data)

                            file_name = self.save_file(sufix="CAM")
                            if not file_name:
                                return

                            def download(url):
                                webbrowser.open_new(url)

                            def uefi_tool(event):
                                subprocess.Popen(['uefitool//UEFITool.exe', '-new-tab'])

                            with open(file_name, "w+b") as file:
                                file.write(self.new_dump.dump_full.replace(nvar_mod_dump, nvar_mod_data))

                                name_file_save = os.path.basename(file_name).rsplit(".", 1)[0]

                                label_save = tk.Label(root, justify=tk.LEFT,
                                                      text=self.msg_save_file.format(name_file_save),
                                                      fg="grey", font="Verdana 10")
                                label_save.place(x=2, y=120)
                                self.label_list.append(label_save)
                                # TODO обьединить в один метод

                                var = tk.StringVar()
                                label_info = tk.Label(root, justify=tk.LEFT, textvariable=var,
                                                           fg="orange", font="Verdana 10")
                                var.set("Don't forget to change DXE_driver_UsbCameraCtrlDxe!")
                                label_info.place(x=2, y=180)
                                self.label_list.append(label_info)

                                label_download = tk.Label(root, justify=tk.LEFT, text="Download UsbCameraCtrlDxe",
                                                           fg="blue", cursor="hand2")
                                label_download.pack()
                                label_download.place(x=5, y=200)
                                uri = "https://mega.nz/file/Hx1RUI5J#thRGIXVtGsVisbDJ0VphQ7jrCGhpMW2dyH_Ga0M_4UQ"
                                label_download.bind("<Button-1>", lambda e: download(uri))
                                self.label_list.append(label_download)

                                label_uefitool = tk.Label(root, justify=tk.LEFT, text="Open UEFITool",
                                                          fg="green", cursor="hand2")
                                label_uefitool.pack()
                                label_uefitool.place(x=5, y=220)
                                label_uefitool.bind("<Button-1>", uefi_tool)
                                self.label_list.append(label_uefitool)

                        else:
                            mb.showerror(title="Size Error", message="inconsistency of sizes NVRAM_NVAR")


if __name__ == "__main__":
    root = tk.Tk()
    app = Main(root)
    app.pack()
    root.title("PanasonicTool")
    root.geometry("350x450+400+200")
    root.resizable(False, False)
    root.geometry("360x450")
    icon = tk.PhotoImage(file='img/p_blue.ico')
    root.tk.call('wm', 'iconphoto', root._w, icon)
    root.mainloop()
