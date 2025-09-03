#!/usr/bin/env python3
"""
liquid_op_cat_demo_plain.py

Demonstrates OP_CAT spend on Liquid regtest using P2WSH without confidential addresses.
"""

import requests, json, hashlib, sys, binascii
from decimal import Decimal, getcontext

getcontext().prec = 8

# -------------------------
RPC_USER = "user"
RPC_PASS = "pass"
RPC_PORT = 19443
RPC_URL = f"http://127.0.0.1:{RPC_PORT}/"
WALLET_NAME = "default"
FUND_AMOUNT = Decimal("1.0")
FEE = Decimal("0.0001")
# -------------------------

HEADERS = {"content-type": "application/json"}

def rpc(method, params=None, wallet=None):
    if params is None: params = []
    url = RPC_URL
    if wallet:
        url = RPC_URL + "wallet/" + wallet
    payload = json.dumps({
        "jsonrpc": "1.0",
        "id": "cli",
        "method": method,
        "params": params
    })
    resp = requests.post(url, headers=HEADERS, data=payload, auth=(RPC_USER, RPC_PASS))
    if resp.status_code != 200:
        print("RPC error", resp.status_code, resp.text)
        raise SystemExit("RPC call failed")
    j = resp.json()
    if j.get("error"):
        raise SystemExit(f"RPC error: {j['error']}")
    return j["result"]

def hex_push(data_bytes: bytes) -> str:
    L = len(data_bytes)
    if L <= 75:
        return "{:02x}".format(L) + data_bytes.hex()
    else:
        raise ValueError("Data too long for single-byte push in this demo")

def build_redeem_script_hex():
    a = b"Hello"
    b = b"World"
    push_a = hex_push(a)
    push_b = hex_push(b)
    expected = hashlib.sha256(a + b).digest()
    # OP_CAT=0x7e, OP_SHA256=0xa8, OP_EQUALVERIFY=0x88, OP_TRUE=0x51
    redeem_hex = push_a + push_b + "7e" + "a8" + "20" + expected.hex() + "88" + "51"
    return redeem_hex, expected.hex()

def main():
    print("=== OP_CAT demo on Liquid regtest (plain addresses) ===")

    redeem_hex, expected_hash_hex = build_redeem_script_hex()
    print("\nRedeem (witness) script hex:", redeem_hex)
    print("Expected SHA256('HelloWorld') =", expected_hash_hex)

    # Get P2WSH address
    decoded = rpc("decodescript", [redeem_hex])
    p2wsh_addr = decoded["segwit"]["address"]
    print("P2WSH address for redeem script:", p2wsh_addr)

    # Fund the P2WSH output
    print(f"\nSending {FUND_AMOUNT} to {p2wsh_addr} ...")
    fund_txid = rpc("sendtoaddress", [p2wsh_addr, float(FUND_AMOUNT)])
    print("fund txid:", fund_txid)

    # Mine 1 block to confirm
    miner_addr = rpc("getnewaddress", ["", "bech32"])  # plain address
    print("Mining 1 block to address:", miner_addr)
    rpc("generatetoaddress", [1, miner_addr])

    # Locate the UTXO
    txout = rpc("gettxout", [fund_txid, 0])
    if not txout:
        print("UTXO not found. Exiting.")
        sys.exit(1)
    amount = Decimal(str(txout["value"]))
    scriptPubKey = txout["scriptPubKey"]["hex"]
    print(f"Located UTXO {fund_txid}:0 amount={amount}")

    # Destination address (plain, unconfidential)
    dest_addr = rpc("getnewaddress", ["", "bech32"])
    send_amount = amount - FEE
    outputs = {dest_addr: float(send_amount)}

    # Build raw transaction
    rawhex = rpc("createrawtransaction", [[{"txid": fund_txid, "vout": 0}], [outputs]])
    print("raw tx hex (no witness yet):", rawhex)

    # Prepare prevtx info
    prevtx = {
        "txid": fund_txid,
        "vout": 0,
        "scriptPubKey": scriptPubKey,
        "witnessScript": redeem_hex,
        "amount": float(amount)
    }

    # Sign transaction using witnessScript only (no keys needed)
    sign_result = rpc("signrawtransactionwithwallet", [rawhex, [prevtx]])
    if not sign_result.get("complete"):
        print("Signing not complete. Result:", sign_result)
        sys.exit(1)
    signed_hex = sign_result["hex"]

    # Broadcast
    spend_txid = rpc("sendrawtransaction", [signed_hex])
    print("\nSpending txid:", spend_txid)

    # Mine to confirm
    miner_addr2 = rpc("getnewaddress", ["", "bech32"])
    rpc("generatetoaddress", [1, miner_addr2])

    print("\nDone. Funds spent back to wallet using OP_CAT P2WSH (plain addresses).")
    print("Funding txid:", fund_txid)
    print("Spending txid:", spend_txid)

if __name__ == "__main__":
    main()
