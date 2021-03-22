from pyteal import *
from algosdk.v2client import algod
import os

# App args constants
COMMAND_INDEX = 0  # index of command in app args slice
CURRENT_ROOT_INDEX = 1  # index of current root in app args slice
NEW_ROOT_INDEX = 2  # index of new root in app args slice
VALUE_INDEX = 3  # index of value to validate/append in app args slice

TREE_HEIGHT = 3  # merkle tree height. leaves are height 0. min: 3, max: 12
MAX_APP_ARGS = VALUE_INDEX + TREE_HEIGHT + 1  # number of app args

# Transactions group constants
GROUP_SIZE = 3
APP_GROUP_IDX = 0  # index of app call in group
PAYMENT_GROUP_IDX = 1  # index of payment transaction to the smart contract
SC_GROUP_IDX = 2  # index of smart contract txn in group
STATELESS_ADDRESS = ''


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


def approval(smart_contract_address: str):
    on_creation = Seq([
        App.globalPut(Bytes('Creator'), Txn.sender()),  # set creator
        App.globalPut(Bytes('Root'), Bytes('')),  # init root
        App.globalPut(Bytes('Size'), Int(0)),  # init size
        Return(Int(1)),
    ])

    sc_txn = Gtxn[SC_GROUP_IDX]  # get the stateless smart contract txn

    test_group = And(
        Global.group_size() == Int(GROUP_SIZE),
        Txn.group_index() == Int(APP_GROUP_IDX),  # app call should be 1st in group
        sc_txn.type_enum() == EnumInt('pay'),
        sc_txn.sender() == Addr(smart_contract_address),
    )
    test_txn = And(
        Txn.amount() == Int(0),
        Txn.type_enum() == EnumInt('appl'),
        Txn.close_remainder_to() == Global.zero_address(),
        Txn.rekey_to() == Global.zero_address()
    )
    test_args = Txn.application_args.length() == Int(MAX_APP_ARGS)  # validate fixed number of app args
    test_root = App.globalGet(Bytes('Root')) == Txn.application_args[CURRENT_ROOT_INDEX]  # validate root

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
        [Txn.application_args[COMMAND_INDEX] == Bytes('validate'), Return(Int(1))]
    )

    return program


def clear_state_program():
    program = Seq([
        Return(Int(1))
    ])

    return program


def stateless():
    app_txn = Gtxn[APP_GROUP_IDX]
    fee_payment_txn = Gtxn[PAYMENT_GROUP_IDX]
    test_group = And(
        Global.group_size() == Int(GROUP_SIZE),
        Txn.group_index() == Int(SC_GROUP_IDX),  # stateless smart contract txn should be 2nd in group
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

    program = If(
        Not(And(test_group, test_txn, test_args)),
        Return(Int(0)),
        Seq(
            [
                If(app_txn.application_args[COMMAND_INDEX] == Bytes('append'),
                   sv.store(Bytes('')),
                   sv.store(Sha256(app_txn.application_args[VALUE_INDEX]))),
                Seq(  # concat with provided siblings along path to root
                    [
                        concat_and_hash(app_txn, i, sv) for i in range(VALUE_INDEX + 1, MAX_APP_ARGS)
                    ]
                ),
                If(app_txn.application_args[COMMAND_INDEX] == Bytes('validate'),
                   Return(sv.load() == app_txn.application_args[CURRENT_ROOT_INDEX]),
                   If(sv.load() == app_txn.application_args[CURRENT_ROOT_INDEX],
                      Seq(
                          [
                              sv.store(Sha256(app_txn.application_args[VALUE_INDEX])),
                              Seq(  # concat with provided siblings along path to root
                                  [
                                      concat_and_hash(app_txn, i, sv) for i in range(VALUE_INDEX + 1, MAX_APP_ARGS)
                                  ]
                              ),
                              Return(sv.load() == app_txn.application_args[NEW_ROOT_INDEX])
                          ]
                      ),
                      Return(sv.load() == app_txn.application_args[NEW_ROOT_INDEX]))
                   )
            ]
        )
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
    with open('stateless.teal', 'w') as f:
        compiled = compileTeal(stateless(), Mode.Signature)
        f.write(compiled)
        print('compiled stateless.teal')
        try:
            res = algod_client.compile(compiled)
        except Exception as e:
            print(f'error compiling stateless TEAL {e}')
            exit(1)
    print(f'smart contract address: {res["hash"]}')
    with open('mt_approval.teal', 'w') as f:
        compiled = compileTeal(approval(res['hash']), Mode.Application)
        f.write(compiled)
        print('compiled mt_approval.teal')

    with open('mt_clear.teal', 'w') as f:
        compiled = compileTeal(clear_state_program(), Mode.Application)
        f.write(compiled)
        print('compiled mt_clear.teal')
