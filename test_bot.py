import bot
import collections


# patch post_message from bot.py
def mockup(sc, sch, msg):
    print(msg)


bot.post_message = mockup


def test_get_poll_options():
    msg = "hey @bot, create a poll with options: 1, 2, 3"
    opts = bot.get_poll_options(msg)

    assert isinstance(opts, list)
    assert 3 == len(opts)


def test_get_empty_poll_options():
    bot.POLL_MAP = collections.defaultdict(dict)

    msg = "hey @bot, create a poll with options: "
    opts = bot.get_poll_options(msg)

    assert 0 == len(opts)


def test_create_poll():
    bot.POLL_MAP = collections.defaultdict(dict)

    msg = "hey @bot, create a poll with options: 1, 2, 3"
    bot.create_poll_and_respond(None, None, "py.test", msg)

    assert 1 == len(bot.POLL_MAP)
    assert bot.POLL_MAP.get("1") is not None


def test_create_broken_poll():
    bot.POLL_MAP = collections.defaultdict(dict)

    msg = "hey @bot, create a poll with options: "
    bot.create_poll_and_respond(None, None, "py.test", msg)

    assert 0 == len(bot.POLL_MAP)


def test_accept_vote():
    bot.POLL_MAP = collections.defaultdict(dict)

    msg = "hey @bot, create a poll with options: 1, 2, 3"
    bot.create_poll_and_respond(None, None, "py.test", msg)

    vote_msg = "hey @bot, vote #1 1"
    bot.accept_vote(None, None, "py.test", vote_msg)

    assert 1 == len(bot.POLL_MAP)
    assert 1 == bot.POLL_MAP["1"]["1"]


def test_accept_vote_missing_opt():
    bot.POLL_MAP = collections.defaultdict(dict)

    msg = "hey @bot, create a poll with options: 1, 2, 3"
    bot.create_poll_and_respond(None, None, "py.test", msg)

    vote_msg = "hey @bot, vote #1 666"
    bot.accept_vote(None, None, "py.test", vote_msg)

    assert 1 == len(bot.POLL_MAP)
    assert 0 == bot.POLL_MAP["1"]["1"]


def test_accept_vote_missing_poll():
    bot.POLL_MAP = collections.defaultdict(dict)

    msg = "hey @bot, create a poll with options: 1, 2, 3"
    bot.create_poll_and_respond(None, None, "py.test", msg)

    vote_msg = "hey @bot, vote #666 1"
    bot.accept_vote(None, None, "py.test", vote_msg)

    assert 1 == len(bot.POLL_MAP)
    assert 0 == bot.POLL_MAP["1"]["1"]


def test_get_results():
    bot.POLL_MAP = collections.defaultdict(dict)

    msg = "hey @bot, create a poll with options: 1, 2, 3"
    bot.create_poll_and_respond(None, None, "py.test", msg)

    vote_msg = "hey @bot, vote #1 1"
    bot.accept_vote(None, None, "py.test", vote_msg)

    res_msg = "hey @bot, show results for poll #1"
    vote_id, stats = bot.collect_stats(res_msg)

    print(stats)
    assert "" != stats


def test_get_missing_poll_results():
    bot.POLL_MAP = collections.defaultdict(dict)
    res_msg = "hey @bot, show results for poll #1"
    vote_id, stats = bot.collect_stats(res_msg)
    print(stats)

    assert "Poll #1 results: " == stats
    assert "1" == vote_id
