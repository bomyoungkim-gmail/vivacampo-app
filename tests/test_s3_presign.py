import types


def test_presign_s3_uri(monkeypatch):
    from app.infrastructure import s3_client

    class DummyClient:
        def generate_presigned_url(self, *args, **kwargs):  # noqa: ANN001
            return "https://signed.example.com/object"

    monkeypatch.setattr(s3_client, "get_s3_client", lambda: DummyClient())

    signed = s3_client.presign_s3_uri("s3://bucket/key.tif")
    assert signed == "https://signed.example.com/object"


def test_presign_row_s3_fields(monkeypatch):
    from app.infrastructure import s3_client

    def _fake_presign(uri):
        if uri is None:
            return None
        return f"https://signed/{uri.split('://', 1)[1]}"

    monkeypatch.setattr(s3_client, "presign_s3_uri", _fake_presign)

    row = {
        "ndvi_s3_uri": "s3://bucket/ndvi.tif",
        "anomaly_s3_uri": None,
        "other": "keep",
    }
    signed = s3_client.presign_row_s3_fields(row, ["ndvi_s3_uri", "anomaly_s3_uri"])

    assert signed["ndvi_s3_uri"] == "https://signed/bucket/ndvi.tif"
    assert signed["anomaly_s3_uri"] is None
    assert signed["other"] == "keep"
