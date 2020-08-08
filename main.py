import binascii
import mmap

class Dump:

    def __init__(self, name_dump):
        self.path_dump = name_dump
        self.sn_full_bytes = bytearray()
        self.dump_full = None
        self.misc_b = bytearray(b'\x4E\x56\x41\x52\xEA\x02\xFF\xFF\xFF')
        self.misc_t = bytearray(b'\x4E\x56\x41\x52\x8A\x00\xFF\xFF\xFF')

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

    def _get_data(self, *, offset: int, count: int) -> bytes:
        """

        :param offset: read start offset
        :param count: number of bytes read
        :return:
        """

        with open(self.path_dump, "rb") as file:
            self.dump_full = file.read()
            # print(self.misc_t)
            # mm = mmap.mmap(file.fileno(), 0)
            offset_t = self.dump_full.find(self.misc_t, 0)
            offset_b = self.dump_full.find(self.misc_b, 0)
            print(hex(offset_t))
            print(bool(offset_b))
            # print(mm.find(s_byte, 0))
            file.seek(offset_t)
            misk_t = file.read(int('8A', 16))
            # file.seek(offset_b)
            # misk_b = file.read(int('2EA', 16))
            with open(self.path_dump, 'wb') as _f:
                _f.write(self.dump_full.replace(misk_t, misk_t))
            # print(hex(_f))
            print(misk_t)
            # print(misk_b)

            file.seek(offset)
            data = file.read(count)
        return data

    def read_sn(self, *, offset: int) -> str:
        count_bytes = 8
        self.sn_full_bytes = self._get_data(offset=offset, count=count_bytes)
        sn_str = self.sn_full_bytes[0:5].decode('utf-8')
        sn_dec_hex = binascii.hexlify(self.sn_full_bytes[5:8][::-1])

        return "{0}{1}".format(sn_str, int(sn_dec_hex, 16))
