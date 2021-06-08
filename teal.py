from pyteal import *
from algosdk.v2client import algod
import os

# App args constants
COMMAND_INDEX = 0  # index of command in app args slice
CURRENT_ROOT_INDEX = 1  # index of current root in app args slice
NEW_ROOT_INDEX = 2  # index of new root in app args slice
VALUE_INDEX = 3  # index of value to verify/append in app args slice

TREE_HEIGHT = 3  # merkle tree height. leaves are height 0. min: 3, max: 11
MAX_APP_ARGS = VALUE_INDEX + TREE_HEIGHT + 1  # number of app args

# Transactions group constants
GROUP_SIZE = 5
APP_GROUP_IDX = 0  # index of app call in group
PAYMENT_GROUP_IDX = 1  # index of payment transaction to the smart contract
VERIFY_FEE_PAYMENT_GROUP_IDX = 1  # index of payment transaction to the verify smart contract
VERIFY_SC_GROUP_IDX = 2  # index of verify smart contract txn in group
APPEND_FEE_PAYMENT_GROUP_IDX = 3  # index of payment transaction to the append smart contract
APPEND_SC_GROUP_IDX = 4  # index of append smart contract txn in group


# creates expressions to concat and hash nodes in the merkle tree
# application args are expected to be empty or 33 bytes long where the 1st byte indicates right or left sibling
# 0xaa for right sibling and 0xbb (actually any other byte) for left sibling
def concat_and_hash(txn: TxnObject, i: int, scratch_var: ScratchVar):
    concat_to_right_sibling = Concat(scratch_var.load(), Substring(txn.application_args[i], Int(1), Int(33)))
    concat_to_left_sibling = Concat(Substring(txn.application_args[i], Int(1), Int(33)), scratch_var.load())
    return If(Len(txn.application_args[i]) == Int(33),
              If(Substring(txn.application_args[i], Int(0), Int(1)) == Bytes('base16', 'aa'),
                 scratch_var.store(Sha256(concat_to_right_sibling)),
                 scratch_var.store(Sha256(concat_to_left_sibling)),
                 ),
              If(scratch_var.load() == Bytes(''),  # checks if we're in an empty subtree
                 scratch_var.store(Bytes('')),
                 scratch_var.store(Sha256(scratch_var.load()))
                 )
              )


def approval(verify_sc_addr: str, append_sc_addr: str):
    on_creation = Seq([
        App.globalPut(Bytes('Creator'), Txn.sender()),  # set creator
        App.globalPut(Bytes('Root'), Bytes('')),  # init root
        App.globalPut(Bytes('Size'), Int(0)),  # init size
        Return(Int(1)),
    ])

    verify_sc_txn = Gtxn[VERIFY_SC_GROUP_IDX]  # get the verify stateless smart contract txn
    append_sc_txn = Gtxn[APPEND_SC_GROUP_IDX]  # get the append stateless smart contract txn

    test_group = And(
        Global.group_size() == Int(GROUP_SIZE),
        Txn.group_index() == Int(APP_GROUP_IDX),  # app call should be 1st in group
        verify_sc_txn.type_enum() == EnumInt('pay'),
        verify_sc_txn.sender() == Addr(verify_sc_addr),
        append_sc_txn.type_enum() == EnumInt('pay'),
        append_sc_txn.sender() == Addr(append_sc_addr),
    )
    test_txn = And(
        Txn.amount() == Int(0),
        Txn.type_enum() == EnumInt('appl'),
        Txn.close_remainder_to() == Global.zero_address(),
        Txn.rekey_to() == Global.zero_address()
    )
    test_args = Txn.application_args.length() == Int(MAX_APP_ARGS)  # verify fixed number of app args
    test_root = App.globalGet(Bytes('Root')) == Txn.application_args[CURRENT_ROOT_INDEX]  # verify root

    inc_size = Seq([
        App.globalPut(Bytes('Size'), Int(1) + App.globalGet(Bytes('Size')))
    ])

    append = Seq([
        App.globalPut(Bytes('Root'), Txn.application_args[NEW_ROOT_INDEX]),
        inc_size,
        Int(1)
    ])

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == EnumInt('DeleteApplication'), Return(Int(1))],
        [Txn.on_completion() == EnumInt('OptIn'), Return(Int(1))],
        [Not(And(test_group, test_txn, test_args, test_root)), Return(Int(0))],
        [Txn.application_args[COMMAND_INDEX] == Bytes('append'), Return(append)],
        [Txn.application_args[COMMAND_INDEX] == Bytes('verify'), Return(Int(1))]
    )

    return program


def clear_state_program():
    program = Seq([
        Return(Int(1))
    ])

    return program


