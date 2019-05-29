import collections

import os

import slack
from yahoo_weather import weather


SLACK_TOKEN = os.environ.get("SLACK_API_TOKEN")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")

CREATE_POLL_EVENT_PATTERN = ", create a poll with options:"
ACCEPT_VOTE_PATTERN = ", vote #"
GET_STATS_PATTERN = ", show results for poll"
WEATHER_PATTERN = ", what’s the current weather in"

POLL_MAP = collections.defaultdict(dict)


def get_weather_client() -> weather.YahooWeather:
    """
    Yahoo weather client init func
    :return:
    """
    return weather.YahooWeather(
        APP_ID=os.getenv("YAHOO_WEATHER_APP_ID"),
        api_key=os.getenv("YAHOO_WEATHER_API_KEY"),
        api_secret=os.getenv("YAHOO_WEATHER_API_SECRET")
    )


def get_poll_options(message: str) -> list:
    """
    Turns string into a list of poll options
    :param message:
    :return:
    """
    parts = message.split(CREATE_POLL_EVENT_PATTERN)
    if len(parts) > 1:
        votes = parts[-1].split(",")
        if len(votes) == 1 and votes[0] == ' ':
            return []
        else:
            return votes
    return []


def create_poll(poll_options: list) -> dict:
    """
    Creates a poll of a list of options
    :param poll_options:
    :return:
    """
    poll_opts_map = {}
    for opt in poll_options:
        poll_opts_map.update({opt.lstrip(" ").rstrip(" "): 0})

    return poll_opts_map


def create_poll_and_respond(slack_client, slack_channel, username, message):
    """
    High-level poll creator
    :param slack_client:
    :param slack_channel:
    :param username:
    :param message:
    :return:
    """
    next_id = len(POLL_MAP.keys()) + 1
    opts = get_poll_options(message)
    if len(opts) > 0:
        POLL_MAP[str(next_id)] = create_poll(
            opts
        )

        post_message(
            slack_client,
            slack_channel,
            f"hey <@{username}>, poll #{next_id} created."
        )
    else:
        post_message(
            slack_client,
            slack_channel,
            f"malformed vote options"
        )


def post_message(slack_client, slack_channel, msg):
    """
    Posts a message to a channel
    :param slack_client:
    :param slack_channel:
    :param msg:
    :return:
    """
    slack_client.chat_postMessage(
        channel=slack_channel,
        text=msg,
    )


def setup_statistics(vote_id):
    """
    Does stats calculations
    :param vote_id:
    :return:
    """
    opts = POLL_MAP[vote_id]
    str_opts = [f"Poll #{vote_id} results: ", ]
    total = sum(opts.values())
    for opt, value in opts.items():
        str_opts.append(f"{opt} - {value} ({float(value/total) * 100}%)")

    return ", ".join(str_opts)


def accept_vote(slack_client, slack_channel, username, message: str):
    """
    High-level vote acceptor
    :param slack_client:
    :param slack_channel:
    :param username:
    :param message:
    :return:
    """
    parts = message.split(ACCEPT_VOTE_PATTERN)
    if len(parts) > 1:
        id_vote = parts[-1]
        id_vote_parts = id_vote.split(" ")
        if len(id_vote) > 1:
            vote_id = id_vote_parts[0]
            vote = id_vote_parts[1]
            if vote_id in POLL_MAP:
                votes = POLL_MAP[vote_id]
                if vote != '' and vote in votes:
                    votes[vote] += 1
                    post_message(
                        slack_client,
                        slack_channel,
                        f"hey <@{username}>, your vote has been registered."
                    )
                else:
                    post_message(
                        slack_client,
                        slack_channel,
                        "malformed vote option"
                    )
            else:
                post_message(
                    slack_client,
                    slack_channel,
                    "poll not found"
                )
        else:
            post_message(
                slack_client,
                slack_channel,
                "malformed vote ID and vote data"
            )
    else:
        post_message(
            slack_client,
            slack_channel,
            "malformed poll inquiry"
        )


def collect_stats(message) -> tuple:
    """
    Stats collector
    :param message:
    :return:
    """
    stats = ""
    vote_id = None
    parts = message.split("#")
    if len(parts) > 1:
        vote_id = parts[-1]
        stats = setup_statistics(vote_id)

    return vote_id, stats


def get_weather(message) -> tuple:
    """
    Allocates weather info based on the submitted message
    :param message:
    :return:
    """
    parts = message.split(WEATHER_PATTERN)
    if len(parts) > 1:
        possible_location = parts[-1].rstrip("?")
        wc = get_weather_client()

        location_weather = wc.get_yahoo_weather_by_city(possible_location)
        condition = location_weather.condition
        return (possible_location,
                condition.text,
                condition.temperature)


def parse_bot_commands(slack_client: slack.WebClient, slack_channel: str,
                       username: str, message: str):
    """
    High-level message parser
    :param slack_client:
    :param slack_channel:
    :param username:
    :param message:
    :return:
    """

    if CREATE_POLL_EVENT_PATTERN in message:
        create_poll_and_respond(
            slack_client, slack_channel,
            username, message
        )
        return

    if ACCEPT_VOTE_PATTERN in message:
        accept_vote(
            slack_client, slack_channel,
            username, message
        )
        return

    if GET_STATS_PATTERN in message:
        vote_id, stats = collect_stats(message)
        if vote_id in POLL_MAP:
            post_message(
                slack_client,
                slack_channel,
                stats
            )
            return

    if WEATHER_PATTERN in message:
        try:
            loc, condition, temperature = get_weather(message)
            post_message(slack_client, slack_channel,
                         f"It’s currently {condition} in {loc}, "
                         f"temperature is {temperature} degrees celsius.")
        except Exception as _:
            post_message(slack_client, slack_channel,
                         "weather info is not available at this moment.")


@slack.RTMClient.run_on(event='message')
def processor(**payload):
    data = payload['data']
    web_client: slack.WebClient = payload['web_client']
    msg = data.get("text")
    channel_id = data['channel']
    user = data.get("user")
    if msg is not None and SLACK_CHANNEL_ID == channel_id:
        parse_bot_commands(web_client, channel_id, user, msg)


if __name__ == "__main__":
    if all((SLACK_TOKEN, SLACK_CHANNEL_ID)):

        rtm_client = slack.RTMClient(token=SLACK_TOKEN)
        rtm_client.start()
    else:
        raise Exception("SLACK_TOKEN or SLACK_CHANNEL is not set, aborting")
