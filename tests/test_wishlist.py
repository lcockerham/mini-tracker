def create_wishlist_item(client, name="Beholder", **kwargs):
    data = {"name": name, **kwargs}
    response = client.post("/wishlist", data=data)
    assert response.status_code == 200
    return response


class TestWishlist:
    def test_empty_wishlist(self, client):
        response = client.get("/wishlist")
        assert response.status_code == 200

    def test_add_item(self, client):
        create_wishlist_item(client, name="Beholder")
        response = client.get("/wishlist")
        assert "Beholder" in response.text

    def test_add_item_with_manufacturer(self, client):
        create_wishlist_item(client, name="Dragon", manufacturer="Reaper")
        response = client.get("/wishlist")
        assert "Dragon" in response.text
        assert "Reaper" in response.text

    def test_delete_item(self, client):
        create_wishlist_item(client, name="Goblin")
        list_resp = client.get("/wishlist")
        import re
        item_id = re.search(r'/wishlist/(\d+)/delete', list_resp.text).group(1)
        client.post(f"/wishlist/{item_id}/delete")
        response = client.get("/wishlist")
        assert "Goblin" not in response.text


class TestWishlistPurchase:
    def test_purchase_creates_mini(self, client):
        create_wishlist_item(client, name="Lich", manufacturer="Wizkids")
        list_resp = client.get("/wishlist")
        import re
        item_id = re.search(r'/wishlist/(\d+)/purchase', list_resp.text).group(1)

        response = client.post(f"/wishlist/{item_id}/purchase", data={"quantity": 1})
        assert response.status_code == 200
        # should redirect to mini detail
        assert "Lich" in response.text

    def test_purchase_removes_from_wishlist(self, client):
        create_wishlist_item(client, name="Vampire")
        list_resp = client.get("/wishlist")
        import re
        item_id = re.search(r'/wishlist/(\d+)/purchase', list_resp.text).group(1)
        client.post(f"/wishlist/{item_id}/purchase", data={"quantity": 1})

        wishlist = client.get("/wishlist")
        assert "Vampire" not in wishlist.text

    def test_purchase_copies_manufacturer(self, client):
        create_wishlist_item(client, name="Troll", manufacturer="Reaper")
        list_resp = client.get("/wishlist")
        import re
        item_id = re.search(r'/wishlist/(\d+)/purchase', list_resp.text).group(1)
        response = client.post(f"/wishlist/{item_id}/purchase", data={"quantity": 2})
        assert "Reaper" in response.text

    def test_purchase_sets_unpainted_status(self, client):
        create_wishlist_item(client, name="Zombie")
        list_resp = client.get("/wishlist")
        import re
        item_id = re.search(r'/wishlist/(\d+)/purchase', list_resp.text).group(1)
        response = client.post(f"/wishlist/{item_id}/purchase", data={"quantity": 1})
        assert "Unpainted" in response.text
