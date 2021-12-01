import hashlib
import base64


EMPTY_HASH = hashlib.sha256(b'').digest()
RIGHT_EMPTY_HASH_B64 = base64.b64encode(b'\xaa' + EMPTY_HASH)
LEFT_EMPTY_HASH_B64 = base64.b64encode(b'\xbb' + EMPTY_HASH)


class Node:
    def __init__(self, height: int):
        self.height = height
        if height == 0:
            self.left_sibling = None
            self.right_sibling = None
            self.value = hashlib.sha256(b'')
        else:
            self.left_sibling = Node(height-1)
            self.right_sibling = Node(height-1)
            self.value = hashlib.sha256(self.left_sibling.value.digest() + self.right_sibling.value.digest())

    def get_value(self):
        to_return = b''
        if self.value != b'':
            to_return = base64.b64encode(self.value.digest())
        return f'b64:{to_return.decode()}'

    def append(self, value):
        if self.height == 0:
            if self.value.digest() == EMPTY_HASH:
                self.value = hashlib.sha256(value.encode('utf-8'))
                return 0, [f'str:{value}']
            else:
                return -1, []
        left = self.left_sibling.append(value)
        if left[0] == 0:
            sib = RIGHT_EMPTY_HASH_B64
            if self.right_sibling.value.digest() != EMPTY_HASH:
                self.value = hashlib.sha256(self.left_sibling.value.digest() + self.right_sibling.value.digest())
                sib = base64.b64encode(b'\xaa' + self.right_sibling.value.digest())
            else:
                self.value = hashlib.sha256(self.left_sibling.value.digest() + EMPTY_HASH)
            return 0, left[1] + [f'b64:{sib.decode()}']
        right = self.right_sibling.append(value)
        if right[0] == 0:
            sib = base64.b64encode(b'\xbb' + self.left_sibling.value.digest())
            self.value = hashlib.sha256(self.left_sibling.value.digest() + self.right_sibling.value.digest())
            return 0, right[1] + [f'b64:{sib.decode()}']
        return -1, []

    def verify(self, value):
        if self.height == 0:
            if self.value.digest() == hashlib.sha256(value.encode('utf-8')).digest():
                return 0, [f'str:{value}']
            else:
                return -1, []
        left = self.left_sibling.verify(value)
        if left[0] == 0:
            sib = RIGHT_EMPTY_HASH_B64
            if self.right_sibling.value.digest() != EMPTY_HASH:
                sib = base64.b64encode(b'\xaa' + self.right_sibling.value.digest())
            return 0, left[1] + [f'b64:{sib.decode()}']
        right = self.right_sibling.verify(value)
        if right[0] == 0:
            sib = base64.b64encode(b'\xbb' + self.left_sibling.value.digest())
            return 0, right[1] + [f'b64:{sib.decode()}']
        return -1, []

    def update(self, old_value, new_value):
        if self.height == 0:
            if self.value.digest() == hashlib.sha256(old_value.encode('utf-8')).digest():
                self.value = hashlib.sha256(new_value.encode('utf-8'))
                return 0, [f'str:{old_value}', f'str:{new_value}']
            else:
                return -1, []
        left = self.left_sibling.update(old_value, new_value)
        if left[0] == 0:
            sib = RIGHT_EMPTY_HASH_B64
            if self.right_sibling.value.digest() != EMPTY_HASH:
                self.value = hashlib.sha256(self.left_sibling.value.digest() + self.right_sibling.value.digest())
                sib = base64.b64encode(b'\xaa' + self.right_sibling.value.digest())
            else:
                self.value = hashlib.sha256(self.left_sibling.value.digest() + EMPTY_HASH)
            return 0, left[1][:-1] + [f'b64:{sib.decode()}'] + left[1][-1:]
        right = self.right_sibling.update(old_value, new_value)
        if right[0] == 0:
            sib = LEFT_EMPTY_HASH_B64
            if self.left_sibling.value.digest() != EMPTY_HASH:
                self.value = hashlib.sha256(self.left_sibling.value.digest() + self.right_sibling.value.digest())
                sib = base64.b64encode(b'\xbb' + self.left_sibling.value.digest())
            else:
                self.value = hashlib.sha256(EMPTY_HASH + self.right_sibling.value.digest())
            return 0, right[1][:-1] + [f'b64:{sib.decode()}'] + right[1][-1:]
        return -1, []


class MerkleTree:
    def __init__(self, height: int):
        self.root = Node(height)
        self.max_records = 2**height
        self.size = 0

    def append(self, value: str):
        if self.size == self.max_records:
            return []
        ok, path = self.root.append(value)
        if ok != 0:
            return []
        new_root = self.root.get_value()
        args = ['str:append'] + path
        return '--app-arg ' + ' --app-arg '.join([f'"{arg}"' for arg in args])

    def verify(self, value: str):
        ok, path = self.root.verify(value)
        if ok != 0:
            return []
        args = ['str:verify'] + path
        return '--app-arg ' + ' --app-arg '.join([f'"{arg}"' for arg in args])

    def update(self, old_value, new_value):
        ok, path = self.root.update(old_value, new_value)
        if ok != 0:
            return []
        args = ['str:update'] + path
        return '--app-arg ' + ' --app-arg '.join([f'"{arg}"' for arg in args])