def stateless_verify():
    app_txn = Gtxn[APP_GROUP_IDX]
    fee_payment_txn = Gtxn[VERIFY_FEE_PAYMENT_GROUP_IDX]
    test_group = And(
        Global.group_size() == Int(GROUP_SIZE),
        Txn.group_index() == Int(VERIFY_SC_GROUP_IDX),
        app_txn.type_enum() == EnumInt('appl'),
        fee_payment_txn.amount() == Txn.fee(),
        fee_payment_txn.type_enum() == EnumInt('pay'),
        fee_payment_txn.receiver() == Txn.sender(),
    )
    test_txn = And(
        Txn.amount() == Int(0),
        Txn.type_enum() == EnumInt('pay'),
        Txn.close_remainder_to() == Global.zero_address(),
        Txn.rekey_to() == Global.zero_address(),
    )
    test_args = app_txn.application_args.length() == Int(MAX_APP_ARGS)

    sv = ScratchVar(TealType.bytes)

    logic = Seq(
        [
            sv.store(Bytes('')),
            If(
                app_txn.application_args[COMMAND_INDEX] == Bytes('verify'),
                sv.store(Sha256(app_txn.application_args[VALUE_INDEX])),  # init sv to hold hash of value to verify
            ),
            Seq(  # concat with provided siblings along path to root
                [
                    concat_and_hash(app_txn, i, sv) for i in range(VALUE_INDEX + 1, MAX_APP_ARGS)
                ]
            ),
            sv.load() == app_txn.application_args[CURRENT_ROOT_INDEX],  # test that result is matching the expected root
        ]
    )

    program = Cond(
        [Not(And(test_group, test_txn, test_args)), Return(Int(0))],
        [
            Or(
                app_txn.application_args[COMMAND_INDEX] == Bytes('verify'),
                app_txn.application_args[COMMAND_INDEX] == Bytes('append'),
            ),
            Return(logic)
        ]
    )

    return program


def stateless_append():
    app_txn = Gtxn[APP_GROUP_IDX]
    fee_payment_txn = Gtxn[APPEND_FEE_PAYMENT_GROUP_IDX]
    test_group = And(
        Global.group_size() == Int(GROUP_SIZE),
        Txn.group_index() == Int(APPEND_SC_GROUP_IDX),
        app_txn.type_enum() == EnumInt('appl'),
        fee_payment_txn.amount() == Txn.fee(),
        fee_payment_txn.type_enum() == EnumInt('pay'),
        fee_payment_txn.receiver() == Txn.sender(),
    )
    test_txn = And(
        Txn.amount() == Int(0),
        Txn.type_enum() == EnumInt('pay'),
        Txn.close_remainder_to() == Global.zero_address(),
        Txn.rekey_to() == Global.zero_address(),
    )
    test_args = app_txn.application_args.length() == Int(MAX_APP_ARGS)

    sv = ScratchVar(TealType.bytes)

    logic = Seq(
        [
            sv.store(Sha256(app_txn.application_args[VALUE_INDEX])),  # init sv to hold the hash of value to append
            Seq(  # concat with provided siblings along path to root
                [
                    concat_and_hash(app_txn, i, sv) for i in range(VALUE_INDEX + 1, MAX_APP_ARGS)
                ]
            ),
            sv.load() == app_txn.application_args[NEW_ROOT_INDEX]  # check that result is matching the expected new root
        ]
    )

    program = Cond(
        [Not(And(test_group, test_txn, test_args)), Return(Int(0))],
        [app_txn.application_args[COMMAND_INDEX] == Bytes('append'), Return(logic)],
        [app_txn.application_args[COMMAND_INDEX] == Bytes('verify'), Return(Int(1))]
    )

    return program


if __name__ == '__main__':
    algod_url = os.getenv('MT_ALGOD_URL')
    algod_token = os.getenv('MT_ALGOD_TOKEN')
    if algod_url == '':
        print('please export MT_ALGOD_URL and MT_ALGOD_TOKEN environment variables to a valid v2 algod client')
        exit(1)
    print(f'starting algod client: {algod_url}')
    algod_client = algod.AlgodClient(algod_token, algod_url)
    res = None
    with open('verify_sc.teal', 'w') as f:
        compiled = compileTeal(stateless_verify(), Mode.Signature)
        f.write(compiled)
        print('verify_sc.teal')
        try:
            res = algod_client.compile(compiled)
        except Exception as e:
            print(f'error compiling stateless TEAL {e}')
            exit(1)
    verify_sc_addr = res["hash"]
    print(f'verify smart contract address: {verify_sc_addr}')
    with open('append_sc.teal', 'w') as f:
        compiled = compileTeal(stateless_append(), Mode.Signature)
        f.write(compiled)
        print('append_sc.teal')
        try:
            res = algod_client.compile(compiled)
        except Exception as e:
            print(f'error compiling stateless TEAL {e}')
            exit(1)
    append_sc_addr = res["hash"]
    print(f'append smart contract address: {append_sc_addr}')
    with open('mt_approval.teal', 'w') as f:
        compiled = compileTeal(approval(verify_sc_addr, append_sc_addr), Mode.Application)
        f.write(compiled)
        print('compiled mt_approval.teal')

    with open('mt_clear.teal', 'w') as f:
        compiled = compileTeal(clear_state_program(), Mode.Application)
        f.write(compiled)
        print('compiled mt_clear.teal')
