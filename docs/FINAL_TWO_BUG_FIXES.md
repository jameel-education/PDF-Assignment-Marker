# Final two bug fixes — 2026-11-02

Version: 11.0.0

1. Windows title: removed leftover “UI Trial” text from the visible window title in the prior title-fix baseline.
2. Document 2 in Single View: tool settings use Document 2’s visible viewport for positioning beside the marking ribbon. Document 1 and Split View positioning logic is unchanged.

No marking tools, PDF operations, approved header layout, About text, or other functionality intentionally changed.

## Required Windows regression check

Build using `build_windows.bat` from a fresh extracted folder. Start the executable, verify the title and About v11.0.0, open both PDFs and test a double-click on the upper and lower tool icons in: (1) Document 1 Single View, (2) Document 2 Single View, (3) Split View with either PDF active. Check settings beside the corresponding tool, window edges, and the red X close control. Confirm Save and Save As still work. Build final installer only after these pass.
