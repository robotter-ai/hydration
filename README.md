# Hummingbot + Hydration Quickstart
A repository with scripts to easily set up Hummingbot to do market-making with Hydration (HDX).

While this repository is fully functional, it serves as a product preview until the Hummingbot Foundation officially merges the code. In the meantime, the setup flow demonstrated here, using the Hummingbot Client and Gateway, remains compatible with the latest Hummingbot versions by updating the docker-compose.yml file accordingly.

We greatly encorage you to read all the code available here and undestand how to setup script, the docker compose, and the python scripts work and what they do.

## Instructions

### Prerequisites

- [Docker (or Docker Desktop)](https://www.docker.com/products/docker-desktop/)
- Unix-like system (Linux, MacOS) or WSL (for Windows)

### Create and configure the Hummingbot Client

```sh
git clone https://github.com/robotter-ai/hydration.git
cd hydration

./setup
```

After running the commands above, follow the instructions to correctly configure your Hummingbot Client and Gateway
(for example informing which password you want to use for the Humminbot Client and which one for the Hummingbot Gateway certificates).

Basically, the `setup` script work as the following:
 - Pulls the docker images from docker hub
(if you don't have them locally yet, these operations might take some time, but they will happen only once)
 - Create a shared volumes folder (this folder has 3 folders, the `client`, the `gateway` and the `common` folders) and they will be shared with the container and have the certificates, the strategies scripts, the log files, the encrypted wallets files, etc.
 - Ask for the Hummingbot Client password, and using a python script, it configures the client password for you (we use this because we can simplify the Gateway configuration step, but you can do this manually if you prefer in this case use `./setup hummingbot` instead)
 - Ask for the Hummingbot Gateway certificeates passphrase, and also using a python script, it configures the GATEWAY_PASSPHRASE for you (again you can do this manually with `./setup gateway` if you prefer)
 - After that the script restarts the containers and attach to the Hummingbot Client, after informing your password, you should be able to see that the Hummingbot Gateway is online, and you can operate as normal

### How to run strategies

Once the configuration above is done, you can run your preferred strategies.
Please refer to the Hummingbot documentation on how to use and configure them.
Note that Hydration is an AMM (Automated Market Maker) connector, so only the strategies compatible with them can be run.

https://hummingbot.org/docs/#ways-to-use-hummingbot

https://hummingbot.org/v1-strategies/

https://hummingbot.org/strategies/

Some interesting strategies and scripts to try are:
- [scripts/amm_portfolio_manager.py](https://github.com/robotter-ai/hummingbot/blob/feat/hydration/scripts/amm_portfolio_manager.py) (Our own strategy, fully customizable and full of features for you to build on top of it)
- [amm_arb](https://hummingbot.org/strategies/amm-arbitrage/) (Hummingbot v1 arbitrage strategy, so you can make arbitrages between different connectors)
- [scripts/amm_price_example.py](https://github.com/robotter-ai/hummingbot/blob/feat/hydration/scripts/amm_price_example.py) (Hummingbot script to check the price functionality from an AMM connector)
- [scripts/amm_trade_example.py](https://github.com/robotter-ai/hummingbot/blob/feat/hydration/scripts/amm_trade_example.py) (Hummingbot script to place a trade using an AMM connector)
- [scripts/amm_data_feed.py](https://github.com/robotter-ai/hummingbot/blob/feat/hydration/scripts/amm_data_feed_example.py) (Hummingbot script that fetchs data from an AMM connector)
- (Other strategies are in the making by the Hummingbot foundation, since the support for AMM connectors is quite new, there are a lot of good ones to come)
