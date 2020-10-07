import binascii
import mmap


class Dump:

    def __init__(self, name_dump):
        self.path_dump = name_dump
        self.sn_full_bytes = bytearray()
        self.sig_amit = bytearray(b'\x41\x4D\x49\x54\x53\x45\x53\x65\x74\x75\x70')
        self.vol_dxe = bytearray(b'\x93\xFD\x21\x9E\x72\x9C\x15\x4C\x8C\x4B\xE7\x7F\x1D\xB2\xD7\x92')
        self.sig_drv_cam = bytearray(b'\x00\x51\x57\xD5\x16\xD8\x82\x43\x97\x26\xB1\xDC\x5F\x1D\xF3\x77')
        self.sig_misc_b = bytearray(b'\x4D\x69\x73\x63\x45\x78\x74\x42\x6C\x6F\x63\x6B\x42\x61\x63\x6B\x75\x70')
        self.sig_misc_t = bytearray(b'\x4D\x69\x73\x63\x54\x61\x62\x6C\x65\x42\x61\x63\x6B\x75\x70')
        self.sig_nvar_full = bytearray(b'\xA3\xB9\xF5\xCE\x6D\x47\x7F\x49\x9F\xDC\xE9\x81\x43\xE0\x42\x2C')
        self.ful_size_drv_cam = int('BB6', 16)
        self.ful_size_vol_dxe = int('3983B4', 16)
        self.ful_size_amit = int('98', 16)
        self.ful_size_nvar = int('3FFB8', 16)
        self.ful_size_misk_t = int('9B', 16)
        self.ful_size_misk_b = int('44F', 16)
        self.dump_full = None
        self.misk_t_data = None
        self.misk_b_data = None

    def __repr__(self):
        return self.path_dump

    @staticmethod
    def find_get_data_n_var(*, mm_instance, signature, size):
        ind = mm_instance.find(signature)
        mm_instance.seek(ind - 11)
        return mm_instance.read(size)

    def get_misc_data(self, save_full=False):
        if self.path_dump != -1:
            with open(self.path_dump, "r+b") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:

                    # misc
                    self.misk_t_data = self.find_get_data_n_var(mm_instance=mm, signature=self.sig_misc_t,
                                                                size=self.ful_size_misk_t)

                    self.misk_b_data = self.find_get_data_n_var(mm_instance=mm, signature=self.sig_misc_b,
                                                                size=self.ful_size_misk_b)
                if save_full:
                    self.dump_full = f.read()
            return self.misk_t_data, self.misk_b_data

    @staticmethod
    def serial_dec_to_byte(serial_l) -> bytes:

        serial_hex_l = hex(int(serial_l))[2:]

        if len(serial_hex_l) % 6 != 0:
            serial_hex_l = "{0}{1}".format("0" * (6 - len(serial_hex_l)), serial_hex_l)

        return bytes.fromhex(serial_hex_l)[::-1]

    def write_sn(self, *, file_name: str, serial: str):

        word_byte = bytearray()
        serial_str, serial_dec = serial[0:5], serial[5:10]

        for byte in serial_str:
            word_byte += bytes(byte, 'utf-8')

        word_byte += self.serial_dec_to_byte(serial_dec)

        if len(word_byte) != 8:
            raise ValueError

        with open(file_name, 'wb') as file:
            file.write(self.dump_full.replace(self.sn_full_bytes, word_byte))

    def _get_data_from_dump(self, *, offset: int, count: int) -> bytes:
        """
        returns data from dump in specified range

        :param offset: read start offset
        :param count: number of bytes read
        :return: data bytes from file
        """

        with open(self.path_dump, "rb") as file:
            self.dump_full = file.read()
            file.seek(offset)
            data = file.read(count)
        return data

    def read_sn(self, *, offset: int) -> str:
        count_bytes = 8
        self.sn_full_bytes = self._get_data_from_dump(offset=offset, count=count_bytes)
        sn_str = self.sn_full_bytes[0:5].decode('utf-8')
        sn_dec_hex = binascii.hexlify(self.sn_full_bytes[5:8][::-1])

        return "{0}{1}".format(sn_str, int(sn_dec_hex, 16))
