"""Install the browser release paired with camoufox==0.4.11 in uv.lock."""

from camoufox.addons import DefaultAddons, maybe_download_addons
from camoufox.locale import ALLOW_GEOIP, download_mmdb
from camoufox.pkgman import OS_NAME, CamoufoxFetcher, Version


class PinnedCamoufoxFetcher(CamoufoxFetcher):
    def fetch_latest(self) -> None:
        # 0.4.11's CLI cannot select a release. Override only release selection;
        # retain the package's extraction, permissions, and version metadata logic.
        self._version_obj = Version(version="135.0.1", release="beta.24")
        self._url = (
            "https://github.com/daijro/camoufox/releases/download/v135.0.1-beta.24/"
            f"camoufox-135.0.1-beta.24-{OS_NAME}.{self.arch}.zip"
        )


if __name__ == "__main__":
    PinnedCamoufoxFetcher().install()
    if ALLOW_GEOIP:
        download_mmdb()
    maybe_download_addons(list(DefaultAddons))
