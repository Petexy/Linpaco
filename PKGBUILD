# Maintainer: Petexy <https://github.com/Petexy>

pkgname=linpaco
pkgver=1.0.0.r
pkgrel=1
_currentdate=$(date +"%Y-%m-%d%H-%M-%S")
pkgdesc="Linexin's Package Converter Tool for .deb and .rpm files"
url='https://github.com/Petexy'
arch=(x86_64)
license=('GPL-3.0')
depends=(
  python-gobject
  gtk4
  libadwaita
  linexin-center
  wget
  libarchive
  binutils
  tar
)
makedepends=(
)

package() {
   mkdir -p ${pkgdir}/usr/share/linexin/widgets
   mkdir -p ${pkgdir}/usr/icons   
   cp -rf ${srcdir}/* ${pkgdir}/
}
