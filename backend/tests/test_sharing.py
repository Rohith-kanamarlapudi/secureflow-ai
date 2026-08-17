def test_expired_share_rejected(client, expired_share, other_user_token):
    r = client.get(
        f"/documents/{expired_share.document_id}/download",
        headers={"Authorization": f"Bearer {other_user_token}"},
    )

    assert r.status_code == 403


def test_revoked_share_rejected(client, revoked_share, other_user_token):
    r = client.get(
        f"/documents/{revoked_share.document_id}/download",
        headers={"Authorization": f"Bearer {other_user_token}"},
    )

    assert r.status_code == 403