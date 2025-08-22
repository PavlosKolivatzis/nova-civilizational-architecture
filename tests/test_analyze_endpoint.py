import pytest

from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_analyze_endpoint_validation(client):
    response = client.post('/api/analyze', json={})
    assert response.status_code == 400
    assert "Missing required fields" in response.get_json()['error']

    response = client.post('/api/analyze', json={
        'content': 'test content',
        'cultural_context': {'type': 'western'}
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('ok') is True
    assert 'individualism_index' in data
