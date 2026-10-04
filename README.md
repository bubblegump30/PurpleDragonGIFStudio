# Purple Dragon GIF Studio — v0.6.1

A black-and-purple desktop GIF editor with a single, readable workspace.

[Download v0.6.1](https://github.com/bubblegump30/PurpleDragonGIFStudio/raw/refs/heads/main/downloads/PurpleDragonGIFStudio-v0.6.1.zip) · [Donate via PayPal](https://www.paypal.com/paypalme/KyleAustin85)

## Start on Windows

Extract the ZIP, then double-click **Start-GIF-Studio.bat**. Install Python 3.11 or newer with the Python launcher if needed. First launch downloads the dependencies, so internet access is required during setup.

## One workspace

- **Editor & Preview:** Import video, GIFs, or still images. Video start and duration appear inline. View a large animated preview, add captions and color effects, reverse or ping-pong animation, and apply moving flames. Every action button has a text label.
- **Find Online GIFs:** Search Wikimedia Commons without a key, or GIPHY with your own API key. Scroll through thumbnail results, preview the selected animation, and import it directly into the editor. Direct HTTPS GIF URLs are also supported. Results remain available when switching tabs.
- **Output Settings:** Set width, FPS, playback speed, palette size, and looping. Width and video FPS apply during import; reimport to change them. GIF frame timing is preserved. Native file-open and save dialogs are the only separate workflow windows.

Click **Apply Changes** after editing effects. **Export GIF** renders the current effect settings. Ctrl+O imports still images; Ctrl+S exports.

## Flame options

Six animated styles: Campfire, Inferno, Torch jets, Wispy fire, Ember storm, and Smoke and fire. Eight color choices: Orange, Crimson, Gold, Blue, Cyan, Purple, Green, and Rainbow. Adjust intensity and placement inside the editor.

Output widths up to 3840 pixels are supported. Flame simulation runs at up to 1536 pixels on its longest side and is resized to the output; it is procedural fire, not filmed footage. GIF palettes are limited to 256 colors. Large output sizes require short clips; a 96-million-pixel processing budget and 300-frame cap limit memory use.

## Notes

Online availability depends on the provider. Respect the source GIF's licensing and attribution; use **Open Source Page** to review its origin. Enable **Remember API key**, then click **Save API Key** to keep your GIPHY key between launches. Search also saves the current key when Remember is enabled. Saved keys use Windows DPAPI encryption tied to your Windows account, in `%LOCALAPPDATA%/PurpleDragonGIFStudio/giphy-key.dpapi`. Unchecking Remember deletes the stored key while keeping the current session key. **Forget Saved Key** deletes it and clears the field. Keys stay masked, and are never included in the distribution ZIP. Secure saving requires Windows; other platforms can use a session-only key.

The launcher creates a local virtual environment. Manual setup: `python -m pip install -r requirements.txt`, then `python app.py`. Pillow, NumPy, and imageio-ffmpeg are required.

## Fonts, emojis, and larger searches

Caption styles include Sans, Bold, Serif, Monospace, Handwritten, and Impact. Windows fonts are used when installed; unavailable presets fall back to an available font. Choose Custom Font supports TTF/OTF files; Use Selected Font Style switches back to the preset. Caption size is a percentage of image width. Use the emoji buttons or paste text into Caption, then Apply Changes. Emoji fallback uses Segoe UI Emoji on Windows; exported emoji are monochrome and unsupported glyphs depend on installed font coverage. Custom fonts must remain accessible for later exports.

Search now requests 50 results per page. Load More (50) appends another page while retaining earlier results. Available counts depend on the provider and search term. Change a query or provider and run Search to start a fresh result list.

## Creator and support

Created by **Purple Dragon Foundation Ltd**. The Output Settings tab includes clickable buttons for our [website](https://www.purpledragonfoundationltd.xyz/), [GitHub](https://github.com/bubblegump30), and optional [PayPal donations](https://www.paypal.com/paypalme/KyleAustin85).
