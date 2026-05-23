"""Pure-logic tests for the page-bundle helpers (no browser, no I/O).

These functions transform the resource tree and rewrite asset URLs for the
offline ``save_bundle`` zip. The end-to-end behaviour is covered by the
real-Chrome suite; here we pin the branchy edge cases of the pure helpers:
which resources are skipped, how filenames are derived, and how data-URI /
unknown URLs are left untouched while known ones are rewritten or inlined.
"""

from __future__ import annotations

from pydoll.protocol.cdp.network.types import ResourceType
from pydoll.utils.bundle import (
    build_asset_filename,
    collect_frame_resources,
    filter_fetchable_resources,
    inline_css_urls,
    rewrite_css_urls,
)


def _res(url, rtype=ResourceType.STYLESHEET, mime='text/css', **extra):
    return {'url': url, 'type': rtype, 'mimeType': mime, **extra}


def test_filter_skips_failed_canceled_data_uri_page_and_nonbundleable():
    page_url = 'http://x/'
    resources = [
        ('f', _res('http://x/a.css')),
        ('f', _res('http://x/b.css', failed=True)),
        ('f', _res('http://x/c.css', canceled=True)),
        ('f', _res('data:image/png;base64,AA', ResourceType.IMAGE, 'image/png')),
        ('f', _res(page_url, ResourceType.DOCUMENT, 'text/html')),
        ('f', _res('http://x/data.json', ResourceType.XHR, 'application/json')),
    ]
    kept = [res['url'] for _fid, res in filter_fetchable_resources(resources, page_url)]
    assert kept == ['http://x/a.css']


def test_collect_frame_resources_recurses_into_child_frames():
    tree = {
        'frame': {'id': 'root'},
        'resources': [_res('http://x/a.css')],
        'childFrames': [
            {
                'frame': {'id': 'child'},
                'resources': [_res('http://x/b.js', ResourceType.SCRIPT, 'text/javascript')],
            }
        ],
    }
    assert sorted(fid for fid, _res_ in collect_frame_resources(tree)) == ['child', 'root']


def test_build_asset_filename_derives_basename_and_extension():
    assert build_asset_filename('http://x', 'text/css', 0).endswith('resource.css')
    assert build_asset_filename('http://x/style', 'text/css', 1).endswith('style.css')
    assert build_asset_filename('http://x/a.png', 'image/png', 2).endswith('a.png')


def test_rewrite_css_urls_skips_data_uri_and_unknown_rewrites_known():
    css = (
        'a{background:url("data:image/png;base64,AA")}'
        'b{background:url("http://x/unknown.png")}'
        'c{background:url("http://x/known.png")}'
    )
    asset_map = {'http://x/known.png': ('0000_known.png', b'', 'image/png', ResourceType.IMAGE)}
    result = rewrite_css_urls(css, 'http://x/style.css', asset_map)
    assert 'data:image/png;base64,AA' in result
    assert 'http://x/unknown.png' in result
    assert 'url("0000_known.png")' in result


def test_inline_css_urls_skips_data_uri_and_unknown_inlines_known():
    css = (
        'a{background:url("data:image/png;base64,AA")}'
        'b{background:url("http://x/unknown.png")}'
        'c{background:url("http://x/known.png")}'
    )
    asset_map = {'http://x/known.png': ('f', b'\x89PNG', 'image/png', ResourceType.IMAGE)}
    result = inline_css_urls(css, 'http://x/style.css', asset_map)
    assert 'data:image/png;base64,AA' in result
    assert 'http://x/unknown.png' in result
    assert 'url("data:image/png;base64,' in result
