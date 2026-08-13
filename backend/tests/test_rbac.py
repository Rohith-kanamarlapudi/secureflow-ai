def test_viewer_cannot_delete_document(
    client,
    viewer_token,
    seeded_document,
):
    response = client.delete(
        f"/documents/{seeded_document.id}",
        headers={
            "Authorization": f"Bearer {viewer_token}"
        },
    )

    assert response.status_code == 403