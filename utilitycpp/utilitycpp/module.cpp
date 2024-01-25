#include "pch.h"

#include <atomic>

#include <pybind11/pybind11.h>
#include <pybind11/embed.h>
#include <pybind11/stl.h>
#include <cpr/cpr.h>
#include <spdlog/spdlog.h>

#include "utility.h"
#include "ThreadPool.h"

namespace py = pybind11;

struct Tweet {
	Tweet(const std::string& text_, const std::vector<std::string>& urls_, const std::string& created_at_):
		text(text_), 
		urls(urls_), 
		created_at(created_at_) 
	{}
	
	std::string text;
	std::vector<std::string> urls;
	std::string created_at;
};

extern std::atomic_flag running;

std::time_t download(const std::vector<Tweet>& tweets, const std::string& user_path) {
	if (!running.test_and_set()) {
		PyErr_SetInterrupt();
		throw py::error_already_set();
	}
	std::vector<Tweet> fails;
	std::mutex mtx, file_mtx;
	std::atomic<int> count;
	std::time_t latest{};

	auto block_handler = [&](
		const Tweet* tweet
	)->std::time_t {
		auto cmd = fmt::format(R"(python src\strptime.py "{}" "{}")", tweet->created_at, "%a %b %d %H:%M:%S %z %Y");
		auto created_at = system(cmd.c_str());

		auto file_path = std::filesystem::path(user_path) / (tweet->text.size()? tweet->text : "null");
		for (const auto &u : tweet->urls) {
			// 从 url 获取扩展名
			auto extension = std::filesystem::path(u).extension().string();
			// 擦除 url 参数
			if (auto idx = extension.rfind('?'); idx != std::string::npos)
				extension.erase(idx);

			file_path.replace_extension(extension);
			std::unique_lock<std::mutex> ul(file_mtx);
			if (std::filesystem::exists(file_path)) {
				file_path = generate_norepeat(file_path);
			}
			ul.unlock();
				
			std::ofstream of(file_path, std::ios::binary);
			if (!of) {
				spdlog::warn("Failed to open {}", file_path.string());
				continue;
			}

			// 尝试 5 次
			for (int i = 0; i < 5; ++i) {
				std::this_thread::sleep_for(std::chrono::seconds(static_cast<long long>(pow(2, i) * 0.1)));

				auto res = cpr::Download(
					of,
					cpr::Url(u)
				);
					
				if (res.status_code == 200) {
					std::cout << file_path.string().append("\n") << std::flush;
					// 将文件创建日期设为推文发布日期
					of.close();
					std::filesystem::last_write_time(file_path, ut2ft(created_at));	// UTC+8
					break;
				} else {
					spdlog::warn("[{}] {} {}", i, res.error? res.error.message: res.status_line, res.url.c_str());
					if (i == 4) {
						of.close();
						std::error_code ec;
						std::filesystem::remove(file_path, ec);
						if (ec)
							spdlog::warn("{} {}", ec.category().name(), ec.message());
						std::lock_guard<std::mutex> lock(mtx);
						fails.push_back(*tweet);
						return 0;
					}	
				}
			}
		}
		return created_at;
	};


	std::size_t threads_cnt = std::min<std::size_t>(tweets.size(), static_cast<std::size_t>(std::thread::hardware_concurrency()) * 2ul);
	if (!threads_cnt) threads_cnt = tweets.size();

	ThreadPool tp(threads_cnt);
	std::vector<std::future<std::time_t>> results;

	// 提交任务
	for (const auto& x : tweets) {
		auto f = tp.submit(block_handler, &x);
		results.push_back(std::move(f));
	}
		
	for (auto& x : results) {
		try {
			latest = std::max(x.get(), latest);
		} catch (const std::exception& exp) {
			spdlog::warn(exp.what());
		}
	}

	for (const auto& x : fails)
		spdlog::error(x.text);
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