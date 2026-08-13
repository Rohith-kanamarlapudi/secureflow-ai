def test_viewer_cannot_delete_document(
    client,
    viewer_token,
    seeded_document,
):
    response = client.delete(
        f"/documents/{seeded_document.id}",
        headers={
            "Authorization": f"Bearer {viewer_token}",
        },
    )

    print("RBAC RESPONSE:", response.status_code)
    print("RBAC RESPONSE BODY:", response.json())

    assert response.status_code == 403