"""Tests for bitbrowser.models."""

from __future__ import annotations

import pytest

from bitbrowser.models import Browser, BrowserFingerPrint, ListBrowsersResponse, OpenResult


# ===========================================================================
# BrowserFingerPrint
# ===========================================================================


class TestBrowserFingerPrintToApiDict:
    def test_empty_instance_produces_empty_dict(self):
        fp = BrowserFingerPrint()
        assert fp.to_api_dict() == {}

    def test_set_fields_are_included(self):
        fp = BrowserFingerPrint(core_version="130", ostype="PC", os="Win32")
        d = fp.to_api_dict()
        assert d["coreVersion"] == "130"
        assert d["ostype"] == "PC"
        assert d["os"] == "Win32"

    def test_none_fields_are_excluded(self):
        fp = BrowserFingerPrint(core_version="130")
        d = fp.to_api_dict()
        assert "ostype" not in d
        assert "os" not in d

    def test_camel_case_mapping(self):
        fp = BrowserFingerPrint(
            is_ip_create_time_zone=True,
            open_width=1920,
            open_height=1080,
            hardware_concurrency="8",
        )
        d = fp.to_api_dict()
        assert d["isIpCreateTimeZone"] is True
        assert d["openWidth"] == 1920
        assert d["openHeight"] == 1080
        assert d["hardwareConcurrency"] == "8"

    def test_webrtc_maps_to_webRTC(self):
        fp = BrowserFingerPrint(webrtc="3")
        assert fp.to_api_dict()["webRTC"] == "3"

    def test_webgl_maps_to_webGL(self):
        fp = BrowserFingerPrint(webgl="0")
        assert fp.to_api_dict()["webGL"] == "0"

    def test_host_ip_maps_to_hostIP(self):
        fp = BrowserFingerPrint(host_ip="10.0.0.1")
        assert fp.to_api_dict()["hostIP"] == "10.0.0.1"

    def test_extra_is_merged(self):
        fp = BrowserFingerPrint(extra={"customKey": "val"})
        d = fp.to_api_dict()
        assert d["customKey"] == "val"

    def test_extra_overrides_mapped_field(self):
        fp = BrowserFingerPrint(core_version="130", extra={"coreVersion": "999"})
        d = fp.to_api_dict()
        assert d["coreVersion"] == "999"

    def test_bool_false_is_included(self):
        fp = BrowserFingerPrint(is_ip_create_language=False)
        d = fp.to_api_dict()
        assert d["isIpCreateLanguage"] is False

    def test_zero_int_is_included(self):
        fp = BrowserFingerPrint(open_width=0)
        d = fp.to_api_dict()
        assert d["openWidth"] == 0


class TestBrowserFingerPrintFromApiDict:
    def test_known_keys_are_mapped(self):
        fp = BrowserFingerPrint.from_api_dict(
            {"coreVersion": "130", "ostype": "PC", "os": "Win32"}
        )
        assert fp.core_version == "130"
        assert fp.ostype == "PC"
        assert fp.os == "Win32"

    def test_unknown_keys_go_to_extra(self):
        fp = BrowserFingerPrint.from_api_dict({"unknownField": "val"})
        assert fp.extra == {"unknownField": "val"}
        assert fp.core_version is None

    def test_webRTC_maps_to_webrtc(self):
        fp = BrowserFingerPrint.from_api_dict({"webRTC": "1"})
        assert fp.webrtc == "1"

    def test_webGL_maps_to_webgl(self):
        fp = BrowserFingerPrint.from_api_dict({"webGL": "0"})
        assert fp.webgl == "0"

    def test_hostIP_maps_to_host_ip(self):
        fp = BrowserFingerPrint.from_api_dict({"hostIP": "192.168.1.1"})
        assert fp.host_ip == "192.168.1.1"

    def test_empty_dict_gives_all_none(self):
        fp = BrowserFingerPrint.from_api_dict({})
        assert fp.core_version is None
        assert fp.extra == {}

    def test_roundtrip(self):
        original = BrowserFingerPrint(
            core_version="130",
            ostype="PC",
            os="Win32",
            open_width=1280,
            webrtc="3",
        )
        fp2 = BrowserFingerPrint.from_api_dict(original.to_api_dict())
        assert fp2.core_version == "130"
        assert fp2.ostype == "PC"
        assert fp2.os == "Win32"
        assert fp2.open_width == 1280
        assert fp2.webrtc == "3"


# ===========================================================================
# Browser
# ===========================================================================


class TestBrowserToApiDict:
    def test_empty_browser_produces_empty_dict(self):
        b = Browser()
        assert b.to_api_dict() == {}

    def test_id_is_included(self):
        b = Browser(id="br-1")
        assert b.to_api_dict()["id"] == "br-1"

    def test_none_fields_are_excluded(self):
        b = Browser(name="test")
        d = b.to_api_dict()
        assert "id" not in d
        assert "groupId" not in d

    def test_camel_case_mapping(self):
        b = Browser(group_id="g1", proxy_type="socks5", proxy_user_name="u")
        d = b.to_api_dict()
        assert d["groupId"] == "g1"
        assert d["proxyType"] == "socks5"
        assert d["proxyUserName"] == "u"

    def test_browser_finger_print_nested(self):
        fp = BrowserFingerPrint(core_version="130")
        b = Browser(browser_finger_print=fp)
        d = b.to_api_dict()
        assert "browserFingerPrint" in d
        assert d["browserFingerPrint"]["coreVersion"] == "130"

    def test_browser_finger_print_absent_when_none(self):
        b = Browser(name="x")
        assert "browserFingerPrint" not in b.to_api_dict()

    def test_extra_is_merged(self):
        b = Browser(extra={"customField": 99})
        assert b.to_api_dict()["customField"] == 99

    def test_bool_fields(self):
        b = Browser(abort_image=True, mute_audio=False)
        d = b.to_api_dict()
        assert d["abortImage"] is True
        assert d["muteAudio"] is False

    def test_port_zero_is_excluded(self):
        # port=0 is falsy-ish but not None; it should be included
        b = Browser(port=0)
        assert b.to_api_dict()["port"] == 0


