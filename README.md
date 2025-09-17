# Hummingbot + Hydration Quickstart

This repository provides scripts to quickly set up Hummingbot for market-making using Hydration (HDX).

While fully functional, this repository serves as a product preview until the Hummingbot Foundation officially merges the code. In the meantime, the setup process demonstrated here remains compatible with the latest Hummingbot versions by updating the `docker-compose.yml` file as needed.

We strongly encourage you to review all the provided scripts and configuration files to understand how the setup scripts, Docker Compose, and Python scripts function and interact.

## Instructions

### Prerequisites

* [Docker or Docker Desktop](https://www.docker.com/products/docker-desktop/)
* Unix-like operating system (Linux, macOS) or WSL (Windows)

### Create and configure the Hummingbot Client

```sh
git clone https://github.com/robotter-ai/hydration.git
cd hydration

./setup
```

After executing the commands above, follow the instructions provided to configure your Hummingbot Client and Gateway. You will be prompted to set separate passwords for the Hummingbot Client and the Gateway certificates.

The `setup` script performs the following steps:

* Pulls Docker images from Docker Hub (this may take time initially but will occur only once).
* Creates a shared volume folder with three subfolders (`client`, `gateway`, and `common`), which contain certificates, strategy scripts, log files, encrypted wallet files, etc.
* Prompts for the Hummingbot Client password and configures it automatically using a Python script. (This simplifies the Gateway configuration. If preferred, you can configure this manually by running `./setup hummingbot`).
* Prompts for the Hummingbot Gateway certificates passphrase and configures the `GATEWAY_PASSPHRASE` automatically with a Python script. (You may configure this manually by running `./setup gateway`).
* Restarts the containers and attaches to the Hummingbot Client. After entering your password, you should see confirmation that the Gateway is online and operational.

## Connecting your Wallet

Inside the Hummingbot Client interface type the following command:
```sh
gateway connect
```
* Choose `hydration/amm`, and follow the instructions.

* For the network and the `node URL` you can use the default values, respectively `mainnet` and `wss://rpc.hydradx.cloud`

* When asked to inform your wallet `private key`, and **this is very important**, inform your wallet `mnemonic`.

* If everything went well you'll see a message like this one: `The hydration/amm connector now uses wallet: <wallet public key>`.


### Running Strategies

Once the configuration is complete, you can run your preferred trading strategies. Please refer to the official Hummingbot documentation for detailed guidance on strategy setup and usage.

Note: Hydration is an AMM (Automated Market Maker) connector, so only strategies compatible with AMMs can be used.

* [Hummingbot Documentation](https://hummingbot.org/docs/#ways-to-use-hummingbot)
* [Hummingbot v1 Strategies](https://hummingbot.org/v1-strategies/)
* [Hummingbot Strategies](https://hummingbot.org/strategies/)

Recommended strategies and scripts include:

* [scripts/amm\_triangular\_arbitrage.py](https://github.com/robotter-ai/hummingbot/blob/feat/hydration/scripts/amm_triangular_arbitrage.py): Triangular arbitrage across Hydration pools.
* [scripts/amm\_connectors\_arbitrage.py](https://github.com/robotter-ai/hummingbot/blob/feat/hydration/scripts/amm_connectors_arbitrage.py): Arbitrage between Hydration and other connectors.
* [amm\_arb](https://hummingbot.org/strategies/amm-arbitrage/): Hummingbot v1 arbitrage strategy for arbitraging between different connectors.
* [scripts/amm\_price\_example.py](https://github.com/robotter-ai/hummingbot/blob/feat/hydration/scripts/amm_price_example.py): Demonstrates retrieving prices from an AMM connector.
* [scripts/amm\_trade\_example.py](https://github.com/robotter-ai/hummingbot/blob/feat/hydration/scripts/amm_trade_example.py): Demonstrates placing trades via an AMM connector.
* [scripts/amm\_data\_feed.py](https://github.com/robotter-ai/hummingbot/blob/feat/hydration/scripts/amm_data_feed_example.py): Fetches data from an AMM connector.

Other strategies and enhancements are currently under development by the Hummingbot Foundation, with further exciting AMM-compatible strategies expected soon.

## FAQ

### Why do I see this error?

```
ValueError: Could not find the exchange rate for HDX-USDT using the rate source binance rate oracle (please verify it has been correctly configured)
hummingbot.core.utils.async_utils - ERROR - Unhandled error in background task: Could not find the exchange rate for HDX-USDT using the rate source binance rate oracle (please verify it has been correctly configured)
```

This happens because Hummingbot's default `rate_oracle_source` is `binance`, which does not list the HDX token used by Hydration-based strategies. Without an HDX price from the default oracle, Hummingbot cannot compute rates for your strategy.

Fix: switch the rate oracle to our `custom` source inside the Hummingbot client:

```sh
config rate_oracle_source custom
```
