// SPDX-License-Identifier: GPL-2.0-or-later
// Standalone dependency diagnostic. This is not an original Blender test.
#include <algorithm>
#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <webp/decode.h>
#include <webp/encode.h>
#include <openjpeg.h>
#include <libheif/heif.h>
#include <aom/aom_codec.h>

static constexpr int width = 64;
static constexpr int height = 64;

static void require(bool condition, const char *message)
{
  if (!condition) {
    std::fprintf(stderr, "codec dependency probe failed: %s\n", message);
    std::exit(2);
  }
}

static void heif_ok(heif_error error, const char *operation)
{
  if (error.code != heif_error_Ok) {
    std::fprintf(stderr, "%s: %s (%d/%d)\n", operation, error.message,
                 int(error.code), int(error.subcode));
    std::exit(3);
  }
}

static std::vector<unsigned char> pixels()
{
  const std::array<std::array<unsigned char, 4>, 4> colors = {{
      {{255, 0, 0, 255}}, {{0, 255, 0, 255}},
      {{0, 0, 255, 128}}, {{255, 255, 255, 64}}}};
  std::vector<unsigned char> result(width * height * 4);
  for (int y = 0; y < height; ++y) {
    for (int x = 0; x < width; ++x) {
      const auto &color = colors[(y >= height / 2 ? 2 : 0) + (x >= width / 2 ? 1 : 0)];
      std::copy(color.begin(), color.end(), result.begin() + (y * width + x) * 4);
    }
  }
  return result;
}

static void webp_probe(const std::vector<unsigned char> &input)
{
  uint8_t *compressed = nullptr;
  const size_t size = WebPEncodeLosslessRGBA(input.data(), width, height, width * 4, &compressed);
  require(size > 0 && compressed, "WebP lossless encode");
  int decoded_width = 0, decoded_height = 0;
  uint8_t *decoded = WebPDecodeRGBA(compressed, size, &decoded_width, &decoded_height);
  require(decoded && decoded_width == width && decoded_height == height, "WebP decode dimensions");
  require(std::memcmp(decoded, input.data(), input.size()) == 0, "WebP exact RGBA roundtrip");
  WebPFree(decoded);
  WebPFree(compressed);
  std::printf("{\"codec\":\"webp\",\"encoded_bytes\":%zu,\"max_channel_error\":0}\n", size);
}

static void jpeg2000_probe(const std::vector<unsigned char> &input)
{
  require(opj_has_thread_support(), "OpenJPEG pthread backend");
  std::array<opj_image_cmptparm_t, 4> components{};
  for (auto &component : components) {
    component.dx = component.dy = 1;
    component.w = width;
    component.h = height;
    component.prec = 8;
  }
  opj_image_t *image = opj_image_create(4, components.data(), OPJ_CLRSPC_SRGB);
  require(image, "OpenJPEG allocate image");
  image->x1 = width;
  image->y1 = height;
  image->comps[3].alpha = 1;
  for (int i = 0; i < width * height; ++i) {
    for (int c = 0; c < 4; ++c) {
      image->comps[c].data[i] = input[i * 4 + c];
    }
  }
  opj_cparameters_t options;
  opj_set_default_encoder_parameters(&options);
  options.tcp_numlayers = 1;
  options.tcp_rates[0] = 0;
  options.cp_disto_alloc = 1;
  options.irreversible = 0;
  opj_codec_t *encoder = opj_create_compress(OPJ_CODEC_JP2);
  require(encoder && opj_setup_encoder(encoder, &options, image), "OpenJPEG setup encoder");
  require(opj_codec_set_threads(encoder, 1), "OpenJPEG encoder thread setup");
  opj_stream_t *stream = opj_stream_create_default_file_stream("probe.jp2", OPJ_FALSE);
  require(stream && opj_start_compress(encoder, image, stream) &&
              opj_encode(encoder, stream) && opj_end_compress(encoder, stream),
          "OpenJPEG original lossless encoder");
  opj_stream_destroy(stream);
  opj_destroy_codec(encoder);
  opj_image_destroy(image);

  opj_dparameters_t decode_options;
  opj_set_default_decoder_parameters(&decode_options);
  opj_codec_t *decoder = opj_create_decompress(OPJ_CODEC_JP2);
  require(decoder && opj_setup_decoder(decoder, &decode_options), "OpenJPEG setup decoder");
  stream = opj_stream_create_default_file_stream("probe.jp2", OPJ_TRUE);
  opj_image_t *decoded = nullptr;
  require(stream && opj_read_header(stream, decoder, &decoded) &&
              opj_decode(decoder, stream, decoded) && opj_end_decompress(decoder, stream),
          "OpenJPEG original decoder");
  require(decoded && decoded->numcomps == 4 && decoded->x1 == width && decoded->y1 == height,
          "OpenJPEG decoded dimensions");
  for (int i = 0; i < width * height; ++i) {
    for (int c = 0; c < 4; ++c) {
      require(decoded->comps[c].data[i] == input[i * 4 + c], "OpenJPEG exact RGBA roundtrip");
    }
  }
  opj_stream_destroy(stream);
  opj_destroy_codec(decoder);
  opj_image_destroy(decoded);
  std::printf("{\"codec\":\"jpeg2000\",\"max_channel_error\":0}\n");
}

