def test_login_valid_credentials(client, seeded_user):
    r = client.post(
        "/auth/login",
        json={
            "email": seeded_user.email,
            "password": "correct-pw",
        },
    )

    print("LOGIN RESPONSE:", r.json())

    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_invalid_password(client, seeded_user):
    r = client.post(
        "/auth/login",
        json={
            "email": seeded_user.email,
            "password": "wrong",
        },
    )

    print("INVALID LOGIN RESPONSE:", r.json())

    assert r.status_code == 401