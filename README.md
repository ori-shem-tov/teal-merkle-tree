# Merkle Trees
## requirements
This app is using `ScratchVar` from pyteal which is not supported yet on latest release (v0.6.1).

This means cloning [pyteal](https://github.com/algorand/pyteal) repo is needed:
```
git clone git@github.com:algorand/pyteal.git
cd pyteal
pip install .
```

Note that this is tested with commit `120202cf73b43612426a054d5b731320d13bfdf1`

## Test

Run:
```
./test.sh $CREATOR_ADDRESS
```
To run a simple tests that creates the app and appends and validates 8 time (record0,...,record7)

## Usage

Generate TEAL scripts:
```
python teal.py
```

Create the app using goal:
```
goal app create --creator $CREATOR_ADDRESS --approval-prog ./mt_approval.teal --global-byteslices 2 --global-ints 1 --local-byteslices 0 --local-ints 0 --clear-prog ./mt_clear.teal
```
This will create the stateful app with 2 global `byte slices` and 1 global `int`

Then you'll need to create groups of 2 transactions where the 1st transaction is the app call, and the 2nd is the stateless teal call.

### App args schematics

This implementation supports 2 actions: `append` and `validate`.

Both actions expect the same number of app args (we'll assume 7 app args in the next demonstration)

#### Append
app-arg #0: `str:append` stating the wanted action.

app-arg #1: `b64:$CURRENT_ROOT` the `base64` encoding the current root before appending

app-arg #2: `b64:$NEW_ROOT` the `base64` encoding the new root after appending

app-arg #3: `str:$VALUE` the string representation of the value to append

app-arg #4: `b64:$FIRST_SIBLING_HASH` the `base64` encoding of the `sha256` of the first sibling.

app-arg #5: `b64:$SECOND_SIBLING_HASH` the `base64` encoding of the `sha256` of the second sibling.

app-arg #6: `b64:$THIRD_SIBLING_HASH` the `base64` encoding of the `sha256` of the third sibling.

Note that empty leaf sibling and subtree siblings with only empty leaves should be passed as empty byte slices.

Non-empty siblings should also include a first byte stating if it's a right (0xaa) or left (0xbb) sibling.

#### Validate
app-arg #0: `str:validate` stating the wanted action.

app-arg #1: `b64:$CURRENT_ROOT` the `base64` encoding the current root before appending

app-arg #2: `b64:` ignored for this action, since this is a read-only action

app-arg #3: `str:$VALUE` the string representation of the value to validate

app-arg #4: `b64:$FIRST_SIBLING_HASH` the `base64` encoding of the `sha256` of the first sibling.

app-arg #5: `b64:$SECOND_SIBLING_HASH` the `base64` encoding of the `sha256` of the second sibling.

app-arg #6: `b64:$THIRD_SIBLING_HASH` the `base64` encoding of the `sha256` of the third sibling.

Note that empty leaf sibling and subtree siblings with only empty leaves should be passed as empty byte slices.

Non-empty siblings should also include a first byte stating if it's a right (0xaa) or left (0xbb) sibling.
