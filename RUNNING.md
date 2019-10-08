# Running the Python service

To run the service, you have to create a pip-readable package (e.g. `package.tar.gz`).

Then you should upload it to every node. It can be done with `file_uploader` script
(you can find it in the `python_runtime/tools`), e.g.:

```sh
python file_uploader.py http://127.0.0.1:8090 ../../examples/cryptocurrency/dist/exonum-python-cryptocurrency-0.1.0.tar.gz
```

If everything will be done correctly, you will obtain the hash of the uploaded artifact:

```sh
<Response [200]>
{'exonum-python-cryptocurrency-0.1.0.tar.gz': '8ab0038ac3a569e7944feabbf50d3a94e8f49de7ee90cdda1ad40333ab8feb7b'}
```

Now, you can use [exonum-launcher](https://github.com/popzxc/exonum-launcher) to deploy & init service.

First of all, you need to compile `*.proto` files for python runtime plugin:

```sh
cd exonum-launcher/exonum_launcher/runtimes/proto
protoc --proto_path=. --python_out=. python.proto
```

Now you can create a configuration file, for example
(**important** `hash` field must contain the value obtained earlier):

```yaml
networks:
  - host: "127.0.0.1"
    ssl: false
    public-api-port: 8080
    private-api-port: 8081

deadline_height: 20000

artifacts:
  cryptocurrency:
    runtime: python
    name: "cryptocurrency"
    spec:
      source_wheel_name: "exonum-python-cryptocurrency-0.1.0.tar.gz"
      service_library_name: "cryptocurrency"
      service_class_name: "Cryptocurrency"
      hash: "8ab0038ac3a569e7944feabbf50d3a94e8f49de7ee90cdda1ad40333ab8feb7b"
  
instances:
  xnm-token:
    artifact: cryptocurrency
  nnm-token:
    artifact: cryptocurrency
```

And then just run the `exonum-launcher`:

```sh
python -m exonum_launcher --runtimes python=2 --runtime-parsers python=exonum_launcher.runtimes.python.PythonSpecLoader -i sample.yml
```

If everything will be done correctly, you will see the following output:

```sh
Proto files were compiled successfully
Proto files were compiled successfully
Artifact cryptocurrency -> deploy status: succeed
Instance xnm-token -> start status: started with ID 1024
Instance nnm-token -> start status: started with ID 1025
```
