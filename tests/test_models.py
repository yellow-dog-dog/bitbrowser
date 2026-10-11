"""Tests for bitbrowser.models."""

from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import ValidationError

from bitbrowser.models import (
    Browser,
    BrowserFingerPrint,
    ListBrowsersResponse,
    OpenResult,
)

# ===========================================================================
# BrowserFingerPrint
# ===========================================================================


class TestBrowserFingerPrintModelDump:
    def test_empty_instance_produces_empty_dict(self):
        fp = BrowserFingerPrint()
        assert fp.model_dump(by_alias=True, exclude_none=True) == {}

    def test_set_fields_are_included(self):
        fp = BrowserFingerPrint(core_version="130", ostype="PC", os="Win32")
        d = fp.model_dump(by_alias=True, exclude_none=True)
        assert d["coreVersion"] == "130"
        assert d["ostype"] == "PC"
        assert d["os"] == "Win32"

    def test_none_fields_are_excluded(self):
        fp = BrowserFingerPrint(core_version="130")
        d = fp.model_dump(by_alias=True, exclude_none=True)
        assert "ostype" not in d
        assert "os" not in d

    def test_camel_case_mapping(self):
        fp = BrowserFingerPrint(
            is_ip_create_time_zone=True,
            open_width=1920,
            open_height=1080,
            hardware_concurrency="8",
        )
        d = fp.model_dump(by_alias=True, exclude_none=True)
        assert d["isIpCreateTimeZone"] is True
        assert d["openWidth"] == 1920
        assert d["openHeight"] == 1080
        assert d["hardwareConcurrency"] == "8"

    def test_webrtc_maps_to_webRTC(self):
        fp = BrowserFingerPrint(webrtc="3")
        assert fp.model_dump(by_alias=True, exclude_none=True)["webRTC"] == "3"

    def test_webgl_maps_to_webGL(self):
        fp = BrowserFingerPrint(webgl="0")
        assert fp.model_dump(by_alias=True, exclude_none=True)["webGL"] == "0"

    def test_host_ip_maps_to_hostIP(self):
        fp = BrowserFingerPrint(host_ip="10.0.0.1")
        assert fp.model_dump(by_alias=True, exclude_none=True)["hostIP"] == "10.0.0.1"

    def test_extra_is_merged(self):
        fp = BrowserFingerPrint(customKey="val")
        d = fp.model_dump(by_alias=True, exclude_none=True)
        assert d["customKey"] == "val"

    def test_extra_overrides_mapped_field(self):
        fp = BrowserFingerPrint.model_validate({"coreVersion": "999"})
        assert fp.core_version == "999"

    def test_bool_false_is_included(self):
        fp = BrowserFingerPrint(is_ip_create_language=False)
        d = fp.model_dump(by_alias=True, exclude_none=True)
        assert d["isIpCreateLanguage"] is False

    def test_zero_int_is_included(self):
        fp = BrowserFingerPrint(open_width=0)
        d = fp.model_dump(by_alias=True, exclude_none=True)
        assert d["openWidth"] == 0


class TestBrowserFingerPrintModelValidate:
    def test_known_keys_are_mapped(self):
        fp = BrowserFingerPrint.model_validate(
            {"coreVersion": "130", "ostype": "PC", "os": "Win32"}
        )
        assert fp.core_version == "130"
        assert fp.ostype == "PC"
        assert fp.os == "Win32"

    def test_unknown_keys_go_to_extra(self):
        fp = BrowserFingerPrint.model_validate({"unknownField": "val"})
        assert fp.model_extra == {"unknownField": "val"}
        assert fp.core_version is None

    def test_webRTC_maps_to_webrtc(self):
        fp = BrowserFingerPrint.model_validate({"webRTC": "1"})
        assert fp.webrtc == "1"

    def test_webGL_maps_to_webgl(self):
        fp = BrowserFingerPrint.model_validate({"webGL": "0"})
        assert fp.webgl == "0"

    def test_hostIP_maps_to_host_ip(self):
        fp = BrowserFingerPrint.model_validate({"hostIP": "192.168.1.1"})
        assert fp.host_ip == "192.168.1.1"

    def test_empty_dict_gives_all_none(self):
        fp = BrowserFingerPrint.model_validate({})
        assert fp.core_version is None
        assert fp.model_extra == {}

    def test_roundtrip(self):
        original = BrowserFingerPrint(
            core_version="130",
            ostype="PC",
            os="Win32",
            open_width=1280,
            webrtc="3",
        )
        fp2 = BrowserFingerPrint.model_validate(
            original.model_dump(by_alias=True, exclude_none=True)
        )
        assert fp2.core_version == "130"
        assert fp2.ostype == "PC"
        assert fp2.os == "Win32"
        assert fp2.open_width == 1280
        assert fp2.webrtc == "3"


