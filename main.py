import binascii
import mmap


class Dump:

    def __init__(self, name_dump):
        self.path_dump = name_dump
        self.sn_full_bytes = bytearray()
        self.dump_full = None
        self.sig_amit = bytearray(b'\x41\x4D\x49\x54\x53\x45\x53\x65\x74\x75\x70')
        self.sig_drv_cam = bytearray(b'\x49\x7C\x97\x79\xB5\x0B\x1C\x40\x9A\xDB\xA3\x70\x98\xA4\x5A\x80')
        self.sig_misc_b = bytearray(b'\x4D\x69\x73\x63\x45\x78\x74\x42\x6C\x6F\x63\x6B\x42\x61\x63\x6B\x75\x70')
        self.sig_misc_t = bytearray(b'\x4D\x69\x73\x63\x54\x61\x62\x6C\x65\x42\x61\x63\x6B\x75\x70')
        self.sig_nvar_full = bytearray(b'\xA3\xB9\xF5\xCE\x6D\x47\x7F\x49\x9F\xDC\xE9\x81\x43\xE0\x42\x2C\x34\xAA'
                                       b'\x01\x00\xB8\xFF\x03\xF8')
        self.ful_size_drv_cam = int('177E', 16)
        self.ful_size_amit = int('98', 16)
        self.ful_size_nvar = int('3FFB8', 16)
        self.ful_size_misk_t = int('9B', 16)
        self.ful_size_misk_b = int('44F', 16)

    def __repr__(self):
        return self.path_dump

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

        :param offset: read start offset
        :param count: number of bytes read
        :return:
        """

        with open(self.path_dump, "rb") as file:
            self.dump_full = file.read()
            # # print(self.misc_t)
            # # mm = mmap.mmap(file.fileno(), 0)
            # offset_t = self.dump_full.find(self.sig_misc_t, 0)
            # offset_b = self.dump_full.find(self.sig_misc_b, 0)
            # # TODO misc_b is different in dumps
            # print(hex(offset_t))
            # print(bool(offset_b))
            # # print(mm.find(s_byte, 0))
            # file.seek(offset_t)
            # misk_t = file.read(int('8A', 16))
            # # file.seek(offset_b)
            # # misk_b = file.read(int('2EA', 16))
            # with open(self.path_dump, 'wb') as _f:
            #     _f.write(self.dump_full.replace(misk_t, misk_t))
            # # print(hex(_f))
            # print(misk_t)
            # # print(misk_b)

            file.seek(offset)
            data = file.read(count)
        return data

    def read_sn(self, *, offset: int) -> str:
        count_bytes = 8
        self.sn_full_bytes = self._get_data_from_dump(offset=offset, count=count_bytes)
        sn_str = self.sn_full_bytes[0:5].decode('utf-8')
        sn_dec_hex = binascii.hexlify(self.sn_full_bytes[5:8][::-1])

        return "{0}{1}".format(sn_str, int(sn_dec_hex, 16))
