<p align="center">
  <a href="https://github.com/acostyle/fish_shop_bot">
    <img src="http://www.vectorico.com/download/social_media/Telegram-Icon.png" alt="Logo" width="80" height="80">
  </a>
</p>

<h3 align="center">Fish shop bot</h3>

<p align="center">
  <a href="https://github.com/acostyle/fish_shop_bot/blob/main/LICENSE"><img src="https://img.shields.io/github/license/acostyle/fish_shop_bot?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/wemake-services/wemake-python-styleguide"><img src="https://img.shields.io/badge/style-wemake-blue?style=for-the-badge" alt="Code style"></a>
  <img alt="Commit activity" src="https://img.shields.io/github/commit-activity/m/acostyle/fish_shop_bot?color=GREEN&style=for-the-badge" />
</p>

## Table of content

- [About the project](#about-the-project)
- [Installation](#installation)
- [How to run](#how-to-run)
- [License](#license)


## About the project

Bot for buying fish via Telegram

Demonstration of the bot

![](https://media.giphy.com/media/WAfjTPEh4GNRQzsqch/giphy.gif)

## Installation

* Install make;
* Create your CMS [here](https://www.elasticpath.com)
* Clone github repository:
```bash
git clone https://github.com/acostyle/fish_shop_bot
```
* Go to folder with project:
```bash
cd fish_shop_bot
```
* Install dependencies:
    - On windows:
    ```bash
    make win_install
    ```
    - On linux:
    ```bash
    make linux_install
    ```
* Create a bot in Telegram via [BotFather](https://t.me/BotFather), and get it API token;
* Find out your chat id in the [@userinfobot](https://t.me/userinfobot)
* Create a `.env` file with the following content:
```.env
CLIENT_ID=<CLIENT ID>
CLIENT_SECRET=<CLIENT SECRET>
TELEGRAM_BOT_TOKEN=<TELEGRAM BOT TOKEN>
REDIS_PASSWORD=<REDIS DB PASSWORD>
REDIS_HOST=<REDIS DB HOST>
REDIS_PORT=<REDIS DB PORT>
```


## How to run

```bash
python telegram_bot.py
```

## License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/acostyle/fish_shop_bot/blob/main/LICENSE) file for details.