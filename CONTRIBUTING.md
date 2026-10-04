# Contributing to Purple Dragon GIF Studio

Created by Purple Dragon Foundation Ltd. Thank you for helping improve the project.

## Before opening an issue

Search existing issues. For bugs, use the bug report template and include the app version, Windows version, reproduction steps, expected behavior, and actual behavior. Screenshots and minimal sample media help, but share only files you have permission to distribute. Remove API keys and personal information.

Suggest focused improvements with a clear use case. Follow our [Code of Conduct](CODE_OF_CONDUCT.md). Report vulnerabilities using [SECURITY.md](SECURITY.md), rather than public bug reports.

## Development

1. Fork the repository and create a branch for your change.
2. Install Python 3.11 or newer and create a virtual environment.
3. Install dependencies with `python -m pip install -r requirements.txt`.
4. Run `python app.py`.
5. Keep changes focused and update relevant documentation.

Preserve the readable single-window workflow. Keep Tk operations on the UI thread and expensive processing off it. Do not embed API keys or weaken credential protection. Do not commit virtual environments, cache files, downloaded personal media, or saved credentials.

## Validation

Run `python -m py_compile app.py captions.py credentials.py engine.py flames.py gallery.py online.py`.

Check the affected workflow with representative media. For UI changes, check labels, keyboard access, scrolling, and the minimum window size. For rendering or export changes, open the resulting GIF and check animation timing, looping, and image quality. For saved-key changes, verify save, restart, replacement, and deletion on Windows.

Compilation alone is not enough to verify behavior. Include checks performed, results, and platform limitations in the pull request.

## Pull requests

Explain the problem, resulting behavior, and validation. Link related issues when relevant. Do not change version numbers or distribution ZIPs unless the change requires release work. Maintainers review contributions before merging.

The source is licensed under MIT. Submit only code and assets you have permission to contribute. Third-party media, fonts, and provider services retain their own licenses and terms.
