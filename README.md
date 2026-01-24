<div align="center">
  <img src="src/usr/share/icons/linpaco.svg" alt="Linpaco Icon" width="128" height="128">

  # Linpaco - Linexin Package Converter

  **Seamlessly convert Debian and RPM packages to Arch Linux packages**
</div>

---

## 🚀 Overview

**Linpaco** is a powerful and elegant widget designed for **Linexin** that simplifies the process of installing software from other distributions on Arch Linux. It provides a user-friendly interface to convert `.deb` (Debian/Ubuntu) and `.rpm` (Fedora/RHEL/OpenSUSE) packages into Arch Linux compatible packages (`PKGBUILD`) and supports installing them directly.

Built with **GTK4** and **Libadwaita**, it offers a modern, native experience that fits perfectly with the GNOME desktop environment.

## ✨ Features

-   **📦 Universal Conversion**: effortlessly convert `.deb` and `.rpm` packages to Arch Linux packages.
-   **🖱️ Drag & Drop**: Simply drag your package file onto the window to start.
-   **🛠️ Custom Options**:
    -   **Install Automatically**: Choose to install the package immediately after conversion.
    -   **Dependency Handling**: Option to ignore strict dependency checks for "dumb" conversions (useful for simple binaries).
-   **🌍 Localization**: Fully localized in **12 languages** including English, German, Spanish, French, Polish, Portuguese, Russian, and Chinese.

## 🔧 Requirements

To run this widget on Arch Linux, ensure you have the following dependencies installed:

```bash
sudo pacman -S python gtk4 libadwaita python-gobject binutils tar libarchive pacman rpm-tools xdg-utils linexin-center
```

## 🌐 Supported Languages

Linpaco is available in:
-   🇺🇸 English (en_US)
-   🇩🇪 German (de_DE)
-   🇪🇸 Spanish (es_ES)
-   🇫🇷 French (fr_FR)
-   🇮🇳 Hindi (hi_IN)
-   🇵🇱 Polish (pl_PL)
-   🇧🇷 Portuguese (Brazil) (pt_BR)
-   🇵🇹 Portuguese (Portugal) (pt_PT)
-   🇷🇺 Russian (ru_RU)
-   🇨🇳 Chinese (Simplified) (zh_CN)
-   🇨🇳 Chinese (Variant) (zn_CH/zn_CN)

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve the converter or add new translations.

---

