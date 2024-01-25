#include "pch.h"
#include "utility.h"

#include <fmt/format.h>

std::filesystem::path generate_norepeat(std::filesystem::path path) {
	// 保存扩展名
	auto extension = path.extension();

	while (std::filesystem::exists(path)) {
		auto filename = path.stem().string();	// 无后缀的文件名

		if (filename.back() == ')' && filename.rfind('(') != std::string::npos) {
			// 获取括号索引
			auto l = filename.rfind('(');
			auto r = filename.size() - 1;
			try {
				auto num = std::stoi(filename.substr(l + 1, r - l - 1)) + 1;
				filename = fmt::format("{}({})", filename.erase(l), num);
				path.replace_filename(filename).replace_extension(extension);
				continue;
			} catch (const std::invalid_argument&) {}
		}

		filename += " (1)";
		path.replace_filename(filename).replace_extension(extension);
	}
	return path;
}