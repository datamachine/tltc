from collections import namedtuple
from struct import Struct
import io

combinators = {}

def serialize(combinator, *args, **kwargs):
    c = None
    if type(combinator) is bytes:
        c = combinators.get(combinator)
    else:
        c = combinators.get(combinator.number)
    if c is None:
        raise Exception('combinator "{}" does not exist'.format(combinator))

    return c.serialize(*args, **kwargs)


def deserialize(io_bytes, *args, **kwargs):
    cons = combinators.get(io_bytes.read(4))
    if cons is None:
        print('combinator "{}" does not exist'.format(combinator), file=sys.stderr)
        return None

    if not cons.is_base:
        io_bytes.seek(-4, 1)
    
    return cons.deserialize(io_bytes, *args, **kwargs)


_pack_number_struct = Struct('<I')
pack_number = _pack_number_struct.pack


class int_c:
    number = pack_number(0xa8509bda)
    is_base = True

    _struct = Struct('<i')

    @staticmethod
    def serialize(_int):
        return int_c._struct.pack(_int)

    @staticmethod
    def deserialize(io_bytes):
        return int_c._struct.unpack(io_bytes.read(4))[0]
combinators[int_c.number] = int_c


class long_c:
    number = pack_number(0x22076cba)
    is_base = True

    _struct = Struct('<q')

    @staticmethod
    def serialize(_long):
        return long_c._struct.pack(_long)

    @staticmethod
    def deserialize(io_bytes):
        return long_c._struct.unpack(io_bytes.read(8))[0]     
combinators[long_c.number] = long_c


class double_c:
    number = pack_number(0x2210c154)
    is_base = True

    _struct = Struct('<d')

    @staticmethod
    def serialize(_double):
        return double_c._struct.pack(_double)

    @staticmethod
    def deserialize(io_bytes):
        return double_c._struct.unpack(io_bytes.read(8))[0]    
combinators[double_c.number] = double_c


class string_c:
    number = pack_number(0xb5286e24)
    is_base = True

    @staticmethod
    def serialize(string):
        result = bytearray()

        str_bytes = string.encode()

        size_pfx = len(str_bytes)
        if size_pfx < 254:
            result += size_pfx.to_bytes(1, byteorder='little')
        else:
            result += b'\xfe'
            result += size_pfx.to_bytes(3, byteorder='little')

        result += str_bytes

        padding = len(result)%4
        result += bytes(padding)

        return bytes(result)


    @staticmethod
    def deserialize(io_bytes):
        size = int.from_bytes(io_bytes.read(1), byteorder='little')
        pfx_bytes = 1
        if size == 254:
            size = b'\xfe'
            pfx_bytes = 4

        result = io_bytes.read(size)

        remainder = 4 - (pfx_bytes + size)%4
        io_bytes.read(remainder)

        return result.decode()
combinators[string_c.number] = string_c


class bytes_c:
    number = pack_number(0xebefb69e)
    is_base = True

    @staticmethod
    def serialize(_bytes):
        result = bytearray()

        size_pfx = len(_bytes)
        if size_pfx < 254:
            result += size_pfx.to_bytes(1, byteorder='little')
        else:
            result += int(254).to_bytes(1, byteorder='little')
            result += size_pfx.to_bytes(3, byteorder='little')

        result += _bytes

        padding = len(result)%4
        result += bytes(padding)

        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        size = int.from_bytes(io_bytes.read(1), byteorder='little')
        pfx_bytes = 1
        if size == 254:
            size = int.from_bytes(io_bytes.read(3), byteorder='little')
            pfx_bytes = 4

        result = io_bytes.read(size)

        remainder = 4 - (pfx_bytes + size)%4
        io_bytes.read(remainder)

        return result
combinators[bytes_c.number] = bytes_c


class vector_c:
    number = pack_number(0x1cb5c415)
    is_base = True

    @staticmethod
    def serialize(iterable, vector_type):
        result = bytearray(vector_c.number)
        result += len(iterable).to_bytes(4, byteorder='little')
        for i in iterable:
            if not vector_type.is_base:
                result += vector_type.number
            result += vector_type.serialize(i)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes, vector_type=None):
        count = int.from_bytes(io_bytes.read(4), byteorder='little')
        items = []
        cons = None
        if vector_type is not None:
            cons = vector_type
        for i in range(count):
            if vector_type is None:
                cnum = int.from_bytes(io_bytes.read(4), byteorder='little')
                cons = combinators.get(cnum) 
            items.append(cons.deserialize(io_bytes))
        return items
combinators[vector_c.number] = vector_c


