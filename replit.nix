{ pkgs }: {
  deps = [
    pkgs.zlib
    pkgs.lcms2
    pkgs.libjpeg
    pkgs.openjpeg
    pkgs.libimagequant
    pkgs.libpng
    pkgs.libwebp
    pkgs.tiff
    pkgs.freetype
    pkgs.python310Packages.pillow
  ];
}