import binascii


class Dump:

    def __init__(self, name_dump):
        self.path_dump = name_dump
        self.sn_full_bytes = bytearray()
        self.dump_full = None

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
        # count -> number of bytes read
        # offset -> read start offset
        with open(self.path_dump, "rb") as file:
            self.dump_full = file.read()

            file.seek(offset)
            data = file.read(count)
        return data

    def read_sn(self, *, offset: int) -> str:
        count_bytes = 8
        self.sn_full_bytes = self._get_data(offset=offset, count=count_bytes)
        sn_str = self.sn_full_bytes[0:5].decode('utf-8')
        sn_dec_hex = binascii.hexlify(self.sn_full_bytes[5:8][::-1])

        return "{0}{1}".format(sn_str, int(sn_dec_hex, 16))
