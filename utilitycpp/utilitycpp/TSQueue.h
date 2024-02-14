#pragma once

template <typename T>
class TSQueue2 {
public:
	TSQueue2() : head(std::make_unique<Node>()), tail(head.get()) {}
	TSQueue2(const TSQueue2&) = delete;
	TSQueue2& operator=(const TSQueue2&) = delete;

	void push(T val);
	std::shared_ptr<T> try_pop();
	std::shared_ptr<T> wait_and_pop();
	bool empty() const;
private:
	struct Node {
		std::shared_ptr<T> data;
		std::unique_ptr<Node> next;
	};
	std::unique_ptr<Node> head;
	mutable std::mutex head_mtx;
	std::add_pointer_t<Node> tail;	// 超尾节点
	mutable std::mutex tail_mtx;
	std::condition_variable data_cv;
private:
	Node* get_tail() const {
		std::lock_guard<std::mutex> lg(tail_mtx);
		return tail;
	}
};

template<typename T>
inline void TSQueue2<T>::push(T val) {
	auto data_to_push = std::make_shared<T>(std::move(val));
	auto new_tail = std::make_unique<Node>();	// 新的虚拟节点
	{
		std::lock_guard<std::mutex> tail_lock(tail_mtx);
		tail->data = data_to_push;
		tail->next = std::move(new_tail);
		tail = tail->next.get();
	}
	data_cv.notify_one();	// 这里也没搞懂，为什么要先解锁再 notify_one
}

template<typename T>
inline std::shared_ptr<T> TSQueue2<T>::try_pop() {
	// 这里暂时没搞懂，为什么一定要先锁住 head_mtx
	std::lock_guard<std::mutex> head_lock(head_mtx);
	if (get_tail() == head.get())
		return nullptr;

	auto old_head = std::move(head);
	head = std::move(old_head->next);
	return old_head->data;
}

template<typename T>
inline std::shared_ptr<T> TSQueue2<T>::wait_and_pop() {
	std::unique_lock<std::mutex> head_lock(head_mtx);
	data_cv.wait(head_lock, [this]() {return head.get() != get_tail(); });
	auto old_head = std::move(head);
	head = std::move(old_head->next);
	return old_head->data;
}

template<typename T>
inline bool TSQueue2<T>::empty() const {
	std::lock_guard<std::mutex> head_lock(head_mtx);
	return  get_tail() == head.get();
}
