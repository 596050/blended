// Standalone diagnostic only. No original Blender test or decoder is replaced.
#include <OpenImageIO/filesystem.h>
#include <OpenImageIO/imageio.h>
#include <OpenImageIO/oiioversion.h>

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <exception>
#include <fstream>
#include <iterator>
#include <memory>
#include <string>
#include <thread>
#include <typeinfo>
#include <vector>

namespace {
const char *last_stage = "main_entry";

std::string quote(const std::string &text)
{
  const char *hex = "0123456789abcdef";
  std::string result = "\"";
  for (unsigned char byte : text) {
    if (byte == '\\' || byte == '"') {
      result += '\\';
      result += char(byte);
    }
    else if (byte < 32 || byte >= 127) {
      result += "\\u00";
      result += hex[byte >> 4];
      result += hex[byte & 15];
    }
    else {
      result += char(byte);
    }
  }
  return result + "\"";
}

void event(const char *kind, const std::string &detail = "{}")
{
  std::printf("DPX_STANDALONE_DIAGNOSTIC:{\"kind\":%s,\"stage\":%s,\"detail\":%s,\"qualification_credit\":0}\n",
              quote(kind).c_str(), quote(last_stage).c_str(), detail.c_str());
  std::fflush(stdout);
}

void stage(const char *value)
{
  last_stage = value;
  event("stage");
}

int backend_false(OIIO::ImageInput *input)
{
  event("backend_returned_false", "{\"error\":" + quote(input ? input->geterror() : OIIO::geterror()) + "}");
  return 2;
}

void observe_dpx_header(const std::vector<unsigned char> &encoded)
{
  if (encoded.size() < 816) {
    event("input_header_observation", "{\"complete_first_element_fields\":false}");
    return;
  }
  const std::string magic(encoded.begin(), encoded.begin() + 4);
  if (magic != "SDPX" && magic != "XPDS") {
    event("input_header_observation", "{\"known_endian_magic\":false,\"magic\":" + quote(magic) + "}");
    return;
  }
  const bool little = magic == "XPDS";
  auto integer = [&](size_t offset, size_t width) {
    uint32_t value = 0;
    for (size_t index = 0; index < width; ++index) {
      const size_t shift = 8 * (little ? index : width - 1 - index);
      value |= uint32_t(encoded[offset + index]) << shift;
    }
    return value;
  };
  // Offsets derive from the retained original DPXHeader.h fixed-layout fields.
  event("input_header_observation", "{\"magic\":" + quote(magic) +
        ",\"user_size\":" + std::to_string(integer(32, 4)) +
        ",\"orientation\":" + std::to_string(integer(768, 2)) +
        ",\"element_count\":" + std::to_string(integer(770, 2)) +
        ",\"width\":" + std::to_string(integer(772, 4)) +
        ",\"height\":" + std::to_string(integer(776, 4)) +
        ",\"descriptor\":" + std::to_string(encoded[800]) +
        ",\"transfer\":" + std::to_string(encoded[801]) +
        ",\"bit_depth\":" + std::to_string(encoded[803]) +
        ",\"packing\":" + std::to_string(integer(804, 2)) +
        ",\"encoding\":" + std::to_string(integer(806, 2)) +
        ",\"data_offset\":" + std::to_string(integer(808, 4)) +
        ",\"end_line_padding\":" + std::to_string(integer(812, 4)) + "}");
}

int execute(int argc, char **argv)
{
  if (argc != 4 || (std::string(argv[1]) != "memory" && std::string(argv[1]) != "file")) {
    event("diagnostic_invocation_error", "{\"expected\":\"memory|file INPUT OUTPUT\"}");
    return 2;
  }
  const std::string route = argv[1], input_path = argv[2], output_path = argv[3];
  event("standalone_identity", "{\"oiio_headers\":" + quote(OIIO_VERSION_STRING) +
        ",\"route\":" + quote(route) + ",\"input_path\":" + quote(input_path) +
        ",\"hardware_concurrency\":" + std::to_string(std::thread::hardware_concurrency()) +
        ",\"input_is_regenerated_native_data\":true,\"original_blender_test_cases\":0}");

  stage("read_input_bytes");
  std::ifstream source(input_path, std::ios::binary);
  if (!source) {
    event("diagnostic_input_error", "{\"reason\":\"could not open regenerated input\"}");
    return 2;
  }
  std::vector<unsigned char> encoded((std::istreambuf_iterator<char>(source)), std::istreambuf_iterator<char>());
  source.close();
  event("input_bytes_loaded", "{\"bytes\":" + std::to_string(encoded.size()) + "}");
  observe_dpx_header(encoded);

  // Reader lifetime, empty config and memory-read sequence match the pinned
  // Blender get_oiio_reader/imb_oiio_read path. File I/O is an explicit comparator.
  OIIO::Filesystem::IOMemReader memory_reader(OIIO::cspan<unsigned char>(encoded.data(), encoded.size()));
  OIIO::ImageSpec config, newspec;
  stage("ImageInput_create_before");
  auto input = OIIO::ImageInput::create("dpx");
  if (!input) {
    return backend_false(nullptr);
  }
  stage("ImageInput_create_returned");
  stage("valid_file_before");
  const bool valid = route == "memory" ? input->valid_file(&memory_reader) : input->valid_file(input_path);
  if (!valid) {
    return backend_false(input.get());
  }
  stage("valid_file_returned");
  if (route == "memory") {
    stage("set_ioproxy_before");
    const bool proxy_result = input->set_ioproxy(&memory_reader);
    event("set_ioproxy_returned", std::string("{\"return_value\":") + (proxy_result ? "true}" : "false}"));
    // The original Blender code does not branch on this returned boolean.
  }
  stage("open_before");
  const bool opened = input->open(route == "memory" ? "" : input_path, newspec, config);
  if (!opened) {
    return backend_false(input.get());
  }
  stage("open_returned");

  const OIIO::ImageSpec &spec = input->spec();
  const int width = spec.width, height = spec.height;
  const int channels = std::min(spec.nchannels, 4);
  const bool is_float = spec.format.basesize() > 1;
  event("opened_specification", "{\"width\":" + std::to_string(width) +
        ",\"height\":" + std::to_string(height) + ",\"depth\":" + std::to_string(spec.depth) +
        ",\"channels\":" + std::to_string(spec.nchannels) +
        ",\"read_channels\":" + std::to_string(channels) +
        ",\"base_type\":" + std::to_string(int(spec.format.basetype)) +
        ",\"base_size\":" + std::to_string(spec.format.basesize()) +
        ",\"alpha_channel\":" + std::to_string(spec.alpha_channel) + "}");
  if (width != 32 || height != 32 || spec.depth != 1 || channels != 4) {
    event("diagnostic_input_shape_differs", "{\"reason\":\"regenerated input does not have the planned original shape\"}");
    return 2;
  }

  const OIIO::stride_t xstride = (is_float ? sizeof(float) : sizeof(unsigned char)) * 4;
  const OIIO::stride_t ystride = xstride * width;
  const size_t storage_bytes = size_t(ystride) * size_t(height);
  // Match the original uninitialized pixel allocation before read_image.
  std::unique_ptr<unsigned char[]> pixels(new unsigned char[storage_bytes]);
  void *bottom_row = pixels.get() + (OIIO::stride_t(height) - 1) * ystride;
  const OIIO::TypeDesc format = is_float ? OIIO::TypeDesc::FLOAT : OIIO::TypeDesc::UINT8;
  event("read_parameters", "{\"subimage\":0,\"miplevel\":0,\"channel_begin\":0,\"channel_end\":" +
        std::to_string(channels) + ",\"is_float\":" + (is_float ? "true" : "false") +
        ",\"xstride\":" + std::to_string(xstride) + ",\"ystride\":" + std::to_string(-ystride) +
        ",\"zstride\":\"AutoStride\",\"destination_offset\":" + std::to_string((height - 1) * ystride) +
        ",\"storage_bytes\":" + std::to_string(storage_bytes) + "}");
  stage("read_image_before");
  const bool read = input->read_image(0, 0, 0, channels, format, bottom_row, xstride, -ystride, OIIO::AutoStride);
  if (!read) {
    return backend_false(input.get());
  }
  stage("read_image_returned");
  std::ofstream output(output_path, std::ios::binary | std::ios::trunc);
  output.write(reinterpret_cast<const char *>(pixels.get()), std::streamsize(storage_bytes));
  output.close();
  if (!output) {
    event("diagnostic_output_error");
    return 2;
  }
  stage("reader_destructor_before");
  input.reset();
  stage("reader_destructor_returned");
  event("standalone_operation_completed", "{\"output_path\":" + quote(output_path) +
        ",\"output_bytes\":" + std::to_string(storage_bytes) + "}");
  return 0;
}
}  // namespace

int main(int argc, char **argv)
{
  try {
    return execute(argc, argv);
  }
  catch (const std::exception &error) {
    event("caught_std_exception", "{\"typeid_name\":" + quote(typeid(error).name()) +
          ",\"what\":" + quote(error.what()) + "}");
    return 3;
  }
  catch (...) {
    event("caught_unknown_cpp_exception", "{\"native_type_and_message\":null}");
    return 4;
  }
}
