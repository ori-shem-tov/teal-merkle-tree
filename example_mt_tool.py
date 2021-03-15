from merkle_tree_tool import MerkleTree

if __name__ == '__main__':
    mt = MerkleTree(3)
    for i in range(8):
        print(f'appending record{i}')
        args = mt.append(f'record{i}')
        print(args)

    for i in range(8):
        print(f'validating record{i}')
        args = mt.validate(f'record{i}')
        print(args)
