#!/usr/bin/env bash
# Install the api-flow-map pre-push gate into a repository.
#
#   tools/install-hook.sh            # into the repo you are standing in
#   tools/install-hook.sh ~/work/orders-service
#
# Uses core.hooksPath when the repo already has a hooks directory under version
# control (so the hook travels with a clone), and .git/hooks otherwise.
#
# It APPENDS rather than replaces: a repo may already have a pre-push, and
# clobbering somebody's existing guard to install your own is a bad trade.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/pre-push"
TARGET_REPO="${1:-$PWD}"

cd "$TARGET_REPO"
root="$(git rev-parse --show-toplevel)"
cd "$root"

hooks_path="$(git config --get core.hooksPath || true)"
if [ -n "$hooks_path" ]; then
  dest_dir="$root/$hooks_path"
else
  dest_dir="$root/.git/hooks"
fi
mkdir -p "$dest_dir"
dest="$dest_dir/pre-push"

if [ -f "$dest" ] && ! grep -q "api-flow-map as a pre-push gate" "$dest"; then
  echo "!! $dest already exists and is not ours."
  echo "   Add this line to it yourself rather than letting me overwrite it:"
  echo ""
  echo "       \"$SRC\" \"\$@\" || exit \$?"
  echo ""
  exit 3
fi

cp "$SRC" "$dest"
chmod +x "$dest"
echo "installed: $dest"
echo ""
echo "  blocks a push when API risk reaches 'high'."
echo "  tune with   APIFLOW_FAIL_ON=medium git push"
echo "  skip once with   git push --no-verify"
