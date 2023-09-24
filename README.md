
# Exchange API Wrapper

This repository provides a unified interface for interacting with various cryptocurrency exchanges like Bitvavo, BTCTurk, etc.

## Structure

- `src/`: Contains the main source code for the exchange wrappers.
  - `exchanges/`: Contains individual exchange implementations and the base exchange interface.
- `tests/`: Contains unit and integration tests for the exchange wrappers.

## Usage

To use an exchange wrapper, you need to initialize the respective exchange class with appropriate API credentials.

```python
from exchanges.bitvavo import BitvavoExchange

bitvavo = BitvavoExchange(public_key="YOUR_public_key", private_key="YOUR_PRIVATE_KEY")
balance = bitvavo.get_balance()
print(balance)

```

To create cloudFormation stack,

```bash
aws cloudformation create-stack --stack-name teststack --template-body file://./DataCollectorEC2Setup.yaml --parameters ParameterKey=S3BucketName,ParameterValue=<yours3Bucket>
# or
aws cloudformation create-stack \
  --stack-name myteststack \
  --template-body file://./DataCollectorEC2Setup.yaml \
  --parameters ParameterKey=S3BucketName,ParameterValue=ibrahimcikotest \
  --capabilities CAPABILITY_IAM
 # to delete
 aws cloudformation delete-stack --stack-name myteststack

 aws cloudformation validate-template --template-body file://./DataCollectorEC2Setup.yaml

# to download the folder to a local dir
aws s3 sync s3://<bucketname>/data/dev/ <local_dir>
# example
aws s3 sync s3://ibrahimcikotest/data/dev/ ./test_data
 

```

For more details, refer to the documentation.

## Documentation

The documentation for the API can be found in the `docs/` directory. It is generated using Sphinx and provides detailed information about each method and class in the repository.



