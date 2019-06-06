from htb import HTB

def test___init__():
    api_key = 'test'
    client = HTB(api_key)
    assert client.api_key == api_key

def test_global_stats():
    assert HTB.global_stats()['success'] == '1'

def test_overview_stats():
    assert len(HTB.overview_stats()) == 3

def test_daily_owns():
    assert HTB.daily_owns()['success'] == '1'