# ===========================================================================
# Browser
# ===========================================================================


class TestBrowserModelDump:
    def test_empty_browser_produces_empty_dict(self):
        b = Browser()
        assert b.model_dump(by_alias=True, exclude_none=True) == {}

    def test_id_is_included(self):
        b = Browser(id="br-1")
        assert b.model_dump(by_alias=True, exclude_none=True)["id"] == "br-1"

    def test_none_fields_are_excluded(self):
        b = Browser(name="test")
        d = b.model_dump(by_alias=True, exclude_none=True)
        assert "id" not in d
        assert "groupId" not in d

    def test_camel_case_mapping(self):
        b = Browser(group_id="g1", proxy_type="socks5", proxy_user_name="u")
        d = b.model_dump(by_alias=True, exclude_none=True)
        assert d["groupId"] == "g1"
        assert d["proxyType"] == "socks5"
        assert d["proxyUserName"] == "u"

    def test_browser_finger_print_nested(self):
        fp = BrowserFingerPrint(core_version="130")
        b = Browser(browser_finger_print=fp)
        d = b.model_dump(by_alias=True, exclude_none=True)
        assert "browserFingerPrint" in d
        assert d["browserFingerPrint"]["coreVersion"] == "130"

    def test_browser_finger_print_absent_when_none(self):
        b = Browser(name="x")
        assert "browserFingerPrint" not in b.model_dump(by_alias=True, exclude_none=True)

    def test_extra_is_merged(self):
        b = Browser(customField=99)
        assert b.model_dump(by_alias=True, exclude_none=True)["customField"] == 99

    def test_bool_fields(self):
        b = Browser(abort_image=True, mute_audio=False)
        d = b.model_dump(by_alias=True, exclude_none=True)
        assert d["abortImage"] is True
        assert d["muteAudio"] is False

    def test_port_zero_is_excluded(self):
        # port=0 is falsy-ish but not None; it should be included
        b = Browser(port=0)
        assert b.model_dump(by_alias=True, exclude_none=True)["port"] == 0


class TestBrowserModelValidate:
    def test_known_fields_mapped(self):
        b = Browser.model_validate(
            {"id": "br-1", "name": "test", "groupId": "g1", "seq": 5}
        )
        assert b.id == "br-1"
        assert b.name == "test"
        assert b.group_id == "g1"
        assert b.seq == 5

    def test_unknown_fields_go_to_extra(self):
        b = Browser.model_validate({"unknownKey": "val"})
        assert b.model_extra == {"unknownKey": "val"}

    def test_nested_browser_finger_print(self):
        b = Browser.model_validate(
            {"browserFingerPrint": {"coreVersion": "130", "os": "Win32"}}
        )
        assert isinstance(b.browser_finger_print, BrowserFingerPrint)
        assert b.browser_finger_print.core_version == "130"

    def test_nested_browser_finger_print_must_be_an_object(self):
        with pytest.raises(ValidationError):
            Browser.model_validate({"browserFingerPrint": "string-value"})

    def test_proxy_fields(self):
        b = Browser.model_validate(
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
        b2 = Browser.model_validate(
            original.model_dump(by_alias=True, exclude_none=True)
        )
        assert b2.id == "br-99"
        assert b2.name == "window"
        assert b2.proxy_type == "socks5"
        assert b2.port == 1080
        assert b2.browser_finger_print.core_version == "130"

    def test_empty_dict(self):
        b = Browser.model_validate({})
        assert b.id is None
        assert b.model_extra == {}


# ===========================================================================
# OpenResult
# ===========================================================================


class TestOpenResult:
    FULL_DATA: ClassVar[dict[str, object]] = {
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
        r = OpenResult.model_validate(self.FULL_DATA)
        assert r.ws == self.FULL_DATA["ws"]
        assert r.http == self.FULL_DATA["http"]
        assert r.core_version == "130"
        assert r.driver == "/usr/local/bin/chromedriver"

    def test_optional_fields(self):
        r = OpenResult.model_validate(self.FULL_DATA)
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
        r = OpenResult.model_validate(minimal)
        assert r.seq is None
        assert r.name is None
        assert r.remark is None
        assert r.group_id is None
        assert r.pid is None

    def test_missing_required_key_raises(self):
        with pytest.raises(ValidationError):
            OpenResult.model_validate({"http": "x", "coreVersion": "1", "driver": "d"})


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
