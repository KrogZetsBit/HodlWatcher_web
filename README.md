# HodlWatcher Web 🚀🐶

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/KrogZetsBit/HodlWatcher_web)
[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/KrogZetsBit/HodlWatcher_web) [![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## Description

Tired of constantly refreshing HodlHodl hoping to catch the perfect Bitcoin trade? 😩 Let **HodlWatcher** be your eyes and ears! 👀

This nifty web app monitors HodlHodl offers 24/7 based on **your** specific criteria. Set up a "Watchdog" alert, sit back, and relax. We'll ping you the moment a matching buy or sell opportunity pops up! Never miss out on hitting your price target again! 🎉💰

## ✨ Key Features

* 🔍 **Automated HodlHodl Monitoring:** Checks for BTC offers continuously.
* 🐶 **Customizable "Watchdogs":** Create specific alerts based on:
  * 🛒 **Operation:** Buy or Sell
  * 🪙 **Asset:** Bitcoin (BTC)
  * 💵 **Currency:** EUR, USD, and more!
  * 🔢 **Amount:** Define the quantity you're interested in.
  * 💳 **Payment Method:** Filter by your preferred methods (e.g., SEPA, Revolut, etc.).
  * 📉 **Max Fee Rate:** Only get alerted for offers below your desired fee percentage.
* 🔔 **Instant Notifications:** Get alerts straight to your **Telegram** account 📲 and **Email** ✉️.
* 🔎 **Manual Offer Finder:** Browse and filter current HodlHodl offers directly within the app.
* 🔒 **Secure User Accounts:** Easy Sign Up, Sign In, Password Resets, and Profile Management.
* 🔑 **Enhanced Security:** Supports Two-Factor Authentication (2FA) using:
  * 📱 Authenticator Apps (like Google Authenticator, Authy)
  * 🛡️ Security Keys (like YubiKey)
  * 📄 Recovery Codes
* 🤖 **Smart Telegram Bot:**
  * Link your HodlWatcher account securely.
  * Receive deal alerts directly in chat.
  * Manage your watchdogs.
  * Check configured fees.
  * Get help.
* 🌐 **Multi-language Support:** Speaks English 🇬🇧, Spanish 🇪🇸, and French 🇫🇷!
* ❓ **FAQ Section:** Got questions? Find answers in our handy FAQ.
* 📧 **Contact Form:** Reach out to us easily.
* ⚙️ **Admin Panel:** For site administrators to manage the platform.

## 🤔 How it Works

1. ✍️ **Sign Up:** Create your HodlWatcher account.
2. 🔗 **Link Telegram (Recommended):** Search for our bot on Telegram (`@HodlWatcher_bot` - *replace this*), type `/start`, and follow the prompts to link it to your account for instant alerts.
3. 🐶 **Create a Watchdog:** Head to "My Watchdogs", hit "New Watchdog", and tell us exactly what kind of HodlHodl offer you're looking for (e.g., "Buy 0.05 BTC with EUR via SEPA, max fee 1.5%").
4. ✅ **Activate it!**
5. 🧘 **Relax:** Go live your life! HodlWatcher is on the case.
6. 🚀 **Get Notified:** As soon as an offer matching your criteria appears on HodlHodl, you'll get a Telegram message!

## 🛠️ Tech Stack (Likely)

* 🐍 Python
* 💚 Django Web Framework
* ⚙️ Celery (for background monitoring tasks)
* 🐘 PostgreSQL (or similar relational database)
* 🖼️ HTML, CSS, JavaScript (for the frontend interface)
* 🤖 python-telegram-bot (or similar library for Telegram integration)

## 🚀 Getting Started

*(Add instructions here if you want others to be able to set up and run the project locally. E.g., clone repo, setup virtual environment, install requirements, migrate database, run server)*

```bash
# Example setup commands (customize as needed)
git clone https://github.com/KrogZetsBit/hodlwatcher.git
cd hodlwatcher
python -m venv venv
source venv/bin/activate # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## 🤝 Contributing

Contributions are what make the open-source community amazing! If you have ideas or want to fix something, feel free to fork the repo and create a pull request.

1. Fork the Project
2. Create your Feature Branch (git checkout -b feature/AmazingFeature)
3. Commit your Changes (git commit -m 'Add some AmazingFeature')
4. Push to the Branch (git push origin feature/AmazingFeature)
5. Open a Pull Request

Please try to follow existing code style and add tests where appropriate!

## 📜 License

Distributed under the MIT License. See LICENSE file for more information.

## ✉️ Contact

Having trouble or got a cool idea?

Open an Issue on this GitHub repository.
Use the Contact Form on the HodlWatcher website (if applicable).

Happy Hodling! 📈📉

## Settings

Moved to [settings](https://cookiecutter-django.readthedocs.io/en/latest/1-getting-started/settings.html).

## Basic Commands

### Setting Up Your Users

* To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

* To create a **superuser account**, use this command:

```bash
python manage.py createsuperuser
```

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

mypy hodlwatcher

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

```bash
coverage run -m pytest
coverage html
open htmlcov/index.html
```

#### Running tests with pytest

```bash
pytest
```

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally.html#using-webpack-or-gulp).

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd hodlwatcher
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd hodlwatcher
celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd hodlwatcher
celery -A config.celery_app worker -B -l info
```

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Deployment

The following details how to deploy this application.

### Docker

See detailed [cookiecutter-django Docker documentation](https://cookiecutter-django.readthedocs.io/en/latest/3-deployment/deployment-with-docker.html).
