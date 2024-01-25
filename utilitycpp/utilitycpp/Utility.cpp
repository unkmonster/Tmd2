#include "pch.h"
#include "utility.h"

#include <fmt/format.h>

std::filesystem::path generate_norepeat(std::filesystem::path path) {
	// ������չ��
	auto extension = path.extension();

	while (std::filesystem::exists(path)) {
		auto filename = path.stem().string();	// �޺�׺���ļ���

		if (filename.back() == ')' && filename.rfind('(') != std::string::npos) {
			// ��ȡ��������
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