class boolFalse_c:
    number = pack_number(0xbc799737)
    is_base = False
    _data_cls = namedtuple('Bool', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return boolFalse_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert boolFalse_c.number == number
        return boolFalse_c._data_cls(tag='boolFalse', number=boolFalse_c.number)
combinators[boolFalse_c.number] = boolFalse_c


class boolTrue_c:
    number = pack_number(0x997275b5)
    is_base = False
    _data_cls = namedtuple('Bool', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return boolTrue_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert boolTrue_c.number == number
        return boolTrue_c._data_cls(tag='boolTrue', number=boolTrue_c.number)
combinators[boolTrue_c.number] = boolTrue_c


class error_c:
    number = pack_number(0xc4b9f9bb)
    is_base = False
    _data_cls = namedtuple('Error', ['code', 'text'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += error_c.number
        result += int_c.serialize(data.code)
        result += string_c.serialize(data.text)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return error_c._data_cls(code = int_c.deserialize(io_bytes),
                                 text = string_c.deserialize(io_bytes))
combinators[error_c.number] = error_c


class null_c:
    number = pack_number(0x56730bcc)
    is_base = False
    _data_cls = namedtuple('Null', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return null_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert null_c.number == number
        return null_c._data_cls(tag='null', number=null_c.number)
combinators[null_c.number] = null_c


class inputPeerEmpty_c:
    number = pack_number(0x7f3b18ea)
    is_base = False
    _data_cls = namedtuple('InputPeer', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputPeerEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputPeerEmpty_c.number == number
        return inputPeerEmpty_c._data_cls(tag='inputPeerEmpty', number=inputPeerEmpty_c.number)
combinators[inputPeerEmpty_c.number] = inputPeerEmpty_c


class inputPeerSelf_c:
    number = pack_number(0x7da07ec9)
    is_base = False
    _data_cls = namedtuple('InputPeer', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputPeerSelf_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputPeerSelf_c.number == number
        return inputPeerSelf_c._data_cls(tag='inputPeerSelf', number=inputPeerSelf_c.number)
combinators[inputPeerSelf_c.number] = inputPeerSelf_c


class inputPeerContact_c:
    number = pack_number(0x1023dbe8)
    is_base = False
    _data_cls = namedtuple('InputPeer', ['user_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputPeerContact_c.number
        result += int_c.serialize(data.user_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputPeerContact_c._data_cls(user_id = int_c.deserialize(io_bytes))
combinators[inputPeerContact_c.number] = inputPeerContact_c


class inputPeerForeign_c:
    number = pack_number(0x9b447325)
    is_base = False
    _data_cls = namedtuple('InputPeer', ['user_id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputPeerForeign_c.number
        result += int_c.serialize(data.user_id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputPeerForeign_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                            access_hash = long_c.deserialize(io_bytes))
combinators[inputPeerForeign_c.number] = inputPeerForeign_c


class inputPeerChat_c:
    number = pack_number(0x179be863)
    is_base = False
    _data_cls = namedtuple('InputPeer', ['chat_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputPeerChat_c.number
        result += int_c.serialize(data.chat_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputPeerChat_c._data_cls(chat_id = int_c.deserialize(io_bytes))
combinators[inputPeerChat_c.number] = inputPeerChat_c


class inputUserEmpty_c:
    number = pack_number(0xb98886cf)
    is_base = False
    _data_cls = namedtuple('InputUser', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputUserEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputUserEmpty_c.number == number
        return inputUserEmpty_c._data_cls(tag='inputUserEmpty', number=inputUserEmpty_c.number)
combinators[inputUserEmpty_c.number] = inputUserEmpty_c


class inputUserSelf_c:
    number = pack_number(0xf7c1b13f)
    is_base = False
    _data_cls = namedtuple('InputUser', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputUserSelf_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputUserSelf_c.number == number
        return inputUserSelf_c._data_cls(tag='inputUserSelf', number=inputUserSelf_c.number)
combinators[inputUserSelf_c.number] = inputUserSelf_c


class inputUserContact_c:
    number = pack_number(0x86e94f65)
    is_base = False
    _data_cls = namedtuple('InputUser', ['user_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputUserContact_c.number
        result += int_c.serialize(data.user_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputUserContact_c._data_cls(user_id = int_c.deserialize(io_bytes))
combinators[inputUserContact_c.number] = inputUserContact_c


class inputUserForeign_c:
    number = pack_number(0x655e74ff)
    is_base = False
    _data_cls = namedtuple('InputUser', ['user_id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputUserForeign_c.number
        result += int_c.serialize(data.user_id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputUserForeign_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                            access_hash = long_c.deserialize(io_bytes))
combinators[inputUserForeign_c.number] = inputUserForeign_c


class inputPhoneContact_c:
    number = pack_number(0xf392b7f4)
    is_base = False
    _data_cls = namedtuple('InputContact', ['client_id', 'phone', 'first_name', 'last_name'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputPhoneContact_c.number
        result += long_c.serialize(data.client_id)
        result += string_c.serialize(data.phone)
        result += string_c.serialize(data.first_name)
        result += string_c.serialize(data.last_name)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputPhoneContact_c._data_cls(client_id = long_c.deserialize(io_bytes),
                                             phone = string_c.deserialize(io_bytes),
                                             first_name = string_c.deserialize(io_bytes),
                                             last_name = string_c.deserialize(io_bytes))
combinators[inputPhoneContact_c.number] = inputPhoneContact_c


class inputFile_c:
    number = pack_number(0xf52ff27f)
    is_base = False
    _data_cls = namedtuple('InputFile', ['id', 'parts', 'name', 'md5_checksum'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputFile_c.number
        result += long_c.serialize(data.id)
        result += int_c.serialize(data.parts)
        result += string_c.serialize(data.name)
        result += string_c.serialize(data.md5_checksum)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputFile_c._data_cls(id = long_c.deserialize(io_bytes),
                                     parts = int_c.deserialize(io_bytes),
                                     name = string_c.deserialize(io_bytes),
                                     md5_checksum = string_c.deserialize(io_bytes))
combinators[inputFile_c.number] = inputFile_c


class inputMediaEmpty_c:
    number = pack_number(0x9664f57f)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputMediaEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputMediaEmpty_c.number == number
        return inputMediaEmpty_c._data_cls(tag='inputMediaEmpty', number=inputMediaEmpty_c.number)
combinators[inputMediaEmpty_c.number] = inputMediaEmpty_c


class inputMediaUploadedPhoto_c:
    number = pack_number(0x2dc53a7d)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['file'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaUploadedPhoto_c.number
        result += inputfile_c.serialize(data.file)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaUploadedPhoto_c._data_cls(file = deserialize(io_bytes))
combinators[inputMediaUploadedPhoto_c.number] = inputMediaUploadedPhoto_c


class inputMediaPhoto_c:
    number = pack_number(0x8f2ab2ec)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaPhoto_c.number
        result += inputphoto_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaPhoto_c._data_cls(id = deserialize(io_bytes))
combinators[inputMediaPhoto_c.number] = inputMediaPhoto_c


class inputMediaGeoPoint_c:
    number = pack_number(0xf9c44144)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['geo_point'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaGeoPoint_c.number
        result += inputgeopoint_c.serialize(data.geo_point)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaGeoPoint_c._data_cls(geo_point = deserialize(io_bytes))
combinators[inputMediaGeoPoint_c.number] = inputMediaGeoPoint_c


class inputMediaContact_c:
    number = pack_number(0xa6e45987)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['phone_number', 'first_name', 'last_name'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaContact_c.number
        result += string_c.serialize(data.phone_number)
        result += string_c.serialize(data.first_name)
        result += string_c.serialize(data.last_name)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaContact_c._data_cls(phone_number = string_c.deserialize(io_bytes),
                                             first_name = string_c.deserialize(io_bytes),
                                             last_name = string_c.deserialize(io_bytes))
combinators[inputMediaContact_c.number] = inputMediaContact_c


class inputMediaUploadedVideo_c:
    number = pack_number(0x133ad6f6)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['file', 'duration', 'w', 'h', 'mime_type'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaUploadedVideo_c.number
        result += inputfile_c.serialize(data.file)
        result += int_c.serialize(data.duration)
        result += int_c.serialize(data.w)
        result += int_c.serialize(data.h)
        result += string_c.serialize(data.mime_type)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaUploadedVideo_c._data_cls(file = deserialize(io_bytes),
                                                   duration = int_c.deserialize(io_bytes),
                                                   w = int_c.deserialize(io_bytes),
                                                   h = int_c.deserialize(io_bytes),
                                                   mime_type = string_c.deserialize(io_bytes))
combinators[inputMediaUploadedVideo_c.number] = inputMediaUploadedVideo_c


class inputMediaUploadedThumbVideo_c:
    number = pack_number(0x9912dabf)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['file', 'thumb', 'duration', 'w', 'h', 'mime_type'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaUploadedThumbVideo_c.number
        result += inputfile_c.serialize(data.file)
        result += inputfile_c.serialize(data.thumb)
        result += int_c.serialize(data.duration)
        result += int_c.serialize(data.w)
        result += int_c.serialize(data.h)
        result += string_c.serialize(data.mime_type)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaUploadedThumbVideo_c._data_cls(file = deserialize(io_bytes),
                                                        thumb = deserialize(io_bytes),
                                                        duration = int_c.deserialize(io_bytes),
                                                        w = int_c.deserialize(io_bytes),
                                                        h = int_c.deserialize(io_bytes),
                                                        mime_type = string_c.deserialize(io_bytes))
combinators[inputMediaUploadedThumbVideo_c.number] = inputMediaUploadedThumbVideo_c


class inputMediaVideo_c:
    number = pack_number(0x7f023ae6)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaVideo_c.number
        result += inputvideo_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaVideo_c._data_cls(id = deserialize(io_bytes))
combinators[inputMediaVideo_c.number] = inputMediaVideo_c


class inputChatPhotoEmpty_c:
    number = pack_number(0x1ca48f57)
    is_base = False
    _data_cls = namedtuple('InputChatPhoto', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputChatPhotoEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputChatPhotoEmpty_c.number == number
        return inputChatPhotoEmpty_c._data_cls(tag='inputChatPhotoEmpty', number=inputChatPhotoEmpty_c.number)
combinators[inputChatPhotoEmpty_c.number] = inputChatPhotoEmpty_c


class inputChatUploadedPhoto_c:
    number = pack_number(0x94254732)
    is_base = False
    _data_cls = namedtuple('InputChatPhoto', ['file', 'crop'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputChatUploadedPhoto_c.number
        result += inputfile_c.serialize(data.file)
        result += inputphotocrop_c.serialize(data.crop)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputChatUploadedPhoto_c._data_cls(file = deserialize(io_bytes),
                                                  crop = deserialize(io_bytes))
combinators[inputChatUploadedPhoto_c.number] = inputChatUploadedPhoto_c


class inputChatPhoto_c:
    number = pack_number(0xb2e1bf08)
    is_base = False
    _data_cls = namedtuple('InputChatPhoto', ['id', 'crop'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputChatPhoto_c.number
        result += inputphoto_c.serialize(data.id)
        result += inputphotocrop_c.serialize(data.crop)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputChatPhoto_c._data_cls(id = deserialize(io_bytes),
                                          crop = deserialize(io_bytes))
combinators[inputChatPhoto_c.number] = inputChatPhoto_c


class inputGeoPointEmpty_c:
    number = pack_number(0xe4c123d6)
    is_base = False
    _data_cls = namedtuple('InputGeoPoint', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputGeoPointEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputGeoPointEmpty_c.number == number
        return inputGeoPointEmpty_c._data_cls(tag='inputGeoPointEmpty', number=inputGeoPointEmpty_c.number)
combinators[inputGeoPointEmpty_c.number] = inputGeoPointEmpty_c


class inputGeoPoint_c:
    number = pack_number(0xf3b7acc9)
    is_base = False
    _data_cls = namedtuple('InputGeoPoint', ['lat', 'long'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputGeoPoint_c.number
        result += double_c.serialize(data.lat)
        result += double_c.serialize(data.long)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputGeoPoint_c._data_cls(lat = double_c.deserialize(io_bytes),
                                         long = double_c.deserialize(io_bytes))
combinators[inputGeoPoint_c.number] = inputGeoPoint_c


class inputPhotoEmpty_c:
    number = pack_number(0x1cd7bf0d)
    is_base = False
    _data_cls = namedtuple('InputPhoto', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputPhotoEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputPhotoEmpty_c.number == number
        return inputPhotoEmpty_c._data_cls(tag='inputPhotoEmpty', number=inputPhotoEmpty_c.number)
combinators[inputPhotoEmpty_c.number] = inputPhotoEmpty_c


class inputPhoto_c:
    number = pack_number(0xfb95c6c4)
    is_base = False
    _data_cls = namedtuple('InputPhoto', ['id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputPhoto_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputPhoto_c._data_cls(id = long_c.deserialize(io_bytes),
                                      access_hash = long_c.deserialize(io_bytes))
combinators[inputPhoto_c.number] = inputPhoto_c


class inputVideoEmpty_c:
    number = pack_number(0x5508ec75)
    is_base = False
    _data_cls = namedtuple('InputVideo', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputVideoEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputVideoEmpty_c.number == number
        return inputVideoEmpty_c._data_cls(tag='inputVideoEmpty', number=inputVideoEmpty_c.number)
combinators[inputVideoEmpty_c.number] = inputVideoEmpty_c


class inputVideo_c:
    number = pack_number(0xee579652)
    is_base = False
    _data_cls = namedtuple('InputVideo', ['id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputVideo_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputVideo_c._data_cls(id = long_c.deserialize(io_bytes),
                                      access_hash = long_c.deserialize(io_bytes))
combinators[inputVideo_c.number] = inputVideo_c


class inputFileLocation_c:
    number = pack_number(0x14637196)
    is_base = False
    _data_cls = namedtuple('InputFileLocation', ['volume_id', 'local_id', 'secret'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputFileLocation_c.number
        result += long_c.serialize(data.volume_id)
        result += int_c.serialize(data.local_id)
        result += long_c.serialize(data.secret)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputFileLocation_c._data_cls(volume_id = long_c.deserialize(io_bytes),
                                             local_id = int_c.deserialize(io_bytes),
                                             secret = long_c.deserialize(io_bytes))
combinators[inputFileLocation_c.number] = inputFileLocation_c


class inputVideoFileLocation_c:
    number = pack_number(0x3d0364ec)
    is_base = False
    _data_cls = namedtuple('InputFileLocation', ['id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputVideoFileLocation_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputVideoFileLocation_c._data_cls(id = long_c.deserialize(io_bytes),
                                                  access_hash = long_c.deserialize(io_bytes))
combinators[inputVideoFileLocation_c.number] = inputVideoFileLocation_c


class inputPhotoCropAuto_c:
    number = pack_number(0xade6b004)
    is_base = False
    _data_cls = namedtuple('InputPhotoCrop', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputPhotoCropAuto_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputPhotoCropAuto_c.number == number
        return inputPhotoCropAuto_c._data_cls(tag='inputPhotoCropAuto', number=inputPhotoCropAuto_c.number)
combinators[inputPhotoCropAuto_c.number] = inputPhotoCropAuto_c


class inputPhotoCrop_c:
    number = pack_number(0xd9915325)
    is_base = False
    _data_cls = namedtuple('InputPhotoCrop', ['crop_left', 'crop_top', 'crop_width'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputPhotoCrop_c.number
        result += double_c.serialize(data.crop_left)
        result += double_c.serialize(data.crop_top)
        result += double_c.serialize(data.crop_width)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputPhotoCrop_c._data_cls(crop_left = double_c.deserialize(io_bytes),
                                          crop_top = double_c.deserialize(io_bytes),
                                          crop_width = double_c.deserialize(io_bytes))
combinators[inputPhotoCrop_c.number] = inputPhotoCrop_c


class inputAppEvent_c:
    number = pack_number(0x770656a8)
    is_base = False
    _data_cls = namedtuple('InputAppEvent', ['time', 'type', 'peer', 'data'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputAppEvent_c.number
        result += double_c.serialize(data.time)
        result += string_c.serialize(data.type)
        result += long_c.serialize(data.peer)
        result += string_c.serialize(data.data)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputAppEvent_c._data_cls(time = double_c.deserialize(io_bytes),
                                         type = string_c.deserialize(io_bytes),
                                         peer = long_c.deserialize(io_bytes),
                                         data = string_c.deserialize(io_bytes))
combinators[inputAppEvent_c.number] = inputAppEvent_c


class peerUser_c:
    number = pack_number(0x9db1bc6d)
    is_base = False
    _data_cls = namedtuple('Peer', ['user_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += peerUser_c.number
        result += int_c.serialize(data.user_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return peerUser_c._data_cls(user_id = int_c.deserialize(io_bytes))
combinators[peerUser_c.number] = peerUser_c


class peerChat_c:
    number = pack_number(0xbad0e5bb)
    is_base = False
    _data_cls = namedtuple('Peer', ['chat_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += peerChat_c.number
        result += int_c.serialize(data.chat_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return peerChat_c._data_cls(chat_id = int_c.deserialize(io_bytes))
combinators[peerChat_c.number] = peerChat_c


class fileUnknown_c:
    number = pack_number(0xaa963b05)
    is_base = False
    _data_cls = namedtuple('FileType', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return fileUnknown_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert fileUnknown_c.number == number
        return fileUnknown_c._data_cls(tag='storage.fileUnknown', number=fileUnknown_c.number)
combinators[fileUnknown_c.number] = fileUnknown_c


class fileJpeg_c:
    number = pack_number(0x7efe0e)
    is_base = False
    _data_cls = namedtuple('FileType', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return fileJpeg_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert fileJpeg_c.number == number
        return fileJpeg_c._data_cls(tag='storage.fileJpeg', number=fileJpeg_c.number)
combinators[fileJpeg_c.number] = fileJpeg_c


class fileGif_c:
    number = pack_number(0xcae1aadf)
    is_base = False
    _data_cls = namedtuple('FileType', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return fileGif_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert fileGif_c.number == number
        return fileGif_c._data_cls(tag='storage.fileGif', number=fileGif_c.number)
combinators[fileGif_c.number] = fileGif_c


class filePng_c:
    number = pack_number(0xa4f63c0)
    is_base = False
    _data_cls = namedtuple('FileType', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return filePng_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert filePng_c.number == number
        return filePng_c._data_cls(tag='storage.filePng', number=filePng_c.number)
combinators[filePng_c.number] = filePng_c


class filePdf_c:
    number = pack_number(0xae1e508d)
    is_base = False
    _data_cls = namedtuple('FileType', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return filePdf_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert filePdf_c.number == number
        return filePdf_c._data_cls(tag='storage.filePdf', number=filePdf_c.number)
combinators[filePdf_c.number] = filePdf_c


class fileMp3_c:
    number = pack_number(0x528a0677)
    is_base = False
    _data_cls = namedtuple('FileType', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return fileMp3_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert fileMp3_c.number == number
        return fileMp3_c._data_cls(tag='storage.fileMp3', number=fileMp3_c.number)
combinators[fileMp3_c.number] = fileMp3_c


class fileMov_c:
    number = pack_number(0x4b09ebbc)
    is_base = False
    _data_cls = namedtuple('FileType', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return fileMov_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert fileMov_c.number == number
        return fileMov_c._data_cls(tag='storage.fileMov', number=fileMov_c.number)
combinators[fileMov_c.number] = fileMov_c


class filePartial_c:
    number = pack_number(0x40bc6f52)
    is_base = False
    _data_cls = namedtuple('FileType', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return filePartial_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert filePartial_c.number == number
        return filePartial_c._data_cls(tag='storage.filePartial', number=filePartial_c.number)
combinators[filePartial_c.number] = filePartial_c


class fileMp4_c:
    number = pack_number(0xb3cea0e4)
    is_base = False
    _data_cls = namedtuple('FileType', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return fileMp4_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert fileMp4_c.number == number
        return fileMp4_c._data_cls(tag='storage.fileMp4', number=fileMp4_c.number)
combinators[fileMp4_c.number] = fileMp4_c


class fileWebp_c:
    number = pack_number(0x1081464c)
    is_base = False
    _data_cls = namedtuple('FileType', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return fileWebp_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert fileWebp_c.number == number
        return fileWebp_c._data_cls(tag='storage.fileWebp', number=fileWebp_c.number)
combinators[fileWebp_c.number] = fileWebp_c


class fileLocationUnavailable_c:
    number = pack_number(0x7c596b46)
    is_base = False
    _data_cls = namedtuple('FileLocation', ['volume_id', 'local_id', 'secret'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += fileLocationUnavailable_c.number
        result += long_c.serialize(data.volume_id)
        result += int_c.serialize(data.local_id)
        result += long_c.serialize(data.secret)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return fileLocationUnavailable_c._data_cls(volume_id = long_c.deserialize(io_bytes),
                                                   local_id = int_c.deserialize(io_bytes),
                                                   secret = long_c.deserialize(io_bytes))
combinators[fileLocationUnavailable_c.number] = fileLocationUnavailable_c


class fileLocation_c:
    number = pack_number(0x53d69076)
    is_base = False
    _data_cls = namedtuple('FileLocation', ['dc_id', 'volume_id', 'local_id', 'secret'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += fileLocation_c.number
        result += int_c.serialize(data.dc_id)
        result += long_c.serialize(data.volume_id)
        result += int_c.serialize(data.local_id)
        result += long_c.serialize(data.secret)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return fileLocation_c._data_cls(dc_id = int_c.deserialize(io_bytes),
                                        volume_id = long_c.deserialize(io_bytes),
                                        local_id = int_c.deserialize(io_bytes),
                                        secret = long_c.deserialize(io_bytes))
combinators[fileLocation_c.number] = fileLocation_c


class userEmpty_c:
    number = pack_number(0x200250ba)
    is_base = False
    _data_cls = namedtuple('User', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += userEmpty_c.number
        result += int_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return userEmpty_c._data_cls(id = int_c.deserialize(io_bytes))
combinators[userEmpty_c.number] = userEmpty_c


class userSelf_c:
    number = pack_number(0x720535ec)
    is_base = False
    _data_cls = namedtuple('User', ['id', 'first_name', 'last_name', 'phone', 'photo', 'status', 'inactive'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += userSelf_c.number
        result += int_c.serialize(data.id)
        result += string_c.serialize(data.first_name)
        result += string_c.serialize(data.last_name)
        result += string_c.serialize(data.phone)
        result += userprofilephoto_c.serialize(data.photo)
        result += userstatus_c.serialize(data.status)
        result += bool_c.serialize(data.inactive)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return userSelf_c._data_cls(id = int_c.deserialize(io_bytes),
                                    first_name = string_c.deserialize(io_bytes),
                                    last_name = string_c.deserialize(io_bytes),
                                    phone = string_c.deserialize(io_bytes),
                                    photo = deserialize(io_bytes),
                                    status = deserialize(io_bytes),
                                    inactive = deserialize(io_bytes))
combinators[userSelf_c.number] = userSelf_c


class userContact_c:
    number = pack_number(0xf2fb8319)
    is_base = False
    _data_cls = namedtuple('User', ['id', 'first_name', 'last_name', 'access_hash', 'phone', 'photo', 'status'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += userContact_c.number
        result += int_c.serialize(data.id)
        result += string_c.serialize(data.first_name)
        result += string_c.serialize(data.last_name)
        result += long_c.serialize(data.access_hash)
        result += string_c.serialize(data.phone)
        result += userprofilephoto_c.serialize(data.photo)
        result += userstatus_c.serialize(data.status)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return userContact_c._data_cls(id = int_c.deserialize(io_bytes),
                                       first_name = string_c.deserialize(io_bytes),
                                       last_name = string_c.deserialize(io_bytes),
                                       access_hash = long_c.deserialize(io_bytes),
                                       phone = string_c.deserialize(io_bytes),
                                       photo = deserialize(io_bytes),
                                       status = deserialize(io_bytes))
combinators[userContact_c.number] = userContact_c


class userRequest_c:
    number = pack_number(0x22e8ceb0)
    is_base = False
    _data_cls = namedtuple('User', ['id', 'first_name', 'last_name', 'access_hash', 'phone', 'photo', 'status'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += userRequest_c.number
        result += int_c.serialize(data.id)
        result += string_c.serialize(data.first_name)
        result += string_c.serialize(data.last_name)
        result += long_c.serialize(data.access_hash)
        result += string_c.serialize(data.phone)
        result += userprofilephoto_c.serialize(data.photo)
        result += userstatus_c.serialize(data.status)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return userRequest_c._data_cls(id = int_c.deserialize(io_bytes),
                                       first_name = string_c.deserialize(io_bytes),
                                       last_name = string_c.deserialize(io_bytes),
                                       access_hash = long_c.deserialize(io_bytes),
                                       phone = string_c.deserialize(io_bytes),
                                       photo = deserialize(io_bytes),
                                       status = deserialize(io_bytes))
combinators[userRequest_c.number] = userRequest_c


class userForeign_c:
    number = pack_number(0x5214c89d)
    is_base = False
    _data_cls = namedtuple('User', ['id', 'first_name', 'last_name', 'access_hash', 'photo', 'status'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += userForeign_c.number
        result += int_c.serialize(data.id)
        result += string_c.serialize(data.first_name)
        result += string_c.serialize(data.last_name)
        result += long_c.serialize(data.access_hash)
        result += userprofilephoto_c.serialize(data.photo)
        result += userstatus_c.serialize(data.status)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return userForeign_c._data_cls(id = int_c.deserialize(io_bytes),
                                       first_name = string_c.deserialize(io_bytes),
                                       last_name = string_c.deserialize(io_bytes),
                                       access_hash = long_c.deserialize(io_bytes),
                                       photo = deserialize(io_bytes),
                                       status = deserialize(io_bytes))
combinators[userForeign_c.number] = userForeign_c


class userDeleted_c:
    number = pack_number(0xb29ad7cc)
    is_base = False
    _data_cls = namedtuple('User', ['id', 'first_name', 'last_name'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += userDeleted_c.number
        result += int_c.serialize(data.id)
        result += string_c.serialize(data.first_name)
        result += string_c.serialize(data.last_name)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return userDeleted_c._data_cls(id = int_c.deserialize(io_bytes),
                                       first_name = string_c.deserialize(io_bytes),
                                       last_name = string_c.deserialize(io_bytes))
combinators[userDeleted_c.number] = userDeleted_c


class userProfilePhotoEmpty_c:
    number = pack_number(0x4f11bae1)
    is_base = False
    _data_cls = namedtuple('UserProfilePhoto', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return userProfilePhotoEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert userProfilePhotoEmpty_c.number == number
        return userProfilePhotoEmpty_c._data_cls(tag='userProfilePhotoEmpty', number=userProfilePhotoEmpty_c.number)
combinators[userProfilePhotoEmpty_c.number] = userProfilePhotoEmpty_c


class userProfilePhoto_c:
    number = pack_number(0xd559d8c8)
    is_base = False
    _data_cls = namedtuple('UserProfilePhoto', ['photo_id', 'photo_small', 'photo_big'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += userProfilePhoto_c.number
        result += long_c.serialize(data.photo_id)
        result += filelocation_c.serialize(data.photo_small)
        result += filelocation_c.serialize(data.photo_big)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return userProfilePhoto_c._data_cls(photo_id = long_c.deserialize(io_bytes),
                                            photo_small = deserialize(io_bytes),
                                            photo_big = deserialize(io_bytes))
combinators[userProfilePhoto_c.number] = userProfilePhoto_c


class userStatusEmpty_c:
    number = pack_number(0x9d05049)
    is_base = False
    _data_cls = namedtuple('UserStatus', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return userStatusEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert userStatusEmpty_c.number == number
        return userStatusEmpty_c._data_cls(tag='userStatusEmpty', number=userStatusEmpty_c.number)
combinators[userStatusEmpty_c.number] = userStatusEmpty_c


class userStatusOnline_c:
    number = pack_number(0xedb93949)
    is_base = False
    _data_cls = namedtuple('UserStatus', ['expires'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += userStatusOnline_c.number
        result += int_c.serialize(data.expires)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return userStatusOnline_c._data_cls(expires = int_c.deserialize(io_bytes))
combinators[userStatusOnline_c.number] = userStatusOnline_c


class userStatusOffline_c:
    number = pack_number(0x8c703f)
    is_base = False
    _data_cls = namedtuple('UserStatus', ['was_online'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += userStatusOffline_c.number
        result += int_c.serialize(data.was_online)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return userStatusOffline_c._data_cls(was_online = int_c.deserialize(io_bytes))
combinators[userStatusOffline_c.number] = userStatusOffline_c


class chatEmpty_c:
    number = pack_number(0x9ba2d800)
    is_base = False
    _data_cls = namedtuple('Chat', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += chatEmpty_c.number
        result += int_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return chatEmpty_c._data_cls(id = int_c.deserialize(io_bytes))
combinators[chatEmpty_c.number] = chatEmpty_c


class chat_c:
    number = pack_number(0x6e9c9bc7)
    is_base = False
    _data_cls = namedtuple('Chat', ['id', 'title', 'photo', 'participants_count', 'date', 'left', 'version'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += chat_c.number
        result += int_c.serialize(data.id)
        result += string_c.serialize(data.title)
        result += chatphoto_c.serialize(data.photo)
        result += int_c.serialize(data.participants_count)
        result += int_c.serialize(data.date)
        result += bool_c.serialize(data.left)
        result += int_c.serialize(data.version)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return chat_c._data_cls(id = int_c.deserialize(io_bytes),
                                title = string_c.deserialize(io_bytes),
                                photo = deserialize(io_bytes),
                                participants_count = int_c.deserialize(io_bytes),
                                date = int_c.deserialize(io_bytes),
                                left = deserialize(io_bytes),
                                version = int_c.deserialize(io_bytes))
combinators[chat_c.number] = chat_c


class chatForbidden_c:
    number = pack_number(0xfb0ccc41)
    is_base = False
    _data_cls = namedtuple('Chat', ['id', 'title', 'date'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += chatForbidden_c.number
        result += int_c.serialize(data.id)
        result += string_c.serialize(data.title)
        result += int_c.serialize(data.date)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return chatForbidden_c._data_cls(id = int_c.deserialize(io_bytes),
                                         title = string_c.deserialize(io_bytes),
                                         date = int_c.deserialize(io_bytes))
combinators[chatForbidden_c.number] = chatForbidden_c


class chatFull_c:
    number = pack_number(0x630e61be)
    is_base = False
    _data_cls = namedtuple('ChatFull', ['id', 'participants', 'chat_photo', 'notify_settings'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += chatFull_c.number
        result += int_c.serialize(data.id)
        result += chatparticipants_c.serialize(data.participants)
        result += photo_c.serialize(data.chat_photo)
        result += peernotifysettings_c.serialize(data.notify_settings)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return chatFull_c._data_cls(id = int_c.deserialize(io_bytes),
                                    participants = deserialize(io_bytes),
                                    chat_photo = deserialize(io_bytes),
                                    notify_settings = deserialize(io_bytes))
combinators[chatFull_c.number] = chatFull_c


class chatParticipant_c:
    number = pack_number(0xc8d7493e)
    is_base = False
    _data_cls = namedtuple('ChatParticipant', ['user_id', 'inviter_id', 'date'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += chatParticipant_c.number
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.inviter_id)
        result += int_c.serialize(data.date)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return chatParticipant_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                           inviter_id = int_c.deserialize(io_bytes),
                                           date = int_c.deserialize(io_bytes))
combinators[chatParticipant_c.number] = chatParticipant_c


class chatParticipantsForbidden_c:
    number = pack_number(0xfd2bb8a)
    is_base = False
    _data_cls = namedtuple('ChatParticipants', ['chat_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += chatParticipantsForbidden_c.number
        result += int_c.serialize(data.chat_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return chatParticipantsForbidden_c._data_cls(chat_id = int_c.deserialize(io_bytes))
combinators[chatParticipantsForbidden_c.number] = chatParticipantsForbidden_c


class chatParticipants_c:
    number = pack_number(0x7841b415)
    is_base = False
    _data_cls = namedtuple('ChatParticipants', ['chat_id', 'admin_id', 'participants', 'version'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += chatParticipants_c.number
        result += int_c.serialize(data.chat_id)
        result += int_c.serialize(data.admin_id)
        result += chatparticipant_c.serialize(data.participants)
        result += int_c.serialize(data.version)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return chatParticipants_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                            admin_id = int_c.deserialize(io_bytes),
                                            participants = deserialize(io_bytes),
                                            version = int_c.deserialize(io_bytes))
combinators[chatParticipants_c.number] = chatParticipants_c


class chatPhotoEmpty_c:
    number = pack_number(0x37c1011c)
    is_base = False
    _data_cls = namedtuple('ChatPhoto', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return chatPhotoEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert chatPhotoEmpty_c.number == number
        return chatPhotoEmpty_c._data_cls(tag='chatPhotoEmpty', number=chatPhotoEmpty_c.number)
combinators[chatPhotoEmpty_c.number] = chatPhotoEmpty_c


class chatPhoto_c:
    number = pack_number(0x6153276a)
    is_base = False
    _data_cls = namedtuple('ChatPhoto', ['photo_small', 'photo_big'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += chatPhoto_c.number
        result += filelocation_c.serialize(data.photo_small)
        result += filelocation_c.serialize(data.photo_big)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return chatPhoto_c._data_cls(photo_small = deserialize(io_bytes),
                                     photo_big = deserialize(io_bytes))
combinators[chatPhoto_c.number] = chatPhoto_c


class messageEmpty_c:
    number = pack_number(0x83e5de54)
    is_base = False
    _data_cls = namedtuple('Message', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageEmpty_c.number
        result += int_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageEmpty_c._data_cls(id = int_c.deserialize(io_bytes))
combinators[messageEmpty_c.number] = messageEmpty_c


class message_c:
    number = pack_number(0x22eb6aba)
    is_base = False
    _data_cls = namedtuple('Message', ['id', 'from_id', 'to_id', 'out', 'unread', 'date', 'message', 'media'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += message_c.number
        result += int_c.serialize(data.id)
        result += int_c.serialize(data.from_id)
        result += peer_c.serialize(data.to_id)
        result += bool_c.serialize(data.out)
        result += bool_c.serialize(data.unread)
        result += int_c.serialize(data.date)
        result += string_c.serialize(data.message)
        result += messagemedia_c.serialize(data.media)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return message_c._data_cls(id = int_c.deserialize(io_bytes),
                                   from_id = int_c.deserialize(io_bytes),
                                   to_id = deserialize(io_bytes),
                                   out = deserialize(io_bytes),
                                   unread = deserialize(io_bytes),
                                   date = int_c.deserialize(io_bytes),
                                   message = string_c.deserialize(io_bytes),
                                   media = deserialize(io_bytes))
combinators[message_c.number] = message_c


class messageForwarded_c:
    number = pack_number(0x5f46804)
    is_base = False
    _data_cls = namedtuple('Message', ['id', 'fwd_from_id', 'fwd_date', 'from_id', 'to_id', 'out', 'unread', 'date', 'message', 'media'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageForwarded_c.number
        result += int_c.serialize(data.id)
        result += int_c.serialize(data.fwd_from_id)
        result += int_c.serialize(data.fwd_date)
        result += int_c.serialize(data.from_id)
        result += peer_c.serialize(data.to_id)
        result += bool_c.serialize(data.out)
        result += bool_c.serialize(data.unread)
        result += int_c.serialize(data.date)
        result += string_c.serialize(data.message)
        result += messagemedia_c.serialize(data.media)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageForwarded_c._data_cls(id = int_c.deserialize(io_bytes),
                                            fwd_from_id = int_c.deserialize(io_bytes),
                                            fwd_date = int_c.deserialize(io_bytes),
                                            from_id = int_c.deserialize(io_bytes),
                                            to_id = deserialize(io_bytes),
                                            out = deserialize(io_bytes),
                                            unread = deserialize(io_bytes),
                                            date = int_c.deserialize(io_bytes),
                                            message = string_c.deserialize(io_bytes),
                                            media = deserialize(io_bytes))
combinators[messageForwarded_c.number] = messageForwarded_c


class messageService_c:
    number = pack_number(0x9f8d60bb)
    is_base = False
    _data_cls = namedtuple('Message', ['id', 'from_id', 'to_id', 'out', 'unread', 'date', 'action'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageService_c.number
        result += int_c.serialize(data.id)
        result += int_c.serialize(data.from_id)
        result += peer_c.serialize(data.to_id)
        result += bool_c.serialize(data.out)
        result += bool_c.serialize(data.unread)
        result += int_c.serialize(data.date)
        result += messageaction_c.serialize(data.action)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageService_c._data_cls(id = int_c.deserialize(io_bytes),
                                          from_id = int_c.deserialize(io_bytes),
                                          to_id = deserialize(io_bytes),
                                          out = deserialize(io_bytes),
                                          unread = deserialize(io_bytes),
                                          date = int_c.deserialize(io_bytes),
                                          action = deserialize(io_bytes))
combinators[messageService_c.number] = messageService_c


class messageMediaEmpty_c:
    number = pack_number(0x3ded6320)
    is_base = False
    _data_cls = namedtuple('MessageMedia', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return messageMediaEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert messageMediaEmpty_c.number == number
        return messageMediaEmpty_c._data_cls(tag='messageMediaEmpty', number=messageMediaEmpty_c.number)
combinators[messageMediaEmpty_c.number] = messageMediaEmpty_c


class messageMediaPhoto_c:
    number = pack_number(0xc8c45a2a)
    is_base = False
    _data_cls = namedtuple('MessageMedia', ['photo'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageMediaPhoto_c.number
        result += photo_c.serialize(data.photo)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageMediaPhoto_c._data_cls(photo = deserialize(io_bytes))
combinators[messageMediaPhoto_c.number] = messageMediaPhoto_c


class messageMediaVideo_c:
    number = pack_number(0xa2d24290)
    is_base = False
    _data_cls = namedtuple('MessageMedia', ['video'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageMediaVideo_c.number
        result += video_c.serialize(data.video)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageMediaVideo_c._data_cls(video = deserialize(io_bytes))
combinators[messageMediaVideo_c.number] = messageMediaVideo_c


class messageMediaGeo_c:
    number = pack_number(0x56e0d474)
    is_base = False
    _data_cls = namedtuple('MessageMedia', ['geo'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageMediaGeo_c.number
        result += geopoint_c.serialize(data.geo)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageMediaGeo_c._data_cls(geo = deserialize(io_bytes))
combinators[messageMediaGeo_c.number] = messageMediaGeo_c


class messageMediaContact_c:
    number = pack_number(0x5e7d2f39)
    is_base = False
    _data_cls = namedtuple('MessageMedia', ['phone_number', 'first_name', 'last_name', 'user_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageMediaContact_c.number
        result += string_c.serialize(data.phone_number)
        result += string_c.serialize(data.first_name)
        result += string_c.serialize(data.last_name)
        result += int_c.serialize(data.user_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageMediaContact_c._data_cls(phone_number = string_c.deserialize(io_bytes),
                                               first_name = string_c.deserialize(io_bytes),
                                               last_name = string_c.deserialize(io_bytes),
                                               user_id = int_c.deserialize(io_bytes))
combinators[messageMediaContact_c.number] = messageMediaContact_c


class messageMediaUnsupported_c:
    number = pack_number(0x29632a36)
    is_base = False
    _data_cls = namedtuple('MessageMedia', ['bytes'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageMediaUnsupported_c.number
        result += bytes_c.serialize(data.bytes)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageMediaUnsupported_c._data_cls(bytes = bytes_c.deserialize(io_bytes))
combinators[messageMediaUnsupported_c.number] = messageMediaUnsupported_c


class messageActionEmpty_c:
    number = pack_number(0xb6aef7b0)
    is_base = False
    _data_cls = namedtuple('MessageAction', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return messageActionEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert messageActionEmpty_c.number == number
        return messageActionEmpty_c._data_cls(tag='messageActionEmpty', number=messageActionEmpty_c.number)
combinators[messageActionEmpty_c.number] = messageActionEmpty_c


class messageActionChatCreate_c:
    number = pack_number(0xa6638b9a)
    is_base = False
    _data_cls = namedtuple('MessageAction', ['title', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageActionChatCreate_c.number
        result += string_c.serialize(data.title)
        result += int_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageActionChatCreate_c._data_cls(title = string_c.deserialize(io_bytes),
                                                   users = int_c.deserialize(io_bytes))
combinators[messageActionChatCreate_c.number] = messageActionChatCreate_c


class messageActionChatEditTitle_c:
    number = pack_number(0xb5a1ce5a)
    is_base = False
    _data_cls = namedtuple('MessageAction', ['title'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageActionChatEditTitle_c.number
        result += string_c.serialize(data.title)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageActionChatEditTitle_c._data_cls(title = string_c.deserialize(io_bytes))
combinators[messageActionChatEditTitle_c.number] = messageActionChatEditTitle_c


class messageActionChatEditPhoto_c:
    number = pack_number(0x7fcb13a8)
    is_base = False
    _data_cls = namedtuple('MessageAction', ['photo'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageActionChatEditPhoto_c.number
        result += photo_c.serialize(data.photo)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageActionChatEditPhoto_c._data_cls(photo = deserialize(io_bytes))
combinators[messageActionChatEditPhoto_c.number] = messageActionChatEditPhoto_c


class messageActionChatDeletePhoto_c:
    number = pack_number(0x95e3fbef)
    is_base = False
    _data_cls = namedtuple('MessageAction', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return messageActionChatDeletePhoto_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert messageActionChatDeletePhoto_c.number == number
        return messageActionChatDeletePhoto_c._data_cls(tag='messageActionChatDeletePhoto', number=messageActionChatDeletePhoto_c.number)
combinators[messageActionChatDeletePhoto_c.number] = messageActionChatDeletePhoto_c


class messageActionChatAddUser_c:
    number = pack_number(0x5e3cfc4b)
    is_base = False
    _data_cls = namedtuple('MessageAction', ['user_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageActionChatAddUser_c.number
        result += int_c.serialize(data.user_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageActionChatAddUser_c._data_cls(user_id = int_c.deserialize(io_bytes))
combinators[messageActionChatAddUser_c.number] = messageActionChatAddUser_c


class messageActionChatDeleteUser_c:
    number = pack_number(0xb2ae9b0c)
    is_base = False
    _data_cls = namedtuple('MessageAction', ['user_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageActionChatDeleteUser_c.number
        result += int_c.serialize(data.user_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageActionChatDeleteUser_c._data_cls(user_id = int_c.deserialize(io_bytes))
combinators[messageActionChatDeleteUser_c.number] = messageActionChatDeleteUser_c


class dialog_c:
    number = pack_number(0xab3a99ac)
    is_base = False
    _data_cls = namedtuple('Dialog', ['peer', 'top_message', 'unread_count', 'notify_settings'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += dialog_c.number
        result += peer_c.serialize(data.peer)
        result += int_c.serialize(data.top_message)
        result += int_c.serialize(data.unread_count)
        result += peernotifysettings_c.serialize(data.notify_settings)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return dialog_c._data_cls(peer = deserialize(io_bytes),
                                  top_message = int_c.deserialize(io_bytes),
                                  unread_count = int_c.deserialize(io_bytes),
                                  notify_settings = deserialize(io_bytes))
combinators[dialog_c.number] = dialog_c


class photoEmpty_c:
    number = pack_number(0x2331b22d)
    is_base = False
    _data_cls = namedtuple('Photo', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += photoEmpty_c.number
        result += long_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return photoEmpty_c._data_cls(id = long_c.deserialize(io_bytes))
combinators[photoEmpty_c.number] = photoEmpty_c


class photo_c:
    number = pack_number(0x22b56751)
    is_base = False
    _data_cls = namedtuple('Photo', ['id', 'access_hash', 'user_id', 'date', 'caption', 'geo', 'sizes'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += photo_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.date)
        result += string_c.serialize(data.caption)
        result += geopoint_c.serialize(data.geo)
        result += photosize_c.serialize(data.sizes)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return photo_c._data_cls(id = long_c.deserialize(io_bytes),
                                 access_hash = long_c.deserialize(io_bytes),
                                 user_id = int_c.deserialize(io_bytes),
                                 date = int_c.deserialize(io_bytes),
                                 caption = string_c.deserialize(io_bytes),
                                 geo = deserialize(io_bytes),
                                 sizes = deserialize(io_bytes))
combinators[photo_c.number] = photo_c


class photoSizeEmpty_c:
    number = pack_number(0xe17e23c)
    is_base = False
    _data_cls = namedtuple('PhotoSize', ['type'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += photoSizeEmpty_c.number
        result += string_c.serialize(data.type)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return photoSizeEmpty_c._data_cls(type = string_c.deserialize(io_bytes))
combinators[photoSizeEmpty_c.number] = photoSizeEmpty_c


class photoSize_c:
    number = pack_number(0x77bfb61b)
    is_base = False
    _data_cls = namedtuple('PhotoSize', ['type', 'location', 'w', 'h', 'size'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += photoSize_c.number
        result += string_c.serialize(data.type)
        result += filelocation_c.serialize(data.location)
        result += int_c.serialize(data.w)
        result += int_c.serialize(data.h)
        result += int_c.serialize(data.size)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return photoSize_c._data_cls(type = string_c.deserialize(io_bytes),
                                     location = deserialize(io_bytes),
                                     w = int_c.deserialize(io_bytes),
                                     h = int_c.deserialize(io_bytes),
                                     size = int_c.deserialize(io_bytes))
combinators[photoSize_c.number] = photoSize_c


class photoCachedSize_c:
    number = pack_number(0xe9a734fa)
    is_base = False
    _data_cls = namedtuple('PhotoSize', ['type', 'location', 'w', 'h', 'bytes'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += photoCachedSize_c.number
        result += string_c.serialize(data.type)
        result += filelocation_c.serialize(data.location)
        result += int_c.serialize(data.w)
        result += int_c.serialize(data.h)
        result += bytes_c.serialize(data.bytes)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return photoCachedSize_c._data_cls(type = string_c.deserialize(io_bytes),
                                           location = deserialize(io_bytes),
                                           w = int_c.deserialize(io_bytes),
                                           h = int_c.deserialize(io_bytes),
                                           bytes = bytes_c.deserialize(io_bytes))
combinators[photoCachedSize_c.number] = photoCachedSize_c


class videoEmpty_c:
    number = pack_number(0xc10658a8)
    is_base = False
    _data_cls = namedtuple('Video', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += videoEmpty_c.number
        result += long_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return videoEmpty_c._data_cls(id = long_c.deserialize(io_bytes))
combinators[videoEmpty_c.number] = videoEmpty_c


class video_c:
    number = pack_number(0x388fa391)
    is_base = False
    _data_cls = namedtuple('Video', ['id', 'access_hash', 'user_id', 'date', 'caption', 'duration', 'mime_type', 'size', 'thumb', 'dc_id', 'w', 'h'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += video_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.date)
        result += string_c.serialize(data.caption)
        result += int_c.serialize(data.duration)
        result += string_c.serialize(data.mime_type)
        result += int_c.serialize(data.size)
        result += photosize_c.serialize(data.thumb)
        result += int_c.serialize(data.dc_id)
        result += int_c.serialize(data.w)
        result += int_c.serialize(data.h)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return video_c._data_cls(id = long_c.deserialize(io_bytes),
                                 access_hash = long_c.deserialize(io_bytes),
                                 user_id = int_c.deserialize(io_bytes),
                                 date = int_c.deserialize(io_bytes),
                                 caption = string_c.deserialize(io_bytes),
                                 duration = int_c.deserialize(io_bytes),
                                 mime_type = string_c.deserialize(io_bytes),
                                 size = int_c.deserialize(io_bytes),
                                 thumb = deserialize(io_bytes),
                                 dc_id = int_c.deserialize(io_bytes),
                                 w = int_c.deserialize(io_bytes),
                                 h = int_c.deserialize(io_bytes))
combinators[video_c.number] = video_c


class geoPointEmpty_c:
    number = pack_number(0x1117dd5f)
    is_base = False
    _data_cls = namedtuple('GeoPoint', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return geoPointEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert geoPointEmpty_c.number == number
        return geoPointEmpty_c._data_cls(tag='geoPointEmpty', number=geoPointEmpty_c.number)
combinators[geoPointEmpty_c.number] = geoPointEmpty_c


class geoPoint_c:
    number = pack_number(0x2049d70c)
    is_base = False
    _data_cls = namedtuple('GeoPoint', ['long', 'lat'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += geoPoint_c.number
        result += double_c.serialize(data.long)
        result += double_c.serialize(data.lat)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return geoPoint_c._data_cls(long = double_c.deserialize(io_bytes),
                                    lat = double_c.deserialize(io_bytes))
combinators[geoPoint_c.number] = geoPoint_c


class checkedPhone_c:
    number = pack_number(0xe300cc3b)
    is_base = False
    _data_cls = namedtuple('CheckedPhone', ['phone_registered', 'phone_invited'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += checkedPhone_c.number
        result += bool_c.serialize(data.phone_registered)
        result += bool_c.serialize(data.phone_invited)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return checkedPhone_c._data_cls(phone_registered = deserialize(io_bytes),
                                        phone_invited = deserialize(io_bytes))
combinators[checkedPhone_c.number] = checkedPhone_c


class sentCode_c:
    number = pack_number(0xefed51d9)
    is_base = False
    _data_cls = namedtuple('SentCode', ['phone_registered', 'phone_code_hash', 'send_call_timeout', 'is_password'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sentCode_c.number
        result += bool_c.serialize(data.phone_registered)
        result += string_c.serialize(data.phone_code_hash)
        result += int_c.serialize(data.send_call_timeout)
        result += bool_c.serialize(data.is_password)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sentCode_c._data_cls(phone_registered = deserialize(io_bytes),
                                    phone_code_hash = string_c.deserialize(io_bytes),
                                    send_call_timeout = int_c.deserialize(io_bytes),
                                    is_password = deserialize(io_bytes))
combinators[sentCode_c.number] = sentCode_c


class authorization_c:
    number = pack_number(0xf6b673a4)
    is_base = False
    _data_cls = namedtuple('Authorization', ['expires', 'user'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += authorization_c.number
        result += int_c.serialize(data.expires)
        result += user_c.serialize(data.user)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return authorization_c._data_cls(expires = int_c.deserialize(io_bytes),
                                         user = deserialize(io_bytes))
combinators[authorization_c.number] = authorization_c


class exportedAuthorization_c:
    number = pack_number(0xdf969c2d)
    is_base = False
    _data_cls = namedtuple('ExportedAuthorization', ['id', 'bytes'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += exportedAuthorization_c.number
        result += int_c.serialize(data.id)
        result += bytes_c.serialize(data.bytes)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return exportedAuthorization_c._data_cls(id = int_c.deserialize(io_bytes),
                                                 bytes = bytes_c.deserialize(io_bytes))
combinators[exportedAuthorization_c.number] = exportedAuthorization_c


class inputNotifyPeer_c:
    number = pack_number(0xb8bc5b0c)
    is_base = False
    _data_cls = namedtuple('InputNotifyPeer', ['peer'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputNotifyPeer_c.number
        result += inputpeer_c.serialize(data.peer)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputNotifyPeer_c._data_cls(peer = deserialize(io_bytes))
combinators[inputNotifyPeer_c.number] = inputNotifyPeer_c


class inputNotifyUsers_c:
    number = pack_number(0x193b4417)
    is_base = False
    _data_cls = namedtuple('InputNotifyPeer', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputNotifyUsers_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputNotifyUsers_c.number == number
        return inputNotifyUsers_c._data_cls(tag='inputNotifyUsers', number=inputNotifyUsers_c.number)
combinators[inputNotifyUsers_c.number] = inputNotifyUsers_c


class inputNotifyChats_c:
    number = pack_number(0x4a95e84e)
    is_base = False
    _data_cls = namedtuple('InputNotifyPeer', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputNotifyChats_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputNotifyChats_c.number == number
        return inputNotifyChats_c._data_cls(tag='inputNotifyChats', number=inputNotifyChats_c.number)
combinators[inputNotifyChats_c.number] = inputNotifyChats_c


class inputNotifyAll_c:
    number = pack_number(0xa429b886)
    is_base = False
    _data_cls = namedtuple('InputNotifyPeer', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputNotifyAll_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputNotifyAll_c.number == number
        return inputNotifyAll_c._data_cls(tag='inputNotifyAll', number=inputNotifyAll_c.number)
combinators[inputNotifyAll_c.number] = inputNotifyAll_c


class inputPeerNotifyEventsEmpty_c:
    number = pack_number(0xf03064d8)
    is_base = False
    _data_cls = namedtuple('InputPeerNotifyEvents', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputPeerNotifyEventsEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputPeerNotifyEventsEmpty_c.number == number
        return inputPeerNotifyEventsEmpty_c._data_cls(tag='inputPeerNotifyEventsEmpty', number=inputPeerNotifyEventsEmpty_c.number)
combinators[inputPeerNotifyEventsEmpty_c.number] = inputPeerNotifyEventsEmpty_c


class inputPeerNotifyEventsAll_c:
    number = pack_number(0xe86a2c74)
    is_base = False
    _data_cls = namedtuple('InputPeerNotifyEvents', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputPeerNotifyEventsAll_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputPeerNotifyEventsAll_c.number == number
        return inputPeerNotifyEventsAll_c._data_cls(tag='inputPeerNotifyEventsAll', number=inputPeerNotifyEventsAll_c.number)
combinators[inputPeerNotifyEventsAll_c.number] = inputPeerNotifyEventsAll_c


class inputPeerNotifySettings_c:
    number = pack_number(0x46a2ce98)
    is_base = False
    _data_cls = namedtuple('InputPeerNotifySettings', ['mute_until', 'sound', 'show_previews', 'events_mask'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputPeerNotifySettings_c.number
        result += int_c.serialize(data.mute_until)
        result += string_c.serialize(data.sound)
        result += bool_c.serialize(data.show_previews)
        result += int_c.serialize(data.events_mask)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputPeerNotifySettings_c._data_cls(mute_until = int_c.deserialize(io_bytes),
                                                   sound = string_c.deserialize(io_bytes),
                                                   show_previews = deserialize(io_bytes),
                                                   events_mask = int_c.deserialize(io_bytes))
combinators[inputPeerNotifySettings_c.number] = inputPeerNotifySettings_c


class peerNotifyEventsEmpty_c:
    number = pack_number(0xadd53cb3)
    is_base = False
    _data_cls = namedtuple('PeerNotifyEvents', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return peerNotifyEventsEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert peerNotifyEventsEmpty_c.number == number
        return peerNotifyEventsEmpty_c._data_cls(tag='peerNotifyEventsEmpty', number=peerNotifyEventsEmpty_c.number)
combinators[peerNotifyEventsEmpty_c.number] = peerNotifyEventsEmpty_c


class peerNotifyEventsAll_c:
    number = pack_number(0x6d1ded88)
    is_base = False
    _data_cls = namedtuple('PeerNotifyEvents', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return peerNotifyEventsAll_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert peerNotifyEventsAll_c.number == number
        return peerNotifyEventsAll_c._data_cls(tag='peerNotifyEventsAll', number=peerNotifyEventsAll_c.number)
combinators[peerNotifyEventsAll_c.number] = peerNotifyEventsAll_c


class peerNotifySettingsEmpty_c:
    number = pack_number(0x70a68512)
    is_base = False
    _data_cls = namedtuple('PeerNotifySettings', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return peerNotifySettingsEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert peerNotifySettingsEmpty_c.number == number
        return peerNotifySettingsEmpty_c._data_cls(tag='peerNotifySettingsEmpty', number=peerNotifySettingsEmpty_c.number)
combinators[peerNotifySettingsEmpty_c.number] = peerNotifySettingsEmpty_c


class peerNotifySettings_c:
    number = pack_number(0x8d5e11ee)
    is_base = False
    _data_cls = namedtuple('PeerNotifySettings', ['mute_until', 'sound', 'show_previews', 'events_mask'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += peerNotifySettings_c.number
        result += int_c.serialize(data.mute_until)
        result += string_c.serialize(data.sound)
        result += bool_c.serialize(data.show_previews)
        result += int_c.serialize(data.events_mask)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return peerNotifySettings_c._data_cls(mute_until = int_c.deserialize(io_bytes),
                                              sound = string_c.deserialize(io_bytes),
                                              show_previews = deserialize(io_bytes),
                                              events_mask = int_c.deserialize(io_bytes))
combinators[peerNotifySettings_c.number] = peerNotifySettings_c


class wallPaper_c:
    number = pack_number(0xccb03657)
    is_base = False
    _data_cls = namedtuple('WallPaper', ['id', 'title', 'sizes', 'color'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += wallPaper_c.number
        result += int_c.serialize(data.id)
        result += string_c.serialize(data.title)
        result += photosize_c.serialize(data.sizes)
        result += int_c.serialize(data.color)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return wallPaper_c._data_cls(id = int_c.deserialize(io_bytes),
                                     title = string_c.deserialize(io_bytes),
                                     sizes = deserialize(io_bytes),
                                     color = int_c.deserialize(io_bytes))
combinators[wallPaper_c.number] = wallPaper_c


class userFull_c:
    number = pack_number(0x771095da)
    is_base = False
    _data_cls = namedtuple('UserFull', ['user', 'link', 'profile_photo', 'notify_settings', 'blocked', 'real_first_name', 'real_last_name'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += userFull_c.number
        result += user_c.serialize(data.user)
        result += link_c.serialize(data.link)
        result += photo_c.serialize(data.profile_photo)
        result += peernotifysettings_c.serialize(data.notify_settings)
        result += bool_c.serialize(data.blocked)
        result += string_c.serialize(data.real_first_name)
        result += string_c.serialize(data.real_last_name)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return userFull_c._data_cls(user = deserialize(io_bytes),
                                    link = deserialize(io_bytes),
                                    profile_photo = deserialize(io_bytes),
                                    notify_settings = deserialize(io_bytes),
                                    blocked = deserialize(io_bytes),
                                    real_first_name = string_c.deserialize(io_bytes),
                                    real_last_name = string_c.deserialize(io_bytes))
combinators[userFull_c.number] = userFull_c


class contact_c:
    number = pack_number(0xf911c994)
    is_base = False
    _data_cls = namedtuple('Contact', ['user_id', 'mutual'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += contact_c.number
        result += int_c.serialize(data.user_id)
        result += bool_c.serialize(data.mutual)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return contact_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                   mutual = deserialize(io_bytes))
combinators[contact_c.number] = contact_c


class importedContact_c:
    number = pack_number(0xd0028438)
    is_base = False
    _data_cls = namedtuple('ImportedContact', ['user_id', 'client_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += importedContact_c.number
        result += int_c.serialize(data.user_id)
        result += long_c.serialize(data.client_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return importedContact_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                           client_id = long_c.deserialize(io_bytes))
combinators[importedContact_c.number] = importedContact_c


class contactBlocked_c:
    number = pack_number(0x561bc879)
    is_base = False
    _data_cls = namedtuple('ContactBlocked', ['user_id', 'date'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += contactBlocked_c.number
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.date)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return contactBlocked_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                          date = int_c.deserialize(io_bytes))
combinators[contactBlocked_c.number] = contactBlocked_c


class contactSuggested_c:
    number = pack_number(0x3de191a1)
    is_base = False
    _data_cls = namedtuple('ContactSuggested', ['user_id', 'mutual_contacts'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += contactSuggested_c.number
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.mutual_contacts)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return contactSuggested_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                            mutual_contacts = int_c.deserialize(io_bytes))
combinators[contactSuggested_c.number] = contactSuggested_c


class contactStatus_c:
    number = pack_number(0xaa77b873)
    is_base = False
    _data_cls = namedtuple('ContactStatus', ['user_id', 'expires'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += contactStatus_c.number
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.expires)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return contactStatus_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                         expires = int_c.deserialize(io_bytes))
combinators[contactStatus_c.number] = contactStatus_c


class chatLocated_c:
    number = pack_number(0x3631cf4c)
    is_base = False
    _data_cls = namedtuple('ChatLocated', ['chat_id', 'distance'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += chatLocated_c.number
        result += int_c.serialize(data.chat_id)
        result += int_c.serialize(data.distance)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return chatLocated_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                       distance = int_c.deserialize(io_bytes))
combinators[chatLocated_c.number] = chatLocated_c


class foreignLinkUnknown_c:
    number = pack_number(0x133421f8)
    is_base = False
    _data_cls = namedtuple('ForeignLink', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return foreignLinkUnknown_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert foreignLinkUnknown_c.number == number
        return foreignLinkUnknown_c._data_cls(tag='contacts.foreignLinkUnknown', number=foreignLinkUnknown_c.number)
combinators[foreignLinkUnknown_c.number] = foreignLinkUnknown_c


class foreignLinkRequested_c:
    number = pack_number(0xa7801f47)
    is_base = False
    _data_cls = namedtuple('ForeignLink', ['has_phone'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += foreignLinkRequested_c.number
        result += bool_c.serialize(data.has_phone)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return foreignLinkRequested_c._data_cls(has_phone = deserialize(io_bytes))
combinators[foreignLinkRequested_c.number] = foreignLinkRequested_c


class foreignLinkMutual_c:
    number = pack_number(0x1bea8ce1)
    is_base = False
    _data_cls = namedtuple('ForeignLink', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return foreignLinkMutual_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert foreignLinkMutual_c.number == number
        return foreignLinkMutual_c._data_cls(tag='contacts.foreignLinkMutual', number=foreignLinkMutual_c.number)
combinators[foreignLinkMutual_c.number] = foreignLinkMutual_c


class myLinkEmpty_c:
    number = pack_number(0xd22a1c60)
    is_base = False
    _data_cls = namedtuple('MyLink', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return myLinkEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert myLinkEmpty_c.number == number
        return myLinkEmpty_c._data_cls(tag='contacts.myLinkEmpty', number=myLinkEmpty_c.number)
combinators[myLinkEmpty_c.number] = myLinkEmpty_c


class myLinkRequested_c:
    number = pack_number(0x6c69efee)
    is_base = False
    _data_cls = namedtuple('MyLink', ['contact'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += myLinkRequested_c.number
        result += bool_c.serialize(data.contact)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return myLinkRequested_c._data_cls(contact = deserialize(io_bytes))
combinators[myLinkRequested_c.number] = myLinkRequested_c


class myLinkContact_c:
    number = pack_number(0xc240ebd9)
    is_base = False
    _data_cls = namedtuple('MyLink', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return myLinkContact_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert myLinkContact_c.number == number
        return myLinkContact_c._data_cls(tag='contacts.myLinkContact', number=myLinkContact_c.number)
combinators[myLinkContact_c.number] = myLinkContact_c


class link_c:
    number = pack_number(0xeccea3f5)
    is_base = False
    _data_cls = namedtuple('Link', ['my_link', 'foreign_link', 'user'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += link_c.number
        result += mylink_c.serialize(data.my_link)
        result += foreignlink_c.serialize(data.foreign_link)
        result += user_c.serialize(data.user)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return link_c._data_cls(my_link = deserialize(io_bytes),
                                foreign_link = deserialize(io_bytes),
                                user = deserialize(io_bytes))
combinators[link_c.number] = link_c


class contactsNotModified_c:
    number = pack_number(0xb74ba9d2)
    is_base = False
    _data_cls = namedtuple('Contacts', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return contactsNotModified_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert contactsNotModified_c.number == number
        return contactsNotModified_c._data_cls(tag='contacts.contactsNotModified', number=contactsNotModified_c.number)
combinators[contactsNotModified_c.number] = contactsNotModified_c


class contacts_c:
    number = pack_number(0x6f8b8cb2)
    is_base = False
    _data_cls = namedtuple('Contacts', ['contacts', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += contacts_c.number
        result += contact_c.serialize(data.contacts)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return contacts_c._data_cls(contacts = deserialize(io_bytes),
                                    users = deserialize(io_bytes))
combinators[contacts_c.number] = contacts_c


class importedContacts_c:
    number = pack_number(0xad524315)
    is_base = False
    _data_cls = namedtuple('ImportedContacts', ['imported', 'retry_contacts', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += importedContacts_c.number
        result += importedcontact_c.serialize(data.imported)
        result += long_c.serialize(data.retry_contacts)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return importedContacts_c._data_cls(imported = deserialize(io_bytes),
                                            retry_contacts = long_c.deserialize(io_bytes),
                                            users = deserialize(io_bytes))
combinators[importedContacts_c.number] = importedContacts_c


class blocked_c:
    number = pack_number(0x1c138d15)
    is_base = False
    _data_cls = namedtuple('Blocked', ['blocked', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += blocked_c.number
        result += contactblocked_c.serialize(data.blocked)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return blocked_c._data_cls(blocked = deserialize(io_bytes),
                                   users = deserialize(io_bytes))
combinators[blocked_c.number] = blocked_c


class blockedSlice_c:
    number = pack_number(0x900802a1)
    is_base = False
    _data_cls = namedtuple('Blocked', ['count', 'blocked', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += blockedSlice_c.number
        result += int_c.serialize(data.count)
        result += contactblocked_c.serialize(data.blocked)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return blockedSlice_c._data_cls(count = int_c.deserialize(io_bytes),
                                        blocked = deserialize(io_bytes),
                                        users = deserialize(io_bytes))
combinators[blockedSlice_c.number] = blockedSlice_c


class suggested_c:
    number = pack_number(0x5649dcc5)
    is_base = False
    _data_cls = namedtuple('Suggested', ['results', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += suggested_c.number
        result += contactsuggested_c.serialize(data.results)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return suggested_c._data_cls(results = deserialize(io_bytes),
                                     users = deserialize(io_bytes))
combinators[suggested_c.number] = suggested_c


class dialogs_c:
    number = pack_number(0x15ba6c40)
    is_base = False
    _data_cls = namedtuple('Dialogs', ['dialogs', 'messages', 'chats', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += dialogs_c.number
        result += dialog_c.serialize(data.dialogs)
        result += message_c.serialize(data.messages)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return dialogs_c._data_cls(dialogs = deserialize(io_bytes),
                                   messages = deserialize(io_bytes),
                                   chats = deserialize(io_bytes),
                                   users = deserialize(io_bytes))
combinators[dialogs_c.number] = dialogs_c


class dialogsSlice_c:
    number = pack_number(0x71e094f3)
    is_base = False
    _data_cls = namedtuple('Dialogs', ['count', 'dialogs', 'messages', 'chats', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += dialogsSlice_c.number
        result += int_c.serialize(data.count)
        result += dialog_c.serialize(data.dialogs)
        result += message_c.serialize(data.messages)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return dialogsSlice_c._data_cls(count = int_c.deserialize(io_bytes),
                                        dialogs = deserialize(io_bytes),
                                        messages = deserialize(io_bytes),
                                        chats = deserialize(io_bytes),
                                        users = deserialize(io_bytes))
combinators[dialogsSlice_c.number] = dialogsSlice_c


class messages_c:
    number = pack_number(0x8c718e87)
    is_base = False
    _data_cls = namedtuple('Messages', ['messages', 'chats', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messages_c.number
        result += message_c.serialize(data.messages)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messages_c._data_cls(messages = deserialize(io_bytes),
                                    chats = deserialize(io_bytes),
                                    users = deserialize(io_bytes))
combinators[messages_c.number] = messages_c


class messagesSlice_c:
    number = pack_number(0xb446ae3)
    is_base = False
    _data_cls = namedtuple('Messages', ['count', 'messages', 'chats', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messagesSlice_c.number
        result += int_c.serialize(data.count)
        result += message_c.serialize(data.messages)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messagesSlice_c._data_cls(count = int_c.deserialize(io_bytes),
                                         messages = deserialize(io_bytes),
                                         chats = deserialize(io_bytes),
                                         users = deserialize(io_bytes))
combinators[messagesSlice_c.number] = messagesSlice_c


class messageEmpty_c:
    number = pack_number(0x3f4e0648)
    is_base = False
    _data_cls = namedtuple('Message', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return messageEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert messageEmpty_c.number == number
        return messageEmpty_c._data_cls(tag='messages.messageEmpty', number=messageEmpty_c.number)
combinators[messageEmpty_c.number] = messageEmpty_c


class statedMessages_c:
    number = pack_number(0x969478bb)
    is_base = False
    _data_cls = namedtuple('StatedMessages', ['messages', 'chats', 'users', 'pts', 'seq'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += statedMessages_c.number
        result += message_c.serialize(data.messages)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        result += int_c.serialize(data.pts)
        result += int_c.serialize(data.seq)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return statedMessages_c._data_cls(messages = deserialize(io_bytes),
                                          chats = deserialize(io_bytes),
                                          users = deserialize(io_bytes),
                                          pts = int_c.deserialize(io_bytes),
                                          seq = int_c.deserialize(io_bytes))
combinators[statedMessages_c.number] = statedMessages_c


class statedMessage_c:
    number = pack_number(0xd07ae726)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['message', 'chats', 'users', 'pts', 'seq'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += statedMessage_c.number
        result += message_c.serialize(data.message)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        result += int_c.serialize(data.pts)
        result += int_c.serialize(data.seq)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return statedMessage_c._data_cls(message = deserialize(io_bytes),
                                         chats = deserialize(io_bytes),
                                         users = deserialize(io_bytes),
                                         pts = int_c.deserialize(io_bytes),
                                         seq = int_c.deserialize(io_bytes))
combinators[statedMessage_c.number] = statedMessage_c


class sentMessage_c:
    number = pack_number(0xd1f4d35c)
    is_base = False
    _data_cls = namedtuple('SentMessage', ['id', 'date', 'pts', 'seq'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sentMessage_c.number
        result += int_c.serialize(data.id)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.pts)
        result += int_c.serialize(data.seq)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sentMessage_c._data_cls(id = int_c.deserialize(io_bytes),
                                       date = int_c.deserialize(io_bytes),
                                       pts = int_c.deserialize(io_bytes),
                                       seq = int_c.deserialize(io_bytes))
combinators[sentMessage_c.number] = sentMessage_c


class chats_c:
    number = pack_number(0x8150cbd8)
    is_base = False
    _data_cls = namedtuple('Chats', ['chats', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += chats_c.number
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return chats_c._data_cls(chats = deserialize(io_bytes),
                                 users = deserialize(io_bytes))
combinators[chats_c.number] = chats_c


class chatFull_c:
    number = pack_number(0xe5d7d19c)
    is_base = False
    _data_cls = namedtuple('ChatFull', ['full_chat', 'chats', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += chatFull_c.number
        result += chatfull_c.serialize(data.full_chat)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return chatFull_c._data_cls(full_chat = deserialize(io_bytes),
                                    chats = deserialize(io_bytes),
                                    users = deserialize(io_bytes))
combinators[chatFull_c.number] = chatFull_c


class affectedHistory_c:
    number = pack_number(0xb7de36f2)
    is_base = False
    _data_cls = namedtuple('AffectedHistory', ['pts', 'seq', 'offset'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += affectedHistory_c.number
        result += int_c.serialize(data.pts)
        result += int_c.serialize(data.seq)
        result += int_c.serialize(data.offset)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return affectedHistory_c._data_cls(pts = int_c.deserialize(io_bytes),
                                           seq = int_c.deserialize(io_bytes),
                                           offset = int_c.deserialize(io_bytes))
combinators[affectedHistory_c.number] = affectedHistory_c


class inputMessagesFilterEmpty_c:
    number = pack_number(0x57e2f66c)
    is_base = False
    _data_cls = namedtuple('MessagesFilter', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputMessagesFilterEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputMessagesFilterEmpty_c.number == number
        return inputMessagesFilterEmpty_c._data_cls(tag='inputMessagesFilterEmpty', number=inputMessagesFilterEmpty_c.number)
combinators[inputMessagesFilterEmpty_c.number] = inputMessagesFilterEmpty_c


class inputMessagesFilterPhotos_c:
    number = pack_number(0x9609a51c)
    is_base = False
    _data_cls = namedtuple('MessagesFilter', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputMessagesFilterPhotos_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputMessagesFilterPhotos_c.number == number
        return inputMessagesFilterPhotos_c._data_cls(tag='inputMessagesFilterPhotos', number=inputMessagesFilterPhotos_c.number)
combinators[inputMessagesFilterPhotos_c.number] = inputMessagesFilterPhotos_c


class inputMessagesFilterVideo_c:
    number = pack_number(0x9fc00e65)
    is_base = False
    _data_cls = namedtuple('MessagesFilter', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputMessagesFilterVideo_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputMessagesFilterVideo_c.number == number
        return inputMessagesFilterVideo_c._data_cls(tag='inputMessagesFilterVideo', number=inputMessagesFilterVideo_c.number)
combinators[inputMessagesFilterVideo_c.number] = inputMessagesFilterVideo_c


class inputMessagesFilterPhotoVideo_c:
    number = pack_number(0x56e9f0e4)
    is_base = False
    _data_cls = namedtuple('MessagesFilter', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputMessagesFilterPhotoVideo_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputMessagesFilterPhotoVideo_c.number == number
        return inputMessagesFilterPhotoVideo_c._data_cls(tag='inputMessagesFilterPhotoVideo', number=inputMessagesFilterPhotoVideo_c.number)
combinators[inputMessagesFilterPhotoVideo_c.number] = inputMessagesFilterPhotoVideo_c


class inputMessagesFilterPhotoVideoDocuments_c:
    number = pack_number(0xd95e73bb)
    is_base = False
    _data_cls = namedtuple('MessagesFilter', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputMessagesFilterPhotoVideoDocuments_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputMessagesFilterPhotoVideoDocuments_c.number == number
        return inputMessagesFilterPhotoVideoDocuments_c._data_cls(tag='inputMessagesFilterPhotoVideoDocuments', number=inputMessagesFilterPhotoVideoDocuments_c.number)
combinators[inputMessagesFilterPhotoVideoDocuments_c.number] = inputMessagesFilterPhotoVideoDocuments_c


class inputMessagesFilterDocument_c:
    number = pack_number(0x9eddf188)
    is_base = False
    _data_cls = namedtuple('MessagesFilter', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputMessagesFilterDocument_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputMessagesFilterDocument_c.number == number
        return inputMessagesFilterDocument_c._data_cls(tag='inputMessagesFilterDocument', number=inputMessagesFilterDocument_c.number)
combinators[inputMessagesFilterDocument_c.number] = inputMessagesFilterDocument_c


class inputMessagesFilterAudio_c:
    number = pack_number(0xcfc87522)
    is_base = False
    _data_cls = namedtuple('MessagesFilter', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputMessagesFilterAudio_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputMessagesFilterAudio_c.number == number
        return inputMessagesFilterAudio_c._data_cls(tag='inputMessagesFilterAudio', number=inputMessagesFilterAudio_c.number)
combinators[inputMessagesFilterAudio_c.number] = inputMessagesFilterAudio_c


class updateNewMessage_c:
    number = pack_number(0x13abdb3)
    is_base = False
    _data_cls = namedtuple('Update', ['message', 'pts'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateNewMessage_c.number
        result += message_c.serialize(data.message)
        result += int_c.serialize(data.pts)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateNewMessage_c._data_cls(message = deserialize(io_bytes),
                                            pts = int_c.deserialize(io_bytes))
combinators[updateNewMessage_c.number] = updateNewMessage_c


class updateMessageID_c:
    number = pack_number(0x4e90bfd6)
    is_base = False
    _data_cls = namedtuple('Update', ['id', 'random_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateMessageID_c.number
        result += int_c.serialize(data.id)
        result += long_c.serialize(data.random_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateMessageID_c._data_cls(id = int_c.deserialize(io_bytes),
                                           random_id = long_c.deserialize(io_bytes))
combinators[updateMessageID_c.number] = updateMessageID_c


class updateReadMessages_c:
    number = pack_number(0xc6649e31)
    is_base = False
    _data_cls = namedtuple('Update', ['messages', 'pts'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateReadMessages_c.number
        result += int_c.serialize(data.messages)
        result += int_c.serialize(data.pts)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateReadMessages_c._data_cls(messages = int_c.deserialize(io_bytes),
                                              pts = int_c.deserialize(io_bytes))
combinators[updateReadMessages_c.number] = updateReadMessages_c


class updateDeleteMessages_c:
    number = pack_number(0xa92bfe26)
    is_base = False
    _data_cls = namedtuple('Update', ['messages', 'pts'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateDeleteMessages_c.number
        result += int_c.serialize(data.messages)
        result += int_c.serialize(data.pts)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateDeleteMessages_c._data_cls(messages = int_c.deserialize(io_bytes),
                                                pts = int_c.deserialize(io_bytes))
combinators[updateDeleteMessages_c.number] = updateDeleteMessages_c


class updateUserTyping_c:
    number = pack_number(0x6baa8508)
    is_base = False
    _data_cls = namedtuple('Update', ['user_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateUserTyping_c.number
        result += int_c.serialize(data.user_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateUserTyping_c._data_cls(user_id = int_c.deserialize(io_bytes))
combinators[updateUserTyping_c.number] = updateUserTyping_c


class updateChatUserTyping_c:
    number = pack_number(0x3c46cfe6)
    is_base = False
    _data_cls = namedtuple('Update', ['chat_id', 'user_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateChatUserTyping_c.number
        result += int_c.serialize(data.chat_id)
        result += int_c.serialize(data.user_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateChatUserTyping_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                                user_id = int_c.deserialize(io_bytes))
combinators[updateChatUserTyping_c.number] = updateChatUserTyping_c


class updateChatParticipants_c:
    number = pack_number(0x7761198)
    is_base = False
    _data_cls = namedtuple('Update', ['participants'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateChatParticipants_c.number
        result += chatparticipants_c.serialize(data.participants)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateChatParticipants_c._data_cls(participants = deserialize(io_bytes))
combinators[updateChatParticipants_c.number] = updateChatParticipants_c


class updateUserStatus_c:
    number = pack_number(0x1bfbd823)
    is_base = False
    _data_cls = namedtuple('Update', ['user_id', 'status'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateUserStatus_c.number
        result += int_c.serialize(data.user_id)
        result += userstatus_c.serialize(data.status)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateUserStatus_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                            status = deserialize(io_bytes))
combinators[updateUserStatus_c.number] = updateUserStatus_c


class updateUserName_c:
    number = pack_number(0xda22d9ad)
    is_base = False
    _data_cls = namedtuple('Update', ['user_id', 'first_name', 'last_name'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateUserName_c.number
        result += int_c.serialize(data.user_id)
        result += string_c.serialize(data.first_name)
        result += string_c.serialize(data.last_name)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateUserName_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                          first_name = string_c.deserialize(io_bytes),
                                          last_name = string_c.deserialize(io_bytes))
combinators[updateUserName_c.number] = updateUserName_c


class updateUserPhoto_c:
    number = pack_number(0x95313b0c)
    is_base = False
    _data_cls = namedtuple('Update', ['user_id', 'date', 'photo', 'previous'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateUserPhoto_c.number
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.date)
        result += userprofilephoto_c.serialize(data.photo)
        result += bool_c.serialize(data.previous)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateUserPhoto_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                           date = int_c.deserialize(io_bytes),
                                           photo = deserialize(io_bytes),
                                           previous = deserialize(io_bytes))
combinators[updateUserPhoto_c.number] = updateUserPhoto_c


class updateContactRegistered_c:
    number = pack_number(0x2575bbb9)
    is_base = False
    _data_cls = namedtuple('Update', ['user_id', 'date'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateContactRegistered_c.number
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.date)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateContactRegistered_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                                   date = int_c.deserialize(io_bytes))
combinators[updateContactRegistered_c.number] = updateContactRegistered_c


class updateContactLink_c:
    number = pack_number(0x51a48a9a)
    is_base = False
    _data_cls = namedtuple('Update', ['user_id', 'my_link', 'foreign_link'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateContactLink_c.number
        result += int_c.serialize(data.user_id)
        result += mylink_c.serialize(data.my_link)
        result += foreignlink_c.serialize(data.foreign_link)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateContactLink_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                             my_link = deserialize(io_bytes),
                                             foreign_link = deserialize(io_bytes))
combinators[updateContactLink_c.number] = updateContactLink_c


class updateNewAuthorization_c:
    number = pack_number(0x8f06529a)
    is_base = False
    _data_cls = namedtuple('Update', ['auth_key_id', 'date', 'device', 'location'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateNewAuthorization_c.number
        result += long_c.serialize(data.auth_key_id)
        result += int_c.serialize(data.date)
        result += string_c.serialize(data.device)
        result += string_c.serialize(data.location)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateNewAuthorization_c._data_cls(auth_key_id = long_c.deserialize(io_bytes),
                                                  date = int_c.deserialize(io_bytes),
                                                  device = string_c.deserialize(io_bytes),
                                                  location = string_c.deserialize(io_bytes))
combinators[updateNewAuthorization_c.number] = updateNewAuthorization_c


class state_c:
    number = pack_number(0xa56c2a3e)
    is_base = False
    _data_cls = namedtuple('State', ['pts', 'qts', 'date', 'seq', 'unread_count'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += state_c.number
        result += int_c.serialize(data.pts)
        result += int_c.serialize(data.qts)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.seq)
        result += int_c.serialize(data.unread_count)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return state_c._data_cls(pts = int_c.deserialize(io_bytes),
                                 qts = int_c.deserialize(io_bytes),
                                 date = int_c.deserialize(io_bytes),
                                 seq = int_c.deserialize(io_bytes),
                                 unread_count = int_c.deserialize(io_bytes))
combinators[state_c.number] = state_c


class differenceEmpty_c:
    number = pack_number(0x5d75a138)
    is_base = False
    _data_cls = namedtuple('Difference', ['date', 'seq'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += differenceEmpty_c.number
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.seq)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return differenceEmpty_c._data_cls(date = int_c.deserialize(io_bytes),
                                           seq = int_c.deserialize(io_bytes))
combinators[differenceEmpty_c.number] = differenceEmpty_c


class difference_c:
    number = pack_number(0xf49ca0)
    is_base = False
    _data_cls = namedtuple('Difference', ['new_messages', 'new_encrypted_messages', 'other_updates', 'chats', 'users', 'state'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += difference_c.number
        result += message_c.serialize(data.new_messages)
        result += encryptedmessage_c.serialize(data.new_encrypted_messages)
        result += update_c.serialize(data.other_updates)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        result += state_c.serialize(data.state)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return difference_c._data_cls(new_messages = deserialize(io_bytes),
                                      new_encrypted_messages = deserialize(io_bytes),
                                      other_updates = deserialize(io_bytes),
                                      chats = deserialize(io_bytes),
                                      users = deserialize(io_bytes),
                                      state = deserialize(io_bytes))
combinators[difference_c.number] = difference_c


class differenceSlice_c:
    number = pack_number(0xa8fb1981)
    is_base = False
    _data_cls = namedtuple('Difference', ['new_messages', 'new_encrypted_messages', 'other_updates', 'chats', 'users', 'intermediate_state'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += differenceSlice_c.number
        result += message_c.serialize(data.new_messages)
        result += encryptedmessage_c.serialize(data.new_encrypted_messages)
        result += update_c.serialize(data.other_updates)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        result += state_c.serialize(data.intermediate_state)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return differenceSlice_c._data_cls(new_messages = deserialize(io_bytes),
                                           new_encrypted_messages = deserialize(io_bytes),
                                           other_updates = deserialize(io_bytes),
                                           chats = deserialize(io_bytes),
                                           users = deserialize(io_bytes),
                                           intermediate_state = deserialize(io_bytes))
combinators[differenceSlice_c.number] = differenceSlice_c


class updatesTooLong_c:
    number = pack_number(0xe317af7e)
    is_base = False
    _data_cls = namedtuple('Updates', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return updatesTooLong_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert updatesTooLong_c.number == number
        return updatesTooLong_c._data_cls(tag='updatesTooLong', number=updatesTooLong_c.number)
combinators[updatesTooLong_c.number] = updatesTooLong_c


class updateShortMessage_c:
    number = pack_number(0xd3f45784)
    is_base = False
    _data_cls = namedtuple('Updates', ['id', 'from_id', 'message', 'pts', 'date', 'seq'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateShortMessage_c.number
        result += int_c.serialize(data.id)
        result += int_c.serialize(data.from_id)
        result += string_c.serialize(data.message)
        result += int_c.serialize(data.pts)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.seq)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateShortMessage_c._data_cls(id = int_c.deserialize(io_bytes),
                                              from_id = int_c.deserialize(io_bytes),
                                              message = string_c.deserialize(io_bytes),
                                              pts = int_c.deserialize(io_bytes),
                                              date = int_c.deserialize(io_bytes),
                                              seq = int_c.deserialize(io_bytes))
combinators[updateShortMessage_c.number] = updateShortMessage_c


class updateShortChatMessage_c:
    number = pack_number(0x2b2fbd4e)
    is_base = False
    _data_cls = namedtuple('Updates', ['id', 'from_id', 'chat_id', 'message', 'pts', 'date', 'seq'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateShortChatMessage_c.number
        result += int_c.serialize(data.id)
        result += int_c.serialize(data.from_id)
        result += int_c.serialize(data.chat_id)
        result += string_c.serialize(data.message)
        result += int_c.serialize(data.pts)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.seq)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateShortChatMessage_c._data_cls(id = int_c.deserialize(io_bytes),
                                                  from_id = int_c.deserialize(io_bytes),
                                                  chat_id = int_c.deserialize(io_bytes),
                                                  message = string_c.deserialize(io_bytes),
                                                  pts = int_c.deserialize(io_bytes),
                                                  date = int_c.deserialize(io_bytes),
                                                  seq = int_c.deserialize(io_bytes))
combinators[updateShortChatMessage_c.number] = updateShortChatMessage_c


class updateShort_c:
    number = pack_number(0x78d4dec1)
    is_base = False
    _data_cls = namedtuple('Updates', ['update', 'date'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateShort_c.number
        result += update_c.serialize(data.update)
        result += int_c.serialize(data.date)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateShort_c._data_cls(update = deserialize(io_bytes),
                                       date = int_c.deserialize(io_bytes))
combinators[updateShort_c.number] = updateShort_c


class updatesCombined_c:
    number = pack_number(0x725b04c3)
    is_base = False
    _data_cls = namedtuple('Updates', ['updates', 'users', 'chats', 'date', 'seq_start', 'seq'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updatesCombined_c.number
        result += update_c.serialize(data.updates)
        result += user_c.serialize(data.users)
        result += chat_c.serialize(data.chats)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.seq_start)
        result += int_c.serialize(data.seq)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updatesCombined_c._data_cls(updates = deserialize(io_bytes),
                                           users = deserialize(io_bytes),
                                           chats = deserialize(io_bytes),
                                           date = int_c.deserialize(io_bytes),
                                           seq_start = int_c.deserialize(io_bytes),
                                           seq = int_c.deserialize(io_bytes))
combinators[updatesCombined_c.number] = updatesCombined_c


class updates_c:
    number = pack_number(0x74ae4240)
    is_base = False
    _data_cls = namedtuple('Updates', ['updates', 'users', 'chats', 'date', 'seq'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updates_c.number
        result += update_c.serialize(data.updates)
        result += user_c.serialize(data.users)
        result += chat_c.serialize(data.chats)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.seq)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updates_c._data_cls(updates = deserialize(io_bytes),
                                   users = deserialize(io_bytes),
                                   chats = deserialize(io_bytes),
                                   date = int_c.deserialize(io_bytes),
                                   seq = int_c.deserialize(io_bytes))
combinators[updates_c.number] = updates_c


class photos_c:
    number = pack_number(0x8dca6aa5)
    is_base = False
    _data_cls = namedtuple('Photos', ['photos', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += photos_c.number
        result += photo_c.serialize(data.photos)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return photos_c._data_cls(photos = deserialize(io_bytes),
                                  users = deserialize(io_bytes))
combinators[photos_c.number] = photos_c


class photosSlice_c:
    number = pack_number(0x15051f54)
    is_base = False
    _data_cls = namedtuple('Photos', ['count', 'photos', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += photosSlice_c.number
        result += int_c.serialize(data.count)
        result += photo_c.serialize(data.photos)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return photosSlice_c._data_cls(count = int_c.deserialize(io_bytes),
                                       photos = deserialize(io_bytes),
                                       users = deserialize(io_bytes))
combinators[photosSlice_c.number] = photosSlice_c


class photo_c:
    number = pack_number(0x20212ca8)
    is_base = False
    _data_cls = namedtuple('Photo', ['photo', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += photo_c.number
        result += photo_c.serialize(data.photo)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return photo_c._data_cls(photo = deserialize(io_bytes),
                                 users = deserialize(io_bytes))
combinators[photo_c.number] = photo_c


class file_c:
    number = pack_number(0x96a18d5)
    is_base = False
    _data_cls = namedtuple('File', ['type', 'mtime', 'bytes'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += file_c.number
        result += filetype_c.serialize(data.type)
        result += int_c.serialize(data.mtime)
        result += bytes_c.serialize(data.bytes)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return file_c._data_cls(type = deserialize(io_bytes),
                                mtime = int_c.deserialize(io_bytes),
                                bytes = bytes_c.deserialize(io_bytes))
combinators[file_c.number] = file_c


class dcOption_c:
    number = pack_number(0x2ec2a43c)
    is_base = False
    _data_cls = namedtuple('DcOption', ['id', 'hostname', 'ip_address', 'port'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += dcOption_c.number
        result += int_c.serialize(data.id)
        result += string_c.serialize(data.hostname)
        result += string_c.serialize(data.ip_address)
        result += int_c.serialize(data.port)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return dcOption_c._data_cls(id = int_c.deserialize(io_bytes),
                                    hostname = string_c.deserialize(io_bytes),
                                    ip_address = string_c.deserialize(io_bytes),
                                    port = int_c.deserialize(io_bytes))
combinators[dcOption_c.number] = dcOption_c


class config_c:
    number = pack_number(0x2e54dd74)
    is_base = False
    _data_cls = namedtuple('Config', ['date', 'test_mode', 'this_dc', 'dc_options', 'chat_size_max', 'broadcast_size_max'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += config_c.number
        result += int_c.serialize(data.date)
        result += bool_c.serialize(data.test_mode)
        result += int_c.serialize(data.this_dc)
        result += dcoption_c.serialize(data.dc_options)
        result += int_c.serialize(data.chat_size_max)
        result += int_c.serialize(data.broadcast_size_max)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return config_c._data_cls(date = int_c.deserialize(io_bytes),
                                  test_mode = deserialize(io_bytes),
                                  this_dc = int_c.deserialize(io_bytes),
                                  dc_options = deserialize(io_bytes),
                                  chat_size_max = int_c.deserialize(io_bytes),
                                  broadcast_size_max = int_c.deserialize(io_bytes))
combinators[config_c.number] = config_c


class nearestDc_c:
    number = pack_number(0x8e1a1775)
    is_base = False
    _data_cls = namedtuple('NearestDc', ['country', 'this_dc', 'nearest_dc'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += nearestDc_c.number
        result += string_c.serialize(data.country)
        result += int_c.serialize(data.this_dc)
        result += int_c.serialize(data.nearest_dc)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return nearestDc_c._data_cls(country = string_c.deserialize(io_bytes),
                                     this_dc = int_c.deserialize(io_bytes),
                                     nearest_dc = int_c.deserialize(io_bytes))
combinators[nearestDc_c.number] = nearestDc_c


class appUpdate_c:
    number = pack_number(0x8987f311)
    is_base = False
    _data_cls = namedtuple('AppUpdate', ['id', 'critical', 'url', 'text'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += appUpdate_c.number
        result += int_c.serialize(data.id)
        result += bool_c.serialize(data.critical)
        result += string_c.serialize(data.url)
        result += string_c.serialize(data.text)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return appUpdate_c._data_cls(id = int_c.deserialize(io_bytes),
                                     critical = deserialize(io_bytes),
                                     url = string_c.deserialize(io_bytes),
                                     text = string_c.deserialize(io_bytes))
combinators[appUpdate_c.number] = appUpdate_c


class noAppUpdate_c:
    number = pack_number(0xc45a6536)
    is_base = False
    _data_cls = namedtuple('AppUpdate', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return noAppUpdate_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert noAppUpdate_c.number == number
        return noAppUpdate_c._data_cls(tag='help.noAppUpdate', number=noAppUpdate_c.number)
combinators[noAppUpdate_c.number] = noAppUpdate_c


class inviteText_c:
    number = pack_number(0x18cb9f78)
    is_base = False
    _data_cls = namedtuple('InviteText', ['message'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inviteText_c.number
        result += string_c.serialize(data.message)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inviteText_c._data_cls(message = string_c.deserialize(io_bytes))
combinators[inviteText_c.number] = inviteText_c


class statedMessagesLinks_c:
    number = pack_number(0x3e74f5c6)
    is_base = False
    _data_cls = namedtuple('StatedMessages', ['messages', 'chats', 'users', 'links', 'pts', 'seq'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += statedMessagesLinks_c.number
        result += message_c.serialize(data.messages)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        result += link_c.serialize(data.links)
        result += int_c.serialize(data.pts)
        result += int_c.serialize(data.seq)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return statedMessagesLinks_c._data_cls(messages = deserialize(io_bytes),
                                               chats = deserialize(io_bytes),
                                               users = deserialize(io_bytes),
                                               links = deserialize(io_bytes),
                                               pts = int_c.deserialize(io_bytes),
                                               seq = int_c.deserialize(io_bytes))
combinators[statedMessagesLinks_c.number] = statedMessagesLinks_c


class statedMessageLink_c:
    number = pack_number(0xa9af2881)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['message', 'chats', 'users', 'links', 'pts', 'seq'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += statedMessageLink_c.number
        result += message_c.serialize(data.message)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        result += link_c.serialize(data.links)
        result += int_c.serialize(data.pts)
        result += int_c.serialize(data.seq)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return statedMessageLink_c._data_cls(message = deserialize(io_bytes),
                                             chats = deserialize(io_bytes),
                                             users = deserialize(io_bytes),
                                             links = deserialize(io_bytes),
                                             pts = int_c.deserialize(io_bytes),
                                             seq = int_c.deserialize(io_bytes))
combinators[statedMessageLink_c.number] = statedMessageLink_c


class sentMessageLink_c:
    number = pack_number(0xe9db4a3f)
    is_base = False
    _data_cls = namedtuple('SentMessage', ['id', 'date', 'pts', 'seq', 'links'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sentMessageLink_c.number
        result += int_c.serialize(data.id)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.pts)
        result += int_c.serialize(data.seq)
        result += link_c.serialize(data.links)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sentMessageLink_c._data_cls(id = int_c.deserialize(io_bytes),
                                           date = int_c.deserialize(io_bytes),
                                           pts = int_c.deserialize(io_bytes),
                                           seq = int_c.deserialize(io_bytes),
                                           links = deserialize(io_bytes))
combinators[sentMessageLink_c.number] = sentMessageLink_c


class inputGeoChat_c:
    number = pack_number(0x74d456fa)
    is_base = False
    _data_cls = namedtuple('InputGeoChat', ['chat_id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputGeoChat_c.number
        result += int_c.serialize(data.chat_id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputGeoChat_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                        access_hash = long_c.deserialize(io_bytes))
combinators[inputGeoChat_c.number] = inputGeoChat_c


class inputNotifyGeoChatPeer_c:
    number = pack_number(0x4d8ddec8)
    is_base = False
    _data_cls = namedtuple('InputNotifyPeer', ['peer'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputNotifyGeoChatPeer_c.number
        result += inputgeochat_c.serialize(data.peer)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputNotifyGeoChatPeer_c._data_cls(peer = deserialize(io_bytes))
combinators[inputNotifyGeoChatPeer_c.number] = inputNotifyGeoChatPeer_c


class geoChat_c:
    number = pack_number(0x75eaea5a)
    is_base = False
    _data_cls = namedtuple('Chat', ['id', 'access_hash', 'title', 'address', 'venue', 'geo', 'photo', 'participants_count', 'date', 'checked_in', 'version'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += geoChat_c.number
        result += int_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        result += string_c.serialize(data.title)
        result += string_c.serialize(data.address)
        result += string_c.serialize(data.venue)
        result += geopoint_c.serialize(data.geo)
        result += chatphoto_c.serialize(data.photo)
        result += int_c.serialize(data.participants_count)
        result += int_c.serialize(data.date)
        result += bool_c.serialize(data.checked_in)
        result += int_c.serialize(data.version)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return geoChat_c._data_cls(id = int_c.deserialize(io_bytes),
                                   access_hash = long_c.deserialize(io_bytes),
                                   title = string_c.deserialize(io_bytes),
                                   address = string_c.deserialize(io_bytes),
                                   venue = string_c.deserialize(io_bytes),
                                   geo = deserialize(io_bytes),
                                   photo = deserialize(io_bytes),
                                   participants_count = int_c.deserialize(io_bytes),
                                   date = int_c.deserialize(io_bytes),
                                   checked_in = deserialize(io_bytes),
                                   version = int_c.deserialize(io_bytes))
combinators[geoChat_c.number] = geoChat_c


class geoChatMessageEmpty_c:
    number = pack_number(0x60311a9b)
    is_base = False
    _data_cls = namedtuple('GeoChatMessage', ['chat_id', 'id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += geoChatMessageEmpty_c.number
        result += int_c.serialize(data.chat_id)
        result += int_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return geoChatMessageEmpty_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                               id = int_c.deserialize(io_bytes))
combinators[geoChatMessageEmpty_c.number] = geoChatMessageEmpty_c


class geoChatMessage_c:
    number = pack_number(0x4505f8e1)
    is_base = False
    _data_cls = namedtuple('GeoChatMessage', ['chat_id', 'id', 'from_id', 'date', 'message', 'media'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += geoChatMessage_c.number
        result += int_c.serialize(data.chat_id)
        result += int_c.serialize(data.id)
        result += int_c.serialize(data.from_id)
        result += int_c.serialize(data.date)
        result += string_c.serialize(data.message)
        result += messagemedia_c.serialize(data.media)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return geoChatMessage_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                          id = int_c.deserialize(io_bytes),
                                          from_id = int_c.deserialize(io_bytes),
                                          date = int_c.deserialize(io_bytes),
                                          message = string_c.deserialize(io_bytes),
                                          media = deserialize(io_bytes))
combinators[geoChatMessage_c.number] = geoChatMessage_c


class geoChatMessageService_c:
    number = pack_number(0xd34fa24e)
    is_base = False
    _data_cls = namedtuple('GeoChatMessage', ['chat_id', 'id', 'from_id', 'date', 'action'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += geoChatMessageService_c.number
        result += int_c.serialize(data.chat_id)
        result += int_c.serialize(data.id)
        result += int_c.serialize(data.from_id)
        result += int_c.serialize(data.date)
        result += messageaction_c.serialize(data.action)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return geoChatMessageService_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                                 id = int_c.deserialize(io_bytes),
                                                 from_id = int_c.deserialize(io_bytes),
                                                 date = int_c.deserialize(io_bytes),
                                                 action = deserialize(io_bytes))
combinators[geoChatMessageService_c.number] = geoChatMessageService_c


class statedMessage_c:
    number = pack_number(0x17b1578b)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['message', 'chats', 'users', 'seq'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += statedMessage_c.number
        result += geochatmessage_c.serialize(data.message)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        result += int_c.serialize(data.seq)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return statedMessage_c._data_cls(message = deserialize(io_bytes),
                                         chats = deserialize(io_bytes),
                                         users = deserialize(io_bytes),
                                         seq = int_c.deserialize(io_bytes))
combinators[statedMessage_c.number] = statedMessage_c


class located_c:
    number = pack_number(0x48feb267)
    is_base = False
    _data_cls = namedtuple('Located', ['results', 'messages', 'chats', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += located_c.number
        result += chatlocated_c.serialize(data.results)
        result += geochatmessage_c.serialize(data.messages)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return located_c._data_cls(results = deserialize(io_bytes),
                                   messages = deserialize(io_bytes),
                                   chats = deserialize(io_bytes),
                                   users = deserialize(io_bytes))
combinators[located_c.number] = located_c


class messages_c:
    number = pack_number(0xd1526db1)
    is_base = False
    _data_cls = namedtuple('Messages', ['messages', 'chats', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messages_c.number
        result += geochatmessage_c.serialize(data.messages)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messages_c._data_cls(messages = deserialize(io_bytes),
                                    chats = deserialize(io_bytes),
                                    users = deserialize(io_bytes))
combinators[messages_c.number] = messages_c


class messagesSlice_c:
    number = pack_number(0xbc5863e8)
    is_base = False
    _data_cls = namedtuple('Messages', ['count', 'messages', 'chats', 'users'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messagesSlice_c.number
        result += int_c.serialize(data.count)
        result += geochatmessage_c.serialize(data.messages)
        result += chat_c.serialize(data.chats)
        result += user_c.serialize(data.users)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messagesSlice_c._data_cls(count = int_c.deserialize(io_bytes),
                                         messages = deserialize(io_bytes),
                                         chats = deserialize(io_bytes),
                                         users = deserialize(io_bytes))
combinators[messagesSlice_c.number] = messagesSlice_c


class messageActionGeoChatCreate_c:
    number = pack_number(0x6f038ebc)
    is_base = False
    _data_cls = namedtuple('MessageAction', ['title', 'address'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageActionGeoChatCreate_c.number
        result += string_c.serialize(data.title)
        result += string_c.serialize(data.address)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageActionGeoChatCreate_c._data_cls(title = string_c.deserialize(io_bytes),
                                                      address = string_c.deserialize(io_bytes))
combinators[messageActionGeoChatCreate_c.number] = messageActionGeoChatCreate_c


class messageActionGeoChatCheckin_c:
    number = pack_number(0xc7d53de)
    is_base = False
    _data_cls = namedtuple('MessageAction', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return messageActionGeoChatCheckin_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert messageActionGeoChatCheckin_c.number == number
        return messageActionGeoChatCheckin_c._data_cls(tag='messageActionGeoChatCheckin', number=messageActionGeoChatCheckin_c.number)
combinators[messageActionGeoChatCheckin_c.number] = messageActionGeoChatCheckin_c


class updateNewGeoChatMessage_c:
    number = pack_number(0x5a68e3f7)
    is_base = False
    _data_cls = namedtuple('Update', ['message'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateNewGeoChatMessage_c.number
        result += geochatmessage_c.serialize(data.message)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateNewGeoChatMessage_c._data_cls(message = deserialize(io_bytes))
combinators[updateNewGeoChatMessage_c.number] = updateNewGeoChatMessage_c


class wallPaperSolid_c:
    number = pack_number(0x63117f24)
    is_base = False
    _data_cls = namedtuple('WallPaper', ['id', 'title', 'bg_color', 'color'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += wallPaperSolid_c.number
        result += int_c.serialize(data.id)
        result += string_c.serialize(data.title)
        result += int_c.serialize(data.bg_color)
        result += int_c.serialize(data.color)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return wallPaperSolid_c._data_cls(id = int_c.deserialize(io_bytes),
                                          title = string_c.deserialize(io_bytes),
                                          bg_color = int_c.deserialize(io_bytes),
                                          color = int_c.deserialize(io_bytes))
combinators[wallPaperSolid_c.number] = wallPaperSolid_c


class updateNewEncryptedMessage_c:
    number = pack_number(0x12bcbd9a)
    is_base = False
    _data_cls = namedtuple('Update', ['message', 'qts'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateNewEncryptedMessage_c.number
        result += encryptedmessage_c.serialize(data.message)
        result += int_c.serialize(data.qts)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateNewEncryptedMessage_c._data_cls(message = deserialize(io_bytes),
                                                     qts = int_c.deserialize(io_bytes))
combinators[updateNewEncryptedMessage_c.number] = updateNewEncryptedMessage_c


class updateEncryptedChatTyping_c:
    number = pack_number(0x1710f156)
    is_base = False
    _data_cls = namedtuple('Update', ['chat_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateEncryptedChatTyping_c.number
        result += int_c.serialize(data.chat_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateEncryptedChatTyping_c._data_cls(chat_id = int_c.deserialize(io_bytes))
combinators[updateEncryptedChatTyping_c.number] = updateEncryptedChatTyping_c


class updateEncryption_c:
    number = pack_number(0xb4a2e88d)
    is_base = False
    _data_cls = namedtuple('Update', ['chat', 'date'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateEncryption_c.number
        result += encryptedchat_c.serialize(data.chat)
        result += int_c.serialize(data.date)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateEncryption_c._data_cls(chat = deserialize(io_bytes),
                                            date = int_c.deserialize(io_bytes))
combinators[updateEncryption_c.number] = updateEncryption_c


class updateEncryptedMessagesRead_c:
    number = pack_number(0x38fe25b7)
    is_base = False
    _data_cls = namedtuple('Update', ['chat_id', 'max_date', 'date'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateEncryptedMessagesRead_c.number
        result += int_c.serialize(data.chat_id)
        result += int_c.serialize(data.max_date)
        result += int_c.serialize(data.date)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateEncryptedMessagesRead_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                                       max_date = int_c.deserialize(io_bytes),
                                                       date = int_c.deserialize(io_bytes))
combinators[updateEncryptedMessagesRead_c.number] = updateEncryptedMessagesRead_c


class encryptedChatEmpty_c:
    number = pack_number(0xab7ec0a0)
    is_base = False
    _data_cls = namedtuple('EncryptedChat', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += encryptedChatEmpty_c.number
        result += int_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return encryptedChatEmpty_c._data_cls(id = int_c.deserialize(io_bytes))
combinators[encryptedChatEmpty_c.number] = encryptedChatEmpty_c


class encryptedChatWaiting_c:
    number = pack_number(0x3bf703dc)
    is_base = False
    _data_cls = namedtuple('EncryptedChat', ['id', 'access_hash', 'date', 'admin_id', 'participant_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += encryptedChatWaiting_c.number
        result += int_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.admin_id)
        result += int_c.serialize(data.participant_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return encryptedChatWaiting_c._data_cls(id = int_c.deserialize(io_bytes),
                                                access_hash = long_c.deserialize(io_bytes),
                                                date = int_c.deserialize(io_bytes),
                                                admin_id = int_c.deserialize(io_bytes),
                                                participant_id = int_c.deserialize(io_bytes))
combinators[encryptedChatWaiting_c.number] = encryptedChatWaiting_c


class encryptedChatRequested_c:
    number = pack_number(0xc878527e)
    is_base = False
    _data_cls = namedtuple('EncryptedChat', ['id', 'access_hash', 'date', 'admin_id', 'participant_id', 'g_a'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += encryptedChatRequested_c.number
        result += int_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.admin_id)
        result += int_c.serialize(data.participant_id)
        result += bytes_c.serialize(data.g_a)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return encryptedChatRequested_c._data_cls(id = int_c.deserialize(io_bytes),
                                                  access_hash = long_c.deserialize(io_bytes),
                                                  date = int_c.deserialize(io_bytes),
                                                  admin_id = int_c.deserialize(io_bytes),
                                                  participant_id = int_c.deserialize(io_bytes),
                                                  g_a = bytes_c.deserialize(io_bytes))
combinators[encryptedChatRequested_c.number] = encryptedChatRequested_c


class encryptedChat_c:
    number = pack_number(0xfa56ce36)
    is_base = False
    _data_cls = namedtuple('EncryptedChat', ['id', 'access_hash', 'date', 'admin_id', 'participant_id', 'g_a_or_b', 'key_fingerprint'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += encryptedChat_c.number
        result += int_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.admin_id)
        result += int_c.serialize(data.participant_id)
        result += bytes_c.serialize(data.g_a_or_b)
        result += long_c.serialize(data.key_fingerprint)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return encryptedChat_c._data_cls(id = int_c.deserialize(io_bytes),
                                         access_hash = long_c.deserialize(io_bytes),
                                         date = int_c.deserialize(io_bytes),
                                         admin_id = int_c.deserialize(io_bytes),
                                         participant_id = int_c.deserialize(io_bytes),
                                         g_a_or_b = bytes_c.deserialize(io_bytes),
                                         key_fingerprint = long_c.deserialize(io_bytes))
combinators[encryptedChat_c.number] = encryptedChat_c


class encryptedChatDiscarded_c:
    number = pack_number(0x13d6dd27)
    is_base = False
    _data_cls = namedtuple('EncryptedChat', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += encryptedChatDiscarded_c.number
        result += int_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return encryptedChatDiscarded_c._data_cls(id = int_c.deserialize(io_bytes))
combinators[encryptedChatDiscarded_c.number] = encryptedChatDiscarded_c


class inputEncryptedChat_c:
    number = pack_number(0xf141b5e1)
    is_base = False
    _data_cls = namedtuple('InputEncryptedChat', ['chat_id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputEncryptedChat_c.number
        result += int_c.serialize(data.chat_id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputEncryptedChat_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                              access_hash = long_c.deserialize(io_bytes))
combinators[inputEncryptedChat_c.number] = inputEncryptedChat_c


class encryptedFileEmpty_c:
    number = pack_number(0xc21f497e)
    is_base = False
    _data_cls = namedtuple('EncryptedFile', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return encryptedFileEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert encryptedFileEmpty_c.number == number
        return encryptedFileEmpty_c._data_cls(tag='encryptedFileEmpty', number=encryptedFileEmpty_c.number)
combinators[encryptedFileEmpty_c.number] = encryptedFileEmpty_c


class encryptedFile_c:
    number = pack_number(0x4a70994c)
    is_base = False
    _data_cls = namedtuple('EncryptedFile', ['id', 'access_hash', 'size', 'dc_id', 'key_fingerprint'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += encryptedFile_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        result += int_c.serialize(data.size)
        result += int_c.serialize(data.dc_id)
        result += int_c.serialize(data.key_fingerprint)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return encryptedFile_c._data_cls(id = long_c.deserialize(io_bytes),
                                         access_hash = long_c.deserialize(io_bytes),
                                         size = int_c.deserialize(io_bytes),
                                         dc_id = int_c.deserialize(io_bytes),
                                         key_fingerprint = int_c.deserialize(io_bytes))
combinators[encryptedFile_c.number] = encryptedFile_c


class inputEncryptedFileEmpty_c:
    number = pack_number(0x1837c364)
    is_base = False
    _data_cls = namedtuple('InputEncryptedFile', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputEncryptedFileEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputEncryptedFileEmpty_c.number == number
        return inputEncryptedFileEmpty_c._data_cls(tag='inputEncryptedFileEmpty', number=inputEncryptedFileEmpty_c.number)
combinators[inputEncryptedFileEmpty_c.number] = inputEncryptedFileEmpty_c


class inputEncryptedFileUploaded_c:
    number = pack_number(0x64bd0306)
    is_base = False
    _data_cls = namedtuple('InputEncryptedFile', ['id', 'parts', 'md5_checksum', 'key_fingerprint'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputEncryptedFileUploaded_c.number
        result += long_c.serialize(data.id)
        result += int_c.serialize(data.parts)
        result += string_c.serialize(data.md5_checksum)
        result += int_c.serialize(data.key_fingerprint)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputEncryptedFileUploaded_c._data_cls(id = long_c.deserialize(io_bytes),
                                                      parts = int_c.deserialize(io_bytes),
                                                      md5_checksum = string_c.deserialize(io_bytes),
                                                      key_fingerprint = int_c.deserialize(io_bytes))
combinators[inputEncryptedFileUploaded_c.number] = inputEncryptedFileUploaded_c


class inputEncryptedFile_c:
    number = pack_number(0x5a17b5e5)
    is_base = False
    _data_cls = namedtuple('InputEncryptedFile', ['id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputEncryptedFile_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputEncryptedFile_c._data_cls(id = long_c.deserialize(io_bytes),
                                              access_hash = long_c.deserialize(io_bytes))
combinators[inputEncryptedFile_c.number] = inputEncryptedFile_c


class inputEncryptedFileLocation_c:
    number = pack_number(0xf5235d55)
    is_base = False
    _data_cls = namedtuple('InputFileLocation', ['id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputEncryptedFileLocation_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputEncryptedFileLocation_c._data_cls(id = long_c.deserialize(io_bytes),
                                                      access_hash = long_c.deserialize(io_bytes))
combinators[inputEncryptedFileLocation_c.number] = inputEncryptedFileLocation_c


class encryptedMessage_c:
    number = pack_number(0xed18c118)
    is_base = False
    _data_cls = namedtuple('EncryptedMessage', ['random_id', 'chat_id', 'date', 'bytes', 'file'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += encryptedMessage_c.number
        result += long_c.serialize(data.random_id)
        result += int_c.serialize(data.chat_id)
        result += int_c.serialize(data.date)
        result += bytes_c.serialize(data.bytes)
        result += encryptedfile_c.serialize(data.file)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return encryptedMessage_c._data_cls(random_id = long_c.deserialize(io_bytes),
                                            chat_id = int_c.deserialize(io_bytes),
                                            date = int_c.deserialize(io_bytes),
                                            bytes = bytes_c.deserialize(io_bytes),
                                            file = deserialize(io_bytes))
combinators[encryptedMessage_c.number] = encryptedMessage_c


class encryptedMessageService_c:
    number = pack_number(0x23734b06)
    is_base = False
    _data_cls = namedtuple('EncryptedMessage', ['random_id', 'chat_id', 'date', 'bytes'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += encryptedMessageService_c.number
        result += long_c.serialize(data.random_id)
        result += int_c.serialize(data.chat_id)
        result += int_c.serialize(data.date)
        result += bytes_c.serialize(data.bytes)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return encryptedMessageService_c._data_cls(random_id = long_c.deserialize(io_bytes),
                                                   chat_id = int_c.deserialize(io_bytes),
                                                   date = int_c.deserialize(io_bytes),
                                                   bytes = bytes_c.deserialize(io_bytes))
combinators[encryptedMessageService_c.number] = encryptedMessageService_c


class dhConfigNotModified_c:
    number = pack_number(0xc0e24635)
    is_base = False
    _data_cls = namedtuple('DhConfig', ['random'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += dhConfigNotModified_c.number
        result += bytes_c.serialize(data.random)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return dhConfigNotModified_c._data_cls(random = bytes_c.deserialize(io_bytes))
combinators[dhConfigNotModified_c.number] = dhConfigNotModified_c


class dhConfig_c:
    number = pack_number(0x2c221edd)
    is_base = False
    _data_cls = namedtuple('DhConfig', ['g', 'p', 'version', 'random'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += dhConfig_c.number
        result += int_c.serialize(data.g)
        result += bytes_c.serialize(data.p)
        result += int_c.serialize(data.version)
        result += bytes_c.serialize(data.random)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return dhConfig_c._data_cls(g = int_c.deserialize(io_bytes),
                                    p = bytes_c.deserialize(io_bytes),
                                    version = int_c.deserialize(io_bytes),
                                    random = bytes_c.deserialize(io_bytes))
combinators[dhConfig_c.number] = dhConfig_c


class sentEncryptedMessage_c:
    number = pack_number(0x560f8935)
    is_base = False
    _data_cls = namedtuple('SentEncryptedMessage', ['date'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sentEncryptedMessage_c.number
        result += int_c.serialize(data.date)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sentEncryptedMessage_c._data_cls(date = int_c.deserialize(io_bytes))
combinators[sentEncryptedMessage_c.number] = sentEncryptedMessage_c


class sentEncryptedFile_c:
    number = pack_number(0x9493ff32)
    is_base = False
    _data_cls = namedtuple('SentEncryptedMessage', ['date', 'file'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sentEncryptedFile_c.number
        result += int_c.serialize(data.date)
        result += encryptedfile_c.serialize(data.file)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sentEncryptedFile_c._data_cls(date = int_c.deserialize(io_bytes),
                                             file = deserialize(io_bytes))
combinators[sentEncryptedFile_c.number] = sentEncryptedFile_c


class inputFileBig_c:
    number = pack_number(0xfa4f0bb5)
    is_base = False
    _data_cls = namedtuple('InputFile', ['id', 'parts', 'name'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputFileBig_c.number
        result += long_c.serialize(data.id)
        result += int_c.serialize(data.parts)
        result += string_c.serialize(data.name)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputFileBig_c._data_cls(id = long_c.deserialize(io_bytes),
                                        parts = int_c.deserialize(io_bytes),
                                        name = string_c.deserialize(io_bytes))
combinators[inputFileBig_c.number] = inputFileBig_c


class inputEncryptedFileBigUploaded_c:
    number = pack_number(0x2dc173c8)
    is_base = False
    _data_cls = namedtuple('InputEncryptedFile', ['id', 'parts', 'key_fingerprint'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputEncryptedFileBigUploaded_c.number
        result += long_c.serialize(data.id)
        result += int_c.serialize(data.parts)
        result += int_c.serialize(data.key_fingerprint)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputEncryptedFileBigUploaded_c._data_cls(id = long_c.deserialize(io_bytes),
                                                         parts = int_c.deserialize(io_bytes),
                                                         key_fingerprint = int_c.deserialize(io_bytes))
combinators[inputEncryptedFileBigUploaded_c.number] = inputEncryptedFileBigUploaded_c


class updateChatParticipantAdd_c:
    number = pack_number(0x3a0eeb22)
    is_base = False
    _data_cls = namedtuple('Update', ['chat_id', 'user_id', 'inviter_id', 'version'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateChatParticipantAdd_c.number
        result += int_c.serialize(data.chat_id)
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.inviter_id)
        result += int_c.serialize(data.version)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateChatParticipantAdd_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                                    user_id = int_c.deserialize(io_bytes),
                                                    inviter_id = int_c.deserialize(io_bytes),
                                                    version = int_c.deserialize(io_bytes))
combinators[updateChatParticipantAdd_c.number] = updateChatParticipantAdd_c


class updateChatParticipantDelete_c:
    number = pack_number(0x6e5f8c22)
    is_base = False
    _data_cls = namedtuple('Update', ['chat_id', 'user_id', 'version'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateChatParticipantDelete_c.number
        result += int_c.serialize(data.chat_id)
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.version)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateChatParticipantDelete_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                                       user_id = int_c.deserialize(io_bytes),
                                                       version = int_c.deserialize(io_bytes))
combinators[updateChatParticipantDelete_c.number] = updateChatParticipantDelete_c


class updateDcOptions_c:
    number = pack_number(0x8e5e9873)
    is_base = False
    _data_cls = namedtuple('Update', ['dc_options'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateDcOptions_c.number
        result += dcoption_c.serialize(data.dc_options)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateDcOptions_c._data_cls(dc_options = deserialize(io_bytes))
combinators[updateDcOptions_c.number] = updateDcOptions_c


class inputMediaUploadedAudio_c:
    number = pack_number(0x4e498cab)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['file', 'duration', 'mime_type'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaUploadedAudio_c.number
        result += inputfile_c.serialize(data.file)
        result += int_c.serialize(data.duration)
        result += string_c.serialize(data.mime_type)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaUploadedAudio_c._data_cls(file = deserialize(io_bytes),
                                                   duration = int_c.deserialize(io_bytes),
                                                   mime_type = string_c.deserialize(io_bytes))
combinators[inputMediaUploadedAudio_c.number] = inputMediaUploadedAudio_c


class inputMediaAudio_c:
    number = pack_number(0x89938781)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaAudio_c.number
        result += inputaudio_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaAudio_c._data_cls(id = deserialize(io_bytes))
combinators[inputMediaAudio_c.number] = inputMediaAudio_c


class inputMediaUploadedDocument_c:
    number = pack_number(0x34e794bd)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['file', 'file_name', 'mime_type'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaUploadedDocument_c.number
        result += inputfile_c.serialize(data.file)
        result += string_c.serialize(data.file_name)
        result += string_c.serialize(data.mime_type)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaUploadedDocument_c._data_cls(file = deserialize(io_bytes),
                                                      file_name = string_c.deserialize(io_bytes),
                                                      mime_type = string_c.deserialize(io_bytes))
combinators[inputMediaUploadedDocument_c.number] = inputMediaUploadedDocument_c


class inputMediaUploadedThumbDocument_c:
    number = pack_number(0x3e46de5d)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['file', 'thumb', 'file_name', 'mime_type'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaUploadedThumbDocument_c.number
        result += inputfile_c.serialize(data.file)
        result += inputfile_c.serialize(data.thumb)
        result += string_c.serialize(data.file_name)
        result += string_c.serialize(data.mime_type)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaUploadedThumbDocument_c._data_cls(file = deserialize(io_bytes),
                                                           thumb = deserialize(io_bytes),
                                                           file_name = string_c.deserialize(io_bytes),
                                                           mime_type = string_c.deserialize(io_bytes))
combinators[inputMediaUploadedThumbDocument_c.number] = inputMediaUploadedThumbDocument_c


class inputMediaDocument_c:
    number = pack_number(0xd184e841)
    is_base = False
    _data_cls = namedtuple('InputMedia', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputMediaDocument_c.number
        result += inputdocument_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputMediaDocument_c._data_cls(id = deserialize(io_bytes))
combinators[inputMediaDocument_c.number] = inputMediaDocument_c


class messageMediaDocument_c:
    number = pack_number(0x2fda2204)
    is_base = False
    _data_cls = namedtuple('MessageMedia', ['document'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageMediaDocument_c.number
        result += document_c.serialize(data.document)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageMediaDocument_c._data_cls(document = deserialize(io_bytes))
combinators[messageMediaDocument_c.number] = messageMediaDocument_c


class messageMediaAudio_c:
    number = pack_number(0xc6b68300)
    is_base = False
    _data_cls = namedtuple('MessageMedia', ['audio'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += messageMediaAudio_c.number
        result += audio_c.serialize(data.audio)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return messageMediaAudio_c._data_cls(audio = deserialize(io_bytes))
combinators[messageMediaAudio_c.number] = messageMediaAudio_c


class inputAudioEmpty_c:
    number = pack_number(0xd95adc84)
    is_base = False
    _data_cls = namedtuple('InputAudio', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputAudioEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputAudioEmpty_c.number == number
        return inputAudioEmpty_c._data_cls(tag='inputAudioEmpty', number=inputAudioEmpty_c.number)
combinators[inputAudioEmpty_c.number] = inputAudioEmpty_c


class inputAudio_c:
    number = pack_number(0x77d440ff)
    is_base = False
    _data_cls = namedtuple('InputAudio', ['id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputAudio_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputAudio_c._data_cls(id = long_c.deserialize(io_bytes),
                                      access_hash = long_c.deserialize(io_bytes))
combinators[inputAudio_c.number] = inputAudio_c


class inputDocumentEmpty_c:
    number = pack_number(0x72f0eaae)
    is_base = False
    _data_cls = namedtuple('InputDocument', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return inputDocumentEmpty_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert inputDocumentEmpty_c.number == number
        return inputDocumentEmpty_c._data_cls(tag='inputDocumentEmpty', number=inputDocumentEmpty_c.number)
combinators[inputDocumentEmpty_c.number] = inputDocumentEmpty_c


class inputDocument_c:
    number = pack_number(0x18798952)
    is_base = False
    _data_cls = namedtuple('InputDocument', ['id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputDocument_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputDocument_c._data_cls(id = long_c.deserialize(io_bytes),
                                         access_hash = long_c.deserialize(io_bytes))
combinators[inputDocument_c.number] = inputDocument_c


class inputAudioFileLocation_c:
    number = pack_number(0x74dc404d)
    is_base = False
    _data_cls = namedtuple('InputFileLocation', ['id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputAudioFileLocation_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputAudioFileLocation_c._data_cls(id = long_c.deserialize(io_bytes),
                                                  access_hash = long_c.deserialize(io_bytes))
combinators[inputAudioFileLocation_c.number] = inputAudioFileLocation_c


class inputDocumentFileLocation_c:
    number = pack_number(0x4e45abe9)
    is_base = False
    _data_cls = namedtuple('InputFileLocation', ['id', 'access_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += inputDocumentFileLocation_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return inputDocumentFileLocation_c._data_cls(id = long_c.deserialize(io_bytes),
                                                     access_hash = long_c.deserialize(io_bytes))
combinators[inputDocumentFileLocation_c.number] = inputDocumentFileLocation_c


class audioEmpty_c:
    number = pack_number(0x586988d8)
    is_base = False
    _data_cls = namedtuple('Audio', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += audioEmpty_c.number
        result += long_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return audioEmpty_c._data_cls(id = long_c.deserialize(io_bytes))
combinators[audioEmpty_c.number] = audioEmpty_c


class audio_c:
    number = pack_number(0xc7ac6496)
    is_base = False
    _data_cls = namedtuple('Audio', ['id', 'access_hash', 'user_id', 'date', 'duration', 'mime_type', 'size', 'dc_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += audio_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.duration)
        result += string_c.serialize(data.mime_type)
        result += int_c.serialize(data.size)
        result += int_c.serialize(data.dc_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return audio_c._data_cls(id = long_c.deserialize(io_bytes),
                                 access_hash = long_c.deserialize(io_bytes),
                                 user_id = int_c.deserialize(io_bytes),
                                 date = int_c.deserialize(io_bytes),
                                 duration = int_c.deserialize(io_bytes),
                                 mime_type = string_c.deserialize(io_bytes),
                                 size = int_c.deserialize(io_bytes),
                                 dc_id = int_c.deserialize(io_bytes))
combinators[audio_c.number] = audio_c


class documentEmpty_c:
    number = pack_number(0x36f8c871)
    is_base = False
    _data_cls = namedtuple('Document', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += documentEmpty_c.number
        result += long_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return documentEmpty_c._data_cls(id = long_c.deserialize(io_bytes))
combinators[documentEmpty_c.number] = documentEmpty_c


class document_c:
    number = pack_number(0x9efc6326)
    is_base = False
    _data_cls = namedtuple('Document', ['id', 'access_hash', 'user_id', 'date', 'file_name', 'mime_type', 'size', 'thumb', 'dc_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += document_c.number
        result += long_c.serialize(data.id)
        result += long_c.serialize(data.access_hash)
        result += int_c.serialize(data.user_id)
        result += int_c.serialize(data.date)
        result += string_c.serialize(data.file_name)
        result += string_c.serialize(data.mime_type)
        result += int_c.serialize(data.size)
        result += photosize_c.serialize(data.thumb)
        result += int_c.serialize(data.dc_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return document_c._data_cls(id = long_c.deserialize(io_bytes),
                                    access_hash = long_c.deserialize(io_bytes),
                                    user_id = int_c.deserialize(io_bytes),
                                    date = int_c.deserialize(io_bytes),
                                    file_name = string_c.deserialize(io_bytes),
                                    mime_type = string_c.deserialize(io_bytes),
                                    size = int_c.deserialize(io_bytes),
                                    thumb = deserialize(io_bytes),
                                    dc_id = int_c.deserialize(io_bytes))
combinators[document_c.number] = document_c


class support_c:
    number = pack_number(0x17c6b5f6)
    is_base = False
    _data_cls = namedtuple('Support', ['phone_number', 'user'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += support_c.number
        result += string_c.serialize(data.phone_number)
        result += user_c.serialize(data.user)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return support_c._data_cls(phone_number = string_c.deserialize(io_bytes),
                                   user = deserialize(io_bytes))
combinators[support_c.number] = support_c


class notifyPeer_c:
    number = pack_number(0x9fd40bd8)
    is_base = False
    _data_cls = namedtuple('NotifyPeer', ['peer'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += notifyPeer_c.number
        result += peer_c.serialize(data.peer)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return notifyPeer_c._data_cls(peer = deserialize(io_bytes))
combinators[notifyPeer_c.number] = notifyPeer_c


class notifyUsers_c:
    number = pack_number(0xb4c83b4c)
    is_base = False
    _data_cls = namedtuple('NotifyPeer', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return notifyUsers_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert notifyUsers_c.number == number
        return notifyUsers_c._data_cls(tag='notifyUsers', number=notifyUsers_c.number)
combinators[notifyUsers_c.number] = notifyUsers_c


class notifyChats_c:
    number = pack_number(0xc007cec3)
    is_base = False
    _data_cls = namedtuple('NotifyPeer', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return notifyChats_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert notifyChats_c.number == number
        return notifyChats_c._data_cls(tag='notifyChats', number=notifyChats_c.number)
combinators[notifyChats_c.number] = notifyChats_c


class notifyAll_c:
    number = pack_number(0x74d07c60)
    is_base = False
    _data_cls = namedtuple('NotifyPeer', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return notifyAll_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert notifyAll_c.number == number
        return notifyAll_c._data_cls(tag='notifyAll', number=notifyAll_c.number)
combinators[notifyAll_c.number] = notifyAll_c


class updateUserBlocked_c:
    number = pack_number(0x80ece81a)
    is_base = False
    _data_cls = namedtuple('Update', ['user_id', 'blocked'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateUserBlocked_c.number
        result += int_c.serialize(data.user_id)
        result += bool_c.serialize(data.blocked)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateUserBlocked_c._data_cls(user_id = int_c.deserialize(io_bytes),
                                             blocked = deserialize(io_bytes))
combinators[updateUserBlocked_c.number] = updateUserBlocked_c


class updateNotifySettings_c:
    number = pack_number(0xbec268ef)
    is_base = False
    _data_cls = namedtuple('Update', ['peer', 'notify_settings'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateNotifySettings_c.number
        result += notifypeer_c.serialize(data.peer)
        result += peernotifysettings_c.serialize(data.notify_settings)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateNotifySettings_c._data_cls(peer = deserialize(io_bytes),
                                                notify_settings = deserialize(io_bytes))
combinators[updateNotifySettings_c.number] = updateNotifySettings_c


class invokeAfterMsg_c:
    number = pack_number(0xcb9f372d)
    is_base = False
    _data_cls = namedtuple('X', ['X', 'msg_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += invokeAfterMsg_c.number
        result += type_c.serialize(data.X)
        result += long_c.serialize(data.msg_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return invokeAfterMsg_c._data_cls(X = deserialize(io_bytes),
                                          msg_id = long_c.deserialize(io_bytes))
combinators[invokeAfterMsg_c.number] = invokeAfterMsg_c


class invokeAfterMsgs_c:
    number = pack_number(0x3dc4b4f0)
    is_base = False
    _data_cls = namedtuple('X', ['X', 'msg_ids'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += invokeAfterMsgs_c.number
        result += type_c.serialize(data.X)
        result += long_c.serialize(data.msg_ids)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return invokeAfterMsgs_c._data_cls(X = deserialize(io_bytes),
                                           msg_ids = long_c.deserialize(io_bytes))
combinators[invokeAfterMsgs_c.number] = invokeAfterMsgs_c


class checkPhone_c:
    number = pack_number(0x6fe51dfb)
    is_base = False
    _data_cls = namedtuple('CheckedPhone', ['phone_number'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += checkPhone_c.number
        result += string_c.serialize(data.phone_number)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return checkPhone_c._data_cls(phone_number = string_c.deserialize(io_bytes))
combinators[checkPhone_c.number] = checkPhone_c


class sendCode_c:
    number = pack_number(0x768d5f4d)
    is_base = False
    _data_cls = namedtuple('SentCode', ['phone_number', 'sms_type', 'api_id', 'api_hash', 'lang_code'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sendCode_c.number
        result += string_c.serialize(data.phone_number)
        result += int_c.serialize(data.sms_type)
        result += int_c.serialize(data.api_id)
        result += string_c.serialize(data.api_hash)
        result += string_c.serialize(data.lang_code)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sendCode_c._data_cls(phone_number = string_c.deserialize(io_bytes),
                                    sms_type = int_c.deserialize(io_bytes),
                                    api_id = int_c.deserialize(io_bytes),
                                    api_hash = string_c.deserialize(io_bytes),
                                    lang_code = string_c.deserialize(io_bytes))
combinators[sendCode_c.number] = sendCode_c


class sendCall_c:
    number = pack_number(0x3c51564)
    is_base = False
    _data_cls = namedtuple('Bool', ['phone_number', 'phone_code_hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sendCall_c.number
        result += string_c.serialize(data.phone_number)
        result += string_c.serialize(data.phone_code_hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sendCall_c._data_cls(phone_number = string_c.deserialize(io_bytes),
                                    phone_code_hash = string_c.deserialize(io_bytes))
combinators[sendCall_c.number] = sendCall_c


class signUp_c:
    number = pack_number(0x1b067634)
    is_base = False
    _data_cls = namedtuple('Authorization', ['phone_number', 'phone_code_hash', 'phone_code', 'first_name', 'last_name'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += signUp_c.number
        result += string_c.serialize(data.phone_number)
        result += string_c.serialize(data.phone_code_hash)
        result += string_c.serialize(data.phone_code)
        result += string_c.serialize(data.first_name)
        result += string_c.serialize(data.last_name)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return signUp_c._data_cls(phone_number = string_c.deserialize(io_bytes),
                                  phone_code_hash = string_c.deserialize(io_bytes),
                                  phone_code = string_c.deserialize(io_bytes),
                                  first_name = string_c.deserialize(io_bytes),
                                  last_name = string_c.deserialize(io_bytes))
combinators[signUp_c.number] = signUp_c


class signIn_c:
    number = pack_number(0xbcd51581)
    is_base = False
    _data_cls = namedtuple('Authorization', ['phone_number', 'phone_code_hash', 'phone_code'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += signIn_c.number
        result += string_c.serialize(data.phone_number)
        result += string_c.serialize(data.phone_code_hash)
        result += string_c.serialize(data.phone_code)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return signIn_c._data_cls(phone_number = string_c.deserialize(io_bytes),
                                  phone_code_hash = string_c.deserialize(io_bytes),
                                  phone_code = string_c.deserialize(io_bytes))
combinators[signIn_c.number] = signIn_c


class logOut_c:
    number = pack_number(0x5717da40)
    is_base = False
    _data_cls = namedtuple('Bool', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return logOut_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert logOut_c.number == number
        return logOut_c._data_cls(tag='auth.logOut', number=logOut_c.number)
combinators[logOut_c.number] = logOut_c


class resetAuthorizations_c:
    number = pack_number(0x9fab0d1a)
    is_base = False
    _data_cls = namedtuple('Bool', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return resetAuthorizations_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert resetAuthorizations_c.number == number
        return resetAuthorizations_c._data_cls(tag='auth.resetAuthorizations', number=resetAuthorizations_c.number)
combinators[resetAuthorizations_c.number] = resetAuthorizations_c


class sendInvites_c:
    number = pack_number(0x771c1d97)
    is_base = False
    _data_cls = namedtuple('Bool', ['phone_numbers', 'message'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sendInvites_c.number
        result += string_c.serialize(data.phone_numbers)
        result += string_c.serialize(data.message)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sendInvites_c._data_cls(phone_numbers = string_c.deserialize(io_bytes),
                                       message = string_c.deserialize(io_bytes))
combinators[sendInvites_c.number] = sendInvites_c


class exportAuthorization_c:
    number = pack_number(0xe5bfffcd)
    is_base = False
    _data_cls = namedtuple('ExportedAuthorization', ['dc_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += exportAuthorization_c.number
        result += int_c.serialize(data.dc_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return exportAuthorization_c._data_cls(dc_id = int_c.deserialize(io_bytes))
combinators[exportAuthorization_c.number] = exportAuthorization_c


class importAuthorization_c:
    number = pack_number(0xe3ef9613)
    is_base = False
    _data_cls = namedtuple('Authorization', ['id', 'bytes'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += importAuthorization_c.number
        result += int_c.serialize(data.id)
        result += bytes_c.serialize(data.bytes)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return importAuthorization_c._data_cls(id = int_c.deserialize(io_bytes),
                                               bytes = bytes_c.deserialize(io_bytes))
combinators[importAuthorization_c.number] = importAuthorization_c


class bindTempAuthKey_c:
    number = pack_number(0xcdd42a05)
    is_base = False
    _data_cls = namedtuple('Bool', ['perm_auth_key_id', 'nonce', 'expires_at', 'encrypted_message'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += bindTempAuthKey_c.number
        result += long_c.serialize(data.perm_auth_key_id)
        result += long_c.serialize(data.nonce)
        result += int_c.serialize(data.expires_at)
        result += bytes_c.serialize(data.encrypted_message)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return bindTempAuthKey_c._data_cls(perm_auth_key_id = long_c.deserialize(io_bytes),
                                           nonce = long_c.deserialize(io_bytes),
                                           expires_at = int_c.deserialize(io_bytes),
                                           encrypted_message = bytes_c.deserialize(io_bytes))
combinators[bindTempAuthKey_c.number] = bindTempAuthKey_c


class registerDevice_c:
    number = pack_number(0x446c712c)
    is_base = False
    _data_cls = namedtuple('Bool', ['token_type', 'token', 'device_model', 'system_version', 'app_version', 'app_sandbox', 'lang_code'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += registerDevice_c.number
        result += int_c.serialize(data.token_type)
        result += string_c.serialize(data.token)
        result += string_c.serialize(data.device_model)
        result += string_c.serialize(data.system_version)
        result += string_c.serialize(data.app_version)
        result += bool_c.serialize(data.app_sandbox)
        result += string_c.serialize(data.lang_code)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return registerDevice_c._data_cls(token_type = int_c.deserialize(io_bytes),
                                          token = string_c.deserialize(io_bytes),
                                          device_model = string_c.deserialize(io_bytes),
                                          system_version = string_c.deserialize(io_bytes),
                                          app_version = string_c.deserialize(io_bytes),
                                          app_sandbox = deserialize(io_bytes),
                                          lang_code = string_c.deserialize(io_bytes))
combinators[registerDevice_c.number] = registerDevice_c


class unregisterDevice_c:
    number = pack_number(0x65c55b40)
    is_base = False
    _data_cls = namedtuple('Bool', ['token_type', 'token'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += unregisterDevice_c.number
        result += int_c.serialize(data.token_type)
        result += string_c.serialize(data.token)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return unregisterDevice_c._data_cls(token_type = int_c.deserialize(io_bytes),
                                            token = string_c.deserialize(io_bytes))
combinators[unregisterDevice_c.number] = unregisterDevice_c


class updateNotifySettings_c:
    number = pack_number(0x84be5b93)
    is_base = False
    _data_cls = namedtuple('Bool', ['peer', 'settings'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateNotifySettings_c.number
        result += inputnotifypeer_c.serialize(data.peer)
        result += inputpeernotifysettings_c.serialize(data.settings)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateNotifySettings_c._data_cls(peer = deserialize(io_bytes),
                                                settings = deserialize(io_bytes))
combinators[updateNotifySettings_c.number] = updateNotifySettings_c


class getNotifySettings_c:
    number = pack_number(0x12b3ad31)
    is_base = False
    _data_cls = namedtuple('PeerNotifySettings', ['peer'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getNotifySettings_c.number
        result += inputnotifypeer_c.serialize(data.peer)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getNotifySettings_c._data_cls(peer = deserialize(io_bytes))
combinators[getNotifySettings_c.number] = getNotifySettings_c


class resetNotifySettings_c:
    number = pack_number(0xdb7e1747)
    is_base = False
    _data_cls = namedtuple('Bool', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return resetNotifySettings_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert resetNotifySettings_c.number == number
        return resetNotifySettings_c._data_cls(tag='account.resetNotifySettings', number=resetNotifySettings_c.number)
combinators[resetNotifySettings_c.number] = resetNotifySettings_c


class updateProfile_c:
    number = pack_number(0xf0888d68)
    is_base = False
    _data_cls = namedtuple('User', ['first_name', 'last_name'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateProfile_c.number
        result += string_c.serialize(data.first_name)
        result += string_c.serialize(data.last_name)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateProfile_c._data_cls(first_name = string_c.deserialize(io_bytes),
                                         last_name = string_c.deserialize(io_bytes))
combinators[updateProfile_c.number] = updateProfile_c


class updateStatus_c:
    number = pack_number(0x6628562c)
    is_base = False
    _data_cls = namedtuple('Bool', ['offline'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateStatus_c.number
        result += bool_c.serialize(data.offline)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateStatus_c._data_cls(offline = deserialize(io_bytes))
combinators[updateStatus_c.number] = updateStatus_c


class getWallPapers_c:
    number = pack_number(0xc04cfac2)
    is_base = False
    _data_cls = namedtuple('Vector', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return getWallPapers_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert getWallPapers_c.number == number
        return getWallPapers_c._data_cls(tag='account.getWallPapers', number=getWallPapers_c.number)
combinators[getWallPapers_c.number] = getWallPapers_c


class getUsers_c:
    number = pack_number(0xd91a548)
    is_base = False
    _data_cls = namedtuple('Vector', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getUsers_c.number
        result += inputuser_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getUsers_c._data_cls(id = deserialize(io_bytes))
combinators[getUsers_c.number] = getUsers_c


class getFullUser_c:
    number = pack_number(0xca30a5b1)
    is_base = False
    _data_cls = namedtuple('UserFull', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getFullUser_c.number
        result += inputuser_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getFullUser_c._data_cls(id = deserialize(io_bytes))
combinators[getFullUser_c.number] = getFullUser_c


class getStatuses_c:
    number = pack_number(0xc4a353ee)
    is_base = False
    _data_cls = namedtuple('Vector', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return getStatuses_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert getStatuses_c.number == number
        return getStatuses_c._data_cls(tag='contacts.getStatuses', number=getStatuses_c.number)
combinators[getStatuses_c.number] = getStatuses_c


class getContacts_c:
    number = pack_number(0x22c6aa08)
    is_base = False
    _data_cls = namedtuple('Contacts', ['hash'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getContacts_c.number
        result += string_c.serialize(data.hash)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getContacts_c._data_cls(hash = string_c.deserialize(io_bytes))
combinators[getContacts_c.number] = getContacts_c


class importContacts_c:
    number = pack_number(0xda30b32d)
    is_base = False
    _data_cls = namedtuple('ImportedContacts', ['contacts', 'replace'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += importContacts_c.number
        result += inputcontact_c.serialize(data.contacts)
        result += bool_c.serialize(data.replace)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return importContacts_c._data_cls(contacts = deserialize(io_bytes),
                                          replace = deserialize(io_bytes))
combinators[importContacts_c.number] = importContacts_c


class getSuggested_c:
    number = pack_number(0xcd773428)
    is_base = False
    _data_cls = namedtuple('Suggested', ['limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getSuggested_c.number
        result += int_c.serialize(data.limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getSuggested_c._data_cls(limit = int_c.deserialize(io_bytes))
combinators[getSuggested_c.number] = getSuggested_c


class deleteContact_c:
    number = pack_number(0x8e953744)
    is_base = False
    _data_cls = namedtuple('Link', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += deleteContact_c.number
        result += inputuser_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return deleteContact_c._data_cls(id = deserialize(io_bytes))
combinators[deleteContact_c.number] = deleteContact_c


class deleteContacts_c:
    number = pack_number(0x59ab389e)
    is_base = False
    _data_cls = namedtuple('Bool', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += deleteContacts_c.number
        result += inputuser_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return deleteContacts_c._data_cls(id = deserialize(io_bytes))
combinators[deleteContacts_c.number] = deleteContacts_c


class block_c:
    number = pack_number(0x332b49fc)
    is_base = False
    _data_cls = namedtuple('Bool', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += block_c.number
        result += inputuser_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return block_c._data_cls(id = deserialize(io_bytes))
combinators[block_c.number] = block_c


class unblock_c:
    number = pack_number(0xe54100bd)
    is_base = False
    _data_cls = namedtuple('Bool', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += unblock_c.number
        result += inputuser_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return unblock_c._data_cls(id = deserialize(io_bytes))
combinators[unblock_c.number] = unblock_c


class getBlocked_c:
    number = pack_number(0xf57c350f)
    is_base = False
    _data_cls = namedtuple('Blocked', ['offset', 'limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getBlocked_c.number
        result += int_c.serialize(data.offset)
        result += int_c.serialize(data.limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getBlocked_c._data_cls(offset = int_c.deserialize(io_bytes),
                                      limit = int_c.deserialize(io_bytes))
combinators[getBlocked_c.number] = getBlocked_c


class exportCard_c:
    number = pack_number(0x84e53737)
    is_base = False
    _data_cls = namedtuple('Vector', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return exportCard_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert exportCard_c.number == number
        return exportCard_c._data_cls(tag='contacts.exportCard', number=exportCard_c.number)
combinators[exportCard_c.number] = exportCard_c


class importCard_c:
    number = pack_number(0x4fe196fe)
    is_base = False
    _data_cls = namedtuple('User', ['export_card'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += importCard_c.number
        result += int_c.serialize(data.export_card)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return importCard_c._data_cls(export_card = int_c.deserialize(io_bytes))
combinators[importCard_c.number] = importCard_c


class getMessages_c:
    number = pack_number(0x4222fa74)
    is_base = False
    _data_cls = namedtuple('Messages', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getMessages_c.number
        result += int_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getMessages_c._data_cls(id = int_c.deserialize(io_bytes))
combinators[getMessages_c.number] = getMessages_c


class getDialogs_c:
    number = pack_number(0xeccf1df6)
    is_base = False
    _data_cls = namedtuple('Dialogs', ['offset', 'max_id', 'limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getDialogs_c.number
        result += int_c.serialize(data.offset)
        result += int_c.serialize(data.max_id)
        result += int_c.serialize(data.limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getDialogs_c._data_cls(offset = int_c.deserialize(io_bytes),
                                      max_id = int_c.deserialize(io_bytes),
                                      limit = int_c.deserialize(io_bytes))
combinators[getDialogs_c.number] = getDialogs_c


class getHistory_c:
    number = pack_number(0x92a1df2f)
    is_base = False
    _data_cls = namedtuple('Messages', ['peer', 'offset', 'max_id', 'limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getHistory_c.number
        result += inputpeer_c.serialize(data.peer)
        result += int_c.serialize(data.offset)
        result += int_c.serialize(data.max_id)
        result += int_c.serialize(data.limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getHistory_c._data_cls(peer = deserialize(io_bytes),
                                      offset = int_c.deserialize(io_bytes),
                                      max_id = int_c.deserialize(io_bytes),
                                      limit = int_c.deserialize(io_bytes))
combinators[getHistory_c.number] = getHistory_c


class search_c:
    number = pack_number(0x7e9f2ab)
    is_base = False
    _data_cls = namedtuple('Messages', ['peer', 'q', 'filter', 'min_date', 'max_date', 'offset', 'max_id', 'limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += search_c.number
        result += inputpeer_c.serialize(data.peer)
        result += string_c.serialize(data.q)
        result += messagesfilter_c.serialize(data.filter)
        result += int_c.serialize(data.min_date)
        result += int_c.serialize(data.max_date)
        result += int_c.serialize(data.offset)
        result += int_c.serialize(data.max_id)
        result += int_c.serialize(data.limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return search_c._data_cls(peer = deserialize(io_bytes),
                                  q = string_c.deserialize(io_bytes),
                                  filter = deserialize(io_bytes),
                                  min_date = int_c.deserialize(io_bytes),
                                  max_date = int_c.deserialize(io_bytes),
                                  offset = int_c.deserialize(io_bytes),
                                  max_id = int_c.deserialize(io_bytes),
                                  limit = int_c.deserialize(io_bytes))
combinators[search_c.number] = search_c


class readHistory_c:
    number = pack_number(0xb04f2510)
    is_base = False
    _data_cls = namedtuple('AffectedHistory', ['peer', 'max_id', 'offset'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += readHistory_c.number
        result += inputpeer_c.serialize(data.peer)
        result += int_c.serialize(data.max_id)
        result += int_c.serialize(data.offset)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return readHistory_c._data_cls(peer = deserialize(io_bytes),
                                       max_id = int_c.deserialize(io_bytes),
                                       offset = int_c.deserialize(io_bytes))
combinators[readHistory_c.number] = readHistory_c


class deleteHistory_c:
    number = pack_number(0xf4f8fb61)
    is_base = False
    _data_cls = namedtuple('AffectedHistory', ['peer', 'offset'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += deleteHistory_c.number
        result += inputpeer_c.serialize(data.peer)
        result += int_c.serialize(data.offset)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return deleteHistory_c._data_cls(peer = deserialize(io_bytes),
                                         offset = int_c.deserialize(io_bytes))
combinators[deleteHistory_c.number] = deleteHistory_c


class deleteMessages_c:
    number = pack_number(0x14f2dd0a)
    is_base = False
    _data_cls = namedtuple('Vector', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += deleteMessages_c.number
        result += int_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return deleteMessages_c._data_cls(id = int_c.deserialize(io_bytes))
combinators[deleteMessages_c.number] = deleteMessages_c


class receivedMessages_c:
    number = pack_number(0x28abcb68)
    is_base = False
    _data_cls = namedtuple('Vector', ['max_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += receivedMessages_c.number
        result += int_c.serialize(data.max_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return receivedMessages_c._data_cls(max_id = int_c.deserialize(io_bytes))
combinators[receivedMessages_c.number] = receivedMessages_c


class setTyping_c:
    number = pack_number(0x719839e9)
    is_base = False
    _data_cls = namedtuple('Bool', ['peer', 'typing'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += setTyping_c.number
        result += inputpeer_c.serialize(data.peer)
        result += bool_c.serialize(data.typing)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return setTyping_c._data_cls(peer = deserialize(io_bytes),
                                     typing = deserialize(io_bytes))
combinators[setTyping_c.number] = setTyping_c


class sendMessage_c:
    number = pack_number(0x4cde0aab)
    is_base = False
    _data_cls = namedtuple('SentMessage', ['peer', 'message', 'random_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sendMessage_c.number
        result += inputpeer_c.serialize(data.peer)
        result += string_c.serialize(data.message)
        result += long_c.serialize(data.random_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sendMessage_c._data_cls(peer = deserialize(io_bytes),
                                       message = string_c.deserialize(io_bytes),
                                       random_id = long_c.deserialize(io_bytes))
combinators[sendMessage_c.number] = sendMessage_c


class sendMedia_c:
    number = pack_number(0xa3c85d76)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['peer', 'media', 'random_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sendMedia_c.number
        result += inputpeer_c.serialize(data.peer)
        result += inputmedia_c.serialize(data.media)
        result += long_c.serialize(data.random_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sendMedia_c._data_cls(peer = deserialize(io_bytes),
                                     media = deserialize(io_bytes),
                                     random_id = long_c.deserialize(io_bytes))
combinators[sendMedia_c.number] = sendMedia_c


class forwardMessages_c:
    number = pack_number(0x514cd10f)
    is_base = False
    _data_cls = namedtuple('StatedMessages', ['peer', 'id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += forwardMessages_c.number
        result += inputpeer_c.serialize(data.peer)
        result += int_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return forwardMessages_c._data_cls(peer = deserialize(io_bytes),
                                           id = int_c.deserialize(io_bytes))
combinators[forwardMessages_c.number] = forwardMessages_c


class getChats_c:
    number = pack_number(0x3c6aa187)
    is_base = False
    _data_cls = namedtuple('Chats', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getChats_c.number
        result += int_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getChats_c._data_cls(id = int_c.deserialize(io_bytes))
combinators[getChats_c.number] = getChats_c


class getFullChat_c:
    number = pack_number(0x3b831c66)
    is_base = False
    _data_cls = namedtuple('ChatFull', ['chat_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getFullChat_c.number
        result += int_c.serialize(data.chat_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getFullChat_c._data_cls(chat_id = int_c.deserialize(io_bytes))
combinators[getFullChat_c.number] = getFullChat_c


class editChatTitle_c:
    number = pack_number(0xb4bc68b5)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['chat_id', 'title'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += editChatTitle_c.number
        result += int_c.serialize(data.chat_id)
        result += string_c.serialize(data.title)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return editChatTitle_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                         title = string_c.deserialize(io_bytes))
combinators[editChatTitle_c.number] = editChatTitle_c


class editChatPhoto_c:
    number = pack_number(0xd881821d)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['chat_id', 'photo'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += editChatPhoto_c.number
        result += int_c.serialize(data.chat_id)
        result += inputchatphoto_c.serialize(data.photo)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return editChatPhoto_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                         photo = deserialize(io_bytes))
combinators[editChatPhoto_c.number] = editChatPhoto_c


class addChatUser_c:
    number = pack_number(0x2ee9ee9e)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['chat_id', 'user_id', 'fwd_limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += addChatUser_c.number
        result += int_c.serialize(data.chat_id)
        result += inputuser_c.serialize(data.user_id)
        result += int_c.serialize(data.fwd_limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return addChatUser_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                       user_id = deserialize(io_bytes),
                                       fwd_limit = int_c.deserialize(io_bytes))
combinators[addChatUser_c.number] = addChatUser_c


class deleteChatUser_c:
    number = pack_number(0xc3c5cd23)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['chat_id', 'user_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += deleteChatUser_c.number
        result += int_c.serialize(data.chat_id)
        result += inputuser_c.serialize(data.user_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return deleteChatUser_c._data_cls(chat_id = int_c.deserialize(io_bytes),
                                          user_id = deserialize(io_bytes))
combinators[deleteChatUser_c.number] = deleteChatUser_c


class createChat_c:
    number = pack_number(0x419d9aee)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['users', 'title'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += createChat_c.number
        result += inputuser_c.serialize(data.users)
        result += string_c.serialize(data.title)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return createChat_c._data_cls(users = deserialize(io_bytes),
                                      title = string_c.deserialize(io_bytes))
combinators[createChat_c.number] = createChat_c


class getState_c:
    number = pack_number(0xedd4882a)
    is_base = False
    _data_cls = namedtuple('State', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return getState_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert getState_c.number == number
        return getState_c._data_cls(tag='updates.getState', number=getState_c.number)
combinators[getState_c.number] = getState_c


class getDifference_c:
    number = pack_number(0xa041495)
    is_base = False
    _data_cls = namedtuple('Difference', ['pts', 'date', 'qts'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getDifference_c.number
        result += int_c.serialize(data.pts)
        result += int_c.serialize(data.date)
        result += int_c.serialize(data.qts)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getDifference_c._data_cls(pts = int_c.deserialize(io_bytes),
                                         date = int_c.deserialize(io_bytes),
                                         qts = int_c.deserialize(io_bytes))
combinators[getDifference_c.number] = getDifference_c


class updateProfilePhoto_c:
    number = pack_number(0xeef579a0)
    is_base = False
    _data_cls = namedtuple('UserProfilePhoto', ['id', 'crop'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += updateProfilePhoto_c.number
        result += inputphoto_c.serialize(data.id)
        result += inputphotocrop_c.serialize(data.crop)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return updateProfilePhoto_c._data_cls(id = deserialize(io_bytes),
                                              crop = deserialize(io_bytes))
combinators[updateProfilePhoto_c.number] = updateProfilePhoto_c


class uploadProfilePhoto_c:
    number = pack_number(0xd50f9c88)
    is_base = False
    _data_cls = namedtuple('Photo', ['file', 'caption', 'geo_point', 'crop'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += uploadProfilePhoto_c.number
        result += inputfile_c.serialize(data.file)
        result += string_c.serialize(data.caption)
        result += inputgeopoint_c.serialize(data.geo_point)
        result += inputphotocrop_c.serialize(data.crop)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return uploadProfilePhoto_c._data_cls(file = deserialize(io_bytes),
                                              caption = string_c.deserialize(io_bytes),
                                              geo_point = deserialize(io_bytes),
                                              crop = deserialize(io_bytes))
combinators[uploadProfilePhoto_c.number] = uploadProfilePhoto_c


class deletePhotos_c:
    number = pack_number(0x87cf7f2f)
    is_base = False
    _data_cls = namedtuple('Vector', ['id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += deletePhotos_c.number
        result += inputphoto_c.serialize(data.id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return deletePhotos_c._data_cls(id = deserialize(io_bytes))
combinators[deletePhotos_c.number] = deletePhotos_c


class saveFilePart_c:
    number = pack_number(0xb304a621)
    is_base = False
    _data_cls = namedtuple('Bool', ['file_id', 'file_part', 'bytes'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += saveFilePart_c.number
        result += long_c.serialize(data.file_id)
        result += int_c.serialize(data.file_part)
        result += bytes_c.serialize(data.bytes)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return saveFilePart_c._data_cls(file_id = long_c.deserialize(io_bytes),
                                        file_part = int_c.deserialize(io_bytes),
                                        bytes = bytes_c.deserialize(io_bytes))
combinators[saveFilePart_c.number] = saveFilePart_c


class getFile_c:
    number = pack_number(0xe3a6cfb5)
    is_base = False
    _data_cls = namedtuple('File', ['location', 'offset', 'limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getFile_c.number
        result += inputfilelocation_c.serialize(data.location)
        result += int_c.serialize(data.offset)
        result += int_c.serialize(data.limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getFile_c._data_cls(location = deserialize(io_bytes),
                                   offset = int_c.deserialize(io_bytes),
                                   limit = int_c.deserialize(io_bytes))
combinators[getFile_c.number] = getFile_c


class getConfig_c:
    number = pack_number(0xc4f9186b)
    is_base = False
    _data_cls = namedtuple('Config', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return getConfig_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert getConfig_c.number == number
        return getConfig_c._data_cls(tag='help.getConfig', number=getConfig_c.number)
combinators[getConfig_c.number] = getConfig_c


class getNearestDc_c:
    number = pack_number(0x1fb33026)
    is_base = False
    _data_cls = namedtuple('NearestDc', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return getNearestDc_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert getNearestDc_c.number == number
        return getNearestDc_c._data_cls(tag='help.getNearestDc', number=getNearestDc_c.number)
combinators[getNearestDc_c.number] = getNearestDc_c


class getAppUpdate_c:
    number = pack_number(0xc812ac7e)
    is_base = False
    _data_cls = namedtuple('AppUpdate', ['device_model', 'system_version', 'app_version', 'lang_code'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getAppUpdate_c.number
        result += string_c.serialize(data.device_model)
        result += string_c.serialize(data.system_version)
        result += string_c.serialize(data.app_version)
        result += string_c.serialize(data.lang_code)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getAppUpdate_c._data_cls(device_model = string_c.deserialize(io_bytes),
                                        system_version = string_c.deserialize(io_bytes),
                                        app_version = string_c.deserialize(io_bytes),
                                        lang_code = string_c.deserialize(io_bytes))
combinators[getAppUpdate_c.number] = getAppUpdate_c


class saveAppLog_c:
    number = pack_number(0x6f02f748)
    is_base = False
    _data_cls = namedtuple('Bool', ['events'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += saveAppLog_c.number
        result += inputappevent_c.serialize(data.events)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return saveAppLog_c._data_cls(events = deserialize(io_bytes))
combinators[saveAppLog_c.number] = saveAppLog_c


class getInviteText_c:
    number = pack_number(0xa4a95186)
    is_base = False
    _data_cls = namedtuple('InviteText', ['lang_code'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getInviteText_c.number
        result += string_c.serialize(data.lang_code)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getInviteText_c._data_cls(lang_code = string_c.deserialize(io_bytes))
combinators[getInviteText_c.number] = getInviteText_c


class getUserPhotos_c:
    number = pack_number(0xb7ee553c)
    is_base = False
    _data_cls = namedtuple('Photos', ['user_id', 'offset', 'max_id', 'limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getUserPhotos_c.number
        result += inputuser_c.serialize(data.user_id)
        result += int_c.serialize(data.offset)
        result += int_c.serialize(data.max_id)
        result += int_c.serialize(data.limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getUserPhotos_c._data_cls(user_id = deserialize(io_bytes),
                                         offset = int_c.deserialize(io_bytes),
                                         max_id = int_c.deserialize(io_bytes),
                                         limit = int_c.deserialize(io_bytes))
combinators[getUserPhotos_c.number] = getUserPhotos_c


class forwardMessage_c:
    number = pack_number(0x3f3f4f2)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['peer', 'id', 'random_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += forwardMessage_c.number
        result += inputpeer_c.serialize(data.peer)
        result += int_c.serialize(data.id)
        result += long_c.serialize(data.random_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return forwardMessage_c._data_cls(peer = deserialize(io_bytes),
                                          id = int_c.deserialize(io_bytes),
                                          random_id = long_c.deserialize(io_bytes))
combinators[forwardMessage_c.number] = forwardMessage_c


class sendBroadcast_c:
    number = pack_number(0x41bb0972)
    is_base = False
    _data_cls = namedtuple('StatedMessages', ['contacts', 'message', 'media'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sendBroadcast_c.number
        result += inputuser_c.serialize(data.contacts)
        result += string_c.serialize(data.message)
        result += inputmedia_c.serialize(data.media)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sendBroadcast_c._data_cls(contacts = deserialize(io_bytes),
                                         message = string_c.deserialize(io_bytes),
                                         media = deserialize(io_bytes))
combinators[sendBroadcast_c.number] = sendBroadcast_c


class getLocated_c:
    number = pack_number(0x7f192d8f)
    is_base = False
    _data_cls = namedtuple('Located', ['geo_point', 'radius', 'limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getLocated_c.number
        result += inputgeopoint_c.serialize(data.geo_point)
        result += int_c.serialize(data.radius)
        result += int_c.serialize(data.limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getLocated_c._data_cls(geo_point = deserialize(io_bytes),
                                      radius = int_c.deserialize(io_bytes),
                                      limit = int_c.deserialize(io_bytes))
combinators[getLocated_c.number] = getLocated_c


class getRecents_c:
    number = pack_number(0xe1427e6f)
    is_base = False
    _data_cls = namedtuple('Messages', ['offset', 'limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getRecents_c.number
        result += int_c.serialize(data.offset)
        result += int_c.serialize(data.limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getRecents_c._data_cls(offset = int_c.deserialize(io_bytes),
                                      limit = int_c.deserialize(io_bytes))
combinators[getRecents_c.number] = getRecents_c


class checkin_c:
    number = pack_number(0x55b3e8fb)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['peer'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += checkin_c.number
        result += inputgeochat_c.serialize(data.peer)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return checkin_c._data_cls(peer = deserialize(io_bytes))
combinators[checkin_c.number] = checkin_c


class getFullChat_c:
    number = pack_number(0x6722dd6f)
    is_base = False
    _data_cls = namedtuple('ChatFull', ['peer'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getFullChat_c.number
        result += inputgeochat_c.serialize(data.peer)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getFullChat_c._data_cls(peer = deserialize(io_bytes))
combinators[getFullChat_c.number] = getFullChat_c


class editChatTitle_c:
    number = pack_number(0x4c8e2273)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['peer', 'title', 'address'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += editChatTitle_c.number
        result += inputgeochat_c.serialize(data.peer)
        result += string_c.serialize(data.title)
        result += string_c.serialize(data.address)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return editChatTitle_c._data_cls(peer = deserialize(io_bytes),
                                         title = string_c.deserialize(io_bytes),
                                         address = string_c.deserialize(io_bytes))
combinators[editChatTitle_c.number] = editChatTitle_c


class editChatPhoto_c:
    number = pack_number(0x35d81a95)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['peer', 'photo'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += editChatPhoto_c.number
        result += inputgeochat_c.serialize(data.peer)
        result += inputchatphoto_c.serialize(data.photo)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return editChatPhoto_c._data_cls(peer = deserialize(io_bytes),
                                         photo = deserialize(io_bytes))
combinators[editChatPhoto_c.number] = editChatPhoto_c


class search_c:
    number = pack_number(0xcfcdc44d)
    is_base = False
    _data_cls = namedtuple('Messages', ['peer', 'q', 'filter', 'min_date', 'max_date', 'offset', 'max_id', 'limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += search_c.number
        result += inputgeochat_c.serialize(data.peer)
        result += string_c.serialize(data.q)
        result += messagesfilter_c.serialize(data.filter)
        result += int_c.serialize(data.min_date)
        result += int_c.serialize(data.max_date)
        result += int_c.serialize(data.offset)
        result += int_c.serialize(data.max_id)
        result += int_c.serialize(data.limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return search_c._data_cls(peer = deserialize(io_bytes),
                                  q = string_c.deserialize(io_bytes),
                                  filter = deserialize(io_bytes),
                                  min_date = int_c.deserialize(io_bytes),
                                  max_date = int_c.deserialize(io_bytes),
                                  offset = int_c.deserialize(io_bytes),
                                  max_id = int_c.deserialize(io_bytes),
                                  limit = int_c.deserialize(io_bytes))
combinators[search_c.number] = search_c


class getHistory_c:
    number = pack_number(0xb53f7a68)
    is_base = False
    _data_cls = namedtuple('Messages', ['peer', 'offset', 'max_id', 'limit'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getHistory_c.number
        result += inputgeochat_c.serialize(data.peer)
        result += int_c.serialize(data.offset)
        result += int_c.serialize(data.max_id)
        result += int_c.serialize(data.limit)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getHistory_c._data_cls(peer = deserialize(io_bytes),
                                      offset = int_c.deserialize(io_bytes),
                                      max_id = int_c.deserialize(io_bytes),
                                      limit = int_c.deserialize(io_bytes))
combinators[getHistory_c.number] = getHistory_c


class setTyping_c:
    number = pack_number(0x8b8a729)
    is_base = False
    _data_cls = namedtuple('Bool', ['peer', 'typing'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += setTyping_c.number
        result += inputgeochat_c.serialize(data.peer)
        result += bool_c.serialize(data.typing)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return setTyping_c._data_cls(peer = deserialize(io_bytes),
                                     typing = deserialize(io_bytes))
combinators[setTyping_c.number] = setTyping_c


class sendMessage_c:
    number = pack_number(0x61b0044)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['peer', 'message', 'random_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sendMessage_c.number
        result += inputgeochat_c.serialize(data.peer)
        result += string_c.serialize(data.message)
        result += long_c.serialize(data.random_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sendMessage_c._data_cls(peer = deserialize(io_bytes),
                                       message = string_c.deserialize(io_bytes),
                                       random_id = long_c.deserialize(io_bytes))
combinators[sendMessage_c.number] = sendMessage_c


class sendMedia_c:
    number = pack_number(0xb8f0deff)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['peer', 'media', 'random_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sendMedia_c.number
        result += inputgeochat_c.serialize(data.peer)
        result += inputmedia_c.serialize(data.media)
        result += long_c.serialize(data.random_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sendMedia_c._data_cls(peer = deserialize(io_bytes),
                                     media = deserialize(io_bytes),
                                     random_id = long_c.deserialize(io_bytes))
combinators[sendMedia_c.number] = sendMedia_c


class createGeoChat_c:
    number = pack_number(0xe092e16)
    is_base = False
    _data_cls = namedtuple('StatedMessage', ['title', 'geo_point', 'address', 'venue'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += createGeoChat_c.number
        result += string_c.serialize(data.title)
        result += inputgeopoint_c.serialize(data.geo_point)
        result += string_c.serialize(data.address)
        result += string_c.serialize(data.venue)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return createGeoChat_c._data_cls(title = string_c.deserialize(io_bytes),
                                         geo_point = deserialize(io_bytes),
                                         address = string_c.deserialize(io_bytes),
                                         venue = string_c.deserialize(io_bytes))
combinators[createGeoChat_c.number] = createGeoChat_c


class getDhConfig_c:
    number = pack_number(0x26cf8950)
    is_base = False
    _data_cls = namedtuple('DhConfig', ['version', 'random_length'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += getDhConfig_c.number
        result += int_c.serialize(data.version)
        result += int_c.serialize(data.random_length)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return getDhConfig_c._data_cls(version = int_c.deserialize(io_bytes),
                                       random_length = int_c.deserialize(io_bytes))
combinators[getDhConfig_c.number] = getDhConfig_c


class requestEncryption_c:
    number = pack_number(0xf64daf43)
    is_base = False
    _data_cls = namedtuple('EncryptedChat', ['user_id', 'random_id', 'g_a'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += requestEncryption_c.number
        result += inputuser_c.serialize(data.user_id)
        result += int_c.serialize(data.random_id)
        result += bytes_c.serialize(data.g_a)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return requestEncryption_c._data_cls(user_id = deserialize(io_bytes),
                                             random_id = int_c.deserialize(io_bytes),
                                             g_a = bytes_c.deserialize(io_bytes))
combinators[requestEncryption_c.number] = requestEncryption_c


class acceptEncryption_c:
    number = pack_number(0x3dbc0415)
    is_base = False
    _data_cls = namedtuple('EncryptedChat', ['peer', 'g_b', 'key_fingerprint'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += acceptEncryption_c.number
        result += inputencryptedchat_c.serialize(data.peer)
        result += bytes_c.serialize(data.g_b)
        result += long_c.serialize(data.key_fingerprint)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return acceptEncryption_c._data_cls(peer = deserialize(io_bytes),
                                            g_b = bytes_c.deserialize(io_bytes),
                                            key_fingerprint = long_c.deserialize(io_bytes))
combinators[acceptEncryption_c.number] = acceptEncryption_c


class discardEncryption_c:
    number = pack_number(0xedd923c5)
    is_base = False
    _data_cls = namedtuple('Bool', ['chat_id'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += discardEncryption_c.number
        result += int_c.serialize(data.chat_id)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return discardEncryption_c._data_cls(chat_id = int_c.deserialize(io_bytes))
combinators[discardEncryption_c.number] = discardEncryption_c


class setEncryptedTyping_c:
    number = pack_number(0x791451ed)
    is_base = False
    _data_cls = namedtuple('Bool', ['peer', 'typing'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += setEncryptedTyping_c.number
        result += inputencryptedchat_c.serialize(data.peer)
        result += bool_c.serialize(data.typing)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return setEncryptedTyping_c._data_cls(peer = deserialize(io_bytes),
                                              typing = deserialize(io_bytes))
combinators[setEncryptedTyping_c.number] = setEncryptedTyping_c


class readEncryptedHistory_c:
    number = pack_number(0x7f4b690a)
    is_base = False
    _data_cls = namedtuple('Bool', ['peer', 'max_date'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += readEncryptedHistory_c.number
        result += inputencryptedchat_c.serialize(data.peer)
        result += int_c.serialize(data.max_date)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return readEncryptedHistory_c._data_cls(peer = deserialize(io_bytes),
                                                max_date = int_c.deserialize(io_bytes))
combinators[readEncryptedHistory_c.number] = readEncryptedHistory_c


class sendEncrypted_c:
    number = pack_number(0xa9776773)
    is_base = False
    _data_cls = namedtuple('SentEncryptedMessage', ['peer', 'random_id', 'data'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sendEncrypted_c.number
        result += inputencryptedchat_c.serialize(data.peer)
        result += long_c.serialize(data.random_id)
        result += bytes_c.serialize(data.data)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sendEncrypted_c._data_cls(peer = deserialize(io_bytes),
                                         random_id = long_c.deserialize(io_bytes),
                                         data = bytes_c.deserialize(io_bytes))
combinators[sendEncrypted_c.number] = sendEncrypted_c


class sendEncryptedFile_c:
    number = pack_number(0x9a901b66)
    is_base = False
    _data_cls = namedtuple('SentEncryptedMessage', ['peer', 'random_id', 'data', 'file'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sendEncryptedFile_c.number
        result += inputencryptedchat_c.serialize(data.peer)
        result += long_c.serialize(data.random_id)
        result += bytes_c.serialize(data.data)
        result += inputencryptedfile_c.serialize(data.file)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sendEncryptedFile_c._data_cls(peer = deserialize(io_bytes),
                                             random_id = long_c.deserialize(io_bytes),
                                             data = bytes_c.deserialize(io_bytes),
                                             file = deserialize(io_bytes))
combinators[sendEncryptedFile_c.number] = sendEncryptedFile_c


class sendEncryptedService_c:
    number = pack_number(0x32d439a4)
    is_base = False
    _data_cls = namedtuple('SentEncryptedMessage', ['peer', 'random_id', 'data'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += sendEncryptedService_c.number
        result += inputencryptedchat_c.serialize(data.peer)
        result += long_c.serialize(data.random_id)
        result += bytes_c.serialize(data.data)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return sendEncryptedService_c._data_cls(peer = deserialize(io_bytes),
                                                random_id = long_c.deserialize(io_bytes),
                                                data = bytes_c.deserialize(io_bytes))
combinators[sendEncryptedService_c.number] = sendEncryptedService_c


class receivedQueue_c:
    number = pack_number(0x55a5bb66)
    is_base = False
    _data_cls = namedtuple('Vector', ['max_qts'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += receivedQueue_c.number
        result += int_c.serialize(data.max_qts)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return receivedQueue_c._data_cls(max_qts = int_c.deserialize(io_bytes))
combinators[receivedQueue_c.number] = receivedQueue_c


class saveBigFilePart_c:
    number = pack_number(0xde7b673d)
    is_base = False
    _data_cls = namedtuple('Bool', ['file_id', 'file_part', 'file_total_parts', 'bytes'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += saveBigFilePart_c.number
        result += long_c.serialize(data.file_id)
        result += int_c.serialize(data.file_part)
        result += int_c.serialize(data.file_total_parts)
        result += bytes_c.serialize(data.bytes)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return saveBigFilePart_c._data_cls(file_id = long_c.deserialize(io_bytes),
                                           file_part = int_c.deserialize(io_bytes),
                                           file_total_parts = int_c.deserialize(io_bytes),
                                           bytes = bytes_c.deserialize(io_bytes))
combinators[saveBigFilePart_c.number] = saveBigFilePart_c


class initConnection_c:
    number = pack_number(0x69796de9)
    is_base = False
    _data_cls = namedtuple('X', ['X', 'api_id', 'device_model', 'system_version', 'app_version', 'lang_code'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += initConnection_c.number
        result += type_c.serialize(data.X)
        result += int_c.serialize(data.api_id)
        result += string_c.serialize(data.device_model)
        result += string_c.serialize(data.system_version)
        result += string_c.serialize(data.app_version)
        result += string_c.serialize(data.lang_code)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return initConnection_c._data_cls(X = deserialize(io_bytes),
                                          api_id = int_c.deserialize(io_bytes),
                                          device_model = string_c.deserialize(io_bytes),
                                          system_version = string_c.deserialize(io_bytes),
                                          app_version = string_c.deserialize(io_bytes),
                                          lang_code = string_c.deserialize(io_bytes))
combinators[initConnection_c.number] = initConnection_c


class getSupport_c:
    number = pack_number(0x9cdf08cd)
    is_base = False
    _data_cls = namedtuple('Support', ['tag', 'number'])

    @staticmethod
    def serialize(data=None):
        return getSupport_c.number

    @staticmethod
    def deserialize(io_bytes):
        number = io_bytes.read(4)
        assert getSupport_c.number == number
        return getSupport_c._data_cls(tag='help.getSupport', number=getSupport_c.number)
combinators[getSupport_c.number] = getSupport_c


class invokeWithLayer15_c:
    number = pack_number(0xb4418b64)
    is_base = False
    _data_cls = namedtuple('X', ['X'])

    @staticmethod
    def serialize(data=None):
        result = bytearray()
        result += invokeWithLayer15_c.number
        result += type_c.serialize(data.X)
        return bytes(result)

    @staticmethod
    def deserialize(io_bytes):
        return invokeWithLayer15_c._data_cls(X = deserialize(io_bytes))
combinators[invokeWithLayer15_c.number] = invokeWithLayer15_c

