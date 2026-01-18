from box import Box

PERMISSIONS = Box.from_json(filename='Utils/Permissions.json')
ERRMSG = Box.from_json(filename='Utils/ErrorMsg.json')
METHODS = Box.from_json(filename='Utils/Method.json')
RESPONSE = Box.from_json(filename='Utils/Response.json')
KEY = Box.from_json(filename='Utils/Key.json')
AUDIT = Box.from_json(filename='Utils/Audit.json')

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