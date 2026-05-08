"""BitBrowser resource models — Pydantic v2.

All models use ``alias_generator=to_camel`` so snake_case Python attributes
map to/from the camelCase JSON keys used by the BitBrowser local API.

Six fingerprint fields have non-standard casing that ``to_camel`` cannot
produce automatically (e.g. ``webGL`` instead of ``webGl``) and therefore
use an explicit ``Field(alias=...)`` declaration.

Serialise a model for the API::

    browser.model_dump(by_alias=True, exclude_none=True)

Deserialise from the API::

    Browser.model_validate(data)          # data is a camelCase dict
    Browser.model_validate({"name": …})   # or snake_case (populate_by_name=True)
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


# ---------------------------------------------------------------------------
# Sub-objects
# ---------------------------------------------------------------------------


class BrowserFingerPrint(BaseModel):
    """Browser fingerprint configuration.

    All fields are optional — pass an empty instance (``BrowserFingerPrint()``)
    to let BitBrowser randomise every value.

    Attributes:
        core_product: Rendering engine.  ``"chrome"`` (default) or
            ``"firefox"``.
        core_version: Core version string, e.g. ``"130"`` for Chrome,
            ``"128"`` for Firefox.
        ostype: Platform type.  One of ``"PC"``, ``"Android"``, ``"IOS"``.
        os: ``navigator.platform`` value.  Must match *ostype* exactly:
            ``"Win32"`` (Windows), ``"MacIntel"`` (macOS),
            ``"Linux x86_64"`` (Linux), ``"iPhone"`` (iOS),
            ``"Linux armv81"`` (Android).
        os_version: OS version string.  Leave empty to randomise.
            Comma-separated candidates are allowed,
            e.g. ``"11,10"`` for Windows.
        version: Browser version.  Leave empty to randomise.
        user_agent: Full UA string.  Leave empty to auto-generate.
        is_ip_create_time_zone: Derive timezone from the proxy IP.
        time_zone: IANA timezone identifier (when
            *is_ip_create_time_zone* is ``False``).
        webrtc: WebRTC policy.
            ``"0"`` replace · ``"1"`` allow · ``"2"`` disable ·
            ``"3"`` privacy (default).
        position: Geolocation permission.
            ``"0"`` ask · ``"1"`` allow · ``"2"`` deny.
        is_ip_create_position: Derive geolocation from the proxy IP.
        is_ip_create_language: Derive browser language from the proxy IP.
        languages: Browser language (when *is_ip_create_language* is
            ``False``).
        open_width: Initial window width in pixels (default ``1280``).
        open_height: Initial window height in pixels (default ``720``).
        canvas: Canvas fingerprint.  ``"0"`` random · ``"1"`` off.
        webgl: WebGL image.  ``"0"`` random · ``"1"`` off.
        hardware_concurrency: CPU thread count string, e.g. ``"4"``.
        device_memory: RAM in GB string.  ``"4"`` or ``"8"``.
        launch_args: Comma-separated Chromium CLI flags, e.g.
            ``"--incognito,--no-sandbox"``.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        extra="allow",
    )

    # ---- Core / OS ----
    core_product: str | None = None
    core_version: str | None = None
    ostype: str | None = None
    os: str | None = None
    os_version: str | None = None
    version: str | None = None
    user_agent: str | None = None

    # ---- Time zone ----
    is_ip_create_time_zone: bool | None = None
    time_zone: str | None = None
    time_zone_offset: int | None = None

    # ---- WebRTC — non-standard: "webRTC" not "webRtc" ----
    webrtc: str | None = Field(None, alias="webRTC")

    # ---- HTTPS / Geolocation ----
    ignore_https_errors: bool | None = None
    position: str | None = None
    is_ip_create_position: bool | None = None
    lat: str | None = None
    lng: str | None = None
    precision_data: str | None = None

    # ---- Language ----
    is_ip_create_language: bool | None = None
    languages: str | None = None
    is_ip_create_display_language: bool | None = None
    display_languages: str | None = None

    # ---- Window geometry ----
    open_width: int | None = None
    open_height: int | None = None
    resolution_type: str | None = None
    resolution: str | None = None
    window_size_limit: bool | None = None
    device_pixel_ratio: float | None = None

    # ---- Fonts ----
    font_type: str | None = None

    # ---- Canvas / WebGL — non-standard: "webGL*" not "webGl*" ----
    canvas: str | None = None
    webgl: str | None = Field(None, alias="webGL")
    webgl_meta: str | None = Field(None, alias="webGLMeta")
    webgl_manufacturer: str | None = Field(None, alias="webGLManufacturer")
    webgl_render: str | None = Field(None, alias="webGLRender")

    # ---- Media ----
    audio_context: str | None = None
    media_device: str | None = None
    speech_voices: str | None = None

    # ---- Hardware ----
    hardware_concurrency: str | None = None
    device_memory: str | None = None

    # ---- Misc fingerprint ----
    do_not_track: str | None = None
    client_rect_noise_enabled: bool | None = None
    port_scan_protect: str | None = None
    port_white_list: str | None = None

    # ---- Device info ----
    device_info_enabled: bool | None = None
    computer_name: str | None = None
    mac_addr: str | None = None

    # ---- Host IP — non-standard: "hostIP" not "hostIp" ----
    host_ip: str | None = Field(None, alias="hostIP")

    # ---- SSL / Plugins ----
    disable_ssl_cipher_suites_flag: bool | None = None
    disable_ssl_cipher_suites: Any | None = None
    enable_plugins: bool | None = None
    plugins: str | None = None

    # ---- Launch ----
    launch_args: str | None = None


