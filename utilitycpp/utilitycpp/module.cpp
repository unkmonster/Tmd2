#include "pch.h"

#include <pybind11/pybind11.h>
#include <pybind11/embed.h>
#include <pybind11/stl.h>
#include <cpr/cpr.h>
#include <spdlog/spdlog.h>
#include <fmt/format.h>

#include "utility.h"
#include "ThreadPool.h"

namespace py = pybind11;

extern std::atomic_flag gRunning;

struct Tweet {
	Tweet() = default;
	Tweet(const std::string& text_, const std::vector<std::string>& urls_, const std::string& created_at_):
		text(text_), 
		urls(urls_), 
		created_at(created_at_) 
	{}
	
	std::string text;
	std::vector<std::string> urls;
	std::string created_at;
};

std::time_t download(const std::vector<Tweet>& tweets, const std::string& user_path) {
	if (!gRunning.test_and_set()) {
		PyErr_SetInterrupt();
		throw py::error_already_set();
	}
	std::vector<Tweet> fails;
	std::mutex mtx, file_mtx;
	std::atomic<int> count = 1;
	std::time_t latest{};

	auto block_handler = [&](
		const Tweet* tweet
	)->std::time_t {
		std::time_t result{};
		std::unique_ptr<Tweet> failure;

		auto file_path = std::filesystem::path(user_path) / (tweet->text.size()? tweet->text : "null");
		for (const auto &u : tweet->urls) {
			// Get suffix from url
			auto extension = std::filesystem::path(u).extension().string();
			if (auto idx = extension.rfind('?'); idx != std::string::npos)
				extension.erase(idx);
			file_path.replace_extension(extension);
			
			std::unique_lock guard(file_mtx);
			file_path = GenerateUniqueFileName(file_path);
			std::ofstream of(file_path, std::ios::binary);
			guard.unlock();
			if (!of) {
				spdlog::warn("Failed to open {}", file_path.string());
				continue;
			}

			// 尝试 5 次
			for (int i = 0; i < 5; ++i) {
				std::this_thread::sleep_for(std::chrono::seconds(static_cast<long long>(pow(2, i) * 0.1)));

				auto res = cpr::Download(of, cpr::Url(u));
				if (res.status_code == 200) {
					std::vector<std::filesystem::path> shortPath;
					for (auto it = file_path.begin(); it != file_path.end(); ++it) {
						if (shortPath.size() == 3) {
							shortPath[0] = shortPath[1];
							shortPath[1] = shortPath[2];
							shortPath.resize(2);
						}
						shortPath.push_back(*it);
					}
					fmt::print("<{}/{}> {}\n", count.load(), tweets.size(), (shortPath[0] / shortPath[1] / shortPath[2]).string());
					// 将文件创建日期设为推文发布日期
					of.close();
					auto cmd = fmt::format(R"(python src\strptime.py "{}" "{}")", tweet->created_at, "%a %b %d %H:%M:%S %z %Y");
					result = system(cmd.c_str());
					std::filesystem::last_write_time(file_path, ut2ft(result));	// UTC+8
					break;
				} else {
					//spdlog::warn("[{}] {} {}", i, res.error? res.error.message: res.status_line, res.url.c_str());
					if (i == 4) {
						of.close();
						std::error_code ec;
						std::filesystem::remove(file_path, ec);
						if (ec)
							spdlog::warn("{} {}", ec.category().name(), ec.message());
						if (failure == nullptr)
							failure.reset(new Tweet(tweet->text, {}, tweet->created_at));
						failure->urls.emplace_back(u);
					}	
				}
			}
		}
		if (failure) {
			std::lock_guard<std::mutex> lock(mtx);
			fails.emplace_back(std::move(*failure));
		}
		++count;
		return result;
	};

	auto cpuCount = std::thread::hardware_concurrency();
	ThreadPool tp(cpuCount? tweets.size(): std::min<std::size_t>(cpuCount, tweets.size()));
	
	std::vector<std::future<std::time_t>> results;
	for (const auto& x : tweets) {
		auto f = tp.submit(block_handler, &x);
		results.emplace_back(std::move(f));
	}
		
	for (auto& x : results) {
		try {
			latest = std::max(x.get(), latest);
		} catch (const std::exception& exp) {
			spdlog::warn(exp.what());
		}
	}

	if (!fails.empty()) {
		auto fails_path = std::filesystem::path(user_path) / "fails.txt";
		std::ofstream ofs(fails_path);
		if (ofs.is_open()) {
			for (const auto& x : fails) {
				ofs << x.text << std::endl << x.created_at << std::endl;
				for (const auto& u : x.urls)
					ofs << "\t" << u << std::endl;
			}
			ofs.close();
		}
		system(fmt::format("type \"{}\"", fails_path.string()).c_str());
	}
	return latest;
}

PYBIND11_MODULE(utilitycpp, m) {
	py::class_<Tweet>(m, "Tweet")
		.def(py::init<const std::string&, const std::vector<std::string>&, const std::string&>())
		.def_readwrite("text", &Tweet::text)
		.def_readwrite("urls", &Tweet::urls)
		.def_readwrite("created_at", &Tweet::created_at);
	m.def("cdownload", &download);
}