static void avif_probe(const std::vector<unsigned char> &input)
{
  heif_ok(heif_init(nullptr), "libheif init");
  require(heif_have_encoder_for_format(heif_compression_AV1), "static AV1 encoder");
  require(heif_have_decoder_for_format(heif_compression_AV1), "static AV1 decoder");
  heif_context *context = heif_context_alloc();
  require(context, "libheif context");
  heif_encoder *encoder = nullptr;
  heif_ok(heif_context_get_encoder_for_format(context, heif_compression_AV1, &encoder), "AV1 encoder");
  heif_ok(heif_encoder_set_lossless(encoder, 1), "AV1 lossless mode");
  // Keep this standalone resource diagnostic bounded. Blender's original test
  // configuration is not changed by this probe.
  heif_ok(heif_encoder_set_parameter_integer(encoder, "threads", 1), "AV1 probe thread limit");
  heif_image *image = nullptr;
  heif_ok(heif_image_create(width, height, heif_colorspace_RGB, heif_chroma_interleaved_RGBA, &image), "AV1 image");
  heif_ok(heif_image_add_plane(image, heif_channel_interleaved, width, height, 8), "AV1 image plane");
  int stride = 0;
  unsigned char *plane = heif_image_get_plane(image, heif_channel_interleaved, &stride);
  require(plane && stride >= width * 4, "AV1 writable RGBA plane");
  for (int y = 0; y < height; ++y) {
    std::memcpy(plane + y * stride, input.data() + y * width * 4, width * 4);
  }
  heif_image_handle *encoded = nullptr;
  heif_ok(heif_context_encode_image(context, image, encoder, nullptr, &encoded), "AV1 encode");
  heif_ok(heif_context_write_to_file(context, "probe.avif"), "AVIF container write");
  heif_image_handle_release(encoded);
  heif_image_release(image);
  heif_encoder_release(encoder);
  heif_context_free(context);

  context = heif_context_alloc();
  heif_ok(heif_context_read_from_file(context, "probe.avif", nullptr), "AVIF container read");
  heif_image_handle *handle = nullptr;
  heif_ok(heif_context_get_primary_image_handle(context, &handle), "AVIF primary image");
  require(heif_image_handle_get_width(handle) == width && heif_image_handle_get_height(handle) == height,
          "AVIF decoded dimensions");
  heif_image *decoded = nullptr;
  heif_ok(heif_decode_image(handle, &decoded, heif_colorspace_RGB, heif_chroma_interleaved_RGBA, nullptr), "AV1 decode");
  const unsigned char *result = heif_image_get_plane_readonly(decoded, heif_channel_interleaved, &stride);
  require(result && stride >= width * 4, "AVIF readable RGBA plane");
  int maximum = 0;
  for (int y = 0; y < height; ++y) {
    for (int x = 0; x < width * 4; ++x) {
      maximum = std::max(maximum, std::abs(int(result[y * stride + x]) - int(input[y * width * 4 + x])));
    }
  }
  std::printf("{\"codec\":\"avif\",\"max_channel_error\":%d}\n", maximum);
  // Report the observed color error. Exact Blender/OIIO color handling and its
  // original tolerance are assessed only by the unchanged Blender test suite.
  heif_image_release(decoded);
  heif_image_handle_release(handle);
  heif_context_free(context);
  heif_deinit();
}

int main()
{
  std::printf("{\"scope\":\"standalone-wasm-codec-diagnostic\",\"webp_version\":%d,"
              "\"openjpeg_version\":\"%s\",\"aom_version\":\"%s\",\"libheif_version\":\"%s\"}\n",
              WebPGetEncoderVersion(), opj_version(), aom_codec_version_str(), heif_get_version());
  const auto input = pixels();
  webp_probe(input);
  jpeg2000_probe(input);
  avif_probe(input);
  std::printf("{\"dependency_runtime_diagnostic\":\"passed\",\"blender_cases_executed\":0}\n");
  return 0;
}
