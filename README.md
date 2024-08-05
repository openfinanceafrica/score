### 🚨 UPDATE: This respository is no longer actively maintained. The code can still be modified and used as a library since the API (and website) is not currently available.


# Payment Score API

This project contains source code and supporting files for the [Open Finance Africa](https://openfinance.africa) Payment Score API. 
The API is available for consumption at *https//api.openfinance.africa* and its reference is [here](https://app.theneo.io/open-finance-africa/documentation_2).
Although the current functionality could have been bundled and utilized as a library, the current plan is to examine its application as an API and, over time, expand it to incorporate data sources where a library would not be suitable.

<br/>

## How it works

TL;DR: Head over to the [simulator](https://openfinance.africa/simulator) to see how the scoring works.


A credit score usually takes several factors into account. These factors range from previous loan repayment behavior, down to an individuals age.
Banks and credit bureaus (CRBs) already have the ability to aggregate this data and use it to evaluate loans terms for example. 
But accessing standardized *external* payment data, easily accessible via API is what this project is about.
For now, the code in this repo simply calculates a payment score. And this score can be used as a datapoint among the factors that lenders (or other financial institutions) may use to determine an individuals creditworthiness.
Banks and credit bureaus aren't the only entities that can find this useful. If you're a business that wants to keep track of payment behaviour, this is for you! E.g. if you're a property management company that want's to keep track of rent payment behavior.

### Input Values

To get a score, you'll need the following:
1. **Payment terms:** This includes a start/end date, the day of the month a payment is expected, and the amount expected. For example, a tenant may have a lease which starts on Jan 1 2024 (start) to Dec 31 2024 (end) and expected payment date of the 5th.
2. **Payment history:**: This is a list of payments that have been made by the individual getting scored. This includes the date/time that the payment was made as well as the amount.

### Score Factors

The following factors influence that value of a score.
1. On-time payment
2. How early an on-time payment is made. A payment made 5 days before the expected payment date is considered better than a payment made at the last minute.
3. Late payment
4. How late a payment is made after the expected payment date. A payment made 1 day after the expected payment date is considered better than a payment made 5 days after.
5. The payment amount. If there's an overpayment, like if someone wants to make a payment months ahead, that counts positively towards the score. Partial payments count as well.
6. Payment streaks. This means we take into account consecutive on-time payments or late payments.


### Score Value

The score includes scored months which are aggregated into an overall score. The overall score can range from **0 to 1** (with 1 being an excellent score). Monthly scores may be outside of the 0 to 1 range. 
The main pieces of information in a score are:
1. Overall score
2. Individually scored months
3. Longest on-time payment streak
4. Longest late payment streak

<br/>

## Prerequisites for running locally

In order to test the API locally, you'll use the Serverless Application Model Command Line Interface (SAM CLI) which is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.

To use the SAM CLI, you need the following tools.

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

<br/>
## Using SAM CLI to build and test locally

Build your application with the `sam build --use-container` command.

```bash
scoreapi$ sam build --use-container
```

The SAM CLI installs dependencies defined in `src/requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

Test a single function by invoking it directly with a test event. An event is a JSON document that represents the input that the function receives from the event source. Test events are included in the `events` folder in this project.

Run functions locally and invoke them with the `sam local invoke` command.

```bash
scoreapi$ sam local invoke ScoreApiFunction --event events/event.json
```

The SAM CLI can also emulate the API. Use the command below to run the API locally on port 3001.

```bash
scoreapi$ sam local start-api -p 3001
```

<br/>

## Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called `sam logs`. `sam logs` lets you fetch logs generated by your deployed Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
scoreapi$ sam logs -n ScoreApiFunction --stack-name scoreapi --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

<br/>

## Tests

Tests are defined in the `tests` folder in this project. Use PIP to install the test dependencies and run tests.

```bash
scoreapi$ pip install -r tests/requirements.txt --user
# unit tests
scoreapi$ python -m pytest tests/unit -v
```

<br/>

## Formatting

```bash
scoreapi$ pip install black
scoreapi$ black .
```

<br/>

## Use as a pip package

### Unix/macOS

```bash
$ python3 -m pip install scoreapi
```
### Windows
```bash
C:>  py -m pip install scoreapi
```

You can test that it was installed correctly by importing the package. Make sure you’re still in your virtual environment, then run Python:

### Unix/macOS
```bash
python3
```
### Windows
```bash
py
```
and import the package:
```bash
>>> import scoreapi
>>> def getScore(scoreInput: ScoreInput) -> Score:
```
<br/>

## Contributing

We welcome contributions both big and small ❤️ 

Any questions or feedback? Create an issue

Want to modify code or docs? Ask to get added as a contributor by emailing [hello@openfinance.africa](mailto:hello@openfinance.africa) or simply fork the repo to create pull requests
