#pragma once

#include <filesystem>
#include <chrono>

// path 无法识别空文件名的后缀
std::filesystem::path generate_norepeat(std::filesystem::path path);

// unix timestamp to file time
inline std::filesystem::file_time_type ut2ft(std::time_t timet) {
	using namespace std::filesystem;
	using namespace std::chrono;
	file_time_type::duration ft(__std_fs_file_time_epoch_adjustment);
	ft += seconds(timet);
	return file_time_type(ft);
}