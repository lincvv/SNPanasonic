import mmap
import os
import re
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import messagebox as mb
from main import Dump

# 0x280020 - 19MK3
# 0x600020 - 19MK4


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

    def __init__(self, _root):
        super().__init__(_root)
        self.read_img = None
        self.save_img = None
        self.read_key_img = None
        self.serial_number = None
        self.unlock_cam_img = None
        self.fix_misc_img = None
        self.lab_file = None
        self.label_save = None
        self.label_value = None
        self.text_filed = None
        self.dump_obj = None
        self.current_offset = None
        self.init_main()

    def init_main(self):

        toolbar = tk.Frame(bg="#FFFFFF", bd=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.read_img = tk.PhotoImage(file='img/open.gif')
        btn_read = tk.Button(toolbar, text="Check SN", bg="#FFFFFF", bd=2, command=self.open_file_sn,
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

    def get_check_sn(self, file_name) -> str:
        """ check the serial number in the dump,
            if you need it then return """

        sn = None
        self.dump_obj = Dump(name_dump=file_name)

        for offset in self.OFFSETS:
            try:
                sn = self.dump_obj.read_sn(offset=offset)
            except (ValueError, Exception):
                continue
            else:
                self.current_offset = offset
                break
        return sn

    def open_file(self):
        """ open the file and return the file path,
        if there is no file, return -1 """

        file_path = fd.askopenfile()
        if file_path:
            self.set_label_file(F"File: {os.path.basename(file_path.name)}")
            return file_path.name
        return -1

    def set_key_info(self):
        """ message that the key is not found """

        msg_info = "OEM Product Key not found"
        mb.showinfo("info", msg_info)
        self.set_text(text_field="Key not found", font_txt_field="Verdana 10", text_lbl="OEM Key:")

    def fix_misc(self):
        old_dump = self.open_file()
        misk_t_old, misk_b_old = Dump(name_dump=old_dump).get_misc_data()

        new_dump = self.open_file()
        self.dump_obj = Dump(name_dump=new_dump)
        misk_t_new, misk_b_new = self.dump_obj.get_misc_data(save_full=True)

        if len(misk_b_new) == len(misk_b_old) and len(misk_t_new) == len(misk_t_old):
            with open("data/test.bin", "w+b") as f_test:
                self.dump_obj.dump_full = self.dump_obj.dump_full.replace(misk_t_old, misk_t_new)
                f_test.write(self.dump_obj.dump_full.replace(misk_b_old, misk_b_new))

    def unlock_cam(self):
        """

        :return:
        """

        file = self.open_file()
        self.dump_obj = Dump(name_dump=file)
        if file != -1:
            with open(file, "r+b") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    # amit
                    amit_dump = self.dump_obj.find_get_data_n_var(mm_instance=mm, signature=self.dump_obj.sig_amit,
                                                                  size=self.dump_obj.ful_size_amit)

                    # misc
                    # misk_t_dump = self.dump_obj.find_get_data_n_var(mm_instance=mm, signature=self.dump_obj.sig_misc_t,
                    #                                                 size=self.dump_obj.ful_size_misk_t)
                    #
                    # misk_b_dump = self.dump_obj.find_get_data_n_var(mm_instance=mm, signature=self.dump_obj.sig_misc_b,
                    #                                                 size=self.dump_obj.ful_size_misk_b)

                    # nvar_full
                    nvar_ind = mm.rfind(self.dump_obj.sig_nvar_full, int('840048', 16))
                    r_nvar_ind = mm.find(self.dump_obj.sig_nvar_full, int('840048', 16))
                    print(hex(nvar_ind), hex(r_nvar_ind))
                    mm.seek(nvar_ind)
                    nvar_mod_dump = mm.read(self.dump_obj.ful_size_nvar)

                    # cam driver
                    # cam_dump_ind = mm.find(self.dump_obj.sig_drv_cam)
                    # print(hex(cam_dump_ind))
                    # mm.seek(cam_dump_ind)
                    # cam_dump = mm.read(self.dump_obj.ful_size_drv_cam)
                    #
                    # with open("data/DXE_driver_UsbCameraCtrlDxe.ffs", "r+b") as f_nvar:
                    #     with mmap.mmap(f_nvar.fileno(), 0, access=mmap.ACCESS_READ) as mm_cam_data:
                    #         cam_data = mm_cam_data.read()
                    #         if len(cam_dump) != mm_cam_data.size():
                    #             print(2)

                    with open("data/NVRAM_NVAR_store_full.ffs", "r+b") as f_nvar:
                        with mmap.mmap(f_nvar.fileno(), 0, access=mmap.ACCESS_READ) as mm_nvar_data:
                            if mm_nvar_data.size() != len(nvar_mod_dump):
                                print(1)

                            # amit_data
                            amit_data = self.dump_obj.find_get_data_n_var(mm_instance=mm_nvar_data,
                                                                          signature=self.dump_obj.sig_amit,
                                                                          size=self.dump_obj.ful_size_amit)
                            assert len(amit_data) == len(amit_dump)

                            # misc_data
                            # misk_t_data = self.dump_obj.find_get_data_n_var(mm_instance=mm_nvar_data,
                            #                                                 signature=self.dump_obj.sig_misc_t,
                            #                                                 size=self.dump_obj.ful_size_misk_t)
                            #
                            # misk_b_data = self.dump_obj.find_get_data_n_var(mm_instance=mm_nvar_data,
                            #                                                 signature=self.dump_obj.sig_misc_b,
                            #                                                 size=self.dump_obj.ful_size_misk_b)

                            # assert len(misk_b_dump) == len(misk_b_data)
                            # assert len(misk_t_dump) == len(misk_t_data)

                            mm_nvar_data.seek(0)
                            nvar_mod_data = mm_nvar_data.read()

                            nvar_mod_data = nvar_mod_data.replace(amit_data, amit_dump)
                            # nvar_mod_data = nvar_mod_data.replace(misk_b_data, misk_b_dump)
                            # nvar_mod_data = nvar_mod_data.replace(misk_t_data, misk_t_dump)

                            if len(nvar_mod_data) == mm_nvar_data.size():
                                mm.seek(0)
                                self.dump_obj.dump_full = mm.read()
                                # self.dump_obj.dump_full = self.dump_obj.dump_full.replace(cam_dump, cam_data)
                                
                                file_name_current = os.path.basename(self.dump_obj.path_dump).rsplit(".", 1)[0]
                                file_types = [('bin', '.bin'), ('all files', '.*')]
                                file_name = fd.asksaveasfilename(initialfile=F"{file_name_current}-CAM",
                                                                 filetypes=file_types,
                                                                 defaultextension=".bin")
                                if not file_name:
                                    return        
                                with open(file_name, "w+b") as file:
                                    file.write(self.dump_obj.dump_full.replace(nvar_mod_dump, nvar_mod_data))
                                    self.label_save_ = tk.Label(root, text="Save file...OK",
                                                               fg="grey", font="Verdana 10")
                                    self.label_save_.place(x=2, y=160)
                                    #
                                    self.label_warning = tk.Label(root, text="Don't forget to change "
                                                                             "DXE_driver_UsbCameraCtrlDxe!",
                                                                  fg="grey", font="Verdana 10")
                                    self.label_warning.place(x=5, y=260)

                            else:
                                print("error")

    def open_file_oem(self):
        """ open the file to search for oem key
            and display it """

        file = self.open_file()
        if file != -1:
            with open(file, "r+b") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    key = self.pattern_key.findall(mm)

                    if not key:
                        self.set_key_info()

                        return

                    self.set_text(
                        text_field=key,
                        text_lbl="OEM Key:",
                        width_field=32,
                        height_field=1,
                        font_txt_field="Verdana 8"
                    )

    def open_file_sn(self):
        """ open file to search serial number """

        file = self.open_file()
        if file != -1:
            self.serial_number = self.get_check_sn(file)
            if self.serial_number is None:
                mb.showinfo("info", "У-п-с.... Голяк :=)")
                self.set_text(text_field="Голяк", font_txt_field="Verdana 10")
                return

            self.set_text(
                text_field=self.serial_number,
                font_txt_field="Arial 10"
            )

    def set_text(self, *, text_field, text_lbl="Current SN:", width_field=15, height_field=1, font_txt_field):
        # delete old text
        if self.label_save:
            self.label_save.destroy()
        if self.label_value:
            self.label_value.destroy()
        if self.text_filed:
            self.text_filed.destroy()

        # drawing the text
        self.label_value = tk.Label(root, text=text_lbl, fg="grey", font="Verdana 10")
        self.label_value.place(x=2, y=130)

        self.text_filed = tk.Text(root, width=width_field, height=height_field, font=font_txt_field)
        self.text_filed.pack()
        self.text_filed.place(x=100, y=130)
        self.text_filed.insert(0.1, text_field)

    def set_label_file(self, text):
        # display open file name
        if self.lab_file:
            self.lab_file.destroy()
        self.lab_file = tk.Label(root, text=text, fg="grey", font="Verdana 10")
        self.lab_file.place(x=2, y=100)

    def save_serial(self):
        if self.dump_obj is None:
            mb.showinfo("info", "Not open image for editing Serial Number")
            return
        current_sn = self.text_filed.get(0.1, "end")
        file_name_current = os.path.basename(self.dump_obj.path_dump).rsplit(".", 1)[0]
        file_types = [('bin', '.bin'), ('all files', '.*')]
        file_name = fd.asksaveasfilename(initialfile=F"{file_name_current}-NEW_SN", filetypes=file_types,
                                         defaultextension=".bin")
        if not file_name:
            return
        try:
            self.dump_obj.write_sn(file_name=file_name, serial=current_sn)
        except ValueError:
            mb.showerror("error", "у-п-с.... \n incorrect serial number")
        else:
            self.label_save = tk.Label(root, text=F"Write serial number.....OK", fg="grey", font="Verdana 10")
            self.label_save.place(x=2, y=160)


if __name__ == "__main__":
    root = tk.Tk()
    app = Main(root)
    app.pack()
    root.title("PanasonicTool")
    root.geometry("350x450+400+200")
    root.resizable(False, False)
    icon = tk.PhotoImage(file='img/p_blue.ico')
    root.tk.call('wm', 'iconphoto', root._w, icon)
    root.mainloop()
