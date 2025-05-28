from pydoll.protocol.commands import PageCommands


def test_set_download_path():
    path = '/path/to/download'
    expected_command = {
        'method': 'Page.setDownloadBehavior',
        'params': {
            'behavior': 'allow',
            'downloadPath': path,
        },
    }
    assert PageCommands.set_download_path(path) == expected_command


def test_screenshot_default():
    expected_command = {
        'method': 'Page.captureScreenshot',
        'params': {
            'format': 'jpeg',
            'quality': 100,
        },
    }
    assert PageCommands.screenshot() == expected_command


def test_screenshot_jpeg():
    expected_command = {
        'method': 'Page.captureScreenshot',
        'params': {
            'format': 'jpeg',
            'quality': 80,
        },
    }
    assert PageCommands.screenshot(fmt='jpeg', quality=80) == expected_command


def test_screenshot_png():
    expected_command = {
        'method': 'Page.captureScreenshot',
        'params': {
            'format': 'png',
            'quality': 100,
        },
    }
    assert PageCommands.screenshot(fmt='png') == expected_command


def test_screenshot_with_clip():
    clip = {
        'x': 10,
        'y': 20,
        'width': 30,
        'height': 40,
        'scale': 1,
    }
    expected_command = {
        'method': 'Page.captureScreenshot',
        'params': {
            'format': 'jpeg',
            'quality': 100,
            'clip': clip,
        },
    }
    assert PageCommands.screenshot(clip=clip) == expected_command


def test_go_to():
    url = 'https://example.com'
    expected_command = {
        'method': 'Page.navigate',
        'params': {
            'url': url,
        },
    }
    assert PageCommands.go_to(url) == expected_command


def test_refresh_default():
    expected_command = {
        'method': 'Page.reload',
        'params': {
            'ignoreCache': False,
        },
    }
    assert PageCommands.refresh() == expected_command


def test_refresh_ignore_cache():
    expected_command = {
        'method': 'Page.reload',
        'params': {
            'ignoreCache': True,
        },
    }
    assert PageCommands.refresh(ignore_cache=True) == expected_command


def test_print_to_pdf_default():
    expected_command = {
        'method': 'Page.printToPDF',
        'params': {
            'scale': 1,
            'paperWidth': 8.5,
            'paperHeight': 11,
        },
    }
    assert PageCommands.print_to_pdf() == expected_command


def test_print_to_pdf_custom():
    expected_command = {
        'method': 'Page.printToPDF',
        'params': {
            'scale': 2,
            'paperWidth': 5.5,
            'paperHeight': 8.5,
        },
    }
    assert (
        PageCommands.print_to_pdf(scale=2, paper_width=5.5, paper_height=8.5)
        == expected_command
    )


def test_enable_page():
    expected_command = {'method': 'Page.enable'}
    assert PageCommands.enable_page() == expected_command


def test_disable_page():
    expected_command = {'method': 'Page.disable'}
    assert PageCommands.disable_page() == expected_command


def test_enable_intercept_file_chooser_dialog():
    expected_command = {
        'method': 'Page.setInterceptFileChooserDialog',
        'params': {'enabled': True},
    }
    assert (
        PageCommands.set_intercept_file_chooser_dialog(True)
        == expected_command
    )


def test_disable_intercept_file_chooser_dialog():
    expected_command = {
        'method': 'Page.setInterceptFileChooserDialog',
        'params': {'enabled': False},
    }
    assert (
        PageCommands.set_intercept_file_chooser_dialog(False)
        == expected_command
    )