class TestBrowserFromApiDict:
    def test_known_fields_mapped(self):
        b = Browser.from_api_dict(
            {"id": "br-1", "name": "test", "groupId": "g1", "seq": 5}
        )
        assert b.id == "br-1"
        assert b.name == "test"
        assert b.group_id == "g1"
        assert b.seq == 5

    def test_unknown_fields_go_to_extra(self):
        b = Browser.from_api_dict({"unknownKey": "val"})
        assert b.extra == {"unknownKey": "val"}

    def test_nested_browser_finger_print(self):
        b = Browser.from_api_dict(
            {"browserFingerPrint": {"coreVersion": "130", "os": "Win32"}}
        )
        assert isinstance(b.browser_finger_print, BrowserFingerPrint)
        assert b.browser_finger_print.core_version == "130"

    def test_nested_browser_finger_print_not_dict_goes_to_extra(self):
        b = Browser.from_api_dict({"browserFingerPrint": "string-value"})
        assert b.extra["browserFingerPrint"] == "string-value"
        assert b.browser_finger_print is None

    def test_proxy_fields(self):
        b = Browser.from_api_dict(
            {
                "proxyType": "http",
                "host": "1.2.3.4",
                "port": 8080,
                "proxyUserName": "user",
                "proxyPassword": "pass",
            }
        )
        assert b.proxy_type == "http"
        assert b.host == "1.2.3.4"
        assert b.port == 8080
        assert b.proxy_user_name == "user"
        assert b.proxy_password == "pass"

    def test_roundtrip(self):
        original = Browser(
            id="br-99",
            name="window",
            proxy_type="socks5",
            host="1.2.3.4",
            port=1080,
            browser_finger_print=BrowserFingerPrint(core_version="130"),
        )
        b2 = Browser.from_api_dict(original.to_api_dict())
        assert b2.id == "br-99"
        assert b2.name == "window"
        assert b2.proxy_type == "socks5"
        assert b2.port == 1080
        assert b2.browser_finger_print.core_version == "130"

    def test_empty_dict(self):
        b = Browser.from_api_dict({})
        assert b.id is None
        assert b.extra == {}


# ===========================================================================
# OpenResult
# ===========================================================================


class TestOpenResult:
    FULL_DATA = {
        "ws": "ws://127.0.0.1:9222/devtools/browser/abc",
        "http": "127.0.0.1:9222",
        "coreVersion": "130",
        "driver": "/usr/local/bin/chromedriver",
        "seq": 1,
        "name": "my-window",
        "remark": "note",
        "groupId": "grp-1",
        "pid": 12345,
    }

    def test_required_fields(self):
        r = OpenResult.from_api_dict(self.FULL_DATA)
        assert r.ws == self.FULL_DATA["ws"]
        assert r.http == self.FULL_DATA["http"]
        assert r.core_version == "130"
        assert r.driver == "/usr/local/bin/chromedriver"

    def test_optional_fields(self):
        r = OpenResult.from_api_dict(self.FULL_DATA)
        assert r.seq == 1
        assert r.name == "my-window"
        assert r.remark == "note"
        assert r.group_id == "grp-1"
        assert r.pid == 12345

    def test_optional_fields_default_to_none(self):
        minimal = {
            "ws": "ws://127.0.0.1:9222/devtools/browser/xyz",
            "http": "127.0.0.1:9222",
            "coreVersion": "130",
            "driver": "/path/chromedriver",
        }
        r = OpenResult.from_api_dict(minimal)
        assert r.seq is None
        assert r.name is None
        assert r.remark is None
        assert r.group_id is None
        assert r.pid is None

    def test_missing_required_key_raises(self):
        with pytest.raises(KeyError):
            OpenResult.from_api_dict({"http": "x", "coreVersion": "1", "driver": "d"})


# ===========================================================================
# ListBrowsersResponse
# ===========================================================================


class TestListBrowsersResponse:
    def test_basic_construction(self):
        resp = ListBrowsersResponse(browsers=[], total=0, page=0, page_size=10)
        assert resp.browsers == []
        assert resp.total == 0

    def test_with_browsers(self):
        b = Browser(id="br-1")
        resp = ListBrowsersResponse(browsers=[b], total=1, page=0, page_size=10)
        assert len(resp.browsers) == 1
        assert resp.browsers[0].id == "br-1"

    def test_pagination_fields(self):
        resp = ListBrowsersResponse(browsers=[], total=100, page=3, page_size=20)
        assert resp.page == 3
        assert resp.page_size == 20
        assert resp.total == 100
