# Tools to quickly encode json messages

import json

def encode_json(dct):
    return json.dumps(dct).encode("utf-8")

def decode_json(bts):
    return json.loads(bts.decode())

# test
# dict0 = {"data": "good"}
# encd = encode_json(dict0)
# print(encd)
# print(len(encd))
# decd = decode_json(encd)
# print(decd)
