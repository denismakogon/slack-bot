# Slackbot

## Dependencies

```bash
pip install -r requirements.txt
```

## Start

```bash
export SLACK_API_TOKEN=<...>
export SLACK_CHANNEL_ID=<...>
export YAHOO_WEATHER_APP_ID=<...>
export YAHOO_WEATHER_API_KEY=<...>
export YAHOO_WEATHER_API_SECRET=<...>

python bot.py
```

## Test
```bash
pip install -r test-requirements.txt
pytest -v test_bot.py
```
