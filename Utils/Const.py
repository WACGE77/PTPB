from box import Box
import os

# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PERMISSIONS = Box.from_json(filename=os.path.join(BASE_DIR, 'Permissions.json'))
ERRMSG = Box.from_json(filename=os.path.join(BASE_DIR, 'ErrorMsg.json'))
METHODS = Box.from_json(filename=os.path.join(BASE_DIR, 'Method.json'))
RESPONSE = Box.from_json(filename=os.path.join(BASE_DIR, 'Response.json'))
KEY = Box.from_json(filename=os.path.join(BASE_DIR, 'Key.json'))
AUDIT = Box.from_json(filename=os.path.join(BASE_DIR, 'Audit.json'))
CONFIG = Box.from_json(filename=os.path.join(BASE_DIR, 'Config.json'))
RESPONSE__200__SUCCESS = {
    KEY.CODE:RESPONSE.P_200_OK.CODE,
    KEY.MSG:RESPONSE.P_200_OK.MSG
}
RESPONSE__400__FAILED = {
    KEY.CODE: RESPONSE.P_400_BAD_REQUEST.CODE,
    KEY.MSG: RESPONSE.P_400_BAD_REQUEST.MSG
}

READ_ONLY_FILED = {'read_only':True}
WRITE_ONLY_FILED = {'write_only':True}