#!/usr/bin/env bash

usage() {
    echo ""
    echo "Test the merkle tree app"
    echo ""
    echo "Usage:"
    echo ""
    echo "  $0 \$APP_CREATOR_ADDRESS \$VALIDATE_SC_ADDRESS \$APPEND_SC_ADDRESS"
    echo ""
    echo ""
}

if [ $# -ne 3 ]; then
  usage
  exit 1
fi

creator=$1
validate_sc_addr=$2
append_sc_addr=$3

# create app
echo "Creating app..."
app_id=$(goal app create --creator $creator --approval-prog ./mt_approval.teal --global-byteslices 2 --global-ints 1 --local-byteslices 0 --local-ints 0 --clear-prog ./mt_clear.teal| grep "Created app with app index" | awk '{ print $6 }')
echo "Created app $app_id"

function group_sign_and_send {
  # validate smart contract call
  echo "Creating validate smart contract call"
  goal clerk send -a 0 -F validate_sc.teal -t $validate_sc_addr -o validate_sc.tx

  # payment to validate smart contract
  echo "Creating fee payment txn to the validate smart contract"
  goal clerk send -a 1000 -f $creator -t $validate_sc_addr -o validate_fee_payment.tx

  # append smart contract call
  echo "Creating append smart contract call"
  goal clerk send -a 0 -F append_sc.teal -t $append_sc_addr -o append_sc.tx

  # payment to append smart contract
  echo "Creating fee payment txn to the append smart contract"
  goal clerk send -a 1000 -f $creator -t $append_sc_addr -o append_fee_payment.tx

  # group
  echo "Grouping them together"
  cat app.tx validate_fee_payment.tx validate_sc.tx append_fee_payment.tx append_sc.tx > group.tx
  goal clerk group -i group.tx -o group.tx.out

  # split
  echo "Splitting them apart"
  goal clerk split -i group.tx.out -o ungrp.tx

  # sign
  echo "Signing app call and fee payment txs"
  goal clerk sign -i ungrp-0.tx -o ungrp-0.tx.sig
  goal clerk sign -i ungrp-1.tx -o ungrp-1.tx.sig
  goal clerk sign -i ungrp-3.tx -o ungrp-3.tx.sig

  # join
  echo "Joining signed transactions to 1 file signed.grp"
  cat ungrp-0.tx.sig ungrp-1.tx.sig ungrp-2.tx ungrp-3.tx.sig ungrp-4.tx > signed.grp
  echo "signed.grp created!"

  # send
  echo "sending grouped transactions"
  goal clerk rawsend -f signed.grp
  echo "sent"
}

function append {
  current_root=$1
  new_root=$2
  record=$3
  sib1=$4
  sib2=$5
  sib3=$6
  sib4=$7
  sib5=$8
  sib6=$9
  sib7=${10}
  sib8=${11}
  sib9=${12}
  sib10=${13}
  sib11=${14}

  echo "appending $record"
  goal app call \
    --app-id $app_id \
    --app-arg "str:append" \
    --app-arg "b64:$current_root" \
    --app-arg "b64:$new_root" \
    --app-arg "str:$record" \
    --app-arg "b64:$sib1" \
    --app-arg "b64:$sib2" \
    --app-arg "b64:$sib3" \
    --from $creator --out=app.tx

  group_sign_and_send

}

function validate {
  current_root=$1
  new_root=$2
  record=$3
  sib1=$4
  sib2=$5
  sib3=$6
  sib4=$7
  sib5=$8
  sib6=$9
  sib7=${10}
  sib8=${11}
  sib9=${12}
  sib10=${13}
  sib11=${14}

  echo "validating $record"
  goal app call \
    --app-id $app_id \
    --app-arg "str:validate" \
    --app-arg "b64:$current_root" \
    --app-arg "b64:" \
    --app-arg "str:$record" \
    --app-arg "b64:$sib1" \
    --app-arg "b64:$sib2" \
    --app-arg "b64:$sib3" \
    --from $creator --out=app.tx

  group_sign_and_send

}

append "" "maaDdtN5k2cSsfdEy/XgeLusgjwee/GEXZYNBdiucLI=" "record0" "" "" ""
validate "maaDdtN5k2cSsfdEy/XgeLusgjwee/GEXZYNBdiucLI=" "" "record0" "" "" ""

append "maaDdtN5k2cSsfdEy/XgeLusgjwee/GEXZYNBdiucLI=" "XZMWjv91MVyAibeqDx640mphixE9qSnd6Zfn0BILttI=" "record1" "u6KKwPqiKMcM27iAaNhdlcK4svf+M228XM1aCZnFIQhf" "" ""
validate "XZMWjv91MVyAibeqDx640mphixE9qSnd6Zfn0BILttI=" "" "record1" "u6KKwPqiKMcM27iAaNhdlcK4svf+M228XM1aCZnFIQhf" "" ""

append "XZMWjv91MVyAibeqDx640mphixE9qSnd6Zfn0BILttI=" "952WQhtxb51LJjmVQwJ+8iqRU33abhWGGowEhFaEdDM=" "record2" "" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" ""
validate "952WQhtxb51LJjmVQwJ+8iqRU33abhWGGowEhFaEdDM=" "" "record2" "" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" ""

append "952WQhtxb51LJjmVQwJ+8iqRU33abhWGGowEhFaEdDM=" "y/Y2PGc1RGdUHJDfiUF4Ib2VVswaB9HGZsUyPLscJk8=" "record3" "u5IE0imKp4/r0cg+Sfwt2e7kBeyun/8T/I96TIxoB/Ar" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" ""
validate "y/Y2PGc1RGdUHJDfiUF4Ib2VVswaB9HGZsUyPLscJk8=" "" "record3" "u5IE0imKp4/r0cg+Sfwt2e7kBeyun/8T/I96TIxoB/Ar" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" ""

append "y/Y2PGc1RGdUHJDfiUF4Ib2VVswaB9HGZsUyPLscJk8=" "+oAejua2I8HZTWSUjZEULxcERyvyf9saSdE1UrYQLZc=" "record4" "" "" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
validate "+oAejua2I8HZTWSUjZEULxcERyvyf9saSdE1UrYQLZc=" "" "record4" "" "" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"

append "+oAejua2I8HZTWSUjZEULxcERyvyf9saSdE1UrYQLZc=" "EPr9MEIB9YSnmzv6R7qPgKadsrQffMO5nX8ijXpGcU8=" "record5" "u2NOmDk9wdN+y7dy+XDgffwtsoq2qO+lhAZJ99XmTG9C" "" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
validate "EPr9MEIB9YSnmzv6R7qPgKadsrQffMO5nX8ijXpGcU8=" "" "record5" "u2NOmDk9wdN+y7dy+XDgffwtsoq2qO+lhAZJ99XmTG9C" "" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"

append "EPr9MEIB9YSnmzv6R7qPgKadsrQffMO5nX8ijXpGcU8=" "6E0/8fxYI4ZQrrZRJmL+8oE3xCaiKg+QcrC3EFsGD5Y=" "record6" "" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
validate "6E0/8fxYI4ZQrrZRJmL+8oE3xCaiKg+QcrC3EFsGD5Y=" "" "record6" "" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"

append "6E0/8fxYI4ZQrrZRJmL+8oE3xCaiKg+QcrC3EFsGD5Y=" "hvRZlDZBo2Z2N6fvgvw9w45y79B8HqQUU4RmJrh9SZ4=" "record7" "u19BsA4Tmma4CurYsTUGhwTmAz00sfzPN92APg/QHglf" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
validate "hvRZlDZBo2Z2N6fvgvw9w45y79B8HqQUU4RmJrh9SZ4=" "" "record7" "u19BsA4Tmma4CurYsTUGhwTmAz00sfzPN92APg/QHglf" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"

validate "hvRZlDZBo2Z2N6fvgvw9w45y79B8HqQUU4RmJrh9SZ4=" "" "record0" "qu0AOo9K4Xej8xNE6RClMgwuzlcvi3hgFC17fBOKL6hQ" "quA5ByEEZoif2l0XHKZWpc3P61HFQCFPJNnqaXCJJnju" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF"
validate "hvRZlDZBo2Z2N6fvgvw9w45y79B8HqQUU4RmJrh9SZ4=" "" "record1" "u6KKwPqiKMcM27iAaNhdlcK4svf+M228XM1aCZnFIQhf" "quA5ByEEZoif2l0XHKZWpc3P61HFQCFPJNnqaXCJJnju" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF"
validate "hvRZlDZBo2Z2N6fvgvw9w45y79B8HqQUU4RmJrh9SZ4=" "" "record2" "qlU+XIurZ96YJ7hPo2graSpKwnNUL6yvx48ly2TAhJjH" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF"
validate "hvRZlDZBo2Z2N6fvgvw9w45y79B8HqQUU4RmJrh9SZ4=" "" "record3" "u5IE0imKp4/r0cg+Sfwt2e7kBeyun/8T/I96TIxoB/Ar" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF"
validate "hvRZlDZBo2Z2N6fvgvw9w45y79B8HqQUU4RmJrh9SZ4=" "" "record4" "qthHJFPMJC6Dc06ENnmKQI/2+oeWH5/cLKTWaIDUgita" "qglS1xu5j0JgfN/0zVwGc6x0y/wxvirRdU5qFJ/038Fq" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
validate "hvRZlDZBo2Z2N6fvgvw9w45y79B8HqQUU4RmJrh9SZ4=" "" "record5" "u2NOmDk9wdN+y7dy+XDgffwtsoq2qO+lhAZJ99XmTG9C" "qglS1xu5j0JgfN/0zVwGc6x0y/wxvirRdU5qFJ/038Fq" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
validate "hvRZlDZBo2Z2N6fvgvw9w45y79B8HqQUU4RmJrh9SZ4=" "" "record6" "qhRxHkgVYhMAPe10rIAsSc1zscHRE+NZmlVOsJ8lTzO1" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
validate "hvRZlDZBo2Z2N6fvgvw9w45y79B8HqQUU4RmJrh9SZ4=" "" "record7" "u19BsA4Tmma4CurYsTUGhwTmAz00sfzPN92APg/QHglf" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
