from merkle_tree_tool import MerkleTree

if __name__ == '__main__':
    tree_height = 3

    mt = MerkleTree(tree_height)

    for i in range(2**tree_height):
        args = mt.append(f'record{i}')
        print(args)
        args = mt.verify(f'record{i}')
        print(args)

    for i in range(2**tree_height):
        args = mt.verify(f'record{i}')
        print(args)

    for i in range(2**tree_height):
        args = mt.update(f'record{i}', f'record{i}{i}')
        print(args)

    for i in range(2**tree_height):
        args = mt.verify(f'record{i}{i}')
        print(args)
