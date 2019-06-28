from htb import HTB

def test___init__():
    api_key = 'test'
    client = HTB(api_key)
    assert client.api_key == api_key

def test_global_stats():
    api_key = 'test'
    client = HTB(api_key)
    assert client.global_stats()['success'] == '1'

def test_overview_stats():
    api_key = 'test'
    client = HTB(api_key)
    assert len(client.overview_stats()) == 3

def test_daily_owns():
    api_key = 'test'
    client = HTB(api_key)
    assert client.daily_owns()['success'] == '1'
