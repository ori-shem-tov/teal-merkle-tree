#!/usr/bin/env bash

usage() {
    echo ""
    echo "Test the merkle tree app"
    echo ""
    echo "Usage:"
    echo ""
    echo "  $0 \$APP_CREATOR_ADDRESS"
    echo ""
    echo ""
}

if [ $# -ne 1 ]; then
  usage
  exit 1
fi

creator=$1

goal_cmd="goal"

# create app
echo "Creating app..."
app_id=$($goal_cmd app create --creator $creator --approval-prog ./mt_approval5.teal --global-byteslices 1 --global-ints 1 --local-byteslices 0 --local-ints 0 --clear-prog ./mt_clear.teal| grep "Created app with app index" | awk '{ printf "%d", $6 }')
echo "Created app $app_id"

echo "Creating dummy app..."
dummy_app_id=$($goal_cmd app create --creator $creator --approval-prog ./mt_clear.teal --global-byteslices 0 --global-ints 0 --local-byteslices 0 --local-ints 0 --clear-prog ./mt_clear.teal | grep "Created app with app index" | awk '{ printf "%d", $6 }')
echo "Created app $dummy_app_id"


function append {
  record=$1
  sib1=$2
  sib2=$3
  sib3=$4

  echo "appending $record"
  $goal_cmd app call \
    --app-id $app_id \
    --app-arg "str:append" \
    --app-arg "str:$record" \
    --app-arg "b64:$sib1" \
    --app-arg "b64:$sib2" \
    --app-arg "b64:$sib3" \
    --from $creator --out=app.tx

  $goal_cmd app call \
    --app-id $dummy_app_id \
    --app-arg "str:1" \
    --from $creator --out=app-cost-pool.tx
  $goal_cmd app call \
    --app-id $dummy_app_id \
    --app-arg "str:2" \
    --from $creator --out=app-cost-pool2.tx

  # group
  echo "Grouping them together"
  cat app.tx app-cost-pool.tx app-cost-pool2.tx > group.tx
  $goal_cmd clerk group -i group.tx -o group.tx.out

  # split
  echo "Splitting them apart"
  $goal_cmd clerk split -i group.tx.out -o ungrp.tx

  # sign
  echo "Signing app calls"
  $goal_cmd clerk sign -i ungrp-0.tx -o ungrp-0.tx.sig
  $goal_cmd clerk sign -i ungrp-1.tx -o ungrp-1.tx.sig
  $goal_cmd clerk sign -i ungrp-2.tx -o ungrp-2.tx.sig

  # join
  echo "Joining signed transactions to 1 file signed.grp"
  cat ungrp-0.tx.sig ungrp-1.tx.sig ungrp-2.tx.sig > signed.grp
  echo "signed.grp created!"

  # send
  echo "sending grouped transactions"
  $goal_cmd clerk rawsend -f signed.grp
  echo "sent"

}

function verify {
  record=$1
  sib1=$2
  sib2=$3
  sib3=$4

  echo "verifying $record"
  $goal_cmd app call \
    --app-id $app_id \
    --app-arg "str:verify" \
    --app-arg "str:$record" \
    --app-arg "b64:$sib1" \
    --app-arg "b64:$sib2" \
    --app-arg "b64:$sib3" \
    --from $creator --out=app.tx

  $goal_cmd app call \
    --app-id $dummy_app_id \
    --app-arg "str:1" \
    --from $creator --out=app-cost-pool.tx
  $goal_cmd app call \
    --app-id $dummy_app_id \
    --app-arg "str:2" \
    --from $creator --out=app-cost-pool2.tx

  # group
  echo "Grouping them together"
  cat app.tx app-cost-pool.tx app-cost-pool2.tx > group.tx
  $goal_cmd clerk group -i group.tx -o group.tx.out

  # split
  echo "Splitting them apart"
  $goal_cmd clerk split -i group.tx.out -o ungrp.tx

  # sign
  echo "Signing app calls"
  $goal_cmd clerk sign -i ungrp-0.tx -o ungrp-0.tx.sig
  $goal_cmd clerk sign -i ungrp-1.tx -o ungrp-1.tx.sig
  $goal_cmd clerk sign -i ungrp-2.tx -o ungrp-2.tx.sig

  # join
  echo "Joining signed transactions to 1 file signed.grp"
  cat ungrp-0.tx.sig ungrp-1.tx.sig ungrp-2.tx.sig > signed.grp
  echo "signed.grp created!"

  # send
  echo "sending grouped transactions"
  $goal_cmd clerk rawsend -f signed.grp
  echo "sent"

}

function update {
  old_record=$1
  sib1=$2
  sib2=$3
  sib3=$4
  new_record="${@: -1}"

  echo "updating $old_record"
  $goal_cmd app call \
    --app-id $app_id \
    --app-arg "str:update" \
    --app-arg "str:$old_record" \
    --app-arg "b64:$sib1" \
    --app-arg "b64:$sib2" \
    --app-arg "b64:$sib3" \
    --app-arg "str:$new_record" \
    --from $creator --out=app.tx

  $goal_cmd app call \
    --app-id $dummy_app_id \
    --app-arg "str:1" \
    --from $creator --out=app-cost-pool.tx
  $goal_cmd app call \
    --app-id $dummy_app_id \
    --app-arg "str:2" \
    --from $creator --out=app-cost-pool2.tx

  # group
  echo "Grouping them together"
  cat app.tx app-cost-pool.tx app-cost-pool2.tx > group.tx
  $goal_cmd clerk group -i group.tx -o group.tx.out

  # split
  echo "Splitting them apart"
  $goal_cmd clerk split -i group.tx.out -o ungrp.tx

  # sign
  echo "Signing app calls"
  $goal_cmd clerk sign -i ungrp-0.tx -o ungrp-0.tx.sig
  $goal_cmd clerk sign -i ungrp-1.tx -o ungrp-1.tx.sig
  $goal_cmd clerk sign -i ungrp-2.tx -o ungrp-2.tx.sig

  # join
  echo "Joining signed transactions to 1 file signed.grp"
  cat ungrp-0.tx.sig ungrp-1.tx.sig ungrp-2.tx.sig > signed.grp
  echo "signed.grp created!"

  # send
  echo "sending grouped transactions"
  $goal_cmd clerk rawsend -f signed.grp
  echo "sent"

}
append "record0" "quOwxEKY/BwUmvv0yJlvuSQnrkHkZJuTTKSVmRt4UrhV" "qi26XbwznnMWrqJoP6+DnBt7HuIxPbeSESWIEY3wZqo1" "qlMQozDo+XA4hQPHM0nYC0XNdk22FfG87SgB3NRSSi/0"
append "record0" "quOwxEKY/BwUmvv0yJlvuSQnrkHkZJuTTKSVmRt4UrhV" "qi26XbwznnMWrqJoP6+DnBt7HuIxPbeSESWIEY3wZqo1" "qlMQozDo+XA4hQPHM0nYC0XNdk22FfG87SgB3NRSSi/0"
append "record1" "u6KKwPqiKMcM27iAaNhdlcK4svf+M228XM1aCZnFIQhf" "qi26XbwznnMWrqJoP6+DnBt7HuIxPbeSESWIEY3wZqo1" "qlMQozDo+XA4hQPHM0nYC0XNdk22FfG87SgB3NRSSi/0"
append "record1" "u6KKwPqiKMcM27iAaNhdlcK4svf+M228XM1aCZnFIQhf" "qi26XbwznnMWrqJoP6+DnBt7HuIxPbeSESWIEY3wZqo1" "qlMQozDo+XA4hQPHM0nYC0XNdk22FfG87SgB3NRSSi/0"
append "record2" "quOwxEKY/BwUmvv0yJlvuSQnrkHkZJuTTKSVmRt4UrhV" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" "qlMQozDo+XA4hQPHM0nYC0XNdk22FfG87SgB3NRSSi/0"
append "record2" "quOwxEKY/BwUmvv0yJlvuSQnrkHkZJuTTKSVmRt4UrhV" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" "qlMQozDo+XA4hQPHM0nYC0XNdk22FfG87SgB3NRSSi/0"
append "record3" "u5IE0imKp4/r0cg+Sfwt2e7kBeyun/8T/I96TIxoB/Ar" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" "qlMQozDo+XA4hQPHM0nYC0XNdk22FfG87SgB3NRSSi/0"
append "record3" "u5IE0imKp4/r0cg+Sfwt2e7kBeyun/8T/I96TIxoB/Ar" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" "qlMQozDo+XA4hQPHM0nYC0XNdk22FfG87SgB3NRSSi/0"
append "record4" "quOwxEKY/BwUmvv0yJlvuSQnrkHkZJuTTKSVmRt4UrhV" "qi26XbwznnMWrqJoP6+DnBt7HuIxPbeSESWIEY3wZqo1" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
append "record4" "quOwxEKY/BwUmvv0yJlvuSQnrkHkZJuTTKSVmRt4UrhV" "qi26XbwznnMWrqJoP6+DnBt7HuIxPbeSESWIEY3wZqo1" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
append "record5" "u2NOmDk9wdN+y7dy+XDgffwtsoq2qO+lhAZJ99XmTG9C" "qi26XbwznnMWrqJoP6+DnBt7HuIxPbeSESWIEY3wZqo1" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
append "record5" "u2NOmDk9wdN+y7dy+XDgffwtsoq2qO+lhAZJ99XmTG9C" "qi26XbwznnMWrqJoP6+DnBt7HuIxPbeSESWIEY3wZqo1" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
append "record6" "quOwxEKY/BwUmvv0yJlvuSQnrkHkZJuTTKSVmRt4UrhV" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
append "record6" "quOwxEKY/BwUmvv0yJlvuSQnrkHkZJuTTKSVmRt4UrhV" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
append "record7" "u19BsA4Tmma4CurYsTUGhwTmAz00sfzPN92APg/QHglf" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
append "record7" "u19BsA4Tmma4CurYsTUGhwTmAz00sfzPN92APg/QHglf" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
append "record0" "qu0AOo9K4Xej8xNE6RClMgwuzlcvi3hgFC17fBOKL6hQ" "quA5ByEEZoif2l0XHKZWpc3P61HFQCFPJNnqaXCJJnju" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF"
append "record1" "u6KKwPqiKMcM27iAaNhdlcK4svf+M228XM1aCZnFIQhf" "quA5ByEEZoif2l0XHKZWpc3P61HFQCFPJNnqaXCJJnju" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF"
append "record2" "qlU+XIurZ96YJ7hPo2graSpKwnNUL6yvx48ly2TAhJjH" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF"
append "record3" "u5IE0imKp4/r0cg+Sfwt2e7kBeyun/8T/I96TIxoB/Ar" "u4CK87RS/QiCJAvN+F/B1TaJL+SJoxBwNbJnv5BmXe8i" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF"
append "record4" "qthHJFPMJC6Dc06ENnmKQI/2+oeWH5/cLKTWaIDUgita" "qglS1xu5j0JgfN/0zVwGc6x0y/wxvirRdU5qFJ/038Fq" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
append "record5" "u2NOmDk9wdN+y7dy+XDgffwtsoq2qO+lhAZJ99XmTG9C" "qglS1xu5j0JgfN/0zVwGc6x0y/wxvirRdU5qFJ/038Fq" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
append "record6" "qhRxHkgVYhMAPe10rIAsSc1zscHRE+NZmlVOsJ8lTzO1" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
append "record7" "u19BsA4Tmma4CurYsTUGhwTmAz00sfzPN92APg/QHglf" "u7BULGbcLhN0Emhl48KVicG5AydyOlN4SmfHAuVz3E5i" "u8UPwPey01LNNP4zMvAa4YNrpvxb3GnT3oilanM3kaL5"
update "record0" "qu0AOo9K4Xej8xNE6RClMgwuzlcvi3hgFC17fBOKL6hQ" "quA5ByEEZoif2l0XHKZWpc3P61HFQCFPJNnqaXCJJnju" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF" "record00"
update "record1" "u1kciTLxlPFwB9Zs0XF9kdPt8C1dds5ADXSOG6hAR5O4" "quA5ByEEZoif2l0XHKZWpc3P61HFQCFPJNnqaXCJJnju" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF" "record11"
update "record2" "qlU+XIurZ96YJ7hPo2graSpKwnNUL6yvx48ly2TAhJjH" "u6tKt1Vu7xob+2V7FeHwaNLlWw9ogpKv0MSD9sW/uNlc" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF" "record22"
update "record3" "u1ReJTaWJefFmqAQyfr8ZP9eTRecR94MXd7gL9bg9ee4" "u6tKt1Vu7xob+2V7FeHwaNLlWw9ogpKv0MSD9sW/uNlc" "qhqq1HghiS8VjPVhEKuP+hmb+jXCYohnPnve4jDYHZrF" "record33"
update "record4" "qthHJFPMJC6Dc06ENnmKQI/2+oeWH5/cLKTWaIDUgita" "qglS1xu5j0JgfN/0zVwGc6x0y/wxvirRdU5qFJ/038Fq" "u31WdMSCQeYFoKtiOvVxTkPCJ9xVLVwbd053WRdBoUzs" "record44"
update "record5" "u/xMCx1XuECm8LtT0voleZ4AgUKjn1zrw4sUU1rXCY9n" "qglS1xu5j0JgfN/0zVwGc6x0y/wxvirRdU5qFJ/038Fq" "u31WdMSCQeYFoKtiOvVxTkPCJ9xVLVwbd053WRdBoUzs" "record55"
update "record6" "qhRxHkgVYhMAPe10rIAsSc1zscHRE+NZmlVOsJ8lTzO1" "u08NwtfETndkYWgH0he2CQP03D5GIbC7TmMsttw1LQav" "u31WdMSCQeYFoKtiOvVxTkPCJ9xVLVwbd053WRdBoUzs" "record66"
update "record7" "uywfSO7dr7zwTAP0rDrK+oC+3A1lRzpouGY6Z7XqhTLv" "u08NwtfETndkYWgH0he2CQP03D5GIbC7TmMsttw1LQav" "u31WdMSCQeYFoKtiOvVxTkPCJ9xVLVwbd053WRdBoUzs" "record77"
append "record00" "qpGIoq5ATI6oWy0eW4ZPkYO4K+jr4oXLMXPzsxZI4m5L" "qhekyP0v4r0dGJDl9UiDGTuT0+2cZBgLOO45CaltIRYo" "qsye9ELFZyM1MBBTSIDrzT8Gg4ClfwbYH7MXn+Aoya9n"
append "record11" "u1kciTLxlPFwB9Zs0XF9kdPt8C1dds5ADXSOG6hAR5O4" "qhekyP0v4r0dGJDl9UiDGTuT0+2cZBgLOO45CaltIRYo" "qsye9ELFZyM1MBBTSIDrzT8Gg4ClfwbYH7MXn+Aoya9n"
append "record22" "qo81xL2gtHq35O3ZUTARKTY4bWyDsutZmaKUYfnR01Jv" "u6tKt1Vu7xob+2V7FeHwaNLlWw9ogpKv0MSD9sW/uNlc" "qsye9ELFZyM1MBBTSIDrzT8Gg4ClfwbYH7MXn+Aoya9n"
append "record33" "u1ReJTaWJefFmqAQyfr8ZP9eTRecR94MXd7gL9bg9ee4" "u6tKt1Vu7xob+2V7FeHwaNLlWw9ogpKv0MSD9sW/uNlc" "qsye9ELFZyM1MBBTSIDrzT8Gg4ClfwbYH7MXn+Aoya9n"
append "record44" "qkmdhWiPeDZvQA6A06dzQKo1ZOIJxjpcPGVmIPkpeYW/" "qs4rT2RnXfeYuCEF4QdIHYrQQdi7wcmYclw1fpVA789k" "u31WdMSCQeYFoKtiOvVxTkPCJ9xVLVwbd053WRdBoUzs"
append "record55" "u/xMCx1XuECm8LtT0voleZ4AgUKjn1zrw4sUU1rXCY9n" "qs4rT2RnXfeYuCEF4QdIHYrQQdi7wcmYclw1fpVA789k" "u31WdMSCQeYFoKtiOvVxTkPCJ9xVLVwbd053WRdBoUzs"
append "record66" "qn0ylyaZ+DxkoA17aiT/fC1OAqtIpVHYbcaiPAGsB5ww" "u08NwtfETndkYWgH0he2CQP03D5GIbC7TmMsttw1LQav" "u31WdMSCQeYFoKtiOvVxTkPCJ9xVLVwbd053WRdBoUzs"
append "record77" "uywfSO7dr7zwTAP0rDrK+oC+3A1lRzpouGY6Z7XqhTLv" "u08NwtfETndkYWgH0he2CQP03D5GIbC7TmMsttw1LQav" "u31WdMSCQeYFoKtiOvVxTkPCJ9xVLVwbd053WRdBoUzs"
