#pragma once

#include <spdlog/spdlog.h>

#include "TSQueue.h"

class ThreadPool {
	class FuncBase {
	public:
		virtual ~FuncBase() = default;
		virtual void call() = 0;
	};

	template <typename T>
	class FuncWrapper : public FuncBase {
	public:
		FuncWrapper(std::packaged_task<T()>&& func) : m_func(std::move(func)) {}
		void call() override { m_func(); }
	private:
		std::packaged_task<T()> m_func;
	};
public:
	ThreadPool(std::size_t numThreads) : m_numThreads(numThreads), m_done(false) {
		try {
			for (int i = 0; i < numThreads; ++i)
				m_threads.emplace_back(&ThreadPool::work, this);
		} catch (...) {
			m_done = true;
			throw;
		}
	}

	~ThreadPool() {
		m_done = true;
		for (auto& x : m_threads) {
			if (x.joinable())
				x.join();
		}
		spdlog::debug("shutdown");
	}

	template<typename Func, typename... Args>
	auto submit(Func func, Args&&... args) {
		auto binded = std::bind(func, std::forward<Args>(args)...);
		using result_t = std::invoke_result_t<decltype(binded)>;

		std::packaged_task<result_t()> task(binded);
		auto future = task.get_future();

		std::unique_ptr<FuncBase> ptr(new FuncWrapper<result_t>(std::move(task)));
		m_tasks.push(std::move(ptr));
		return future;
	}
private:
	std::size_t m_numThreads;
	std::atomic_bool m_done;
	TSQueue2<std::unique_ptr<FuncBase>> m_tasks;
	std::vector<std::thread> m_threads;

	void work() {
		while (!m_done) {
			auto task = m_tasks.try_pop();
			if (!task)
				std::this_thread::yield();
			else
				(*task)->call();
		}
	}
};