# ---------------------------------------------------------------------------
# Primary resource
# ---------------------------------------------------------------------------


class Browser(BaseModel):
    """Represents a BitBrowser window / profile.

    This is both a **request** model (used when creating/updating) and a
    **response** model (returned by ``get`` / ``list``).

    Only *browser_finger_print* is required when creating a new window.
    Pass ``BrowserFingerPrint()`` to fully randomise the fingerprint.

    Attributes:
        id: Unique browser window ID (assigned by BitBrowser).
        name: Human-readable window name.
        group_id: Group this window belongs to.  If omitted on creation,
            BitBrowser places the window in the default "API" group.
        seq: Auto-incremented sequence number (read-only from the API).
        platform: Platform URL, e.g. ``"https://www.facebook.com"``.
        url: Extra URLs to open (comma-separated).
        remark: Free-text note / sequence label.
        user_name: Platform account username (auto-fill).
        password: Platform account password (auto-fill).
        fa_secret_key: 2FA TOTP secret key.
        cookie: Platform cookie JSON string.
        proxy_method: ``2`` custom proxy · ``3`` dynamic IP extraction.
        proxy_type: One of ``"noproxy"``, ``"http"``, ``"https"``,
            ``"socks5"``, ``"ssh"``.
        host: Proxy host.
        port: Proxy port.
        proxy_user_name: Proxy username.
        proxy_password: Proxy password.
        ip_check_service: IP lookup provider.
            ``"ip123in"`` (default) · ``"ip-api"`` · ``"luminati"``.
        is_ipv6: Whether the proxy uses IPv6.
        refresh_proxy_url: Proxy refresh URL (provided by proxy vendor).
        enable_socks5_udp: Enable UDP for socks5 proxies.
        country: Country code for dynamic-IP proxies.
        province: Province/state code for dynamic-IP proxies.
        city: City code for dynamic-IP proxies.
        dynamic_ip_url: Extraction URL (when *proxy_method* is ``3``).
        dynamic_ip_channel: Extraction vendor.
        is_dynamic_ip_change_ip: Re-extract IP on every open.
        duplicate_check: ``1`` check for duplicate IPs · ``0`` skip.
        is_global_proxy_info: Use global dynamic-proxy settings.
        workbench: New-tab page.  ``"localserver"`` (default) or
            ``"disable"``.
        abort_image: Block all image loading.
        abort_image_max_size: Block images larger than this (KB).
            Requires *abort_image* to be ``True``.
        abort_media: Prevent auto-playing videos.
        mute_audio: Mute the browser.
        stop_while_net_error: Abort launch on network failure.
        stop_while_ip_change: Abort launch if IP changes.
        stop_while_country_change: Abort launch if IP country changes.
        sync_tabs: Sync browser tabs (default ``True``).
        sync_cookies: Sync cookies (default ``True``).
        sync_indexed_db: Sync IndexedDB.
        sync_local_storage: Sync LocalStorage.
        sync_bookmarks: Sync bookmarks.
        sync_authorization: Sync saved passwords.
        credentials_enable_service: Suppress "save password" popups.
        sync_history: Sync browsing history.
        sync_extensions: Sync extension data.
        is_valid_username: Reject duplicate username/platform combos.
        allowed_signin: Allow Google sign-in within the browser.
        clear_cache_files_before_launch: Clear cache on open.
        clear_cache_without_extensions: Clear cache but keep extension data.
        clear_cookies_before_launch: Clear cookies on open.
        clear_histories_before_launch: Clear history on open.
        random_fingerprint: Re-randomise fingerprint on every open.
        disable_gpu: Disable GPU hardware acceleration.
        disable_translate_popup: Suppress Google Translate popups.
        disable_notifications: Suppress push-notification prompts.
        disable_clipboard: Block sites from reading the clipboard.
        memory_saver: Low-memory mode (may cause instability).
        is_syn_open: Multi-open policy.  ``1`` allow · ``0`` deny.
        browser_finger_print: Fingerprint configuration object.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        extra="allow",
    )

    # ---- Identity ----
    id: str | None = None
    name: str | None = None
    group_id: str | None = None
    seq: int | None = None

    # ---- URLs ----
    platform: str | None = None
    url: str | None = None
    remark: str | None = None

    # ---- Credentials ----
    user_name: str | None = None
    password: str | None = None
    fa_secret_key: str | None = None
    cookie: str | None = None

    # ---- Proxy ----
    proxy_method: int | None = None
    proxy_type: str | None = None
    host: str | None = None
    port: int | None = None
    proxy_user_name: str | None = None
    proxy_password: str | None = None
    ip_check_service: str | None = None
    is_ipv6: bool | None = None
    refresh_proxy_url: str | None = None
    enable_socks5_udp: bool | None = None
    country: str | None = None
    province: str | None = None
    city: str | None = None
    dynamic_ip_url: str | None = None
    dynamic_ip_channel: str | None = None
    is_dynamic_ip_change_ip: bool | None = None
    duplicate_check: int | None = None
    is_global_proxy_info: bool | None = None

    # ---- Behaviour ----
    workbench: str | None = None
    abort_image: bool | None = None
    abort_image_max_size: int | None = None
    abort_media: bool | None = None
    mute_audio: bool | None = None
    stop_while_net_error: bool | None = None
    stop_while_ip_change: bool | None = None
    stop_while_country_change: bool | None = None

    # ---- Sync ----
    sync_tabs: bool | None = None
    sync_cookies: bool | None = None
    sync_indexed_db: bool | None = None
    sync_local_storage: bool | None = None
    sync_bookmarks: bool | None = None
    sync_authorization: bool | None = None
    credentials_enable_service: bool | None = None
    sync_history: bool | None = None
    sync_extensions: bool | None = None

    # ---- Misc ----
    is_valid_username: bool | None = None
    allowed_signin: bool | None = None
    clear_cache_files_before_launch: bool | None = None
    clear_cache_without_extensions: bool | None = None
    clear_cookies_before_launch: bool | None = None
    clear_histories_before_launch: bool | None = None
    random_fingerprint: bool | None = None
    disable_gpu: bool | None = None
    disable_translate_popup: bool | None = None
    disable_notifications: bool | None = None
    disable_clipboard: bool | None = None
    memory_saver: bool | None = None
    is_syn_open: int | None = None

    # ---- Fingerprint ----
    browser_finger_print: BrowserFingerPrint | None = None


# ---------------------------------------------------------------------------
# Group models
# ---------------------------------------------------------------------------


class Group(BaseModel):
    """Represents a BitBrowser window group.

    Used for both request (create/update) and response (list/detail) contexts.

    Attributes:
        id: Unique group ID (assigned by BitBrowser, 32 chars).
        group_name: Human-readable name of the group.
        sort_num: Integer used for ordering groups in the UI.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        extra="ignore",
    )

    id: str | None = None
    group_name: str | None = None
    sort_num: int | None = None

    @field_validator("sort_num")
    @classmethod
    def _check_sort(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("sort_num must not be negative")
        return v


class ListGroupsResponse(BaseModel):
    """Paginated list of window groups.

    Attributes:
        groups: The groups on this page.
        total: Total number of groups.
        page: Zero-based page index that was requested.
        page_size: Number of items per page that was requested.
    """

    groups: list[Group]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Tag models
# ---------------------------------------------------------------------------


class Tag(BaseModel):
    """Represents a BitBrowser window tag (label).

    At most 20 tags may exist in total; each window may have at most 3 tags.

    Attributes:
        id: Unique tag ID (32 chars, assigned by BitBrowser).
        tag_name: Display name of the tag (max 50 characters).
        tag_color: Hex colour string in ``#rrggbb`` format, e.g.
            ``"#ECC2F3"``.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        extra="ignore",
    )

    id: str | None = None
    tag_name: str | None = None
    tag_color: str | None = None

    @field_validator("tag_name")
    @classmethod
    def _check_name(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 50:
            raise ValueError("tag_name must not exceed 50 characters")
        return v

    @field_validator("tag_color")
    @classmethod
    def _check_color(cls, v: str | None) -> str | None:
        if v is not None and not re.fullmatch(r"#[0-9a-fA-F]{6}", v):
            raise ValueError("tag_color must be in #rrggbb format")
        return v


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class OpenResult(BaseModel):
    """Result returned when a browser window is opened.

    Attributes:
        ws: WebSocket endpoint for Playwright / Puppeteer.
        http: HTTP debugging address (host:port).
        core_version: Chromium/Firefox core version string.
        driver: Absolute path to the matching chromedriver binary.
        seq: Window sequence number.
        name: Window name.
        remark: Window remark/note.
        group_id: Group the window belongs to.
        pid: OS process ID of the browser process.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        extra="ignore",
    )

    ws: str
    http: str
    core_version: str
    driver: str
    seq: int | None = None
    name: str | None = None
    remark: str | None = None
    group_id: str | None = None
    pid: int | None = None


class ListBrowsersResponse(BaseModel):
    """Paginated list of browser windows.

    Attributes:
        browsers: The browsers on this page.
        total: Total number of windows matching the query.
        page: Zero-based page index that was requested.
        page_size: Number of items per page that was requested.
    """

    browsers: list[Browser]
    total: int
    page: int
    page_size: int
