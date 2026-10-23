# KMCR GitHub Profile setup

This starter bundle contains an original KMCR-styled terminal header and GitHub Actions automations for a looping blue contribution snake and an isometric 3D contribution calendar.

## 1. Create your profile repo

On GitHub, create a **public** repository named exactly `KMCR41207` in the `KMCR41207` account and initialize it with `README.md`. The resulting repository must be `KMCR41207/KMCR41207`.

## 2. Upload the starter files

On the new repository, choose **Add file → Upload files**, drag the contents of this folder, and commit on the default branch. Some browser upload UIs do not reliably preserve dotfolders; in that case, create the three workflow files individually using **Add file → Create new file** and paste the contents with their full paths from `.github/workflows/`.

Or clone the profile repository, copy these files into it, and push the files. Do not accidentally create a nested `KMCR41207-profile-starter/` folder inside the profile repo; the README must stay at repository root.

## 3. Enable Actions to write to your repository

In repository **Settings → Actions → General → Workflow permissions**, enable **Read and write permissions** if available. Each workflow also declares `contents: write`.

## 4. Generate the images once

Visit **Actions**, enable Actions if prompted, then run each of:

- `Update terminal profile`
- `Update 3D contributions`
- `Update contribution snake`

Select **Run workflow → Run workflow**. After a successful run and the automatically generated SVG files are committed, refresh your public GitHub profile page.

## 5. Automatic update

The terminal profile, 3D contribution calendar, and contribution snake refresh daily at different UTC times to avoid overlapping commits. GitHub may delay or skip scheduled executions, especially on inactive repositories; if needed, trigger a manual run.

## Notes

- Snake is an **auto-playing SVG animation**, not a controllable game. SVG animation normally repeats in browsers; GitHub rendering may differ across clients.
- Snake colors use Racing Blue `#245BDB`, with GitHub dark-mode contribution colors.
- 3D color and style can be switched in `README.md` by replacing `profile-night-view.svg` with `profile-gitblock.svg` or another generated variant.
- Public GitHub stats come from GitHub's public API. Counts are placeholders (dashes) if the API is temporarily unavailable.
- The ASCII-style KMCR wordmark replaces the other profile's personal photo ASCII portrait. You can later generate an ASCII-art portrait from a photo you own, then customize `scripts/generate_terminal.py`.
- Built with Python standard library; no npm or additional pip packages required.

## Sources

- Platane/snk: https://github.com/Platane/snk
- github-profile-3d-contrib: https://github.com/yoshi389111/github-profile-3d-contrib
