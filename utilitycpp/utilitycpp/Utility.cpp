#include "pch.h"

#include <cmath>

#include "utility.h"

#include <fmt/format.h>
#include <cpr/cpr.h>

std::filesystem::path GenerateUniqueFileName(std::filesystem::path path) {
	// eg. filename (1).txt
	auto extension = path.extension();		// save suffix
	while (std::filesystem::exists(path)) {
		auto filename = path.stem().string();		// file name without suffix
		if (filename.back() == ')' && filename.rfind('(') != std::string::npos) {
			// 获取括号索引
			auto l = filename.rfind('(');
			auto r = filename.size() - 1;
			try {
				auto num = std::stoi(filename.substr(l + 1, r - (l + 1))) + 1;
				filename = fmt::format("{} ({})", filename.erase(l-1), num);
				path.replace_filename(filename).replace_extension(extension);
				continue;
			} catch (const std::invalid_argument&) {}
		}
		filename += " (1)";
		path.replace_filename(filename).replace_extension(extension);
	}
	return path;
}

bool MTDownload(std::filesystem::path url, std::ofstream& ofs, ThreadPool& tp) {
	if (!ofs.is_open()) return false;

	constexpr uint32_t block_size = 512u * 1024u * sizeof BYTE;
	uint32_t content_length{};
	bool accept_range{};
	cpr::Response resp{};

	resp = cpr::Head(
		cpr::Url(url.string())
	);
	if (resp.status_code != 200) 
		return false;

	content_length = std::stoul(resp.header["Content-Length"]);
	accept_range = ((resp.header.find("Accept-Ranges") != resp.header.end())/* && (resp.header["Accept-Ranges"] == "Bytes")*/);
	
	if (!accept_range) {
		resp = cpr::Download(
			ofs,
			cpr::Url(url.string())
		);
		return resp.status_code == 200;
	}
	
	// 确认启动线程数
	auto hardware_threads = std::thread::hardware_concurrency();
	uint32_t num_threads = floor(content_length / static_cast<double>(block_size));
	if (hardware_threads) num_threads = std::min(num_threads, hardware_threads);
		
	uint32_t begin{}, end{};
	std::vector<cpr::AsyncResponse> responses;
	for (int i = 0; i < num_threads - 1; ++i) {
		end = begin + block_size - 1;
		auto resp = cpr::GetAsync(
			cpr::Url(url.string()),
			cpr::Range(begin, end)
		);
		begin = end + 1;
		responses.emplace_back(std::move(resp));
	}
	// the Last Block
	resp = cpr::Get(
		cpr::Url(url.string()),
		cpr::Range(begin, std::nullopt)
	);
	if (resp.status_code != 200 && resp.status_code != 206)
		return false;

	for (auto& x : responses) {
		auto r = x.get();
		if (r.status_code != 200 && r.status_code != 206)
			return false;
		ofs.write(r.text.c_str(), r.downloaded_bytes);
	}
	ofs.write(resp.text.c_str(), resp.downloaded_bytes);
	return true;
}
