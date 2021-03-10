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

    def validate_before_append(self):
        if self.height == 0:
            if self.value == b'':
                return 0
            else:
                return -1
        if self.left_sibling.validate_before_append() == 0:
            if self.right_sibling.value != b'':
                b64 = base64.b64encode(b'\xaa' + self.right_sibling.value.digest())
                print(f'right brother {b64}')
            else:
                print(f'right brother \'\'')
            return 0
        if self.right_sibling.validate_before_append() == 0:
            b64 = base64.b64encode(b'\xbb' + self.left_sibling.value.digest())
            print(f'left brother {b64}')
            return 0
        return -1

    def append(self, value):
        if self.height == 0:
            if self.value == b'':
                self.value = hashlib.sha256(value.encode('utf-8'))
                return 0
            else:
                return -1
        if self.left_sibling.append(value) == 0:
            if self.right_sibling.value != b'':
                self.value = hashlib.sha256(self.left_sibling.value.digest()+self.right_sibling.value.digest())
            else:
                self.value = hashlib.sha256(self.left_sibling.value.digest())
            return 0
        if self.right_sibling.append(value) == 0:
            self.value = hashlib.sha256(self.left_sibling.value.digest() + self.right_sibling.value.digest())
            return 0
        return -1


class MerkleTree:
    def __init__(self, height: int):
        self.root = Node(height)
        self.max_records = 2**height
        self.size = 0

    def append(self, value: str):
        if self.size == self.max_records:
            return
        if self.root.value == b'':
            print(f'current root \'\'')
        else:
            print(f'current root {base64.b64encode(self.root.value.digest())}')
        self.root.append(value)
        print(f'new root {base64.b64encode(self.root.value.digest())}')
        return


if __name__ == '__main__':
    mt = MerkleTree(3)
    for i in range(8):
        print(f'appending record{i}')
        mt.root.validate_before_append()
        mt.append(f'record{i}')
