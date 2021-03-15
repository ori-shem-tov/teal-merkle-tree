import hashlib
import base64


class Node:
    def __init__(self, height: int):
        self.value = b''
        self.height = height
        if height == 0:
            self.left_sibling = None
            self.right_sibling = None
        else:
            self.left_sibling = Node(height-1)
            self.right_sibling = Node(height-1)

    def get_value(self):
        to_return = b''
        if self.value != b'':
            to_return = base64.b64encode(self.value.digest())
        return f'b64:{to_return.decode()}'

    def append(self, value):
        if self.height == 0:
            if self.value == b'':
                self.value = hashlib.sha256(value.encode('utf-8'))
                return 0, [f'str:{value}']
            else:
                return -1, []
        left = self.left_sibling.append(value)
        if left[0] == 0:
            sib = b''
            if self.right_sibling.value != b'':
                self.value = hashlib.sha256(self.left_sibling.value.digest()+self.right_sibling.value.digest())
                sib = base64.b64encode(b'\xaa' + self.right_sibling.value.digest())
            else:
                self.value = hashlib.sha256(self.left_sibling.value.digest())
            return 0, left[1] + [f'b64:{sib.decode()}']
        right = self.right_sibling.append(value)
        if right[0] == 0:
            sib = base64.b64encode(b'\xbb' + self.left_sibling.value.digest())
            self.value = hashlib.sha256(self.left_sibling.value.digest() + self.right_sibling.value.digest())
            return 0, right[1] + [f'b64:{sib.decode()}']
        return -1, []

    def validate(self, value):
        if self.height == 0:
            if self.value.digest() == hashlib.sha256(value.encode('utf-8')).digest():
                return 0, [f'str:{value}']
            else:
                return -1, []
        left = self.left_sibling.validate(value)
        if left[0] == 0:
            sib = b''
            if self.right_sibling.value != b'':
                sib = base64.b64encode(b'\xaa' + self.right_sibling.value.digest())
            return 0, left[1] + [f'b64:{sib.decode()}']
        right = self.right_sibling.validate(value)
        if right[0] == 0:
            sib = base64.b64encode(b'\xbb' + self.left_sibling.value.digest())
            return 0, right[1] + [f'b64:{sib.decode()}']
        return -1, []


class MerkleTree:
    def __init__(self, height: int):
        self.root = Node(height)
        self.max_records = 2**height
        self.size = 0

    def append(self, value: str):
        if self.size == self.max_records:
            return []
        old_root = self.root.get_value()
        ok, path = self.root.append(value)
        if ok != 0:
            return []
        new_root = self.root.get_value()
        args = ['str:append', old_root, new_root] + path
        return '--app-arg ' + ' --app-arg '.join([f'"{arg}"' for arg in args])

    def validate(self, value: str):
        ok, path = self.root.validate(value)
        if ok != 0:
            return []
        args = ['str:validate', self.root.get_value(), 'b64:'] + path
        return '--app-arg ' + ' --app-arg '.join([f'"{arg}"' for arg in args])
