from pyteal import *

# App args constants
COMMAND_INDEX = 0  # index of command in app args slice
VALUE_INDEX = 1  # index of value to verify/append in app args slice
FIRST_SIBLING_INDEX = VALUE_INDEX + 1

TREE_HEIGHT = 3  # merkle tree height. leaves are height 0.
LAST_SIBLING_INDEX = FIRST_SIBLING_INDEX + TREE_HEIGHT - 1
NUM_APP_ARGS_VERIFY = NUM_APP_ARGS_APPEND = LAST_SIBLING_INDEX + 1  # number of app args

NUM_APP_ARGS_UPDATE = NUM_APP_ARGS_VERIFY + 1
UPDATE_VALUE_INDEX = NUM_APP_ARGS_UPDATE - 1


@Subroutine(TealType.bytes)
def hash_concat(left: TealType.bytes, right: TealType.bytes):
    return Sha256(Concat(left, right))


@Subroutine(TealType.bytes)
def calc_root(init_value: Expr):
    """
    Calculates the root of the Merkle tree from a specific leaf.
    Expects its siblings in the 'Txn.application_args' array.
    :param init_value: the hash value of the leaf to start the computation from
    :return: the hash value of the expected root
    """
    i = ScratchVar(TealType.uint64)
    result = ScratchVar(TealType.bytes)

    init = i.store(Int(FIRST_SIBLING_INDEX))
    cond = i.load() <= Int(LAST_SIBLING_INDEX)
    itr = i.store(i.load() + Int(1))

    return Seq([
        result.store(init_value),
        # go over all siblings along the path to the top hash
        For(init, cond, itr).Do(
            # if a sibling starts with 0xaa (170) byte, then it's a right sibling.
            result.store(
                If(GetByte(Txn.application_args[i.load()], Int(0)) == Int(170)).Then(
                    hash_concat(
                        result.load(),
                        Extract(Txn.application_args[i.load()], Int(1), Int(32)),
                    )
                ).Else(
                    hash_concat(
                        Extract(Txn.application_args[i.load()], Int(1), Int(32)),
                        result.load(),
                    )
                )
            )
        ),
        result.load()
    ])


@Subroutine(TealType.bytes)
def calc_init_root(tree_height: Expr):
    """
    Calculates the root of an empty Merkle tree
    :param tree_height: height of the Merkle tree
    :return:
    """
    i = ScratchVar(TealType.uint64)
    result = ScratchVar(TealType.bytes)
    return Seq([
        result.store(Sha256(Bytes(''))),
        For(i.store(Int(0)), i.load() < tree_height, i.store(i.load() + Int(1))).Do(
            result.store(Sha256(Concat(result.load(), result.load())))
        ),
        result.load()
    ])


def approval5():
    on_creation = Seq([
        # Initialize global state 'Root' and 'Size' of an empty tree
        App.globalPut(Bytes('Root'), calc_init_root(Int(TREE_HEIGHT))),  # init root
        App.globalPut(Bytes('Size'), Int(0)),  # init size
        Approve()
    ])

    verify = Seq([
        Assert(Txn.application_args.length() == Int(NUM_APP_ARGS_VERIFY)),
        # Calculate the expected root hash from the input and compare it to the actual stored root hash
        Assert(App.globalGet(Bytes('Root')) == calc_root(
            Sha256(Txn.application_args[VALUE_INDEX])
        )),
        Int(1)
    ])

    append = Seq([
        Assert(Txn.application_args.length() == Int(NUM_APP_ARGS_APPEND)),
        # Since vacant leaves hold the hash of an empty string, only non-empty strings are allowed to be appended
        Assert(Txn.application_args[VALUE_INDEX] != Bytes('')),
        # Make sure leaf is actually vacant by calculating the root starting with an empty string
        Assert(App.globalGet(Bytes('Root')) == calc_root(
            Sha256(Bytes(''))
        )),
        # Calculate and update the new root
        App.globalPut(Bytes('Root'), calc_root(
            Sha256(
                Txn.application_args[VALUE_INDEX]
            )
        )),
        # Increment the size
        App.globalPut(Bytes('Size'), App.globalGet(Bytes('Size')) + Int(1)),
        Int(1)
    ])

    update = Seq([
        Assert(Txn.application_args.length() == Int(NUM_APP_ARGS_UPDATE)),
        # Since vacant leaves hold the hash of an empty string, only non-empty strings are allowed to be appended
        # Essentially this would be a 'delete' op, which we don't support currently
        Assert(Txn.application_args[UPDATE_VALUE_INDEX] != Bytes('')),
        # Verify the old value
        Assert(App.globalGet(Bytes('Root')) == calc_root(
            Sha256(
                Txn.application_args[VALUE_INDEX]
            )
        )),
        # Calculate and update the new root
        App.globalPut(Bytes('Root'), calc_root(
            Sha256(
                Txn.application_args[UPDATE_VALUE_INDEX]
            )
        )),
        Int(1)
    ])

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.OptIn, Approve()],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Txn.sender() == Global.creator_address())],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Txn.sender() == Global.creator_address())],
        [
            Txn.on_completion() == OnComplete.NoOp,
            Cond(
                [Txn.application_args[COMMAND_INDEX] == Bytes('verify'),
                 Return(verify)],
                [Txn.application_args[COMMAND_INDEX] == Bytes('append'),
                 Return(append)],
                [Txn.application_args[COMMAND_INDEX] == Bytes('update'),
                 Return(update)]
            )
        ]
    )

    return program


if __name__ == '__main__':
    with open('mt_clear.teal', 'w') as f:
        compiled = compileTeal(Approve(), Mode.Application, version=5)
        f.write(compiled)
        print('compiled mt_clear.teal')

    with open('mt_approval5.teal', 'w') as f:
        compiled = compileTeal(approval5(), Mode.Application, version=5)
        f.write(compiled)
        print('compiled mt_approval5.teal')
