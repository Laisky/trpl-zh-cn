#!/usr/bin/env bash
# render-book.sh renders the committed source to the requested local output directory.
# Input: optional output path, BOOK_RUNTIME_DIR for cache reuse. Output: HTML and PDF.
set -euo pipefail
book_source=$(cd -- "$(dirname -- "$0")/../.." && pwd)
book_head=$(git -C "$book_source" rev-parse HEAD)
book_output=$(realpath -m "${1:-$book_source/book}")
task_runtime="${BOOK_RUNTIME_DIR:-}"
if [ -z "$task_runtime" ]; then
  task_runtime=$(mktemp -d /tmp/book-release-runtime.XXXXXX)
fi
mkdir -p "$task_runtime/tools" "$task_runtime/fonts" "$task_runtime/cache" "$book_output"
tools="$task_runtime/tools"
if [ ! -f "$tools/mdbook-v0.4.14-x86_64-unknown-linux-gnu.tar.gz" ]; then
  curl -fL --connect-timeout 20 --max-time 180 \
    https://github.com/rust-lang/mdBook/releases/download/v0.4.14/mdbook-v0.4.14-x86_64-unknown-linux-gnu.tar.gz \
    -o "$tools/mdbook-v0.4.14-x86_64-unknown-linux-gnu.tar.gz"
fi
printf '%s  %s\n' 0ed75f6e4115f02d806932c4b1a8d9aca276ea1bbc3979524b4a8847bd3510e4 "$tools/mdbook-v0.4.14-x86_64-unknown-linux-gnu.tar.gz" | sha256sum -c -
tar -xzf "$tools/mdbook-v0.4.14-x86_64-unknown-linux-gnu.tar.gz" -C "$tools"
if [ ! -f "$tools/mdbook-latex-pdf" ]; then
  curl -fL --connect-timeout 20 --max-time 180 \
    https://github.com/KaiserY/mdbook-latex-pdf/releases/download/0.1.0/mdbook-latex-pdf-x86_64-unknown-linux-gnu \
    -o "$tools/mdbook-latex-pdf"
fi
printf '%s  %s\n' b82a19f253b466d7c52b8dd51ed7cb8606dd87f6f2583b21e90f0c3a1ab584af "$tools/mdbook-latex-pdf" | sha256sum -c -
chmod u+x "$tools/mdbook" "$tools/mdbook-latex-pdf"
font_commit=f8d157532fbfaeda587e826d4cd5b21a49186f7c
for language in SC KR; do
  font="$task_runtime/fonts/NotoSans$language-Regular.otf"
  if [ ! -f "$font" ]; then
    curl -fL --connect-timeout 20 --max-time 180 \
      "https://raw.githubusercontent.com/notofonts/noto-cjk/$font_commit/Sans/SubsetOTF/$language/NotoSans$language-Regular.otf" \
      -o "$font"
  fi
done
printf '%s  %s\n' faa6c9df652116dde789d351359f3d7e5d2285a2b2a1f04a2d7244df706d5ea9 "$task_runtime/fonts/NotoSansSC-Regular.otf" | sha256sum -c -
printf '%s  %s\n' 69975a0ac8472717870aefeab0a4d52739308d90856b9955313b2ad5e0148d68 "$task_runtime/fonts/NotoSansKR-Regular.otf" | sha256sum -c -
clean_source="$task_runtime/source-$book_head"
mkdir -p "$clean_source"
git -C "$book_source" archive "$book_head" | tar -x -C "$clean_source"
timeout 900 docker run --rm --init --cpuset-cpus 0,1 --memory 3g \
  -v "$clean_source:/workspace:ro" -v "$tools:/tools:ro" \
  -v "$book_output:/render" -v "$task_runtime/cache:/root/.cache" \
  -v "$task_runtime/fonts:/task-fonts:ro" -w /workspace ubuntu:20.04 bash -c '
    set -e
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends ca-certificates libicu66 libssl1.1 \
      libfontconfig1 libfreetype6 libgraphite2-3 libpng16-16 fontconfig \
      fonts-noto-core fonts-noto-mono python3-pip python3-pkg-resources
    python3 -m pip install --no-cache-dir --no-deps --target /opt/task-pygments Pygments==2.19.2
    export PYTHONPATH=/opt/task-pygments
    export PATH=/opt/task-pygments/bin:/tools:$PATH
    mkdir -p /root/.local/share/fonts
    cp /task-fonts/*.otf /root/.local/share/fonts/
    fc-cache -f
    pygmentize -V
    mdbook --version
    mdbook build --dest-dir /render
  '
