import binascii
import logging
import mmap


_logger = logging.getLogger("app.main")
_logger.setLevel(logging.DEBUG)


class Dump:

    def __init__(self, abspath):
        self.path_dump = abspath
        self.list_sig_paddings = [
            (bytearray(b'\x4D\x45\x49\x5F\x46\x5A\x47\x31\x2D\x34\x00\x00\x00\x00\x00\00'), '40000'),
            (bytearray(b'\x4D\x45\x49\x5F\x43\x46\x31\x39\x2D\x36\x00\x00\x00\x00\x00\x00'), '30000'),
            (bytearray(b'\x4D\x45\x49\x5F\x43\x46\x31\x39\x2D\x37\x00\x00\x00\x00\x00\x00'), '30000'),
            (bytearray(b'\x4D\x45\x49\x5F\x46\x5A\x47\x31\x2D\x35\x00\x00\x00\x00\x00\x00'), '40000')
        ]
        self.list_sig_misc_t = [
            (bytearray(b'\x4E\x56\x41\x52\x8A\x00\xFF\xFF\xFF\x88\x4D\x45\x49\x5F\x43\x46'), '8A'),
            (bytearray(b'\x4E\x56\x41\x52\x8A\x00\xFF\xFF\xFF\x88\x4D\x45\x49\x5F\x46\x5A'), '8A'),
            (bytearray(b'\x4E\x56\x41\x52\x9B\x00\xFF\xFF\xFF\x83\x02\x4D\x69\x73\x63\x54'), '9B'),
            (bytearray(b'\x4E\x56\x41\x52\x9B\x00\xFF\xFF\xFF\x83\x03\x4D\x69\x73\x63\x54'), '9B'),
        ]
        self.list_sig_n_var_full = [
            (bytearray(b'\x00\x00\x04\x00\x00\x00\x00\x00\x5F\x46\x56\x48\xFF\xFE\x04\x00'), '40000')
        ]
        self.sn_full_bytes = bytearray()
        self.sig_amit = bytearray(b'\x41\x4D\x49\x54\x53\x45\x53\x65\x74\x75\x70')
        self.vol_dxe = bytearray(b'\x93\xFD\x21\x9E\x72\x9C\x15\x4C\x8C\x4B\xE7\x7F\x1D\xB2\xD7\x92')
        self.sig_drv_cam = bytearray(b'\x00\x51\x57\xD5\x16\xD8\x82\x43\x97\x26\xB1\xDC\x5F\x1D\xF3\x77')
        self.sig_misc_b = bytearray(b'\x4E\x56\x41\x52\x3B\x04\xFF\xFF\xFF\x88\x0F\x00\x86\x00\x00\x00')
        self.sig_misc_t_g1_5 = bytearray(b'\x4E\x56\x41\x52\x8A\x00\xFF\xFF\xFF\x88\x4D\x45\x49\x5F\x46\x5A')
        self.sig_nvar_full = bytearray(b'\xA3\xB9\xF5\xCE\x6D\x47\x7F\x49\x9F\xDC\xE9\x81\x43\xE0\x42\x2C')
        self.ful_size_drv_cam = int('BB6', 16)
        self.ful_size_vol_dxe = int('3983B4', 16)
        self.ful_size_amit = int('98', 16)
        self.ful_size_nvar = int('3FFB8', 16)
        self.ful_size_misc_t = int('8A', 16)
        self.ful_size_misc_b = int('43B', 16)
        self.offset_data = 108
        self.dump_full = None
        self.data_padding = None
        self.misc_b_data = None
        self.misc_t_data = None
        self.name_model = None

    def __repr__(self):
        return self.path_dump

    @staticmethod
    def is_check_data(data1: str, data2: str) -> bool:
        if data1 is None or data2 is None:
            return False
        return len(data1) == len(data2)

    @staticmethod
    def find_get_data_n_var(*, mm_instance, signature, size, offset_n=0):
        """
        Finds and returns nvar data by its signature
        :param mm_instance:
        :param signature:
        :param size:
        :param offset_n:
        :return:
        """
        ind = mm_instance.find(signature)
        mm_instance.seek(ind - offset_n)
        return mm_instance.read(size)

    def get_misc_data(self, list_sig, save_full=False):
        """
        Finds and returns data to modify
        :param list_sig:
        :param save_full:
        :param padding:
        :param n_offset:
        :return: str data or None if not found data
        """
        with open(self.path_dump, "r+b") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:

                if save_full:
                    self.dump_full = f.read()
                # TODO sig padding обрабатывать в вазывающей функции
                for sig_padding, size in self.list_sig_paddings:
                    if (mm.find(sig_padding, int('580000', 16))) != -1:
                        self.name_model = sig_padding[4:10].decode("utf-8")
                        _logger.debug(self.name_model)

                for sig, size in list_sig:
                    if (ind := mm.find(sig, int('580000', 16))) != -1:

                        _logger.debug(f"highest index {hex(mm.rfind(sig, int('580000', 16)))}")
                        _logger.debug(f"lowest index {hex(mm.find(sig, int('580000', 16)))}")
                        _logger.debug(f"current ind == {hex(ind)} and size == {hex(int(size, 16))}")

                        ind_data_end = ind + int(size, 16)
                        ind_data_start = ind_data_end - self.offset_data
                        mm.seek(ind_data_end)
                        # проверяю что после начинается следуюшщая nvar
                        if mm.read(1) == b"\x4E":
                            mm.seek(ind_data_start)
                            data = mm.read(self.offset_data)
                            # проверяю начало данных
                            if data[:1] == b"\x08":
                                return data
                        else:
                            return
                return

    def _get_data_from_dump(self, *, offset: int, size: int) -> bytes:
        """
        returns data from dump in specified range

        :param offset: read start offset
        :param size: number of bytes read
        :return: data bytes from file
        """

        with open(self.path_dump, "rb") as file:
            self.dump_full = file.read()
            file.seek(offset)
            data = file.read(size)
        return data

    @staticmethod
    def serial_dec_to_byte(serial_l) -> bytes:
        """
        Сonverts serial number from decimal to bytes
        :param serial_l:
        :return: bytes minor(low) part of serial number
        """

        serial_hex_l = hex(int(serial_l))[2:]

        if len(serial_hex_l) % 6 != 0:
            serial_hex_l = "{0}{1}".format("0" * (6 - len(serial_hex_l)), serial_hex_l)

        return bytes.fromhex(serial_hex_l)[::-1]

    def write_sn(self, *, file_name: str, serial: str):
        """
        Writes serial number to file
        :param file_name: file name
        :param serial: serial number
        :return:
        """

        word_byte = bytearray()
        serial_str, serial_dec = serial[0:5], serial[5:10]

        for byte in serial_str:
            word_byte += bytes(byte, 'utf-8')

        word_byte += self.serial_dec_to_byte(serial_dec)

        if len(word_byte) != 8:
            raise ValueError

        with open(file_name, 'wb') as file:
            file.write(self.dump_full.replace(self.sn_full_bytes, word_byte))

    def read_sn(self, *, offset: int) -> str:
        """
        Read serial number
        :param offset: offset in file
        :return: serial number str
        """
        count_bytes = 8
        self.sn_full_bytes = self._get_data_from_dump(offset=offset, size=count_bytes)
        sn_str = self.sn_full_bytes[0:5].decode('utf-8')
        sn_dec_hex = binascii.hexlify(self.sn_full_bytes[5:8][::-1])

        return "{0}{1}".format(sn_str, int(sn_dec_hex, 16))
