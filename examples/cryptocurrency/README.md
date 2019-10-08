# Example Python Cryptocurrency Service

This example project is an Python implementation of Cryptocurrency service.

It copies an interface from the [Rust example Cryptocurrency project](https://github.com/exonum/exonum/tree/ba62f89c8708a7d4d822ad5f9b691fdaf2400596/examples/cryptocurrency).

To get this example working, compile `*.proto` files first:

```sh
cd cryptocurrency/proto
protoc --proto_path=. --python_out=. helpers.proto service.proto
```

To create a deployable artifact, then just run:

```sh
python3 setup.py sdist
```

It will create a `dist` folder which will contain `exonum-python-cryptocurrency-0.1.0.tar.gz`.

With that file you will be able to deploy & init service. To figure out how to do it,
follow [RUNNING.md](https://github.com/popzxc/exonum-python-backend/blob/master/RUNNING.md).

## Sending transactions to the Python Cryptocurrency service

In the `examples` folder you can find `send_txs.py` file which will send several transactions.

To get it running, install the `exonum-light-client` before.

If you'll do everything correctly, you should see the following output:

```sh
Proto files were compiled successfully
Proto files were compiled successfully
Successfully created wallet with name 'Alice'
Successfully created wallet with name 'Bob'
Created the wallets for Alice and Bob. Balance:
 Alice => 100
 Bob => 100
Transferred 10 tokens from Alice's wallet to Bob's one
 Alice => 90
 Bob => 110
Transferred 25 tokens from Bob's wallet to Alice's one
 Alice => 115
 Bob => 85
```
