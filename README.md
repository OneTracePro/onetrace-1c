# OneTrace.pro for 1C: in-store receipts

[![CI](https://github.com/OneTracePro/onetrace-1c/actions/workflows/ci.yml/badge.svg)](https://github.com/OneTracePro/onetrace-1c/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A 1C:Enterprise configuration extension that sends retail receipts and the store directory to [OneTrace.pro](https://onetrace.pro), the customer data platform. An in-store purchase is linked to the customer's online history — website visits, product views, emails — and the ROPO report shows how many store sales came from customers who researched online first. In-store purchases are available to segments and journeys.

[Русская версия](README.ru.md) — the full documentation: installation, settings, what is sent.

- 1C:Enterprise 8.3.21 or later; **1C:Retail 2.3 and 3.0, 1C:Small Business Management (UNF) 1.6 and 3.0, 1C:Trade Management 11** — configurations with the "Чек ККМ" document
- File and client-server modes; outgoing HTTPS to the platform address
- The configuration itself is not modified: everything lives in an extension with the `ОТ_` prefix

## What it sends

| Data | When | How |
|---|---|---|
| Posted receipts: date, number, store, amount, products (id, quantity, price) | a scheduled job every 15 minutes: receipts after the last sent one, at least 5 minutes old | the purchase event (`order_completed` by default) with `channel = offline`, `store_id`, `amount`, `order_id`, `products` |
| The customer: phone, email, loyalty card number | with the receipt | `context.traits` — the platform finds or creates the customer profile |
| Stores: id, name, address | daily and with "Send now" | the OneTrace store directory (`/api/v1/stores`) |

Field names differ between Retail, UNF and Trade Management, so the extension finds them through the metadata (store, loyalty card, goods table). Receipts without a phone, email or card are skipped and logged: they cannot be linked to online activity.

## Installation

1. Download `onetrace-1c.zip` from the [latest release](https://github.com/OneTracePro/onetrace-1c/releases).
2. In **Designer**: **Configuration → Configuration extensions → Add**, then **Configuration → Load configuration from files…** with `src/Configuration.xml`; update the database configuration.
3. In 1C:Enterprise turn off **Safe mode** and **Unsafe action protection** of the OneTrace extension: it makes HTTP requests.
4. Create a **secret** API key in your OneTrace project with `products.write` (for the store directory; receipts are accepted with any secret key).
5. Open **All functions → Data processors → OneTrace: настройка**, enter the platform address and the key, click **Test connection** and **Save** (this enables the scheduled job).

If loading from files fails on your platform version, [README.ru.md](README.ru.md#если-загрузка-из-файлов-не-прошла) lists the objects to create by hand and the module files to paste.

## Tests

`tests/run.sh` checks the syntax of every module and runs the exchange core (`ОТ_КлиентAPI`) in [OneScript](https://oscript.io) — the same code 1C runs — against a mock platform; `tests/run.sh --live` with `ONETRACE_URL` and `ONETRACE_KEY` runs it against a real project. Reading receipts of a specific configuration and loading the extension need the 1C platform and are not covered: please [report issues](https://github.com/OneTracePro/onetrace-1c/issues) with your platform and configuration versions.

## License

MIT
