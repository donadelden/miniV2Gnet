import requests
r = requests.post("http://localhost:9000", headers={"Format":"EXI"}, 
data=b"809802107f860d7bae65dd8a891a1d1d1c0e8bcbddddddcb9dcccb9bdc99cbd5148bd8d85b9bdb9a58d85b0b595e1a50d5a1d1d1c0e8bcbddddddcb9dcccb9bdc99cbcc8c0c0c4bcc0d0bde1b5b191cda59cb5b5bdc9948d958d91cd84b5cda184c8d4d9002b4b21890623696431024687474703a2f2f7777772e77332e6f72672f54522f63616e6f6e6963616c2d6578694852d0e8e8e0745e5eeeeeee5cee665cdee4ce5e646060625e60685ef0dad8cadcc646e6d0c2646a6c84165aa773adf12a841e302f171698e9c4d1e6bb2afdac13826f13ba6a09532c82a2841400000000000501c030a0161005696431001000100240880e201081203840110260a88032940000081030c08018503f03102400c0c3010031039804461800080")
print(r.text)