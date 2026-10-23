# SPDX-License-Identifier: GPL-2.0-or-later
# Exact static codec packages for Blender's original ImBuf implementations.
# Included after Threads is resolved and before the static OIIO package.

foreach(_bw_codec_flag WITH_IMAGE_CINEON WITH_IMAGE_OPENJPEG WITH_IMAGE_WEBP)
  if(NOT ${_bw_codec_flag})
    message(FATAL_ERROR "browser codecs require ${_bw_codec_flag}=ON")
  endif()
endforeach()
unset(_bw_codec_flag)

# Blender's FindWebP module accepts incomplete component lists. Require every
# archive explicitly, including the HEIF/AOM chain used by unconditional AVIF.
foreach(_bw_codec_file
    lib/libwebp.a
    lib/libwebpmux.a
    lib/libwebpdemux.a
    lib/libsharpyuv.a
    lib/libopenjp2.a
    lib/libaom.a
    lib/libheif.a
    include/webp/decode.h
    include/openjpeg-2.5/openjpeg.h
    include/libheif/heif.h)
  if(NOT EXISTS "${LIBDIR}/${_bw_codec_file}" OR IS_DIRECTORY "${LIBDIR}/${_bw_codec_file}")
    message(FATAL_ERROR "Missing required wasm codec artifact: ${LIBDIR}/${_bw_codec_file}")
  endif()
endforeach()
unset(_bw_codec_file)

# OIIO 3.1.13.1's installed static config references optional codec targets but
# does not find them itself. Load only the selected wasm prefix, before OIIO.
set(WebP_DIR "${LIBDIR}/share/WebP/cmake")
set(OpenJPEG_DIR "${LIBDIR}/lib/cmake/openjpeg-2.5")
set(Libheif_DIR "${LIBDIR}/lib/cmake/libheif")
find_package(WebP CONFIG REQUIRED PATHS "${WebP_DIR}" NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH)
find_package(OpenJPEG CONFIG REQUIRED PATHS "${OpenJPEG_DIR}" NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH)
find_package(Libheif CONFIG REQUIRED PATHS "${Libheif_DIR}" NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH)
foreach(_bw_codec_target WebP::webp WebP::webpdemux WebP::libwebpmux WebP::sharpyuv openjp2 heif)
  if(NOT TARGET ${_bw_codec_target})
    message(FATAL_ERROR "Missing required wasm codec target: ${_bw_codec_target}")
  endif()
endforeach()
unset(_bw_codec_target)

# Populate the unchanged Blender Find modules and dependency_targets.cmake.
set(WEBP_INCLUDE_DIR "${LIBDIR}/include")
set(WEBP_WEBP_LIBRARY "${LIBDIR}/lib/libwebp.a")
set(WEBP_WEBPMUX_LIBRARY "${LIBDIR}/lib/libwebpmux.a")
set(WEBP_WEBPDEMUX_LIBRARY "${LIBDIR}/lib/libwebpdemux.a")
set(WEBP_SHARPYUV_LIBRARY "${LIBDIR}/lib/libsharpyuv.a")
find_package(WebP MODULE REQUIRED)
set(OPENJPEG_INCLUDE_DIR "${LIBDIR}/include/openjpeg-2.5")
set(OPENJPEG_LIBRARY "${LIBDIR}/lib/libopenjp2.a")
find_package(OpenJPEG MODULE REQUIRED)
